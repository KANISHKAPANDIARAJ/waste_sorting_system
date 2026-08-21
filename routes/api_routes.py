from flask import Blueprint, request, jsonify, current_app
from werkzeug.utils import secure_filename
import os
import uuid
from datetime import datetime

from models.database import db
from models.device import Device
from models.bin import Bin
from models.detection import Detection
from models.sensor_reading import SensorReading
from models.alert import Alert
from models.sorting_action import SortingAction

from services.device_service import register_heartbeat, get_device_uptime_string
from services.classification_service import classify_waste_image
from services.sorting_service import process_sorting_decision
from services.analytics_service import get_dashboard_kpis, get_waste_overview_data, get_detailed_analytics_data
from services.alert_service import mark_alert_as_read, mark_all_alerts_as_read, create_alert
from services.realtime_service import socketio

# Create blueprint
api_bp = Blueprint('api', __name__)

def allowed_file(filename):
    """Checks if a file extension is in the allowed set."""
    allowed = current_app.config.get('ALLOWED_EXTENSIONS', {'png', 'jpg', 'jpeg', 'webp'})
    return '.' in filename and filename.rsplit('.', 1)[1].lower() in allowed

# --- DEVICE telemetries & heartbeats ---

@api_bp.route('/device/heartbeat', methods=['POST'])
def device_heartbeat():
    """
    Heartbeat endpoint for IoT devices.
    Expected payload: { "device_id": "SIM-001", "firmware_version": "v1.0.0", "device_name": "Main Conveyor", "location": "Line A" }
    """
    data = request.get_json() or {}
    device_id = data.get('device_id')
    
    if not device_id:
        return jsonify({'error': 'device_id is required'}), 400
        
    device = register_heartbeat(
        device_id=device_id,
        device_name=data.get('device_name'),
        location=data.get('location'),
        firmware_version=data.get('firmware_version')
    )
    
    if not device:
        return jsonify({'error': 'Failed to process heartbeat'}), 500
        
    return jsonify({
        'status': 'success',
        'message': f'Heartbeat registered for {device_id}',
        'device': device.to_dict()
    }), 200

@api_bp.route('/device/data', methods=['POST'])
def device_data():
    """
    Telemetry endpoint for sensor data (moisture, weight, temperature, fill levels).
    Expected payload:
    {
       "device_id": "SIM-001",
       "sensor_data": {
           "weight": 120.0,
           "moisture": 30.5,
           "temperature": 28.2
       }
    }
    """
    data = request.get_json() or {}
    device_id = data.get('device_id')
    sensor_data = data.get('sensor_data', {})
    
    if not device_id:
        return jsonify({'error': 'device_id is required'}), 400
        
    # Register heartbeat first to keep device status ONLINE
    register_heartbeat(device_id)
    
    saved_readings = []
    units = {
        'weight': 'g',
        'moisture': '%',
        'temperature': '°C',
        'fill_level': '%'
    }
    
    # Save each reading to the database
    for sensor_type, value in sensor_data.items():
        unit = units.get(sensor_type, '')
        reading = SensorReading(
            device_id=device_id,
            sensor_type=sensor_type,
            value=float(value),
            unit=unit,
            timestamp=datetime.utcnow()
        )
        db.session.add(reading)
        saved_readings.append(reading)
        
    try:
        db.session.commit()
        
        # Broadcast real-time sensor updates
        dict_readings = {r.sensor_type: {'value': r.value, 'unit': r.unit} for r in saved_readings}
        socketio.emit('sensor_data', {
            'device_id': device_id,
            'timestamp': datetime.utcnow().isoformat(),
            'readings': dict_readings
        })
        
        # Check abnormal reading limits
        temp_val = sensor_data.get('temperature')
        if temp_val and float(temp_val) > 45.0:
            create_alert(
                alert_type="abnormal_reading",
                severity="WARNING",
                message=f"High temperature warning: {temp_val}°C detected on {device_id}.",
                device_id=device_id
            )
            
        return jsonify({
            'status': 'success',
            'message': f'Stored {len(saved_readings)} sensor readings',
            'readings': [r.to_dict() for r in saved_readings]
        }), 201
        
    except Exception as e:
        db.session.rollback()
        return jsonify({'error': f'Failed to store telemetry: {str(e)}'}), 500

@api_bp.route('/device/status', methods=['GET'])
def device_status():
    """Retrieve current status and metadata of active devices."""
    devices = Device.query.all()
    return jsonify([d.to_dict() for d in devices]), 200

# --- BINS STATUS ---

@api_bp.route('/bins', methods=['GET'])
def get_bins():
    """Retrieve levels and health of all waste sorting bins."""
    bins = Bin.query.all()
    return jsonify([b.to_dict() for b in bins]), 200

@api_bp.route('/bins/<int:bin_id>', methods=['PUT'])
def update_bin(bin_id):
    """Manually update bin parameters (e.g. empty the bin)."""
    bin_obj = Bin.query.get_or_404(bin_id)
    data = request.get_json() or {}
    
    if 'current_level' in data:
        bin_obj.current_level = float(data.get('current_level'))
        if bin_obj.current_level < 0:
            bin_obj.current_level = 0
            
        # Recalculate status based on new level
        fill_pct = bin_obj.fill_percentage
        warning_t = current_app.config.get('BIN_WARNING_THRESHOLD', 70.0)
        full_t = current_app.config.get('BIN_FULL_THRESHOLD', 90.0)
        
        if fill_pct >= full_t:
            bin_obj.status = "FULL"
        elif fill_pct >= warning_t:
            bin_obj.status = "WARNING"
        else:
            bin_obj.status = "NORMAL"
            
    if 'capacity' in data:
        bin_obj.capacity = float(data.get('capacity'))
        
    bin_obj.updated_at = datetime.utcnow()
    
    try:
        db.session.commit()
        # Broadcast update
        socketio.emit('bin_updated', bin_obj.to_dict())
        # Broadcast recalculated stats
        socketio.emit('statistics_updated', get_dashboard_kpis())
        
        return jsonify({
            'status': 'success',
            'message': f'Bin {bin_obj.bin_name} updated successfully',
            'bin': bin_obj.to_dict()
        }), 200
    except Exception as e:
        db.session.rollback()
        return jsonify({'error': str(e)}), 500

# --- CLASSIFICATION & DETECTION ---

@api_bp.route('/classify', methods=['POST'])
def classify_only():
    """
    Direct image prediction endpoint.
    Accepts an uploaded image file, processes it, and returns prediction
    category and confidence WITHOUT saving results to database or altering bin levels.
    """
    if 'file' not in request.files:
        return jsonify({'error': 'No file part in the request'}), 400
        
    file = request.files['file']
    if file.filename == '':
        return jsonify({'error': 'No file selected for uploading'}), 400
        
    if not allowed_file(file.filename):
        return jsonify({'error': 'Invalid image format. Allowed: PNG, JPG, JPEG, WEBP'}), 400
        
    # Temporary save
    temp_filename = f"temp_{uuid.uuid4().hex}_{secure_filename(file.filename)}"
    temp_dir = os.path.join(current_app.config.get('UPLOAD_FOLDER'), 'temp')
    os.makedirs(temp_dir, exist_ok=True)
    temp_path = os.path.join(temp_dir, temp_filename)
    
    try:
        file.save(temp_path)
        # Classify
        result = classify_waste_image(temp_path)
        return jsonify(result), 200
    except Exception as e:
        return jsonify({'error': f'Classification failed: {str(e)}'}), 500
    finally:
        # Clean up temp file
        if os.path.exists(temp_path):
            os.remove(temp_path)

@api_bp.route('/detection', methods=['POST'])
def detection_upload():
    """
    Submit image for complete processing:
    Image Upload -> Validation -> Classification -> Sorting Rule Decision -> Bin Update -> DB Save -> Socket Broadcast.
    """
    from flask import session
    from PIL import Image
    
    # Source is explicit so demo/simulator records cannot be confused with
    # normal user uploads.
    source = request.form.get('source', 'USER_UPLOAD').upper()
    if source not in {'USER_UPLOAD', 'SIMULATOR'}:
        source = 'USER_UPLOAD'
    device_id = request.form.get('device_id', current_app.config.get('DEVICE_ID', 'SIM-001'))
    
    # 1. Handle image upload or manual classification parameters
    if 'file' in request.files:
        file = request.files['file']
        if file.filename == '':
            return jsonify({'error': 'Empty filename uploaded'}), 400
            
        if not allowed_file(file.filename):
            return jsonify({'error': 'Unsupported file extension. Allowed: PNG, JPG, JPEG, WEBP'}), 400
            
        # Validate MIME type
        if file.content_type and not file.content_type.startswith('image/'):
            return jsonify({'error': 'Invalid MIME type. Upload must be an image.'}), 400
            
        # Validate file size (16MB max)
        file.seek(0, 2)
        file_size = file.tell()
        file.seek(0)
        if file_size > 16 * 1024 * 1024:
            return jsonify({'error': 'File size exceeds 16MB limit.'}), 400
            
        # Validate corrupted image
        try:
            img = Image.open(file)
            img.verify()
            file.seek(0)
        except Exception:
            return jsonify({'error': 'Uploaded image file is corrupted or unreadable.'}), 400
            
        # Secure and save uploaded image
        unique_fn = f"{datetime.utcnow().strftime('%Y%m%d%H%M%S')}_{uuid.uuid4().hex[:6]}_{secure_filename(file.filename)}"
        upload_dir = current_app.config.get('UPLOAD_FOLDER')
        os.makedirs(upload_dir, exist_ok=True)
        img_path = os.path.join(upload_dir, unique_fn)
        file.save(img_path)
        
        # Save relative path for display in dashboard
        relative_img_path = os.path.join('uploads/waste', unique_fn).replace('\\', '/')
        
        # 2. Run Classification Pipeline
        classification = classify_waste_image(img_path)
        material = classification['material']
        confidence = classification['confidence']
        proc_time = classification['processing_time']
        model_ver = classification['model_version']
        
    elif request.is_json:
        # Fallback to direct parameters (e.g. from a simulator reporting pre-processed detections)
        data = request.get_json() or {}
        device_id = data.get('device_id', device_id)
        source = data.get('source', 'SIMULATOR')
        material = data.get('material')
        confidence = float(data.get('confidence', 1.0))
        proc_time = float(data.get('processing_time', 0.05))
        model_ver = data.get('model_version', 'v1.0')
        relative_img_path = data.get('image_path')
        
        if not material:
            return jsonify({'error': 'material parameter is required'}), 400
    else:
        return jsonify({'error': 'No file uploaded or JSON payload provided'}), 400

    # 3. Register device heartbeat
    register_heartbeat(device_id)

    # 4. Trigger Sorting Service
    detection = process_sorting_decision(
        device_id=device_id,
        material=material,
        confidence=confidence,
        processing_time=proc_time,
        image_path=relative_img_path,
        model_version=model_ver,
        source=source
    )
    
    if not detection:
        return jsonify({'error': 'Error executing sorting engine'}), 500
        
    # Store user upload detection ID in session
    if source == 'USER_UPLOAD':
        session['latest_detection_id'] = detection.id
        session.modified = True
        
    return jsonify({
        'status': 'success',
        'message': 'Waste processed successfully',
        'detection': detection.to_dict()
    }), 201

@api_bp.route('/detections', methods=['GET'])
def get_detections():
    """Query and filter database detection history records."""
    material_filter = request.args.get('material')
    status_filter = request.args.get('status')
    limit = request.args.get('limit', 50, type=int)
    
    query = Detection.query
    if material_filter:
        query = query.filter_by(material=material_filter)
    if status_filter:
        query = query.filter_by(sorting_status=status_filter)
        
    results = query.order_by(Detection.timestamp.desc()).limit(limit).all()
    return jsonify([d.to_dict() for d in results]), 200

# --- ANALYTICS ---

@api_bp.route('/analytics', methods=['GET'])
def get_analytics():
    """Retrieve detailed charts series and aggregated operational data."""
    period = request.args.get('period', 'today')
    overview_chart = get_waste_overview_data(period)
    detailed_stats = get_detailed_analytics_data()
    
    return jsonify({
        'chart_data': overview_chart,
        'detailed_stats': detailed_stats
    }), 200

# --- ALERTS CONTROLS ---

@api_bp.route('/alerts/read', methods=['POST'])
def mark_alerts_read():
    """Mark alert events as read by operator."""
    data = request.get_json() or {}
    alert_id = data.get('alert_id')
    
    if alert_id:
        success = mark_alert_as_read(alert_id)
    else:
        success = mark_all_alerts_as_read()
        
    if not success:
        return jsonify({'error': 'Failed to update alerts'}), 500
        
    return jsonify({'status': 'success', 'message': 'Alerts updated'}), 200

# --- SIMULATOR WEB CONTROLS ---

# Global variable to track the simulator instance running within the server process
flask_simulator = None

@api_bp.route('/simulator/start', methods=['POST'])
def start_simulator_web():
    global flask_simulator
    if flask_simulator and flask_simulator.running:
        return jsonify({'running': True, 'message': 'Simulator already running'}), 200
        
    upload_dir = current_app.config.get('UPLOAD_FOLDER')
    samples_dir = os.path.join(upload_dir, 'train_samples')
    interval = current_app.config.get('SIMULATOR_INTERVAL', 5)
    device_id = current_app.config.get('DEVICE_ID', 'SIM-001')
    
    from iot.simulator import IoTSimulator
    flask_simulator = IoTSimulator(
        device_id=device_id,
        base_url='http://127.0.0.1:5000',
        interval=interval,
        samples_dir=samples_dir
    )
    flask_simulator.start()
    return jsonify({'running': True, 'message': 'IoT Simulator started'}), 200

@api_bp.route('/simulator/stop', methods=['POST'])
def stop_simulator_web():
    global flask_simulator
    if not flask_simulator or not flask_simulator.running:
        return jsonify({'running': False, 'message': 'Simulator not running'}), 200
        
    flask_simulator.stop()
    flask_simulator = None
    return jsonify({'running': False, 'message': 'IoT Simulator stopped'}), 200

@api_bp.route('/simulator/status', methods=['GET'])
def get_simulator_web_status():
    global flask_simulator
    is_running = flask_simulator.running if flask_simulator else False
    return jsonify({'running': is_running}), 200


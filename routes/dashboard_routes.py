from functools import wraps
from flask import Blueprint, render_template, redirect, url_for, request, session, flash, current_app
from models.user import User
from models.device import Device
from models.bin import Bin
from models.detection import Detection
from models.alert import Alert
from services.device_service import get_device_uptime_string
from services.analytics_service import get_dashboard_kpis
import os

# Create blueprint
dashboard_bp = Blueprint('dashboard', __name__)

def login_required(f):
    """Decorator to protect routes from unauthorized guest access."""
    @wraps(f)
    def decorated_function(*args, **kwargs):
        if 'user_id' not in session:
            flash("Please log in to access this page.", "warning")
            return redirect(url_for('dashboard.login'))
        return f(*args, **kwargs)
    return decorated_function

@dashboard_bp.route('/')
def index():
    """Redirect root to dashboard if logged in, otherwise to login."""
    if 'user_id' in session:
        return redirect(url_for('dashboard.dashboard_view'))
    return redirect(url_for('dashboard.login'))

@dashboard_bp.route('/login', methods=['GET', 'POST'])
def login():
    """Admin/operator authentication handler."""
    if 'user_id' in session:
        return redirect(url_for('dashboard.dashboard_view'))
        
    if request.method == 'POST':
        username = request.form.get('username')
        password = request.form.get('password')
        
        user = User.query.filter_by(username=username).first()
        if user and user.check_password(password):
            session['user_id'] = user.id
            session['username'] = user.username
            session['role'] = user.role
            flash("Welcome back, administrator!", "success")
            return redirect(url_for('dashboard.dashboard_view'))
        else:
            flash("Invalid username or password.", "danger")
            
    return render_template('login.html')

@dashboard_bp.route('/logout')
def logout():
    """Logs the user out of the session."""
    session.clear()
    flash("You have been logged out successfully.", "info")
    return redirect(url_for('dashboard.login'))

@dashboard_bp.route('/dashboard')
@login_required
def dashboard_view():
    """Renders the main industrial monitoring dashboard page."""
    # Fetch device status for SIM-001
    dev_id = current_app.config.get('DEVICE_ID', 'SIM-001')
    device = Device.query.filter_by(device_id=dev_id).first()
    
    # Get general KPIs
    kpis = get_dashboard_kpis()
    
    # Fetch bins
    bins = Bin.query.all()
    
    # Fetch latest 5 detections (only active uploads or simulator records, excluding seed DEMO)
    recent_detections = Detection.query.filter(Detection.source.in_(['USER_UPLOAD', 'SIMULATOR'])).order_by(Detection.timestamp.desc()).limit(5).all()
    
    # Fetch current user upload detection for Advanced CV panel (isolated from database historical queries)
    latest_det_id = session.get('latest_detection_id')
    current_detection = None
    if latest_det_id:
        current_detection = Detection.query.filter_by(
            id=latest_det_id,
            source='USER_UPLOAD'
        ).first()
    
    # Calculate uptime
    uptime_str = get_device_uptime_string(dev_id)
    
    # Count unread alerts
    unread_alert_count = Alert.query.filter_by(is_read=False).count()
    
    return render_template(
        'dashboard.html',
        device=device,
        kpis=kpis,
        bins=bins,
        recent_detections=recent_detections,
        current_detection=current_detection,
        uptime=uptime_str,
        unread_alerts=unread_alert_count
    )

@dashboard_bp.route('/live_monitoring')
@login_required
def live_monitoring_view():
    """Renders the real-time IoT device telemetry and streaming page."""
    dev_id = current_app.config.get('DEVICE_ID', 'SIM-001')
    device = Device.query.filter_by(device_id=dev_id).first()
    bins = Bin.query.all()
    uptime_str = get_device_uptime_string(dev_id)
    unread_alert_count = Alert.query.filter_by(is_read=False).count()
    
    # Fetch latest 10 detections (excluding seed DEMO)
    recent_detections = Detection.query.filter(Detection.source.in_(['USER_UPLOAD', 'SIMULATOR'])).order_by(Detection.timestamp.desc()).limit(10).all()
    
    return render_template(
        'live_monitoring.html',
        device=device,
        bins=bins,
        uptime=uptime_str,
        unread_alerts=unread_alert_count,
        recent_detections=recent_detections
    )

@dashboard_bp.route('/detections')
@login_required
def detections_view():
    """Renders the filterable detections search history page."""
    dev_id = current_app.config.get('DEVICE_ID', 'SIM-001')
    device = Device.query.filter_by(device_id=dev_id).first()
    uptime_str = get_device_uptime_string(dev_id)
    unread_alert_count = Alert.query.filter_by(is_read=False).count()
    
    # Pagination & Filtering parameters
    page = request.args.get('page', 1, type=int)
    material_filter = request.args.get('material', '')
    status_filter = request.args.get('status', '')
    min_confidence = request.args.get('confidence', 0.0, type=float)
    
    query = Detection.query
    if material_filter:
        query = query.filter_by(material=material_filter)
    if status_filter:
        query = query.filter_by(sorting_status=status_filter)
    if min_confidence > 0.0:
        query = query.filter(Detection.confidence >= min_confidence)
        
    pagination = query.order_by(Detection.timestamp.desc()).paginate(
        page=page, per_page=15, error_out=False
    )
    
    return render_template(
        'detections.html',
        device=device,
        pagination=pagination,
        material=material_filter,
        status=status_filter,
        confidence=min_confidence,
        uptime=uptime_str,
        unread_alerts=unread_alert_count
    )

@dashboard_bp.route('/bin_status')
@login_required
def bin_status_view():
    """Renders detailed metrics, capacities, and states for the waste streams."""
    dev_id = current_app.config.get('DEVICE_ID', 'SIM-001')
    device = Device.query.filter_by(device_id=dev_id).first()
    uptime_str = get_device_uptime_string(dev_id)
    unread_alert_count = Alert.query.filter_by(is_read=False).count()
    bins = Bin.query.all()
    
    return render_template(
        'bin_status.html',
        device=device,
        bins=bins,
        uptime=uptime_str,
        unread_alerts=unread_alert_count
    )

@dashboard_bp.route('/analytics')
@login_required
def analytics_view():
    """Renders comprehensive charts, summaries, and operation trends."""
    dev_id = current_app.config.get('DEVICE_ID', 'SIM-001')
    device = Device.query.filter_by(device_id=dev_id).first()
    uptime_str = get_device_uptime_string(dev_id)
    unread_alert_count = Alert.query.filter_by(is_read=False).count()
    
    return render_template(
        'analytics.html',
        device=device,
        uptime=uptime_str,
        unread_alerts=unread_alert_count
    )

@dashboard_bp.route('/alerts')
@login_required
def alerts_view():
    """Renders list of alerts generated by low confidence or bin warning conditions."""
    dev_id = current_app.config.get('DEVICE_ID', 'SIM-001')
    device = Device.query.filter_by(device_id=dev_id).first()
    uptime_str = get_device_uptime_string(dev_id)
    alerts = Alert.query.order_by(Alert.created_at.desc()).all()
    unread_alert_count = Alert.query.filter_by(is_read=False).count()
    
    return render_template(
        'alerts.html',
        device=device,
        alerts=alerts,
        uptime=uptime_str,
        unread_alerts=unread_alert_count
    )

@dashboard_bp.route('/settings', methods=['GET', 'POST'])
@login_required
def settings_view():
    """Manage classification thresholds, bin alerts limits, and simulated intervals."""
    dev_id = current_app.config.get('DEVICE_ID', 'SIM-001')
    device = Device.query.filter_by(device_id=dev_id).first()
    uptime_str = get_device_uptime_string(dev_id)
    unread_alert_count = Alert.query.filter_by(is_read=False).count()
    
    # Load environment settings currently active in app.config
    settings_data = {
        'classification_threshold': current_app.config.get('CLASSIFICATION_THRESHOLD'),
        'bin_warning_threshold': current_app.config.get('BIN_WARNING_THRESHOLD'),
        'bin_full_threshold': current_app.config.get('BIN_FULL_THRESHOLD'),
        'simulator_interval': current_app.config.get('SIMULATOR_INTERVAL'),
        'device_name': device.device_name if device else "Main Unit",
        'device_location': device.location if device else "Conveyor Line A"
    }

    if request.method == 'POST':
        # Update settings dynamically in app config (and optionally DB or file)
        try:
            current_app.config['CLASSIFICATION_THRESHOLD'] = float(request.form.get('classification_threshold'))
            current_app.config['BIN_WARNING_THRESHOLD'] = float(request.form.get('bin_warning_threshold'))
            current_app.config['BIN_FULL_THRESHOLD'] = float(request.form.get('bin_full_threshold'))
            current_app.config['SIMULATOR_INTERVAL'] = int(request.form.get('simulator_interval'))
            
            # Save device updates
            if device:
                device.device_name = request.form.get('device_name')
                device.location = request.form.get('device_location')
                db.session.commit()
                
            flash("System configuration updated successfully!", "success")
            return redirect(url_for('dashboard.settings_view'))
        except Exception as e:
            flash(f"Failed to update settings: {str(e)}", "danger")

    return render_template(
        'settings.html',
        device=device,
        settings=settings_data,
        uptime=uptime_str,
        unread_alerts=unread_alert_count
    )

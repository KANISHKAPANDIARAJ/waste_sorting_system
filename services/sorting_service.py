from datetime import datetime
from flask import current_app
from models.database import db
from models.detection import Detection
from models.bin import Bin
from models.sorting_action import SortingAction
from services.realtime_service import emit_new_detection, emit_bin_updated, emit_statistics_updated
from services.alert_service import create_alert

# Volume increments per waste category (in m³ assuming 10 m³ capacity)
INCREMENTS = {
    'Plastic': 0.20,  # 2.0%
    'Paper': 0.15,    # 1.5%
    'Metal': 0.20,    # 2.0%
    'Organic': 0.25,  # 2.5%
    'Other': 0.10     # 1.0%
}

def process_sorting_decision(device_id, material, confidence, processing_time, image_path=None, model_version="v1.0", source="USER_UPLOAD"):
    """
    Core business logic for sorting waste and updating status:
    1. Map material to the corresponding database bin.
    2. Check confidence threshold; flag if low.
    3. Update the assigned bin's fill level and check fill warnings/full alerts.
    4. Store detection and sorting action records.
    5. Emit WebSocket updates to dashboard clients.
    """
    # Load config threshold values
    conf_threshold = current_app.config.get('CLASSIFICATION_THRESHOLD', 0.70)
    warning_threshold = current_app.config.get('BIN_WARNING_THRESHOLD', 70.0)
    full_threshold = current_app.config.get('BIN_FULL_THRESHOLD', 90.0)
    
    # 1. Map category to bin by searching for bin associated with material type
    assigned_bin = Bin.query.filter_by(material_type=material).first()
    if not assigned_bin:
        # Fallback to Other/Reject Bin
        assigned_bin = Bin.query.filter_by(material_type='Other').first()
        if not assigned_bin:
            # Fallback to first bin if database is unseeded
            assigned_bin = Bin.query.first()
            
    bin_name = assigned_bin.bin_name if assigned_bin else "Other Bin"
    bin_id = assigned_bin.id if assigned_bin else 5
    
    # 2. Determine sorting status based on confidence
    action_type = "SORTED"
    status_label = "SORTED"
    
    if confidence < conf_threshold:
        action_type = "FLAGGED"
        status_label = "FLAGGED"
        # Trigger low confidence alert
        create_alert(
            alert_type="low_confidence",
            severity="WARNING",
            message=f"Low confidence classification ({confidence*100:.1f}%) for {material}. Diverting item.",
            device_id=device_id,
            bin_id=bin_id
        )
    
    # Create the Detection record
    detection = Detection(
        device_id=device_id,
        image_path=image_path,
        material=material,
        confidence=confidence,
        assigned_bin=bin_name,
        sorting_status=status_label,
        processing_time=processing_time,
        model_version=model_version,
        source=source,
        timestamp=datetime.utcnow()
    )
    
    db.session.add(detection)
    # Commit here to generate the detection.id
    try:
        db.session.commit()
    except Exception as e:
        db.session.rollback()
        print(f"Failed to save detection: {e}")
        return None
        
    # 3. Update bin fill levels if not failed/diverted
    if assigned_bin and status_label == "SORTED":
        old_level = assigned_bin.current_level
        old_status = assigned_bin.status
        increment = INCREMENTS.get(material, 0.10)
        
        # Increment level, capped at total capacity
        assigned_bin.current_level = min(assigned_bin.current_level + increment, assigned_bin.capacity)
        
        # Calculate new fill percentage
        fill_pct = assigned_bin.fill_percentage
        
        # Determine status
        if fill_pct >= full_threshold:
            assigned_bin.status = "FULL"
            if old_status != "FULL":
                create_alert(
                    alert_type="bin_full",
                    severity="CRITICAL",
                    message=f"Critical Alert: {assigned_bin.bin_name} is FULL ({fill_pct:.1f}%). Conveyor line halted.",
                    bin_id=assigned_bin.id
                )
        elif fill_pct >= warning_threshold:
            assigned_bin.status = "WARNING"
            if old_status == "NORMAL":
                create_alert(
                    alert_type="bin_warning",
                    severity="WARNING",
                    message=f"Warning Alert: {assigned_bin.bin_name} is almost full ({fill_pct:.1f}%).",
                    bin_id=assigned_bin.id
                )
        else:
            assigned_bin.status = "NORMAL"
            
        assigned_bin.updated_at = datetime.utcnow()
        
    # Create the Sorting Action record
    sorting_action = SortingAction(
        detection_id=detection.id,
        bin_id=bin_id,
        action=action_type,
        status="SUCCESS",
        timestamp=datetime.utcnow()
    )
    
    db.session.add(sorting_action)
    
    try:
        db.session.commit()
        
        # 4. Broadcast updates in real-time
        emit_new_detection(detection.to_dict())
        
        if assigned_bin:
            emit_bin_updated(assigned_bin.to_dict())
            
        # Recalculate stats and broadcast
        from services.analytics_service import get_dashboard_kpis
        emit_statistics_updated(get_dashboard_kpis())
        
        return detection
    except Exception as e:
        db.session.rollback()
        print(f"Failed to finalize sorting decision: {e}")
        return None

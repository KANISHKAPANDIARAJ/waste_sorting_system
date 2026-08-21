from datetime import datetime, timedelta
from models.database import db
from models.device import Device
from services.realtime_service import emit_device_status
from services.alert_service import create_alert

def register_heartbeat(device_id, device_name=None, location=None, firmware_version=None):
    """
    Registers a heartbeat from a device. Sets its status to ONLINE,
    updates last_seen, and broadcasts the status update.
    """
    device = Device.query.filter_by(device_id=device_id).first()
    
    was_offline = False
    if not device:
        # Create new device
        device = Device(
            device_id=device_id,
            device_name=device_name or "Unknown Simulator",
            location=location or "Lab",
            firmware_version=firmware_version or "v1.0.0",
            status="ONLINE",
            last_seen=datetime.utcnow()
        )
        db.session.add(device)
    else:
        # Check if status is transitioning from OFFLINE
        if device.status == "OFFLINE":
            was_offline = True
        
        device.status = "ONLINE"
        device.last_seen = datetime.utcnow()
        if device_name:
            device.device_name = device_name
        if location:
            device.location = location
        if firmware_version:
            device.firmware_version = firmware_version

    try:
        db.session.commit()
        
        # Broadcast status update
        emit_device_status(device.to_dict())
        
        # If it just reconnected, log an alert
        if was_offline:
            create_alert(
                alert_type="device_online",
                severity="INFO",
                message=f"Device {device_id} ({device.device_name}) has reconnected and is ONLINE.",
                device_id=device_id
            )
            
        return device
    except Exception as e:
        db.session.rollback()
        print(f"Failed to register heartbeat for {device_id}: {e}")
        return None

def check_offline_devices(timeout_seconds=15):
    """
    Scans all devices and flags those that haven't reported in timeout_seconds
    as OFFLINE. Triggers a CRITICAL alert for newly offline devices.
    """
    cutoff_time = datetime.utcnow() - timedelta(seconds=timeout_seconds)
    
    # Find devices that are ONLINE but last seen before the cutoff
    offline_devices = Device.query.filter(
        Device.status == "ONLINE",
        Device.last_seen < cutoff_time
    ).all()
    
    updated_count = 0
    for device in offline_devices:
        device.status = "OFFLINE"
        updated_count += 1
        
        # Create warning alert
        create_alert(
            alert_type="device_offline",
            severity="CRITICAL",
            message=f"Device {device.device_id} ({device.device_name}) is OFFLINE. No heartbeat received for {timeout_seconds}s.",
            device_id=device.device_id
        )
        
        # Emit real-time status update
        emit_device_status(device.to_dict())
        
    if updated_count > 0:
        try:
            db.session.commit()
        except Exception as e:
            db.session.rollback()
            print(f"Failed to commit offline devices update: {e}")
            
    return updated_count

def get_device_uptime_string(device_id):
    """Calculates active session uptime for a device from its creation time."""
    device = Device.query.filter_by(device_id=device_id).first()
    if not device or device.status == "OFFLINE":
        return "00:00:00"
    
    # Calculate duration
    uptime = datetime.utcnow() - device.created_at
    total_seconds = int(uptime.total_seconds())
    
    hours, remainder = divmod(total_seconds, 3600)
    minutes, seconds = divmod(remainder, 60)
    
    return f"{hours:02d}:{minutes:02d}:{seconds:02d}"

from datetime import datetime
from models.database import db
from models.alert import Alert
from services.realtime_service import emit_alert_created

def create_alert(alert_type, severity, message, device_id=None, bin_id=None):
    """
    Creates a new system alert, saves it to the database,
    and emits it in real-time to the dashboard.
    """
    # Create the alert record
    alert = Alert(
        alert_type=alert_type,
        severity=severity,
        message=message,
        device_id=device_id,
        bin_id=bin_id,
        created_at=datetime.utcnow()
    )
    
    try:
        db.session.add(alert)
        db.session.commit()
        
        # Emit real-time notification
        emit_alert_created(alert.to_dict())
        return alert
    except Exception as e:
        db.session.rollback()
        print(f"Failed to create alert: {e}")
        return None

def get_unread_alerts(limit=50):
    """Retrieves all unread alerts, sorted by newest first."""
    return Alert.query.filter_by(is_read=False).order_by(Alert.created_at.desc()).limit(limit).all()

def get_all_alerts(limit=100):
    """Retrieves all alerts, sorted by newest first."""
    return Alert.query.order_by(Alert.created_at.desc()).limit(limit).all()

def mark_alert_as_read(alert_id):
    """Marks a single alert as read in the database."""
    alert = Alert.query.get(alert_id)
    if alert:
        alert.is_read = True
        try:
            db.session.commit()
            return True
        except Exception as e:
            db.session.rollback()
            print(f"Failed to mark alert read: {e}")
    return False

def mark_all_alerts_as_read():
    """Marks all unread alerts as read."""
    unread_alerts = Alert.query.filter_by(is_read=False).all()
    for alert in unread_alerts:
        alert.is_read = True
    try:
        db.session.commit()
        return True
    except Exception as e:
        db.session.rollback()
        print(f"Failed to mark all alerts read: {e}")
    return False

from datetime import datetime
from models.database import db

class Alert(db.Model):
    __tablename__ = 'alerts'
    
    id = db.Column(db.Integer, primary_key=True)
    alert_type = db.Column(db.String(50), nullable=False)  # bin_full, low_confidence, device_offline, etc.
    severity = db.Column(db.String(20), nullable=False)  # INFO, WARNING, CRITICAL
    message = db.Column(db.String(255), nullable=False)
    device_id = db.Column(db.String(50), nullable=True)
    bin_id = db.Column(db.Integer, nullable=True)
    is_read = db.Column(db.Boolean, default=False, nullable=False)
    created_at = db.Column(db.DateTime, default=datetime.utcnow, index=True)

    def to_dict(self):
        return {
            'id': self.id,
            'alert_type': self.alert_type,
            'severity': self.severity,
            'message': self.message,
            'device_id': self.device_id,
            'bin_id': self.bin_id,
            'is_read': self.is_read,
            'created_at': self.created_at.isoformat() if self.created_at else None
        }

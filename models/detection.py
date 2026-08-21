from datetime import datetime
from models.database import db

class Detection(db.Model):
    __tablename__ = 'detections'
    
    id = db.Column(db.Integer, primary_key=True)
    device_id = db.Column(db.String(50), nullable=False)
    image_path = db.Column(db.String(255), nullable=True)
    material = db.Column(db.String(50), nullable=False)  # Plastic, Paper, Metal, Organic, Other
    confidence = db.Column(db.Float, nullable=False)
    assigned_bin = db.Column(db.String(50), nullable=False)
    sorting_status = db.Column(db.String(20), default='SORTED')  # SORTED, FLAGGED, DIVERTED, FAILED
    timestamp = db.Column(db.DateTime, default=datetime.utcnow, index=True)
    processing_time = db.Column(db.Float, nullable=False)  # in seconds
    model_version = db.Column(db.String(20), default='v2.0.0')
    source = db.Column(db.String(20), default='USER_UPLOAD')  # DEMO, USER_UPLOAD, SIMULATOR

    def to_dict(self):
        return {
            'id': self.id,
            'source': self.source,
            'device_id': self.device_id,
            'image_path': self.image_path,
            'material': self.material,
            'confidence': self.confidence,
            'assigned_bin': self.assigned_bin,
            'sorting_status': self.sorting_status,
            'timestamp': self.timestamp.isoformat() if self.timestamp else None,
            'processing_time': self.processing_time,
            'model_version': self.model_version
        }

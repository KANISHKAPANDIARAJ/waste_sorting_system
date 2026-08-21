from datetime import datetime
from models.database import db

class SortingAction(db.Model):
    __tablename__ = 'sorting_actions'
    
    id = db.Column(db.Integer, primary_key=True)
    detection_id = db.Column(db.Integer, nullable=False)
    bin_id = db.Column(db.Integer, nullable=False)
    action = db.Column(db.String(50), nullable=False)  # SORTED, DIVERTED, FLAGGED, FAILED
    status = db.Column(db.String(20), default='SUCCESS')  # SUCCESS, FAILED
    timestamp = db.Column(db.DateTime, default=datetime.utcnow)

    def to_dict(self):
        return {
            'id': self.id,
            'detection_id': self.detection_id,
            'bin_id': self.bin_id,
            'action': self.action,
            'status': self.status,
            'timestamp': self.timestamp.isoformat() if self.timestamp else None
        }

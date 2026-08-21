from datetime import datetime
from models.database import db

class Bin(db.Model):
    __tablename__ = 'bins'
    
    id = db.Column(db.Integer, primary_key=True)
    bin_name = db.Column(db.String(50), unique=True, nullable=False)
    material_type = db.Column(db.String(50), nullable=False)  # Plastic, Paper, Metal, Organic, Other
    capacity = db.Column(db.Float, nullable=False, default=10.0)  # Max capacity (e.g. 10.0)
    current_level = db.Column(db.Float, nullable=False, default=0.0)  # Current level in unit (e.g. 0.0 to 10.0)
    unit = db.Column(db.String(20), default='m³')
    status = db.Column(db.String(20), default='NORMAL')  # NORMAL, WARNING, FULL
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    @property
    def fill_percentage(self):
        if self.capacity <= 0:
            return 0.0
        return min((self.current_level / self.capacity) * 100.0, 100.0)

    def to_dict(self):
        return {
            'id': self.id,
            'bin_name': self.bin_name,
            'material_type': self.material_type,
            'capacity': self.capacity,
            'current_level': round(self.current_level, 2),
            'fill_percentage': round(self.fill_percentage, 1),
            'unit': self.unit,
            'status': self.status,
            'updated_at': self.updated_at.isoformat() if self.updated_at else None
        }

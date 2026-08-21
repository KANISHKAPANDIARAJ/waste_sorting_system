import os
import sys
import pytest

# Add root folder to sys.path
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from app import create_app
from models.database import db
from models.bin import Bin
from models.detection import Detection
from models.alert import Alert
from services.sorting_service import process_sorting_decision

@pytest.fixture
def app_ctx():
    """Initializes a Flask app with an in-memory SQLite database for clean testing isolation."""
    app = create_app({
        'TESTING': True,
        'SQLALCHEMY_DATABASE_URI': 'sqlite:///:memory:',
        'CLASSIFICATION_THRESHOLD': 0.70
    })
    
    with app.app_context():
        db.create_all()
        # Seed test bins
        bins = [
            Bin(bin_name='Plastic Bin', material_type='Plastic', capacity=10.0, current_level=1.0),
            Bin(bin_name='Other Bin', material_type='Other', capacity=10.0, current_level=1.0)
        ]
        db.session.add_all(bins)
        db.session.commit()
        yield app
        db.session.remove()
        db.drop_all()

def test_sorting_sorted_decision(app_ctx):
    """Verify routing and bin increments on high confidence."""
    # Process high confidence plastic
    det = process_sorting_decision('SIM-001', 'Plastic', 0.94, 0.015, None)
    
    assert det is not None
    assert det.sorting_status == 'SORTED'
    assert det.assigned_bin == 'Plastic Bin'
    
    # Check bin level increased from 1.0 by increment (0.20 for Plastic)
    pb = Bin.query.filter_by(material_type='Plastic').first()
    assert pb.current_level == pytest.approx(1.20)

def test_sorting_flagged_decision(app_ctx):
    """Verify warning flags and alerts on low confidence uploads."""
    # Process low confidence plastic (below 0.70)
    det = process_sorting_decision('SIM-001', 'Plastic', 0.65, 0.015, None)
    
    assert det is not None
    assert det.sorting_status == 'FLAGGED'
    
    # Check low confidence alert was created
    alert = Alert.query.filter_by(alert_type='low_confidence').first()
    assert alert is not None
    assert 'Low confidence' in alert.message
    pb = Bin.query.filter_by(material_type='Plastic').first()
    assert pb.current_level == pytest.approx(1.0)

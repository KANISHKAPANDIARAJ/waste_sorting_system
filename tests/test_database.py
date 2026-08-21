import os
import sys
import pytest

# Add root folder to sys.path
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from app import create_app
from models.database import db
from models.user import User
from models.device import Device
from models.bin import Bin

@pytest.fixture
def app_ctx():
    """Initializes a Flask app with an in-memory SQLite database for clean testing isolation."""
    app = create_app({
        'TESTING': True,
        'SQLALCHEMY_DATABASE_URI': 'sqlite:///:memory:',
        'UPLOAD_FOLDER': os.path.join(os.path.dirname(os.path.abspath(__file__)), 'test_uploads')
    })
    
    with app.app_context():
        db.create_all()
        yield app
        db.session.remove()
        db.drop_all()

def test_user_creation_and_password(app_ctx):
    """Verify operator user hashing logic."""
    u = User(username='testop', role='operator')
    u.set_password('testpass123')
    db.session.add(u)
    db.session.commit()
    
    db_user = User.query.filter_by(username='testop').first()
    assert db_user is not None
    assert db_user.role == 'operator'
    assert db_user.check_password('testpass123') is True
    assert db_user.check_password('wrongpass') is False

def test_device_creation(app_ctx):
    """Verify device registration parameters."""
    d = Device(device_id='DEV-TEST', device_name='Conveyor Test', location='Lab')
    db.session.add(d)
    db.session.commit()
    
    db_device = Device.query.filter_by(device_id='DEV-TEST').first()
    assert db_device is not None
    assert db_device.status == 'OFFLINE'  # default is offline
    assert db_device.location == 'Lab'

def test_detection_source_column(app_ctx):
    """Verify the refined Detection model tracks data origin."""
    detection = __import__('models.detection', fromlist=['Detection']).Detection(
        device_id='DEV-TEST',
        material='Plastic',
        confidence=0.94,
        assigned_bin='Plastic Bin',
        processing_time=0.01
    )
    db.session.add(detection)
    db.session.commit()

    assert detection.source == 'USER_UPLOAD'

def test_bin_capacity_and_fill(app_ctx):
    """Verify thermometer gauge properties."""
    b = Bin(bin_name='Plastic Bin', material_type='Plastic', capacity=10.0, current_level=2.5, unit='m³')
    db.session.add(b)
    db.session.commit()
    
    db_bin = Bin.query.filter_by(bin_name='Plastic Bin').first()
    assert db_bin is not None
    assert db_bin.fill_percentage == 25.0  # (2.5 / 10.0) * 100
    
    # Check level caps
    db_bin.current_level = 12.0
    assert db_bin.fill_percentage == 100.0

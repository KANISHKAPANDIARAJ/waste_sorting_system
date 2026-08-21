import os
import sys
import json
import pytest

# Add root folder to sys.path
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from app import create_app
from models.database import db
from models.bin import Bin
from models.device import Device

@pytest.fixture
def client():
    """Initializes testing client with memory database."""
    app = create_app({
        'TESTING': True,
        'SQLALCHEMY_DATABASE_URI': 'sqlite:///:memory:'
    })
    
    with app.test_client() as client:
        with app.app_context():
            db.create_all()
            # Seed default bin
            db.session.add(Bin(bin_name='Plastic Bin', material_type='Plastic', capacity=10.0, current_level=1.0))
            db.session.commit()
        yield client

def test_heartbeat_api(client):
    """Assert successful device heartbeat registration."""
    res = client.post('/api/device/heartbeat', json={
        'device_id': 'TEST-DEV-10',
        'device_name': 'Test Device',
        'location': 'Lab Room',
        'firmware_version': 'v1.0'
    })
    assert res.status_code == 200
    data = json.loads(res.data)
    assert data['status'] == 'success'
    assert data['device']['device_id'] == 'TEST-DEV-10'

def test_sensor_data_api(client):
    """Assert successful storage of telemetry lists."""
    res = client.post('/api/device/data', json={
        'device_id': 'TEST-DEV-10',
        'sensor_data': {
            'weight': 45.2,
            'moisture': 12.0,
            'temperature': 25.4
        }
    })
    assert res.status_code == 201
    data = json.loads(res.data)
    assert data['status'] == 'success'
    assert len(data['readings']) == 3

def test_bins_api(client):
    """Assert status collection of bins."""
    res = client.get('/api/bins')
    assert res.status_code == 200
    data = json.loads(res.data)
    assert len(data) == 1
    assert data[0]['bin_name'] == 'Plastic Bin'

import os
import sys
import pytest

# Add root folder to sys.path
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from iot.device_protocol import format_heartbeat_payload, format_telemetry_payload
from iot.sensor_generator import generate_telemetry_reading, generate_detection_event

def test_payload_formatting():
    """Verify heartbeat and telemetry JSON payload schemas."""
    hb = format_heartbeat_payload('SIM-001', 'v1.0', 'Conveyor Unit', 'Zone A')
    assert hb['device_id'] == 'SIM-001'
    assert hb['firmware_version'] == 'v1.0'
    assert hb['device_name'] == 'Conveyor Unit'
    assert hb['location'] == 'Zone A'
    
    tel = format_telemetry_payload('SIM-001', 120.5, 30.2, 28.5)
    assert tel['device_id'] == 'SIM-001'
    assert tel['sensor_data']['weight'] == 120.5
    assert tel['sensor_data']['moisture'] == 30.2
    assert tel['sensor_data']['temperature'] == 28.5

def test_sensor_generator_profiles():
    """Verify generated values stay within plausible limits."""
    # Test Plastic profile
    r = generate_telemetry_reading('Plastic')
    assert r['category'] == 'Plastic'
    assert 15.0 <= r['weight'] <= 80.0
    assert 5.0 <= r['moisture'] <= 15.0
    
    # Test random generation
    r2 = generate_telemetry_reading()
    assert r2['category'] in ['Plastic', 'Paper', 'Metal', 'Organic', 'Other']
    assert r2['weight'] > 0
    assert r2['moisture'] >= 0
    
    det = generate_detection_event()
    assert det['material'] in ['Plastic', 'Paper', 'Metal', 'Organic', 'Other']
    assert 0.0 <= det['confidence'] <= 1.0

import json
import time

def format_heartbeat_payload(device_id, firmware_version="v1.0.0", device_name="Main Unit", location="Conveyor Line A"):
    """Serializes a heartbeat message for the Flask API."""
    return {
        "device_id": device_id,
        "firmware_version": firmware_version,
        "device_name": device_name,
        "location": location,
        "timestamp": int(time.time())
    }

def format_telemetry_payload(device_id, weight, moisture, temperature):
    """Serializes a sensor reading message for the Flask API."""
    return {
        "device_id": device_id,
        "timestamp": int(time.time()),
        "sensor_data": {
            "weight": round(weight, 1),
            "moisture": round(moisture, 1),
            "temperature": round(temperature, 1)
        }
    }

def format_detection_payload(device_id, material, confidence, processing_time, image_path=None):
    """Serializes a waste detection result message for the Flask API."""
    return {
        "device_id": device_id,
        "material": material,
        "confidence": round(confidence, 3),
        "processing_time": round(processing_time, 4),
        "image_path": image_path or "uploads/waste/conveyor_sample.png",
        "model_version": "v1.0",
        "timestamp": int(time.time())
    }

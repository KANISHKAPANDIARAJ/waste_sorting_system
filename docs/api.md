# API Documentation

This document describes the REST API endpoints exposed by the **Smart Waste Segregation Backend**. These endpoints are used by both the IoT Simulator and the Dashboard front-end, and are designed for direct hardware compatibility (e.g. ESP32 microcontroller integrations).

---

## 1. Device Heartbeat
Keep device status online and sync network configurations.

* **Endpoint**: `POST /api/device/heartbeat`
* **Content-Type**: `application/json`
* **Payload**:
  ```json
  {
    "device_id": "SIM-001",
    "device_name": "Conveyor Line A",
    "location": "Conveyor Line A",
    "firmware_version": "v1.0.0"
  }
  ```
* **Success Response (200 OK)**:
  ```json
  {
    "status": "success",
    "message": "Heartbeat registered for SIM-001",
    "device": {
      "device_id": "SIM-001",
      "device_name": "Conveyor Line A",
      "location": "Conveyor Line A",
      "status": "ONLINE",
      "firmware_version": "v1.0.0",
      "last_seen": "2026-08-19T08:14:22Z"
    }
  }
  ```

---

## 2. Sensor Telemetry
Submit environmental and load sensor data logs.

* **Endpoint**: `POST /api/device/data`
* **Content-Type**: `application/json`
* **Payload**:
  ```json
  {
    "device_id": "SIM-001",
    "sensor_data": {
      "weight": 142.5,
      "moisture": 18.2,
      "temperature": 27.5
    }
  }
  ```
* **Success Response (201 Created)**:
  ```json
  {
    "status": "success",
    "message": "Stored 3 sensor readings",
    "readings": [
      { "device_id": "SIM-001", "sensor_type": "weight", "value": 142.5, "unit": "g" },
      { "device_id": "SIM-001", "sensor_type": "moisture", "value": 18.2, "unit": "%" },
      { "device_id": "SIM-001", "sensor_type": "temperature", "value": 27.5, "unit": "°C" }
    ]
  }
  ```

---

## 3. Waste Detection & Classification Upload
Upload a camera image for real-time classification, routing, database logging, and dashboard updates.

* **Endpoint**: `POST /api/detection`
* **Content-Type**: `multipart/form-data`
* **Parameters**:
  - `file`: Raw image binary file (`.png`, `.jpg`, `.jpeg`, `.webp`)
  - `device_id`: ID of reporting device (default: `SIM-001`)
* **Success Response (201 Created)**:
  ```json
  {
    "status": "success",
    "message": "Waste processed successfully",
    "detection": {
      "id": 14,
      "device_id": "SIM-001",
      "material": "Plastic",
      "confidence": 0.942,
      "assigned_bin": "Plastic Bin",
      "sorting_status": "SORTED",
      "timestamp": "2026-08-19T08:14:24Z",
      "processing_time": 0.0124,
      "model_version": "v1.0",
      "image_path": "uploads/waste/20260819081424_a3e2_specimen.png"
    }
  }
  ```

---

## 4. Retrieve Bins Status
Check fill level and status warning metrics of all 5 bins.

* **Endpoint**: `GET /api/bins`
* **Success Response (200 OK)**:
  ```json
  [
    {
      "id": 1,
      "bin_name": "Plastic Bin",
      "material_type": "Plastic",
      "capacity": 10.0,
      "current_level": 7.2,
      "fill_percentage": 72.0,
      "unit": "m³",
      "status": "WARNING"
    },
    ...
  ]
  ```

---

## 5. Empty Bin
Manually reset a bin's fill level to empty (0.0).

* **Endpoint**: `PUT /api/bins/<bin_id>`
* **Content-Type**: `application/json`
* **Payload**:
  ```json
  {
    "current_level": 0.0
  }
  ```
* **Success Response (200 OK)**:
  ```json
  {
    "status": "success",
    "message": "Bin Plastic Bin updated successfully",
    "bin": {
      "id": 1,
      "bin_name": "Plastic Bin",
      "current_level": 0.0,
      "fill_percentage": 0.0,
      "status": "NORMAL"
    }
  }
  ```

---

## 6. Directly Classify Image (Classify Only)
Evaluate classification category and confidence score *without* logging it in the database or incrementing bin volumes.

* **Endpoint**: `POST /api/classify`
* **Content-Type**: `multipart/form-data`
* **Parameters**:
  - `file`: Raw image binary
* **Success Response (200 OK)**:
  ```json
  {
    "material": "Metal",
    "confidence": 0.892,
    "processing_time": 0.0118,
    "model_version": "v1.0"
  }
  ```

---

## 7. Get History Logs
Retrieve paginated/filtered list of detections.

* **Endpoint**: `GET /api/detections`
* **Query Parameters**:
  - `material`: `Plastic`, `Paper`, `Metal`, `Organic`, `Other`
  - `status`: `SORTED`, `FLAGGED`, `DIVERTED`, `FAILED`
  - `limit`: Integer count (default: 50)
* **Success Response (200 OK)**: An array of detection dictionaries.

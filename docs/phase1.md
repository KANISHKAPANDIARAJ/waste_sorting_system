# Phase 1 Prototype & Future Phase 2 Hardware Integration

This document outlines the scope of the current Phase 1 prototype and details the roadmap for Phase 2 physical hardware deployment.

---

## 1. Phase 1 Scope & Limitations

The current Phase 1 is a **software-only simulation and telemetry dashboard**:
- **No Physical Hardware Needed**: No ESP32 microcontrollers, servos, ultrasonic sensors, weight scales, or conveyors are required.
- **Conveyor Belt & Camera Simulation**: Pre-generated synthetic images representing 5 waste classes (Plastic, Paper, Metal, Organic, Other) are stored on disk. The simulator selects and posts them to mimic camera uploads.
- **Environmental Sensor Simulation**: Telemetry streams (weights, temperatures, moisture values) are generated using random distribution profiles representing materials, and are sent to the REST API periodically.
- **Bin level Increments**: Stored waste volume increases mathematically (+2% for plastic, etc.) upon successful classifications.

---

## 2. Future Phase 2 — Physical Hardware Integration

To transition from the Phase 1 prototype to a physical sorting station, you will deploy physical components using the existing backend without restructuring code:

```
[Waste Item on Conveyor]
          │
          ▼
    [ESP32-CAM] ────────► uploads image ────────► Flask API: POST /api/detection
          │                                                    │
    (reads Load Cell                                           ▼
      weight sensor)                                     [ML Classifier]
          │                                                    │
          ▼                                                    ▼
    [ESP32 Main Controller] ◄── receives bin choice ◄─── [Sorting Engine]
          │                     (e.g., Plastic Bin)
          ▼
    [Servo Motors / Relays] ──► activates flap ──► dumps item in bin
          │
          ▼
    [Ultrasonic Sensor] ──────► reads fill level ───► Flask API: PUT /api/bins/<id>
```

### Components Checklist
1. **ESP32-CAM Module**:
   - Captures high-resolution images of waste arriving on the conveyor belt.
   - Connected to local Wi-Fi.
   - Transmits HTTP multipart POST requests containing raw images directly to:
     `http://<server-ip>:5000/api/detection`
2. **Main ESP32 / Arduino Microcontroller**:
   - Manages conveyor motor speed, load cell (weight), and moisture sensors.
   - Posts telemetry JSON logs to `/api/device/data` periodically.
   - Listens to the response from `/api/detection` containing `"assigned_bin"` (e.g. `"Plastic Bin"`).
   - Operates a **Servo Motor** or **Pneumatic Solenoid** to align the sorting deflector to divert the item into the designated bin.
3. **HC-SR04 Ultrasonic Distance Sensors**:
   - Mounted at the top of each bin pointing downward.
   - Measures distance to compute depth (current fill level).
   - ESP32 posts updated levels to:
     `PUT /api/bins/<bin_id>` with payload `{"current_level": <measured_level>}`
4. **Relay Modules**:
   - Used to switch high-voltage conveyor motors on or off based on emergency halts (e.g. when a bin status transitions to "FULL", the Flask backend issues an alert and the ESP32 shuts down conveyor relays).

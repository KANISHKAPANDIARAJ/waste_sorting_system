# Phase 1 Walkthrough — IoT-Enabled Automated Waste Segregation and Material Sorting System

## 1. Start the application

From the project root:

```powershell
python app.py
```

Open:

`http://127.0.0.1:5000`

## 2. Login

Default seeded credentials:

- Username: `admin`
- Password: `admin123`

The login page uses high-contrast text so labels, placeholders, and errors remain readable.

## 3. Dashboard initial state

After login, the Advanced Computer Vision panel starts in an empty state:

> Waiting for Waste Image

No `DEMO` record is displayed as the current detection.

## 4. Process a real waste image

1. Click **Choose Waste Image**.
2. Select a JPG, JPEG, PNG, or WEBP image.
3. Confirm the preview.
4. Click **Process Waste**.
5. The backend validates the file, stores it with a unique secure filename, and verifies that it is a readable image.
6. The classifier preprocesses the uploaded image and runs the Random Forest model.
7. The sorting service maps the predicted material to its corresponding bin.
8. The detection is stored with `source='USER_UPLOAD'`.
9. The dashboard updates through Socket.IO polling.

## 5. Source tracking

Detection records use:

- `USER_UPLOAD` — real user-submitted waste image
- `SIMULATOR` — explicitly simulated device detection
- `DEMO` — seeded historical/demo records

Demo records are excluded from operational KPI calculations.

## 6. Simulator

The simulator continues to send heartbeat and telemetry data, but it no longer generates waste detections automatically.

A simulator detection is only generated when the explicit `simulate_detection()` action is invoked and is stored with `source='SIMULATOR'`.

## 7. Database migration

The application applies an idempotent migration at startup. If an existing SQLite database lacks `detections.source`, the column is added without deleting existing records. Existing records pointing to `uploads/waste/conveyor_sample.png` are classified as `DEMO`.

## 8. Socket.IO

The dashboard uses Socket.IO polling transport for the local Windows Phase 1 environment. This avoids repeated failed WebSocket upgrade requests while retaining real-time application events.

## 9. Evaluator demonstration

Demonstrate:

`Login → Empty Dashboard → Upload Waste Image → Preview → AI Classification → Confidence → Assigned Bin → Database → Bin Update → Analytics → Dashboard Update`

Then upload a second material and show that the corresponding bin changes rather than every bin changing.

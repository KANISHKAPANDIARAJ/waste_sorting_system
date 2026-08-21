# IoT-Enabled Automated Waste Segregation and Material Sorting System

A modular, real-time industrial IoT dashboard and machine learning classification platform designed for automated waste sorting. This project serves as a **Phase 1 Software-Only Prototype** designed to run completely on local virtual components without requiring ESP32 boards, physical sensors, or conveyor systems.

## Key Features
- **Modern Industrial UI**: Sleek sidebar and topbar containing live status indicators, KPI analytics cards, and recent logs matching the design reference layout.
- **Real-Time WebSockets**: Full integration with Flask-SocketIO pushes telemetries (temperature, moisture, weight), heartbeats, sorting decisions, and overflow warnings to the frontend without page refreshes.
- **Embedded ML Classifier**: An active OpenCV and scikit-learn preprocessing and Random Forest classification pipeline. Automatically trains and serializes itself on setup.
- **Integrated IoT Simulator**: Features a background simulation loop that mimics sensor streams and uploads conveyor photos to trigger classification and bin levels.
- **Relational Data Storage**: SQLite database mapped via SQLAlchemy tracking devices, history, telemetries, and alerts.

---

## Project Structure
```
waste_sorting_system/
├── app.py                      # Flask Application entry point
├── config.py                   # Environment config loader
├── requirements.txt            # Python dependencies
├── .env                        # Active environment configurations
│
├── models/                     # SQLAlchemy Database models
│   ├── database.py
│   ├── device.py
│   ├── bin.py
│   ├── detection.py
│   ├── sensor_reading.py
│   ├── alert.py
│   └── user.py
│
├── routes/                     # Blueprint controllers
│   ├── dashboard_routes.py     # HTML pages rendering
│   └── api_routes.py           # REST API endpoints
│
├── services/                   # Business Logic Layer
│   ├── classification_service.py
│   ├── sorting_service.py
│   ├── device_service.py
│   ├── alert_service.py
│   └── realtime_service.py
│
├── ml/                         # Preprocessing and ML Classifiers
│   ├── preprocessing.py
│   └── classifier.py
│
├── iot/                        # Simulator libraries
│   ├── simulator.py
│   ├── sensor_generator.py
│   └── device_protocol.py
│
├── static/                     # Assets served statically
│   ├── css/                    # Style, dashboard, responsive sheets
│   └── js/                     # Real-time WebSocket clients
│
├── templates/                  # Jinja2 HTML layout pages
│
└── tests/                      # Automated test scripts
```

---

## Installation & Setup

Follow these exact steps to set up the project on Windows:

### 1. Extract and Navigate to Project
Open PowerShell or Command Prompt on D drive and navigate to the project directory:
```powershell
d:
cd \waste_sorting_system
```

### 2. Create and Activate Virtual Environment
```powershell
python -m venv venv
venv\Scripts\activate
```

### 3. Install Dependencies
```powershell
pip install -r requirements.txt
```

### 4. Initialize Database
Create database tables and register the default operator account:
```powershell
python scripts/init_db.py
```

### 5. Generate Samples & Train Classifier (Seed Data)
This script generates a set of 125 synthetic waste images representing colors and edges, trains the Random Forest model, serializes it to `ml/models/waste_classifier.pkl`, and seeds historical data for charts:
```powershell
python scripts/seed_data.py
```

### 6. Run Automated Tests
Verify all configurations, classifier features, database connections, and routes are functional:
```powershell
pytest
```

---

## Running the Application

### 1. Launch Flask Server
In your activated terminal, start the main application:
```powershell
python app.py
```
*The server is now listening at: **`http://127.0.0.1:5000`***

### 2. Access the Dashboard
- Open your browser and navigate to: `http://127.0.0.1:5000`
- Log in using the operator credentials:
  - **Username**: `admin`
  - **Password**: `admin123`

### 3. Start IoT Simulator
You can simulate the conveyor belt and telemetry sensors in two ways:
1. **Directly from the Dashboard Web UI**: Go to **Live Monitoring** and click **Start Sim**.
2. **From a Separate Terminal**: Open a new terminal, activate the virtual environment, and run:
   ```powershell
   venv\Scripts\activate
   python scripts/run_simulator.py --interval 5
   ```



import os
import time
import random
import requests
import threading
from glob import glob

from iot.device_protocol import format_heartbeat_payload, format_telemetry_payload
from iot.sensor_generator import generate_telemetry_reading

class IoTSimulator:
    def __init__(self, device_id="SIM-001", base_url="http://127.0.0.1:5000", interval=5, samples_dir=None):
        self.device_id = device_id
        self.base_url = base_url.rstrip('/')
        self.interval = interval
        self.running = False
        self.thread = None
        self._stop_event = threading.Event()
        
        # Resolve samples dir
        if not samples_dir:
            # Fallback relative to project root
            self.samples_dir = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), 'uploads', 'waste', 'train_samples')
        else:
            self.samples_dir = samples_dir
            
    def start(self):
        """Starts the background simulator thread."""
        if self.running:
            print("Simulator is already running.")
            return
            
        self.running = True
        self._stop_event.clear()
        self.thread = threading.Thread(target=self._run_loop, daemon=True)
        self.thread.start()
        print(f"IoT Simulator started for {self.device_id} at {self.base_url} (Interval: {self.interval}s)")

    def stop(self):
        """Stops the background simulator thread."""
        if not self.running:
            return
            
        self.running = False
        self._stop_event.set()
        if self.thread:
            self.thread.join(timeout=3)
        print("IoT Simulator stopped.")

    def _run_loop(self):
        """Main simulator execution loop."""
        iteration = 0
        
        # Send initial heartbeat immediately
        self._send_heartbeat()
        
        while not self._stop_event.is_set():
            time.sleep(1)
            iteration += 1
            
            # Perform actions based on interval
            if iteration % self.interval == 0:
                # 1. Send heartbeat
                self._send_heartbeat()
                
                # 2. Send sensor telemetries
                telemetry = generate_telemetry_reading()
                self._send_telemetry(telemetry)
                
                # Waste detection is intentionally NOT automatic. Phase 1
                # classifies real user uploads; simulator detection is an
                # explicit action via simulate_detection().

    def simulate_detection(self):
        """Explicitly simulate one waste item; never called automatically."""
        self._simulate_waste_upload()

    def _send_heartbeat(self):
        """Sends a POST heartbeat request to API."""
        url = f"{self.base_url}/api/device/heartbeat"
        payload = format_heartbeat_payload(
            device_id=self.device_id,
            device_name="Conveyor Simulator Unit",
            location="Conveyor Line A",
            firmware_version="v1.0.0"
        )
        try:
            r = requests.post(url, json=payload, timeout=2)
            if r.status_code == 200:
                print(f"[Simulator] Heartbeat sent. Status: {r.status_code}")
            else:
                print(f"[Simulator] Heartbeat failed. Status: {r.status_code}")
        except requests.exceptions.RequestException as e:
            print(f"[Simulator] Heartbeat connection error: {e}")

    def _send_telemetry(self, telemetry):
        """Sends a POST telemetry request to API."""
        url = f"{self.base_url}/api/device/data"
        payload = format_telemetry_payload(
            device_id=self.device_id,
            weight=telemetry['weight'],
            moisture=telemetry['moisture'],
            temperature=telemetry['temperature']
        )
        try:
            r = requests.post(url, json=payload, timeout=2)
            if r.status_code == 201:
                print(f"[Simulator] Telemetry sent: Temp={telemetry['temperature']:.1f}°C, Weight={telemetry['weight']:.1f}g, Moisture={telemetry['moisture']:.1f}%. Status: {r.status_code}")
            else:
                print(f"[Simulator] Telemetry failed. Status: {r.status_code}")
        except requests.exceptions.RequestException as e:
            print(f"[Simulator] Telemetry connection error: {e}")

    def _simulate_waste_upload(self):
        """Selects a random image from training samples and uploads it to the classification API."""
        url = f"{self.base_url}/api/detection"
        
        # Look for PNG files in samples directory
        images = glob(os.path.join(self.samples_dir, "*.png"))
        if not images:
            print("[Simulator] No synthetic images found in uploads/waste/train_samples/ directory. Skipping detection simulation.")
            return
            
        selected_img = random.choice(images)
        print(f"[Simulator] Conveyor sensor triggered. Uploading {os.path.basename(selected_img)} for classification...")
        
        try:
            with open(selected_img, 'rb') as f:
                files = {'file': (os.path.basename(selected_img), f, 'image/png')}
                data = {'device_id': self.device_id, 'source': 'SIMULATOR'}
                
                r = requests.post(url, data=data, files=files, timeout=5)
                
            if r.status_code == 201:
                res_json = r.json()
                det = res_json.get('detection', {})
                print(f"[Simulator] Classification Result: {det.get('material')} (Conf: {det.get('confidence')*100:.1f}%) -> Sorted into {det.get('assigned_bin')}")
            else:
                print(f"[Simulator] Detection upload failed. Status: {r.status_code}. Response: {r.text}")
        except requests.exceptions.RequestException as e:
            print(f"[Simulator] Detection upload connection error: {e}")

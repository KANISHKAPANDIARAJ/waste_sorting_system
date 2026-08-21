import sys
import os
import random
import cv2
import numpy as np
from datetime import datetime, timedelta

# Add root folder to sys.path so we can import app and models
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from app import create_app
from models.database import db
from models.device import Device
from models.bin import Bin
from models.detection import Detection
from models.sensor_reading import SensorReading
from models.alert import Alert
from models.sorting_action import SortingAction
from models.user import User
from ml.classifier import WasteClassifier, CATEGORIES
from ml.preprocessing import extract_features, preprocess_image

def generate_synthetic_image(category, output_path):
    """
    Generates a synthetic waste image using OpenCV drawing functions to represent
    specific visual characteristics for each category, saved to output_path.
    """
    # Create dark gray conveyor-belt background
    img = np.ones((128, 128, 3), dtype=np.uint8) * 40
    
    # Draw conveyor lines
    cv2.line(img, (0, 30), (128, 30), (60, 60, 60), 1)
    cv2.line(img, (0, 98), (128, 98), (60, 60, 60), 1)
    
    # Draw noise
    noise = np.random.normal(0, 5, img.shape).astype(np.int16)
    img = np.clip(img.astype(np.int16) + noise, 0, 255).astype(np.uint8)

    # Draw specific shapes based on category to train classification features
    if category == 'Plastic':
        # Plastic: draw a blue/clear bottle shape (rectangle + neck)
        color = (random.randint(180, 240), random.randint(120, 160), random.randint(10, 50)) # Blue/cyan in BGR
        cv2.rectangle(img, (40, 50), (88, 88), color, -1)
        cv2.rectangle(img, (54, 38), (74, 50), color, -1)
        # Cap
        cv2.rectangle(img, (58, 32), (70, 38), (10, 50, 220), -1)
        
    elif category == 'Paper':
        # Paper: draw a light-brown/white crumpled cardboard sheet or box
        color = (random.randint(120, 150), random.randint(160, 200), random.randint(200, 230)) # Brownish BGR
        pts = np.array([[30, 40], [90, 35], [100, 85], [40, 95]], np.int32)
        cv2.fillPoly(img, [pts], color)
        # Draw some lines representing text print
        cv2.line(img, (45, 50), (85, 47), (50, 50, 50), 2)
        cv2.line(img, (45, 65), (80, 62), (50, 50, 50), 2)
        
    elif category == 'Metal':
        # Metal: draw a cylindrical gray soda can with reflective metallic lines
        cv2.ellipse(img, (64, 50), (24, 8), 0, 0, 360, (180, 180, 180), -1)
        cv2.rectangle(img, (40, 50), (88, 82), (160, 160, 160), -1)
        cv2.ellipse(img, (64, 82), (24, 8), 0, 0, 360, (120, 120, 120), -1)
        # Metallic stripes
        cv2.line(img, (50, 50), (50, 82), (230, 230, 230), 2)
        cv2.line(img, (64, 50), (64, 82), (220, 220, 220), 3)
        cv2.line(img, (78, 50), (78, 82), (100, 100, 100), 2)
        
    elif category == 'Organic':
        # Organic: draw a green/red apple or leaf shape
        # Draw red apple
        cv2.circle(img, (56, 64), 22, (20, 30, 200), -1) # Red BGR
        cv2.circle(img, (72, 64), 22, (20, 30, 200), -1)
        # Draw brown stem
        cv2.line(img, (64, 46), (68, 32), (10, 50, 100), 2)
        # Draw green leaf
        leaf_pts = np.array([[68, 32], [80, 26], [74, 38]], np.int32)
        cv2.fillPoly(img, [leaf_pts], (30, 180, 50)) # Green BGR
        
    else:  # Other
        # Other/Reject: weird random grey blob or composite trash
        color = (random.randint(80, 120), random.randint(80, 120), random.randint(80, 120))
        pts = np.array([[50, 40], [80, 45], [90, 75], [70, 90], [45, 70]], np.int32)
        cv2.fillPoly(img, [pts], color)
        # Add random noise dots
        for _ in range(15):
            x, y = random.randint(45, 90), random.randint(40, 90)
            cv2.circle(img, (x, y), 2, (10, 10, 10), -1)
            
    cv2.imwrite(output_path, img)

def seed_system_data():
    app = create_app()
    with app.app_context():
        print("Seeding system data...")
        
        # 1. Clear existing data to avoid duplicates
        db.drop_all()
        db.create_all()
        
        # Seed default admin User
        admin = User(username='admin', role='admin')
        admin.set_password('admin123')
        db.session.add(admin)

        # 2. Seed Device SIM-001
        device_id = app.config.get('DEVICE_ID', 'SIM-001')
        device = Device(
            device_id=device_id,
            device_name=app.config.get('DEVICE_NAME', 'Main Unit'),
            location=app.config.get('DEVICE_LOCATION', 'Conveyor Line A'),
            status='ONLINE',
            firmware_version='v1.0.0',
            last_seen=datetime.utcnow() - timedelta(seconds=2)
        )
        db.session.add(device)
        print("Seeded device SIM-001")

        # 3. Seed Bins with levels representing reference dashboard layout
        # Visual Reference stats: Plastic = 72%, Paper = 48%, Metal = 31%, Organic = 65%, Other = 20%
        # assuming capacity = 10.0 m³
        bins_data = [
            {'name': 'Plastic Bin', 'material': 'Plastic', 'level': 7.2},
            {'name': 'Paper Bin', 'material': 'Paper', 'level': 4.8},
            {'name': 'Metal Bin', 'material': 'Metal', 'level': 3.1},
            {'name': 'Organic Bin', 'material': 'Organic', 'level': 6.5},
            {'name': 'Other Bin', 'material': 'Other', 'level': 2.0}
        ]
        
        bins_list = []
        for bd in bins_data:
            bin_status = 'NORMAL'
            if bd['level'] >= 9.0:
                bin_status = 'FULL'
            elif bd['level'] >= 7.0:
                bin_status = 'WARNING'
                
            b = Bin(
                bin_name=bd['name'],
                material_type=bd['material'],
                capacity=10.0,
                current_level=bd['level'],
                unit='m³',
                status=bin_status,
                updated_at=datetime.utcnow()
            )
            db.session.add(b)
            bins_list.append(b)
            
        print("Seeded 5 material sorting bins")

        # 4. Generate training samples and train ML classifier
        print("Generating synthetic waste training dataset...")
        train_dir = os.path.join(app.config.get('UPLOAD_FOLDER'), 'train_samples')
        os.makedirs(train_dir, exist_ok=True)
        
        X_train = []
        y_train = []
        
        for cat in CATEGORIES:
            for i in range(25):  # 25 samples per class
                fn = f"{cat.lower()}_{i}.png"
                path = os.path.join(train_dir, fn)
                generate_synthetic_image(cat, path)
                
                # Preprocess and extract features
                gray_img, color_img = preprocess_image(path)
                features = extract_features(color_img, gray_img)
                X_train.append(features)
                y_train.append(cat)
                
        print(f"Generated {len(X_train)} training images in uploads/waste/train_samples/")
        
        # Train and save the model
        classifier = WasteClassifier()
        classifier.train(np.array(X_train), np.array(y_train))
        print("Trained Random Forest Classifier model")

        # 5. Generate historical detections (last 7 days) to load dashboard charts beautifully
        print("Generating historical detections...")
        now = datetime.utcnow()
        total_days = 7
        detections_count = 150
        
        # Ensure directory for mock uploads exists
        os.makedirs(app.config.get('UPLOAD_FOLDER'), exist_ok=True)
        
        # Create a blank default conveyor image for history
        default_history_img = os.path.join(app.config.get('UPLOAD_FOLDER'), 'conveyor_sample.png')
        if not os.path.exists(default_history_img):
            generate_synthetic_image('Plastic', default_history_img)
            
        for i in range(detections_count):
            # Distribute detections exponentially/randomly over 7 days
            hours_offset = random.uniform(0, total_days * 24)
            timestamp = now - timedelta(hours=hours_offset)
            
            material = random.choices(
                CATEGORIES, 
                weights=[35, 20, 15, 20, 10],  # Plastic, Paper, Metal, Organic, Other distributions
                k=1
            )[0]
            
            confidence = random.uniform(0.72, 0.98)
            status = 'SORTED'
            
            # 5% chance of low confidence / flagged event
            if random.random() < 0.05:
                confidence = random.uniform(0.55, 0.69)
                status = 'FLAGGED'
            
            # 2% chance of failure
            if random.random() < 0.02:
                status = 'DIVERTED' if random.random() < 0.5 else 'FAILED'
                
            detection = Detection(
                device_id=device_id,
                image_path='uploads/waste/conveyor_sample.png',
                material=material,
                confidence=confidence,
                assigned_bin=f"{material} Bin" if material != 'Other' else 'Other Bin',
                sorting_status=status,
                timestamp=timestamp,
                processing_time=random.uniform(0.008, 0.024),
                model_version='v1.0',
                source='DEMO'
            )
            db.session.add(detection)
            db.session.flush() # Flush to generate ID
            
            # Add corresponding sorting action
            bin_idx = CATEGORIES.index(material)
            action = SortingAction(
                detection_id=detection.id,
                bin_id=bin_idx + 1,
                action='FLAGGED' if status == 'FLAGGED' else status,
                status='SUCCESS' if status != 'FAILED' else 'FAILED',
                timestamp=timestamp
            )
            db.session.add(action)
            
        print(f"Seeded {detections_count} historical detections and sorting actions")

        # 6. Seed mock sensor readings (temperature, moisture, weight)
        print("Generating historical sensor logs...")
        for i in range(50):
            timestamp = now - timedelta(hours=i * 2)
            
            # Weight reading
            db.session.add(SensorReading(
                device_id=device_id,
                sensor_type='weight',
                value=random.uniform(50.0, 350.0),
                unit='g',
                timestamp=timestamp
            ))
            # Moisture reading
            db.session.add(SensorReading(
                device_id=device_id,
                sensor_type='moisture',
                value=random.uniform(10.0, 50.0),
                unit='%',
                timestamp=timestamp
            ))
            # Temperature reading
            db.session.add(SensorReading(
                device_id=device_id,
                sensor_type='temperature',
                value=random.uniform(22.0, 35.0),
                unit='°C',
                timestamp=timestamp
            ))
            
        print("Seeded sensor log data")

        # 7. Seed simulated Alerts
        print("Generating mock system alerts...")
        # A critical offline alert in the past (marked read)
        alert_1 = Alert(
            alert_type='device_offline',
            severity='CRITICAL',
            message=f"Device {device_id} is OFFLINE. No heartbeat received.",
            device_id=device_id,
            is_read=True,
            created_at=now - timedelta(days=2)
        )
        db.session.add(alert_1)
        
        # A warning alert for plastic bin (marked read)
        alert_2 = Alert(
            alert_type='bin_warning',
            severity='WARNING',
            message="Warning Alert: Plastic Bin is almost full (72.0%).",
            bin_id=1,
            is_read=True,
            created_at=now - timedelta(hours=5)
        )
        db.session.add(alert_2)
        
        # An unread low confidence alert (recent)
        alert_3 = Alert(
            alert_type='low_confidence',
            severity='WARNING',
            message="Low confidence classification (64.2%) for Metal. Diverting item.",
            device_id=device_id,
            is_read=False,
            created_at=now - timedelta(minutes=45)
        )
        db.session.add(alert_3)
        
        db.session.commit()
        print("Database seeding completed successfully.")

if __name__ == '__main__':
    seed_system_data()

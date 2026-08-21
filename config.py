import os
from dotenv import load_dotenv

# Load variables from .env file
load_dotenv()

class Config:
    SECRET_KEY = os.environ.get('SECRET_KEY', 'default-dev-key')
    
    # Database
    SQLALCHEMY_DATABASE_URI = os.environ.get(
        'DATABASE_URL',
        'sqlite:///waste_system.db'
    )
    SQLALCHEMY_TRACK_MODIFICATIONS = False
    
    # Uploads
    UPLOAD_FOLDER = os.environ.get('UPLOAD_FOLDER', 'uploads/waste')
    MAX_CONTENT_LENGTH = int(os.environ.get('MAX_CONTENT_LENGTH', 16 * 1024 * 1024))
    ALLOWED_EXTENSIONS = {'png', 'jpg', 'jpeg', 'webp'}
    
    # Thresholds & Rules
    CLASSIFICATION_THRESHOLD = float(os.environ.get('CLASSIFICATION_THRESHOLD', 0.70))
    BIN_WARNING_THRESHOLD = float(os.environ.get('BIN_WARNING_THRESHOLD', 70.0))
    BIN_FULL_THRESHOLD = float(os.environ.get('BIN_FULL_THRESHOLD', 90.0))
    
    # Simulator Settings
    SIMULATOR_INTERVAL = int(os.environ.get('SIMULATOR_INTERVAL', 5))
    DEVICE_ID = os.environ.get('DEVICE_ID', 'SIM-001')
    DEVICE_NAME = os.environ.get('DEVICE_NAME', 'Main Unit')
    DEVICE_LOCATION = os.environ.get('DEVICE_LOCATION', 'Conveyor Line A')

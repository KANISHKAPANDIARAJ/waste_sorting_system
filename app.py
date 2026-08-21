import os
import logging
from flask import Flask, send_from_directory
from flask_cors import CORS

from config import Config
from models.database import db
from routes.dashboard_routes import dashboard_bp
from routes.api_routes import api_bp
from services.realtime_service import socketio
from services.device_service import check_offline_devices

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s [%(levelname)s] %(name)s: %(message)s',
    handlers=[
        logging.FileHandler(os.path.join(os.path.dirname(os.path.abspath(__file__)), 'waste_system.log')),
        logging.StreamHandler()
    ]
)
logger = logging.getLogger(__name__)

def create_app(config_override=None):
    """Initializes and configures the Flask application."""
    app = Flask(__name__)
    app.config.from_object(Config)
    
    if config_override:
        app.config.update(config_override)
    
    # Enable CORS
    CORS(app)
    
    # Create instance and upload directories if they don't exist
    os.makedirs(app.instance_path, exist_ok=True)
    os.makedirs(app.config['UPLOAD_FOLDER'], exist_ok=True)
    os.makedirs(os.path.join(app.config['UPLOAD_FOLDER'], 'temp'), exist_ok=True)
    os.makedirs(os.path.join(os.path.dirname(os.path.abspath(__file__)), 'outputs', 'predictions'), exist_ok=True)
    
    # Initialize extensions
    db.init_app(app)

    # Create missing tables and apply lightweight schema migrations without
    # deleting existing SQLite data. In particular, this adds the Detection
    # `source` column to databases created before source tracking was added.
    with app.app_context():
        db.create_all()
        from models.database import migrate_schema
        migrate_schema()

    socketio.init_app(app)
    
    # Register blueprints
    app.register_blueprint(dashboard_bp)
    app.register_blueprint(api_bp, url_prefix='/api')
    
    # Custom route to serve uploaded waste files statically
    @app.route('/uploads/waste/<path:filename>')
    def serve_uploaded_waste(filename):
        return send_from_directory(app.config['UPLOAD_FOLDER'], filename)
    
    # Start background task to check device heartbeats
    def background_device_monitor():
        with app.app_context():
            while True:
                socketio.sleep(10)  # Check every 10 seconds
                try:
                    offline_count = check_offline_devices(timeout_seconds=15)
                    if offline_count > 0:
                        logger.warning(f"Device monitor: {offline_count} device(s) went OFFLINE due to timeout.")
                except Exception as e:
                    logger.error(f"Error running background device monitor: {e}")

    # Start the monitor thread upon WebSocket server start
    @socketio.on('connect')
    def handle_connect():
        logger.info("Dashboard web client connected via WebSocket.")
        
    # Start monitor task
    socketio.start_background_task(background_device_monitor)
    
    # Simple error handling
    @app.errorhandler(404)
    def page_not_found(e):
        return send_from_directory('templates', 'error.html'), 404
        
    return app

app = create_app()

if __name__ == '__main__':
    logger.info("Starting Waste Segregation System on http://127.0.0.1:5000")
    socketio.run(app, host='127.0.0.1', port=5000, debug=True)

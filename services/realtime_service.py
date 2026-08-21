from flask_socketio import SocketIO

# Initialize socketio instance to be registered with the app in app.py
socketio = SocketIO(cors_allowed_origins="*")

def emit_new_detection(detection_data):
    """Broadcasts a new waste detection event to all connected dashboard clients."""
    socketio.emit('new_detection', detection_data)

def emit_bin_updated(bin_data):
    """Broadcasts updated bin fill-levels and status to all connected dashboard clients."""
    socketio.emit('bin_updated', bin_data)

def emit_device_status(device_data):
    """Broadcasts changes in device heartbeat/online status to all connected dashboard clients."""
    socketio.emit('device_status', device_data)

def emit_alert_created(alert_data):
    """Broadcasts new system alerts to trigger toast notifications on the dashboard."""
    socketio.emit('alert_created', alert_data)

def emit_statistics_updated(stats_data):
    """Broadcasts recalculated KPI statistics (Accuracy, Savings, etc.) to all connected dashboard clients."""
    socketio.emit('statistics_updated', stats_data)

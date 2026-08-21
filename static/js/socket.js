// Establish WebSocket connection using Flask-SocketIO client library
const socket = io({ transports: ['polling'], upgrade: false });

socket.on('connect', () => {
    console.log('Connected to server via polling.');
    updateConnectionStatus(true);
});

socket.on('disconnect', () => {
    console.log('Disconnected from server.');
    updateConnectionStatus(false);
});

function updateConnectionStatus(isOnline) {
    const statusText = document.getElementById('connection-status-text');
    const statusDot = document.getElementById('connection-status-dot');
    const sysDot = document.getElementById('sidebar-sys-dot');
    const statusContainer = document.getElementById('connection-status-container');
    
    if (isOnline) {
        if (statusText) statusText.textContent = 'System Online';
        if (statusDot) {
            statusDot.className = 'status-dot';
            statusDot.style.animation = 'pulse 2s infinite';
        }
        if (sysDot) sysDot.className = 'sys-dot';
        if (statusContainer) {
            statusContainer.classList.remove('offline');
        }
    } else {
        if (statusText) statusText.textContent = 'System Offline';
        if (statusDot) {
            statusDot.className = 'status-dot offline';
            statusDot.style.animation = 'none';
        }
        if (sysDot) sysDot.className = 'sys-dot offline';
        if (statusContainer) {
            statusContainer.classList.add('offline');
        }
    }
}

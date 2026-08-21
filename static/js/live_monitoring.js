document.addEventListener('DOMContentLoaded', () => {
    // 1. Initial Simulator Status check
    checkSimulatorStatus();
    
    // 2. Setup button event listeners
    setupSimulatorControls();
    
    // 3. Register Socket listeners for Live parameters
    registerLiveSocketListeners();
});

function checkSimulatorStatus() {
    fetch('/api/simulator/status')
        .then(res => res.json())
        .then(data => {
            updateSimulatorUI(data.running);
        })
        .catch(err => console.error("Error checking simulator status:", err));
}

function setupSimulatorControls() {
    const startBtn = document.getElementById('sim-start-btn');
    const stopBtn = document.getElementById('sim-stop-btn');
    
    if (startBtn) {
        startBtn.addEventListener('click', () => {
            fetch('/api/simulator/start', { method: 'POST' })
                .then(res => res.json())
                .then(data => {
                    updateSimulatorUI(data.running);
                    logEvent('System', 'IoT Simulator START request sent.', 'info');
                })
                .catch(err => console.error("Error starting simulator:", err));
        });
    }
    
    if (stopBtn) {
        stopBtn.addEventListener('click', () => {
            fetch('/api/simulator/stop', { method: 'POST' })
                .then(res => res.json())
                .then(data => {
                    updateSimulatorUI(data.running);
                    logEvent('System', 'IoT Simulator STOP request sent.', 'warning');
                })
                .catch(err => console.error("Error stopping simulator:", err));
        });
    }
}

function updateSimulatorUI(isRunning) {
    const statusText = document.getElementById('simulator-status-text');
    const startBtn = document.getElementById('sim-start-btn');
    const stopBtn = document.getElementById('sim-stop-btn');
    const activeDot = document.getElementById('sim-active-dot');
    
    if (isRunning) {
        if (statusText) statusText.textContent = 'RUNNING';
        if (activeDot) activeDot.className = 'status-dot';
        if (startBtn) startBtn.disabled = true;
        if (stopBtn) stopBtn.disabled = false;
    } else {
        if (statusText) statusText.textContent = 'STOPPED';
        if (activeDot) activeDot.className = 'status-dot offline';
        if (startBtn) startBtn.disabled = false;
        if (stopBtn) stopBtn.disabled = true;
    }
}

function registerLiveSocketListeners() {
    // 1. Sensor Telemetry values
    socket.on('sensor_data', (telemetry) => {
        console.log("Live telemetry update:", telemetry);
        const weightVal = document.getElementById('live-val-weight');
        const moistureVal = document.getElementById('live-val-moisture');
        const tempVal = document.getElementById('live-val-temp');
        const telemetryTime = document.getElementById('live-val-heartbeat');
        
        if (weightVal) weightVal.textContent = `${telemetry.readings.weight.value.toFixed(1)} ${telemetry.readings.weight.unit}`;
        if (moistureVal) moistureVal.textContent = `${telemetry.readings.moisture.value.toFixed(1)}${telemetry.readings.moisture.unit}`;
        if (tempVal) tempVal.textContent = `${telemetry.readings.temperature.value.toFixed(1)}${telemetry.readings.temperature.unit}`;
        
        if (telemetryTime) {
            const timeObj = new Date(telemetry.timestamp);
            telemetryTime.textContent = timeObj.toLocaleTimeString();
        }
        
        logEvent('Sensor', `Readings received: Weight=${telemetry.readings.weight.value.toFixed(1)}g, Moisture=${telemetry.readings.moisture.value.toFixed(1)}%`, 'debug');
    });
    
    // 2. Detection events
    socket.on('new_detection', (det) => {
        logEvent('Classifier', `Waste classified: ${det.material} (Conf: ${(det.confidence * 100).toFixed(1)}%) -> ${det.assigned_bin}`, 'success');
        
        // Update live panel
        const liveMat = document.getElementById('live-det-material');
        const liveConf = document.getElementById('live-det-confidence');
        const liveBin = document.getElementById('live-det-bin');
        const liveImg = document.getElementById('live-det-img');
        
        if (liveMat) {
            liveMat.textContent = det.material;
            liveMat.className = `badge badge-${det.sorting_status.toLowerCase()}`;
        }
        if (liveConf) liveConf.textContent = `${(det.confidence * 100).toFixed(1)}%`;
        if (liveBin) liveBin.textContent = det.assigned_bin;
        if (liveImg) liveImg.src = `/${det.image_path}?t=${new Date().getTime()}`;
    });
    
    // 3. Heartbeats
    socket.on('device_status', (device) => {
        const liveDevStatus = document.getElementById('live-dev-status-badge');
        const liveDevTime = document.getElementById('live-val-uptime');
        
        if (liveDevStatus) {
            liveDevStatus.textContent = device.status;
            liveDevStatus.className = device.status === 'ONLINE' ? 'badge badge-sorted' : 'badge badge-failed';
        }
        
        logEvent('Device', `Status report: Device ${device.device_id} is ${device.status}.`, device.status === 'ONLINE' ? 'info' : 'critical');
    });
}

function logEvent(sender, message, level = 'info') {
    const stream = document.getElementById('live-events-stream');
    if (!stream) return;
    
    const timeStr = new Date().toLocaleTimeString();
    const logItem = document.createElement('div');
    logItem.className = `log-item log-${level}`;
    logItem.style.padding = '0.35rem 0.5rem';
    logItem.style.borderBottom = '1px solid #f1f5f9';
    logItem.style.fontSize = '0.75rem';
    logItem.style.fontFamily = 'monospace';
    
    let color = '#64748b'; // default gray
    if (level === 'success') color = '#16a34a';
    if (level === 'warning') color = '#ca8a04';
    if (level === 'critical') color = '#dc2626';
    if (level === 'info') color = '#2563eb';
    
    logItem.innerHTML = `
        <span style="color: #94a3b8">[${timeStr}]</span>
        <span style="color: ${color}; font-weight: bold;">[${sender.toUpperCase()}]</span>
        <span>${message}</span>
    `;
    
    stream.appendChild(logItem);
    // Auto scroll to bottom
    stream.scrollTop = stream.scrollHeight;
    
    // Keep max 50 logs
    while (stream.children.length > 50) {
        stream.removeChild(stream.firstChild);
    }
}

let wasteChart = null;

function initializeWasteUpload() {
    const form = document.getElementById('waste-upload-form');
    const input = document.getElementById('waste-image-input');
    const preview = document.getElementById('waste-preview');
    const previewWrap = document.getElementById('waste-preview-wrap');
    const processBtn = document.getElementById('waste-process-btn');
    const status = document.getElementById('waste-upload-status');

    if (!form || !input) return;

    input.addEventListener('change', () => {
        const file = input.files && input.files[0];
        if (!file) {
            processBtn.disabled = true;
            previewWrap?.classList.add('d-none');
            if (status) status.textContent = 'No image selected.';
            return;
        }

        const allowed = ['image/jpeg', 'image/png', 'image/webp'];
        if (!allowed.includes(file.type)) {
            input.value = '';
            processBtn.disabled = true;
            previewWrap?.classList.add('d-none');
            if (status) {
                status.textContent = 'Please select a JPG, JPEG, PNG, or WEBP image.';
                status.className = 'small text-danger';
            }
            return;
        }

        if (file.size > 16 * 1024 * 1024) {
            input.value = '';
            processBtn.disabled = true;
            previewWrap?.classList.add('d-none');
            if (status) {
                status.textContent = 'Image must be smaller than 16 MB.';
                status.className = 'small text-danger';
            }
            return;
        }

        const reader = new FileReader();
        reader.onload = event => {
            if (preview) preview.src = event.target.result;
            previewWrap?.classList.remove('d-none');
        };
        reader.readAsDataURL(file);

        processBtn.disabled = false;
        if (status) {
            status.textContent = `${file.name} selected. Ready to process.`;
            status.className = 'small text-muted';
        }
    });

    form.addEventListener('submit', async event => {
        event.preventDefault();
        const file = input.files && input.files[0];
        if (!file) return;

        const originalText = processBtn.innerHTML;
        processBtn.disabled = true;
        processBtn.innerHTML = '<span class="spinner-border spinner-border-sm me-1"></span> Processing...';
        if (status) {
            status.textContent = 'Uploading image and running classification...';
            status.className = 'small text-primary';
        }

        const formData = new FormData();
        formData.append('file', file);
        formData.append('source', 'USER_UPLOAD');

        try {
            const response = await fetch('/api/detection', {
                method: 'POST',
                body: formData
            });
            const payload = await response.json();

            if (!response.ok) {
                throw new Error(payload.error || 'Waste processing failed.');
            }

            updateComputerVisionPanel(payload.detection);
            prependToDetectionsTable(payload.detection);

            if (status) {
                status.textContent = `Processed: ${payload.detection.material} → ${payload.detection.assigned_bin}`;
                status.className = 'small text-success fw-semibold';
            }

            // Refresh the chart with the newly stored USER_UPLOAD detection.
            const periodSelect = document.getElementById('chart-period-select');
            if (periodSelect) {
                periodSelect.dispatchEvent(new Event('change'));
            }

            // The server emits bin/statistics events as well; this gives the
            // UI an immediate response even when polling takes a moment.
        } catch (error) {
            console.error('Waste upload failed:', error);
            if (status) {
                status.textContent = error.message;
                status.className = 'small text-danger';
            }
        } finally {
            processBtn.disabled = false;
            processBtn.innerHTML = originalText;
        }
    });
}


document.addEventListener('DOMContentLoaded', () => {
    // 1. Initialize Uptime Ticker
    const initialUptime = document.getElementById('sidebar-uptime-val')?.textContent || "00:00:00";
    startUptimeTicker(initialUptime);
    
    // 2. Load Chart.js overview chart
    initializeOverviewChart();
    
    // 3. Setup real user image upload workflow
    initializeWasteUpload();

    // 4. Setup Socket.IO Event Handlers
    registerSocketListeners();
});

// Tickers to dynamically increment the device uptime string in the sidebar
function startUptimeTicker(initialUptime) {
    const uptimeVal = document.getElementById('sidebar-uptime-val');
    if (!uptimeVal) return;
    
    const parts = initialUptime.split(':');
    if (parts.length !== 3) return;
    
    let totalSeconds = parseInt(parts[0], 10) * 3600 + parseInt(parts[1], 10) * 60 + parseInt(parts[2], 10);
    
    setInterval(() => {
        totalSeconds++;
        const hours = Math.floor(totalSeconds / 3600);
        const minutes = Math.floor((totalSeconds % 3600) / 60);
        const seconds = totalSeconds % 60;
        
        const pad = num => String(num).padStart(2, '0');
        uptimeVal.textContent = `${pad(hours)}:${pad(minutes)}:${pad(seconds)}`;
    }, 1000);
}

// Draw the Stacked Area Chart showing category distribution over time
function initializeOverviewChart() {
    const ctx = document.getElementById('wasteChart');
    if (!ctx) return;
    
    const periodSelect = document.getElementById('chart-period-select');
    
    // Fetch data and build chart
    const loadChartData = (period) => {
        fetch(`/api/analytics?period=${period}`)
            .then(res => res.json())
            .then(data => {
                const chartData = data.chart_data;
                
                if (wasteChart) {
                    wasteChart.destroy();
                }
                
                wasteChart = new Chart(ctx, {
                    type: 'line',
                    data: chartData,
                    options: {
                        responsive: true,
                        maintainAspectRatio: false,
                        plugins: {
                            legend: {
                                position: 'top',
                                labels: { boxWidth: 10, font: { family: 'Inter', size: 11 } }
                            }
                        },
                        scales: {
                            x: { grid: { display: false } },
                            y: {
                                stacked: true,
                                grid: { color: '#f1f5f9' },
                                title: { display: true, text: 'Items Sorted' }
                            }
                        }
                    }
                });
            })
            .catch(err => console.error("Error loading chart data:", err));
    };
    
    // Initial Load
    loadChartData(periodSelect ? periodSelect.value : 'today');
    
    // Dropdown change listener
    if (periodSelect) {
        periodSelect.addEventListener('change', (e) => {
            loadChartData(e.target.value);
        });
    }
}

// Listen for server broadcasts
function registerSocketListeners() {
    // 1. Telemetry heartbeat status updates
    socket.on('device_status', (device) => {
        console.log("Device status updated:", device);
        const uptimeVal = document.getElementById('sidebar-uptime-val');
        
        // Update sidebar values if matching device
        const sidebarDevId = document.getElementById('sidebar-dev-id');
        if (sidebarDevId && sidebarDevId.textContent.trim() === device.device_id) {
            const sidebarDevStatus = document.getElementById('sidebar-dev-status');
            if (sidebarDevStatus) {
                if (device.status === 'ONLINE') {
                    sidebarDevStatus.className = 'sys-dot';
                } else {
                    sidebarDevStatus.className = 'sys-dot offline';
                }
            }
        }
    });

    // 2. Handle a new item classification and sorting event
    socket.on('new_detection', (detection) => {
        console.log("New detection received:", detection);
        
        // Update CV panel
        updateComputerVisionPanel(detection);
        
        // Add to Recent Detections table
        prependToDetectionsTable(detection);
        
        // Refresh charts
        if (wasteChart) {
            const periodSelect = document.getElementById('chart-period-select');
            // Re-fetch data
            fetch(`/api/analytics?period=${periodSelect ? periodSelect.value : 'today'}`)
                .then(res => res.json())
                .then(data => {
                    wasteChart.data = data.chart_data;
                    wasteChart.update();
                });
        }
    });

    // 3. Handle bin level increments
    socket.on('bin_updated', (bin) => {
        console.log("Bin level updated:", bin);
        updateBinWidget(bin);
    });

    // 4. Handle updated statistics card values
    socket.on('statistics_updated', (stats) => {
        console.log("Stats recalculated:", stats);
        
        const accuracyEl = document.getElementById('kpi-accuracy');
        const savingsEl = document.getElementById('kpi-savings');
        const contaminationEl = document.getElementById('kpi-contamination');
        const downtimeEl = document.getElementById('kpi-downtime');
        
        if (accuracyEl) accuracyEl.textContent = stats.accuracy;
        if (savingsEl) savingsEl.textContent = stats.savings;
        if (contaminationEl) contaminationEl.textContent = stats.contamination_risk;
        if (downtimeEl) downtimeEl.textContent = stats.downtime;
    });

    // 5. Toast alert notifications
    socket.on('alert_created', (alert) => {
        console.log("System alert triggered:", alert);
        showToastAlert(alert);
        
        // Increment alerts icon count if exists
        const alertBadge = document.getElementById('alert-badge-count');
        if (alertBadge) {
            let currentCount = parseInt(alertBadge.textContent, 10) || 0;
            alertBadge.textContent = currentCount + 1;
            alertBadge.style.display = 'flex';
        }
    });
}

function updateComputerVisionPanel(det) {
    const feedImg = document.getElementById('cv-feed-img');
    const matVal = document.getElementById('cv-val-material');
    const confVal = document.getElementById('cv-val-confidence');
    const binVal = document.getElementById('cv-val-bin');
    const timeVal = document.getElementById('cv-val-time');
    const procTimeVal = document.getElementById('cv-overlay-inference');
    
    // Transition from empty state to the real uploaded image.
    const emptyState = document.getElementById('cv-empty-state');
    if (emptyState) emptyState.classList.add('d-none');
    if (feedImg) {
        feedImg.classList.remove('d-none');
        feedImg.src = `/${det.image_path}?t=${new Date().getTime()}`;
    }
    
    // Update labels
    if (matVal) {
        matVal.textContent = det.material;
        matVal.className = `cv-meta-val highlight ${det.material.toLowerCase()}`;
    }
    
    if (confVal) confVal.textContent = `${(det.confidence * 100).toFixed(1)}%`;
    if (binVal) binVal.textContent = det.assigned_bin;
    
    if (timeVal) {
        const dateObj = new Date(det.timestamp);
        timeVal.textContent = dateObj.toLocaleTimeString();
    }
    
    if (procTimeVal) {
        procTimeVal.textContent = `Inference: ${(det.processing_time * 1000).toFixed(0)}ms`;
    }
    
    // Update bounding box overlays dynamically
    const container = document.getElementById('cv-feed-container');
    let boundingBox = document.getElementById('cv-dynamic-bbox');
    
    if (!boundingBox && container) {
        boundingBox = document.createElement('div');
        boundingBox.id = 'cv-dynamic-bbox';
        boundingBox.className = 'cv-bounding-box';
        container.appendChild(boundingBox);
    }
    
    if (boundingBox) {
        // Place bounding box in middle area (can be simulated or actual)
        boundingBox.style.top = '30%';
        boundingBox.style.left = '35%';
        boundingBox.style.width = '30%';
        boundingBox.style.height = '40%';
        boundingBox.innerHTML = `<span class="cv-box-label">${det.material} (${(det.confidence*100).toFixed(0)}%)</span>`;
        boundingBox.style.borderColor = getCategoryColor(det.material);
        const boxLabel = boundingBox.querySelector('.cv-box-label');
        if (boxLabel) {
            boxLabel.style.backgroundColor = getCategoryColor(det.material);
            boxLabel.style.color = '#fff';
        }
        boundingBox.style.display = 'block';
    }
}

function getCategoryColor(material) {
    const colors = {
        'Plastic': '#0284c7',
        'Paper': '#eab308',
        'Metal': '#7c3aed',
        'Organic': '#16a34a',
        'Other': '#dc2626'
    };
    return colors[material] || '#cbd5e1';
}

function updateBinWidget(bin) {
    // Search for column by data-material property
    const col = document.querySelector(`.bin-column[data-material="${bin.material_type}"]`);
    if (!col) return;
    
    const fluid = col.querySelector('.bin-fill-fluid');
    const label = col.querySelector('.bin-fill-label');
    
    if (fluid) {
        // Handle desktop vertical percentage vs mobile width
        if (window.innerWidth <= 768) {
            fluid.style.width = `${bin.fill_percentage}%`;
            fluid.style.height = '100%';
        } else {
            fluid.style.height = `${bin.fill_percentage}%`;
            fluid.style.width = '100%';
        }
    }
    
    if (label) {
        label.textContent = `${bin.fill_percentage.toFixed(0)}% Full`;
    }
}

function prependToDetectionsTable(det) {
    const tbody = document.getElementById('recent-detections-tbody');
    if (!tbody) return;
    
    // Remove empty row if present
    const emptyRow = tbody.querySelector('.empty-row');
    if (emptyRow) emptyRow.remove();
    
    const row = document.createElement('tr');
    row.style.opacity = 0;
    row.style.transition = 'opacity 0.5s ease-in-out';
    
    const dateObj = new Date(det.timestamp);
    const timeStr = dateObj.toLocaleTimeString();
    
    row.innerHTML = `
        <td>#${det.id}</td>
        <td><strong>${det.material}</strong></td>
        <td>${(det.confidence * 100).toFixed(1)}%</td>
        <td>${det.assigned_bin}</td>
        <td>${timeStr}</td>
        <td><span class="badge badge-${det.sorting_status.toLowerCase()}">${det.sorting_status}</span></td>
    `;
    
    tbody.insertBefore(row, tbody.firstChild);
    
    // Fade in
    setTimeout(() => { row.style.opacity = 1; }, 50);
    
    // Keep max 5 rows
    while (tbody.rows.length > 5) {
        tbody.deleteRow(tbody.rows.length - 1);
    }
}

function showToastAlert(alert) {
    // Create container if not exists
    let toastContainer = document.getElementById('toast-container');
    if (!toastContainer) {
        toastContainer = document.createElement('div');
        toastContainer.id = 'toast-container';
        toastContainer.style.position = 'fixed';
        toastContainer.style.top = '20px';
        toastContainer.style.right = '20px';
        toastContainer.style.zIndex = '9999';
        toastContainer.style.display = 'flex';
        toastContainer.style.flexDirection = 'column';
        toastContainer.style.gap = '10px';
        document.body.appendChild(toastContainer);
    }
    
    const toast = document.createElement('div');
    const colors = {
        'CRITICAL': '#fee2e2',
        'WARNING': '#fef9c3',
        'INFO': '#dbeafe'
    };
    const borderColors = {
        'CRITICAL': '#ef4444',
        'WARNING': '#eab308',
        'INFO': '#3b82f6'
    };
    const textColors = {
        'CRITICAL': '#991b1b',
        'WARNING': '#854d0e',
        'INFO': '#1e40af'
    };
    
    toast.style.backgroundColor = colors[alert.severity] || '#fff';
    toast.style.borderColor = borderColors[alert.severity] || '#ccc';
    toast.style.borderWidth = '1px';
    toast.style.borderStyle = 'solid';
    toast.style.borderLeft = `5px solid ${borderColors[alert.severity]}`;
    toast.style.color = textColors[alert.severity] || '#000';
    toast.style.padding = '12px 18px';
    toast.style.borderRadius = '6px';
    toast.style.boxShadow = '0 10px 15px -3px rgb(0 0 0 / 0.1)';
    toast.style.minWidth = '300px';
    toast.style.maxWidth = '400px';
    toast.style.fontSize = '0.85rem';
    toast.style.fontWeight = '500';
    toast.style.display = 'flex';
    toast.style.justifyContent = 'space-between';
    toast.style.alignItems = 'center';
    
    toast.innerHTML = `
        <div>
            <strong style="display: block; font-size: 0.75rem; text-transform: uppercase; margin-bottom: 2px;">${alert.severity}</strong>
            ${alert.message}
        </div>
        <button style="background:none; border:none; color:inherit; font-weight:bold; font-size:1.1rem; cursor:pointer; margin-left: 10px;" onclick="this.parentElement.remove()">×</button>
    `;
    
    toastContainer.appendChild(toast);
    
    // Auto-remove after 6 seconds
    setTimeout(() => {
        toast.style.opacity = 0;
        toast.style.transition = 'opacity 0.5s';
        setTimeout(() => toast.remove(), 500);
    }, 6000);
}

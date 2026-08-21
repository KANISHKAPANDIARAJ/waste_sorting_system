document.addEventListener('DOMContentLoaded', () => {
    loadDetailedAnalytics();
});

function loadDetailedAnalytics() {
    fetch('/api/analytics')
        .then(res => res.json())
        .then(data => {
            const stats = data.detailed_stats;
            
            // Populate numeric stats
            document.getElementById('stat-total-items').textContent = stats.total_count.toLocaleString();
            document.getElementById('stat-avg-inference').textContent = `${stats.average_processing_time_ms.toFixed(0)} ms`;
            
            // Build 1. Material Distribution Doughnut Chart
            buildDistributionChart(stats.distribution);
            
            // Build 2. Sorting Status Bar Chart
            buildSortingStatusChart(stats.sorting_actions);
        })
        .catch(err => console.error("Error loading analytics data:", err));
}

function buildDistributionChart(dist) {
    const ctx = document.getElementById('analyticsDistributionChart');
    if (!ctx) return;
    
    new Chart(ctx, {
        type: 'doughnut',
        data: {
            labels: Object.keys(dist),
            datasets: [{
                data: Object.values(dist),
                backgroundColor: [
                    '#0284c7', // Plastic (Blue)
                    '#eab308', // Paper (Yellow)
                    '#7c3aed', // Metal (Purple)
                    '#16a34a', // Organic (Green)
                    '#dc2626'  // Other (Red)
                ],
                borderWidth: 1
            }]
        },
        options: {
            responsive: true,
            maintainAspectRatio: false,
            plugins: {
                legend: {
                    position: 'right',
                    labels: { boxWidth: 12, font: { family: 'Inter', size: 12 } }
                }
            }
        }
    });
}

function buildSortingStatusChart(actions) {
    const ctx = document.getElementById('analyticsStatusChart');
    if (!ctx) return;
    
    new Chart(ctx, {
        type: 'bar',
        data: {
            labels: Object.keys(actions),
            datasets: [{
                label: 'Item Actions',
                data: Object.values(actions),
                backgroundColor: [
                    'rgba(22, 163, 74, 0.75)',  // SORTED - Green
                    'rgba(234, 179, 8, 0.75)',  // FLAGGED - Yellow
                    'rgba(37, 99, 235, 0.75)',  // DIVERTED - Blue
                    'rgba(220, 38, 38, 0.75)'   // FAILED - Red
                ],
                borderColor: [
                    'rgb(22, 163, 74)',
                    'rgb(234, 179, 8)',
                    'rgb(37, 99, 235)',
                    'rgb(220, 38, 38)'
                ],
                borderWidth: 1
            }]
        },
        options: {
            responsive: true,
            maintainAspectRatio: false,
            plugins: {
                legend: { display: false }
            },
            scales: {
                x: { grid: { display: false } },
                y: {
                    grid: { color: '#f1f5f9' },
                    title: { display: true, text: 'Volume Count' },
                    ticks: { precision: 0 }
                }
            }
        }
    });
}

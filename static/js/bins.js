document.addEventListener('DOMContentLoaded', () => {
    setupBinActions();
    
    // If on bins page, update bins when websocket broadcasts bin changes
    if (typeof socket !== 'undefined') {
        socket.on('bin_updated', (bin) => {
            console.log("Bins page received WebSocket update:", bin);
            const detailCard = document.querySelector(`.bin-detail-card[data-id="${bin.id}"]`);
            if (detailCard) {
                // Update fill text
                const levelVal = detailCard.querySelector('.bin-level-val');
                const fillPct = detailCard.querySelector('.bin-fill-pct');
                const progressFluid = detailCard.querySelector('.bin-progress-fluid');
                const statusBadge = detailCard.querySelector('.bin-status-badge');
                
                if (levelVal) levelVal.textContent = `${bin.current_level.toFixed(2)} ${bin.unit} / ${bin.capacity} ${bin.unit}`;
                if (fillPct) fillPct.textContent = `${bin.fill_percentage.toFixed(1)}%`;
                
                if (progressFluid) {
                    progressFluid.style.width = `${bin.fill_percentage}%`;
                    // Update coloring class based on level
                    progressFluid.className = 'progress-bar progress-bar-striped progress-bar-animated bin-progress-fluid';
                    if (bin.status === 'FULL') {
                        progressFluid.classList.add('bg-danger');
                    } else if (bin.status === 'WARNING') {
                        progressFluid.classList.add('bg-warning');
                    } else {
                        progressFluid.classList.add('bg-success');
                    }
                }
                
                if (statusBadge) {
                    statusBadge.textContent = bin.status;
                    statusBadge.className = 'badge bin-status-badge';
                    if (bin.status === 'FULL') statusBadge.classList.add('badge-failed');
                    else if (bin.status === 'WARNING') statusBadge.classList.add('badge-flagged');
                    else statusBadge.classList.add('badge-sorted');
                }
            }
        });
    }
});

function setupBinActions() {
    const emptyButtons = document.querySelectorAll('.empty-bin-btn');
    
    emptyButtons.forEach(btn => {
        btn.addEventListener('click', (e) => {
            e.preventDefault();
            const binId = btn.getAttribute('data-id');
            const binName = btn.getAttribute('data-name');
            
            if (confirm(`Are you sure you want to empty the ${binName}? This will reset the fill level in the database.`)) {
                // Call API
                fetch(`/api/bins/${binId}`, {
                    method: 'PUT',
                    headers: { 'Content-Type': 'application/json' },
                    body: JSON.stringify({ current_level: 0.0 })
                })
                .then(res => res.json())
                .then(data => {
                    if (data.status === 'success') {
                        // Alert success
                        alert(`${binName} successfully emptied!`);
                        // Refresh page to be safe if socket didn't update
                        window.location.reload();
                    } else {
                        alert(`Failed to empty bin: ${data.error}`);
                    }
                })
                .catch(err => console.error("Error resetting bin level:", err));
            }
        });
    });
}

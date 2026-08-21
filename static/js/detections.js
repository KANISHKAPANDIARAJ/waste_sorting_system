document.addEventListener('DOMContentLoaded', () => {
    setupDetailModalTriggers();
});

function setupDetailModalTriggers() {
    const detailButtons = document.querySelectorAll('.view-details-btn');
    
    detailButtons.forEach(btn => {
        btn.addEventListener('click', (e) => {
            e.preventDefault();
            
            // Get attributes from clicked element
            const id = btn.getAttribute('data-id');
            const material = btn.getAttribute('data-material');
            const confidence = btn.getAttribute('data-confidence');
            const bin = btn.getAttribute('data-bin');
            const time = btn.getAttribute('data-time');
            const status = btn.getAttribute('data-status');
            const speed = btn.getAttribute('data-speed');
            const model = btn.getAttribute('data-model');
            const imgPath = btn.getAttribute('data-img');
            
            // Populate Modal elements
            const modalTitle = document.getElementById('det-modal-title');
            const modalImg = document.getElementById('det-modal-img');
            const modalMat = document.getElementById('det-modal-material');
            const modalConf = document.getElementById('det-modal-confidence');
            const modalBin = document.getElementById('det-modal-bin');
            const modalTime = document.getElementById('det-modal-time');
            const modalStatus = document.getElementById('det-modal-status');
            const modalSpeed = document.getElementById('det-modal-speed');
            const modalModel = document.getElementById('det-modal-model');
            
            if (modalTitle) modalTitle.textContent = `Detection Record #${id}`;
            if (modalImg) modalImg.src = `/${imgPath}`;
            if (modalMat) {
                modalMat.textContent = material;
                modalMat.className = `cv-meta-val highlight ${material.toLowerCase()}`;
            }
            if (modalConf) modalConf.textContent = `${(parseFloat(confidence) * 100).toFixed(1)}%`;
            if (modalBin) modalBin.textContent = bin;
            if (modalTime) modalTime.textContent = time;
            
            if (modalStatus) {
                modalStatus.textContent = status;
                modalStatus.className = `badge badge-${status.toLowerCase()}`;
            }
            if (modalSpeed) modalSpeed.textContent = `${(parseFloat(speed) * 1000).toFixed(0)} ms`;
            if (modalModel) modalModel.textContent = model;
            
            // Show Bootstrap Modal
            const myModal = new bootstrap.Modal(document.getElementById('detectionDetailsModal'));
            myModal.show();
        });
    });
}

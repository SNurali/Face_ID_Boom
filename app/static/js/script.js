const dropZone = document.getElementById('dropZone');
const fileInput = document.getElementById('fileInput');
const selectBtn = document.getElementById('selectBtn');
const previewContainer = document.getElementById('previewContainer');
const previewImage = document.getElementById('previewImage');
const resultInfo = document.getElementById('resultInfo');
const loading = document.getElementById('loading');

selectBtn.addEventListener('click', () => fileInput.click());

fileInput.addEventListener('change', handleFiles);

dropZone.addEventListener('dragover', (e) => {
    e.preventDefault();
    dropZone.classList.add('dragover');
});

dropZone.addEventListener('dragleave', () => {
    dropZone.classList.remove('dragover');
});

dropZone.addEventListener('drop', (e) => {
    e.preventDefault();
    dropZone.classList.remove('dragover');
    const files = e.dataTransfer.files;
    if (files.length > 0) handleFiles({ target: { files } });
});

function handleFiles(e) {
    const file = e.target.files[0];
    if (!file || !file.type.startsWith('image/')) return;

    const reader = new FileReader();
    reader.onload = function() {
        previewImage.src = reader.result;
        previewContainer.style.display = 'block';
        uploadPhoto(file);
    };
    reader.readAsDataURL(file);
}

async function uploadPhoto(file) {
    loading.style.display = 'block';
    resultInfo.innerHTML = '';

    const formData = new FormData();
    formData.append('file', file);

    try {
        const response = await fetch('/test-upload', {
            method: 'POST',
            body: formData
        });

        const data = await response.json();

        if (data.error) {
            resultInfo.innerHTML = `<div class="alert alert-danger">${data.error}</div>`;
        } else {
            resultInfo.innerHTML = `
                <div class="alert alert-success">
                    Лицо найдено!<br>
                    <strong>Детекция:</strong> ${data.det_score.toFixed(3)}<br>
                    <strong>Чёткость:</strong> ${data.blur.toFixed(1)}<br>
                    <strong>Размер:</strong> ${data.face_size}px<br>
                    <strong>Лиц:</strong> ${data.faces_found}
                </div>
            `;
        }
    } catch (err) {
        resultInfo.innerHTML = `<div class="alert alert-danger">Ошибка: ${err.message}</div>`;
    } finally {
        loading.style.display = 'none';
    }
}
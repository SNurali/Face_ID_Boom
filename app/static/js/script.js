let video = document.getElementById('video');
let modalVideo = document.getElementById('modalVideo');

let modeCamera = document.getElementById('modeCamera');
let modeUpload = document.getElementById('modeUpload');

let cameraBlock = document.getElementById('cameraBlock');
let uploadBlock = document.getElementById('uploadBlock');

let photoFile = document.getElementById('photoFile');
let photoPreview = document.getElementById('photoPreview');

let stream = null;

const registerModal = new bootstrap.Modal(document.getElementById('registerModal'));

// ───── CAMERA ─────
async function startCamera() {
    try {
        stream = await navigator.mediaDevices.getUserMedia({ video: true });
        video.srcObject = stream;
        modalVideo.srcObject = stream;
        await video.play();
        await modalVideo.play();
    } catch (err) {
        console.error("Ошибка доступа к камере:", err);
        alert("Не удалось включить камеру. Проверьте разрешения.");
    }
}

function captureFromCamera(videoElement) {
    if (!videoElement || videoElement.videoWidth === 0) {
        alert("Камера не готова. Попробуйте снова.");
        return null;
    }
    const c = document.createElement('canvas');
    c.width = videoElement.videoWidth;
    c.height = videoElement.videoHeight;
    c.getContext('2d').drawImage(videoElement, 0, 0);
    return c.toDataURL('image/jpeg', 0.85);
}

// ───── FILE UPLOAD (регистрация) ─────
photoFile.onchange = (e) => {
    const file = e.target.files[0];
    if (!file) return;
    const reader = new FileReader();
    reader.onload = () => {
        photoPreview.src = reader.result;
        photoPreview.classList.remove('d-none');
    };
    reader.readAsDataURL(file);
};

// ───── MODE SWITCH (регистрация) ─────
modeCamera.onchange = () => {
    cameraBlock.classList.remove('d-none');
    uploadBlock.classList.add('d-none');
};

modeUpload.onchange = () => {
    cameraBlock.classList.add('d-none');
    uploadBlock.classList.remove('d-none');
};

// ───── SEARCH MODE SWITCH & UPLOAD ─────
const searchModeCamera = document.getElementById('searchModeCamera');
const searchModeUpload = document.getElementById('searchModeUpload');
const searchCameraBlock = document.getElementById('searchCameraBlock');
const searchUploadBlock = document.getElementById('searchUploadBlock');
const searchPhotoFile = document.getElementById('searchPhotoFile');
const searchPhotoPreview = document.getElementById('searchPhotoPreview');

searchModeCamera.onchange = () => {
    searchCameraBlock.classList.remove('d-none');
    searchUploadBlock.classList.add('d-none');
};

searchModeUpload.onchange = () => {
    searchCameraBlock.classList.add('d-none');
    searchUploadBlock.classList.remove('d-none');
};

searchPhotoFile.onchange = (e) => {
    const file = e.target.files[0];
    if (!file) return;

    const reader = new FileReader();
    reader.onload = (event) => {
        searchPhotoPreview.src = event.target.result;
        searchPhotoPreview.style.display = 'block';
        searchPhotoPreview.classList.remove('d-none'); // на всякий случай
    };
    reader.readAsDataURL(file);
};

// ───── REGISTRATION ─────
document.getElementById('registerBtn').onclick = () => registerModal.show();

document.getElementById('submitRegister').onclick = async () => {
    let photoBase64 = null;

    if (modeCamera.checked) {
        photoBase64 = captureFromCamera(modalVideo);
    } else {
        if (!photoFile.files?.length) {
            alert('Загрузите фотографию');
            return;
        }
        photoBase64 = photoPreview.src;
    }

    if (!photoBase64) return;

    const payload = {
        photos_base64: photoBase64,
        full_name: document.getElementById('full_name').value,
        passport: document.getElementById('passport').value,
        gender: parseInt(document.getElementById('gender').value) || null,
        citizenship: document.getElementById('citizenship').value || null,
        birth_date: document.getElementById('birth_date').value || null,
        visa_type: document.getElementById('visa_type').value || null,
        visa_number: document.getElementById('visa_number').value || null,
        entry_date: document.getElementById('entry_date').value || null,
        exit_date: document.getElementById('exit_date').value || null
    };

    try {
        const r = await fetch('/register', {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify(payload)
        });

        if (!r.ok) {
            const e = await r.json();
            alert(e.detail || 'Ошибка регистрации');
            return;
        }

        alert('Регистрация успешна');
        registerModal.hide();
        document.getElementById('registerForm').reset();
        photoPreview.classList.add('d-none');
        photoFile.value = ''; // очищаем input file
    } catch (err) {
        alert('Ошибка соединения');
        console.error(err);
    }
};

// ───── SEARCH ─────
document.getElementById('checkDbBtn').onclick = async () => {
    let photoBase64 = null;

    if (searchModeCamera.checked) {
        photoBase64 = captureFromCamera(video);
    }
    else if (searchModeUpload.checked) {
        if (!searchPhotoFile.files?.length || !searchPhotoPreview.src || searchPhotoPreview.src === '') {
            alert('Загрузите фотографию для поиска');
            return;
        }
        photoBase64 = searchPhotoPreview.src;
    }

    if (!photoBase64) {
        alert('Изображение не готово');
        return;
    }

    try {
        const r = await fetch('/search', {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({ photos_base64: photoBase64 })
        });

        const data = await r.json();

        if (!r.ok) {
            alert(data.detail || 'Ошибка поиска');
            return;
        }

        const resultBox = document.getElementById('searchResult');
        const matchesBox = document.getElementById('searchMatches');
        matchesBox.innerHTML = '';

        if (!data.matches || !data.matches.length) {
            matchesBox.innerHTML = '<div class="text-center text-muted">Совпадений не найдено</div>';
        } else {
            data.matches.forEach(m => {
                const sim = isFinite(m.similarity) ? m.similarity.toFixed(1) + '%' : '—';
                const div = document.createElement('div');
                div.className = 'list-group-item bg-dark border-secondary text-light';
                div.innerHTML = `
                    <strong>ФИО:</strong> ${m.full_name || '—'}<br>
                    <strong>Паспорт:</strong> ${m.passport || '—'}<br>
                    <strong>Гражданство:</strong> ${m.citizenship || '—'}<br>
                    <strong>Дата рождения:</strong> ${m.birth_date || '—'}<br>
                    <strong>Тип визы:</strong> ${m.visa_type || '—'}<br>
                    <strong>Номер визы:</strong> ${m.visa_number || '—'}<br>
                    <strong>Въезд:</strong> ${m.entry_date || '—'}<br>
                    <strong>Выезд:</strong> ${m.exit_date || '—'}<br>
                    <strong>Схожесть:</strong> ${sim}
                `;
                matchesBox.appendChild(div);
            });
        }

        resultBox.style.display = 'block';

    } catch (err) {
        alert('Ошибка соединения с сервером');
        console.error(err);
    }
};

window.onload = startCamera;
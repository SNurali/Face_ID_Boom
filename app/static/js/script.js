let video = document.getElementById('video');
let modalVideo = document.getElementById('modalVideo');

let modeCamera = document.getElementById('modeCamera');
let modeUpload = document.getElementById('modeUpload');

let cameraBlock = document.getElementById('cameraBlock');
let uploadBlock = document.getElementById('uploadBlock');

let photoFile = document.getElementById('photoFile');
let photoPreview = document.getElementById('photoPreview');

let stream = null;

const registerModal = new bootstrap.Modal(
    document.getElementById('registerModal')
);

// ───── CAMERA ─────
async function startCamera() {
    stream = await navigator.mediaDevices.getUserMedia({ video: true });
    video.srcObject = stream;
    modalVideo.srcObject = stream;
    await video.play();
    await modalVideo.play();
}

function captureFromCamera() {
    const c = document.createElement('canvas');
    c.width = modalVideo.videoWidth;
    c.height = modalVideo.videoHeight;
    c.getContext('2d').drawImage(modalVideo, 0, 0);
    return c.toDataURL('image/jpeg', 0.85);
}

// ───── FILE UPLOAD ─────
photoFile.onchange = () => {
    const file = photoFile.files[0];
    if (!file) return;

    const reader = new FileReader();
    reader.onload = () => {
        photoPreview.src = reader.result;
        photoPreview.classList.remove('d-none');
    };
    reader.readAsDataURL(file);
};

// ───── MODE SWITCH ─────
modeCamera.onchange = () => {
    cameraBlock.classList.remove('d-none');
    uploadBlock.classList.add('d-none');
};

modeUpload.onchange = () => {
    cameraBlock.classList.add('d-none');
    uploadBlock.classList.remove('d-none');
};

// ───── REGISTRATION ─────
document.getElementById('registerBtn').onclick = () => registerModal.show();

document.getElementById('submitRegister').onclick = async () => {

    let photoBase64;

    if (modeCamera.checked) {
        photoBase64 = captureFromCamera();
    } else {
        if (!photoFile.files.length) {
            alert('Загрузите фотографию');
            return;
        }
        photoBase64 = photoPreview.src;
    }

    const payload = {
        photos_base64: photoBase64,
        full_name: full_name.value,
        passport: passport.value,
        gender: parseInt(gender.value),
        citizenship: citizenship.value || null,
        birth_date: birth_date.value || null,
        visa_type: visa_type.value || null,
        visa_number: visa_number.value || null,
        entry_date: entry_date.value || null,
        exit_date: exit_date.value || null
    };

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
};

window.onload = startCamera;
// ───────────── SEARCH ─────────────
document.getElementById('checkDbBtn').onclick = async () => {

    let photoBase64;

    // определяем источник фото
    if (modeCamera && modeCamera.checked) {
        photoBase64 = captureFromCamera();
    } else if (photoPreview && photoPreview.src) {
        photoBase64 = photoPreview.src;
    } else {
        alert('Нет изображения для поиска');
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

        // очистка старых результатов
        const resultBox = document.getElementById('searchResult');
        const matchesBox = document.getElementById('searchMatches');

        matchesBox.innerHTML = '';

        if (!data.matches || !data.matches.length) {
            matchesBox.innerHTML =
                '<div class="text-center text-muted">Совпадений не найдено</div>';
        } else {
            data.matches.forEach(m => {
                const sim = isFinite(m.similarity)
                    ? m.similarity.toFixed(1) + '%'
                    : '—';

                const div = document.createElement('div');
                div.className = 'list-group-item';
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

    } catch (e) {
        alert('Ошибка соединения с сервером');
        console.error(e);
    }
};

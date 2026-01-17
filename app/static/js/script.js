let video = document.getElementById('video');
let registerBtn = document.getElementById('registerBtn');
let checkDbBtn = document.getElementById('checkDbBtn');
let clearBtn = document.getElementById('clearBtn');
let statusText = document.getElementById('statusText');
let loadingSpinner = document.getElementById('loadingSpinner');
let overlay = document.getElementById('overlay');
let searchResult = document.getElementById('searchResult');
let searchMatches = document.getElementById('searchMatches');
let alertContainer = document.getElementById('alertContainer');

let stream = null;
let isProcessing = false;

const registerModal = new bootstrap.Modal(
    document.getElementById('registerModal')
);

// ────────────────────────────────────────────────
// UI helpers
// ────────────────────────────────────────────────
function showAlert(message, type = 'success') {
    const alert = document.createElement('div');
    alert.className = `alert alert-${type} alert-dismissible fade show`;
    alert.innerHTML = `
        ${message}
        <button type="button" class="btn-close" data-bs-dismiss="alert"></button>
    `;
    alertContainer.appendChild(alert);
    setTimeout(() => alert.remove(), 6000);
}

function setStatus(text, loading = false) {
    statusText.textContent = text;
    loadingSpinner.style.display = loading ? 'inline-block' : 'none';
}

// ────────────────────────────────────────────────
// Camera
// ────────────────────────────────────────────────
async function startCamera() {
    try {
        stream = await navigator.mediaDevices.getUserMedia({ video: true });
        video.srcObject = stream;
        await video.play();
        overlay.style.opacity = '0';
        setStatus('Камера готова', false);
        registerBtn.disabled = false;
        checkDbBtn.disabled = false;
    } catch (e) {
        setStatus('Нет доступа к камере', false);
        showAlert('Не удалось открыть камеру', 'danger');
    }
}

function stopCamera() {
    stream?.getTracks().forEach(t => t.stop());
}

function captureFrame() {
    const c = document.createElement('canvas');
    c.width = video.videoWidth;
    c.height = video.videoHeight;
    c.getContext('2d').drawImage(video, 0, 0);
    return c.toDataURL('image/jpeg', 0.85);
}

// ────────────────────────────────────────────────
// РЕГИСТРАЦИЯ
// ────────────────────────────────────────────────
registerBtn.addEventListener('click', () => {
    registerModal.show();
});

document.getElementById('submitRegister').addEventListener('click', async () => {
    if (isProcessing) return;
    isProcessing = true;

    try {
        setStatus('Регистрация...', true);

        const fullName = document.getElementById('full_name').value.trim();
        const passport = document.getElementById('passport').value.trim();
        const gender = parseInt(document.getElementById('gender').value, 10);

        if (!fullName || !passport || ![1, 2].includes(gender)) {
            showAlert('Заполните обязательные поля', 'danger');
            return;
        }

        const payload = {
            photos_base64: captureFrame(),
            full_name: fullName,
            passport: passport,
            gender: gender,
            citizenship: document.getElementById('citizenship').value || null,
            birth_date: document.getElementById('birth_date').value || null,
            visa_type: document.getElementById('visa_type').value || null,
            visa_number: document.getElementById('visa_number').value || null,
            entry_date: document.getElementById('entry_date').value || null,
            exit_date: document.getElementById('exit_date').value || null
        };

        const response = await fetch('/register', {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify(payload)
        });

        const data = await response.json();

        if (!response.ok) {
            throw new Error(data.detail || data.message || 'Ошибка регистрации');
        }

        showAlert('Успешно зарегистрирован', 'success');
        registerModal.hide();
        document.getElementById('registerForm').reset();

    } catch (e) {
        showAlert(e.message, 'danger');
    } finally {
        setStatus('Готово', false);
        isProcessing = false;
    }
});

// ────────────────────────────────────────────────
// ПОИСК
// ────────────────────────────────────────────────
checkDbBtn.addEventListener('click', async () => {
    if (isProcessing) return;
    isProcessing = true;

    try {
        setStatus('Поиск...', true);

        const response = await fetch('/search', {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({ photos_base64: captureFrame() })
        });

        const data = await response.json();
        searchMatches.innerHTML = '';

        if (data.matches?.length) {
            data.matches.forEach(m => {
                const similarity =
                    typeof m.similarity === 'number' && isFinite(m.similarity)
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
                        <strong>Схожесть:</strong> ${similarity}
                    `;

                searchMatches.appendChild(div);
            });
            searchResult.style.display = 'block';
        } else {
            searchMatches.innerHTML =
                '<div class="text-muted text-center py-4">Совпадений нет</div>';
            searchResult.style.display = 'block';
        }

    } catch (e) {
        showAlert('Ошибка поиска', 'danger');
    } finally {
        setStatus('Готово', false);
        isProcessing = false;
    }
});

// ────────────────────────────────────────────────
clearBtn.addEventListener('click', () => {
    searchResult.style.display = 'none';
    searchMatches.innerHTML = '';
});

window.addEventListener('load', startCamera);
window.addEventListener('beforeunload', stopCamera);

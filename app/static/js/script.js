const dropZone = document.getElementById('dropZone');
const fileInput = document.getElementById('fileInput');
const selectBtn = document.getElementById('selectBtn');
const registerBtn = document.getElementById('registerBtn');
const checkDbBtn = document.getElementById('checkDbBtn');
const clearBtn = document.getElementById('clearBtn');
const previewContainer = document.getElementById('previewContainer');
const previewImage = document.getElementById('previewImage');
const resultInfo = document.getElementById('resultInfo');
const loading = document.getElementById('loading');
const progressBar = document.getElementById('progressBar').querySelector('.progress-bar');
const searchResult = document.getElementById('searchResult');
const searchMatches = document.getElementById('searchMatches');

let selectedFile = null;

selectBtn.addEventListener('click', () => fileInput.click());
fileInput.addEventListener('change', e => handleFile(e.target.files[0]));

dropZone.addEventListener('dragover', e => {
    e.preventDefault();
    dropZone.classList.add('dragover');
});

dropZone.addEventListener('dragleave', () => dropZone.classList.remove('dragover'));

dropZone.addEventListener('drop', e => {
    e.preventDefault();
    dropZone.classList.remove('dragover');
    handleFile(e.dataTransfer.files[0]);
});

function handleFile(file) {
    if (!file || !file.type.startsWith('image/')) {
        alert("Только изображения!");
        return;
    }

    selectedFile = file;
    resultInfo.innerHTML = '';
    registerBtn.disabled = true;
    checkDbBtn.disabled = true;

    const reader = new FileReader();
    reader.onload = () => {
        previewImage.src = reader.result;
        previewContainer.style.display = 'block';
        uploadPhoto(file); // сразу проверка качества
    };
    reader.readAsDataURL(file);
}

async function uploadPhoto(file) {
    loading.style.display = 'block';
    progressBar.style.width = '0%';
    document.getElementById('progressBar').style.display = 'block';

    const formData = new FormData();
    formData.append('file', file);

    try {
        const xhr = new XMLHttpRequest();
        xhr.open('POST', '/test-upload', true);

        xhr.upload.onprogress = e => {
            if (e.lengthComputable) {
                const percent = (e.loaded / e.total) * 100;
                progressBar.style.width = percent + '%';
            }
        };

        xhr.onload = function () {
            loading.style.display = 'none';
            document.getElementById('progressBar').style.display = 'none';

            if (xhr.status !== 200) {
                resultInfo.innerHTML = `<div class="alert alert-danger">Ошибка сервера: ${xhr.status}</div>`;
                return;
            }

            const data = JSON.parse(xhr.responseText);

            if (data.error) {
                resultInfo.innerHTML = `<div class="alert alert-danger">${data.error}</div>`;
                previewImage.style.border = '5px solid red';
                previewImage.style.boxShadow = '0 0 20px red';
                return;
            }

            // Показываем обработанное фото
            previewImage.src = `data:image/jpeg;base64,${data.image_base64 || data.processed_base64}`;

            // Проверка качества
            const passedQuality = data.det_score >= 0.60 && data.blur >= 60.0 && data.face_size >= 80;
            const borderColor = passedQuality ? 'lime' : 'red';
            const statusText = passedQuality ? 'ОТЛИЧНОЕ качество ✅' : 'НЕ ПРОШЛО контроль ❌';
            const alertClass = passedQuality ? 'alert-success' : 'alert-danger';

            previewImage.style.border = `5px solid ${borderColor}`;
            previewImage.style.boxShadow = `0 0 20px ${borderColor}`;

            resultInfo.innerHTML = `
                <div class="alert ${alertClass}">
                    <strong>${statusText}</strong><br>
                    Детекция: <b>${data.det_score?.toFixed(3) || 'N/A'}</b><br>
                    Чёткость: <b>${data.blur?.toFixed(1) || 'N/A'}</b><br>
                    Размер лица: <b>${data.face_size || 'N/A'} px</b><br>
                    Лиц найдено: <b>${data.faces_found || 'N/A'}</b>
                </div>
            `;

            // Активируем кнопки только при хорошем качестве
            registerBtn.disabled = !passedQuality;
            checkDbBtn.disabled = false;
        };

        xhr.send(formData);
    } catch (err) {
        loading.style.display = 'none';
        document.getElementById('progressBar').style.display = 'none';
        resultInfo.innerHTML = `<div class="alert alert-danger">Ошибка: ${err.message}</div>`;
    }
}

// Кнопка "Зарегистрировать"
registerBtn.addEventListener('click', async () => {
    if (!selectedFile) return alert("Сначала загрузите фото");

    const payload = {
        photos_base64: [],
        full_name: document.getElementById('full_name').value.trim(),
        passport: document.getElementById('passport').value.trim(),
        sex: parseInt(document.getElementById('sex').value),
        citizen: document.getElementById('citizen').value ? parseInt(document.getElementById('citizen').value) : null,
        date_of_birth: document.getElementById('date_of_birth').value || null,
        visa_type: document.getElementById('visa_type').value || null,
        visa_number: document.getElementById('visa_number').value || null,
        visa_date_from: document.getElementById('visa_date_from').value || null,
        visa_date_to: document.getElementById('visa_date_to').value || null
    };

    if (!payload.full_name || !payload.passport || !payload.sex) {
        return alert("Заполните обязательные поля: ФИО, паспорт, пол");
    }

    loading.style.display = 'block';
    registerBtn.disabled = true;

    try {
        const reader = new FileReader();
        reader.onload = async () => {
            const base64 = reader.result.split(',')[1]; // чистый base64
            payload.photos_base64 = [base64];

            const response = await fetch('/register/', {
                method: 'POST',
                headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify(payload)
            });

            const data = await response.json();

            if (response.ok && data.person_id) {
                resultInfo.innerHTML += `
                    <div class="alert alert-success mt-3">
                        <strong>Успешно зарегистрирован!</strong><br>
                        Person ID: ${data.person_id}
                    </div>
                `;
            } else {
                resultInfo.innerHTML += `
                    <div class="alert alert-danger mt-3">
                        Ошибка регистрации: ${data.detail || 'Неизвестная ошибка'}
                    </div>
                `;
            }
        };
        reader.readAsDataURL(selectedFile);
    } catch (err) {
        resultInfo.innerHTML += `<div class="alert alert-danger mt-3">Ошибка: ${err.message}</div>`;
    } finally {
        loading.style.display = 'none';
        registerBtn.disabled = false;
    }
});

// Кнопка "Проверить в базе"
checkDbBtn.addEventListener('click', async () => {
    if (!selectedFile) return alert("Сначала загрузите фото");

    checkDbBtn.disabled = true;
    loading.style.display = 'block';

    const formData = new FormData();
    formData.append('file', selectedFile);

    try {
        const response = await fetch('/test-search', { method: 'POST', body: formData });
        const data = await response.json();

        searchResult.style.display = 'block';

        if (data.error) {
            searchMatches.innerHTML = `<div class="alert alert-danger">${data.error}</div>`;
        } else if (data.matches && data.matches.length > 0) {
            let html = '';
            data.matches.forEach(m => {
                const color = m.confidence >= 80 ? 'success' : m.confidence >= 50 ? 'warning' : 'danger';
                html += `
                    <div class="alert alert-${color} mb-2">
                        <strong>ID:</strong> ${m.person_id}<br>
                        <strong>ФИО:</strong> ${m.full_name || '—'}<br>
                        <strong>Уверенность:</strong> ${m.confidence}% (distance: ${m.distance?.toFixed(3)})
                    </div>
                `;
            });
            searchMatches.innerHTML = html;
        } else {
            searchMatches.innerHTML = '<div class="alert alert-info">Совпадений не найдено</div>';
        }
    } catch (err) {
        searchMatches.innerHTML = `<div class="alert alert-danger">Ошибка поиска: ${err.message}</div>`;
    } finally {
        loading.style.display = 'none';
        checkDbBtn.disabled = false;
    }
});

// Очистка
clearBtn.addEventListener('click', () => {
    fileInput.value = '';
    previewContainer.style.display = 'none';
    resultInfo.innerHTML = '';
    searchResult.style.display = 'none';
    registerBtn.disabled = true;
    checkDbBtn.disabled = true;
    selectedFile = null;
    previewImage.style.border = 'none';
    previewImage.style.boxShadow = 'none';
});
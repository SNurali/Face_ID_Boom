const dropZone = document.getElementById('dropZone');
const fileInput = document.getElementById('fileInput');
const selectBtn = document.getElementById('selectBtn');
const previewContainer = document.getElementById('previewContainer');
const previewImage = document.getElementById('previewImage');
const resultInfo = document.getElementById('resultInfo');
const loading = document.getElementById('loading');
const progressBar = document.getElementById('progressBar').querySelector('.progress-bar');
const saveTemplateBtn = document.getElementById('saveTemplateBtn');

let currentPersonId = null;  // для кнопки "Сохранить шаблон"

selectBtn.addEventListener('click', () => fileInput.click());

fileInput.addEventListener('change', e => handleFiles(e.target.files));

dropZone.addEventListener('dragover', e => {
    e.preventDefault();
    dropZone.classList.add('dragover');
});

dropZone.addEventListener('dragleave', () => dropZone.classList.remove('dragover'));

dropZone.addEventListener('drop', e => {
    e.preventDefault();
    dropZone.classList.remove('dragover');
    handleFiles(e.dataTransfer.files);
});

function handleFiles(files) {
    if (!files || files.length === 0) return;
    const file = files[0];
    if (!file.type.startsWith('image/')) {
        alert("Только изображения!");
        return;
    }

    const reader = new FileReader();
    reader.onload = function() {
        previewImage.src = reader.result;
        previewContainer.style.display = 'block';
        resultInfo.innerHTML = '';
        saveTemplateBtn.style.display = 'none';
        uploadPhoto(file);
    };
    reader.readAsDataURL(file);
}

async function uploadPhoto(file) {
    loading.style.display = 'block';
    progressBar.style.width = '0%';
    progressBar.parentElement.style.display = 'block';

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

        xhr.onload = function() {
            loading.style.display = 'none';
            progressBar.parentElement.style.display = 'none';

            if (xhr.status === 200) {
                const data = JSON.parse(xhr.responseText);
                if (data.error) {
                    resultInfo.innerHTML = `<div class="alert alert-danger">${data.error}</div>`;
                } else {
                    resultInfo.innerHTML = `
                        <div class="alert alert-success">
                            <strong>Обработка завершена!</strong><br>
                            Детекция: ${data.det_score.toFixed(3)}<br>
                            Чёткость: ${data.blur.toFixed(1)}<br>
                            Размер лица: ${data.face_size}px<br>
                            Лиц найдено: ${data.faces_found}
                        </div>
                    `;
                    saveTemplateBtn.style.display = 'inline-block';
                    currentPersonId = data.person_id || null; // если добавим person_id в ответ
                }
            } else {
                resultInfo.innerHTML = `<div class="alert alert-danger">Ошибка сервера: ${xhr.status}</div>`;
            }
        };

        xhr.send(formData);
    } catch (err) {
        loading.style.display = 'none';
        resultInfo.innerHTML = `<div class="alert alert-danger">Ошибка: ${err.message}</div>`;
    }
}

// Кнопка "Сохранить шаблон"
saveTemplateBtn.addEventListener('click', async () => {
    if (!currentPersonId) {
        alert("Сначала загрузите фото и дождитесь обработки");
        return;
    }

    // Здесь можно вызвать /register/ с уже обработанными данными
    // Пока просто алерт
    alert(`Шаблон для person_id ${currentPersonId} сохранён в базу!`);
    // В будущем — POST на /register с person_id и метаданными
});
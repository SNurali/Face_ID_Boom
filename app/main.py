# app/main.py
from fastapi import FastAPI, Request, File, UploadFile
from fastapi.responses import HTMLResponse
from fastapi.staticfiles import StaticFiles
from fastapi.templating import Jinja2Templates
import base64
import cv2
import numpy as np

from app.api.router_register import router as register_router
from app.api.router_search import router as search_router
from app.services.face_pipeline import get_face_embedding_strict
from app.dependencies import get_face_app

app = FastAPI(
    title="Face ID Boom",
    description="Система распознавания лиц нового поколения — Grok-powered",
    version="0.6.0 — clickhouse edition"
)

# Подключаем API-роутеры
app.include_router(register_router, prefix="/register", tags=["register"])
app.include_router(search_router, prefix="/search", tags=["search"])

# Статические файлы (css, js, изображения и т.д.)
app.mount("/static", StaticFiles(directory="app/static"), name="static")

# Jinja2 шаблоны для простого веб-интерфейса
templates = Jinja2Templates(directory="app/templates")


@app.on_event("startup")
async def startup_event():
    get_face_app()  # инициализация модели при старте


# Главная страница с формой загрузки фото
@app.get("/", response_class=HTMLResponse)
async def home(request: Request):
    return templates.TemplateResponse("index.html", {"request": request})


# Тестовый эндпоинт для загрузки и визуализации распознавания
@app.post("/test-upload")
async def test_upload(file: UploadFile = File(...)):
    try:
        contents = await file.read()
        nparr = np.frombuffer(contents, np.uint8)
        img = cv2.imdecode(nparr, cv2.IMREAD_COLOR)

        if img is None:
            return {"error": "Не удалось прочитать изображение"}

        # Запускаем строгий пайплайн
        result = get_face_embedding_strict(
            img,
            get_face_app(),
            min_det_score=0.60,
            min_face_size=80,
            min_blur=60.0
        )

        if result is None:
            # Возвращаем оригинал + ошибку
            orig_base64 = base64.b64encode(contents).decode("ascii")
            return {
                "error": "Лицо не прошло контроль качества (детекция/размер/размытие)",
                "original_image": f"data:image/jpeg;base64,{orig_base64}"
            }

        # Рисуем bbox и метрики на оригинальном изображении
        x1, y1, x2, y2 = map(int, result.meta.bbox)
        cv2.rectangle(img, (x1, y1), (x2, y2), (0, 0, 255), 3)

        text = f"Det: {result.meta.det_score:.2f} | Blur: {result.meta.blur:.1f} | Size: {result.meta.face_size}"
        cv2.putText(img, text, (x1, y1 - 10), cv2.FONT_HERSHEY_SIMPLEX, 0.7, (0, 255, 0), 2)

        # Кодируем результат в base64
        _, buffer = cv2.imencode('.jpg', img)
        processed_base64 = base64.b64encode(buffer).decode("ascii")

        return {
            "success": True,
            "processed_image": f"data:image/jpeg;base64,{processed_base64}",
            "det_score": result.meta.det_score,
            "blur": result.meta.blur,
            "face_size": result.meta.face_size,
            "faces_found": result.meta.faces_found
        }

    except Exception as e:
        return {"error": str(e)}
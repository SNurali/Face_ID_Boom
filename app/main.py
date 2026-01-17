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
    version="0.6.0 — clickhouse edition",
    redirect_slashes=False   # ← отключаем автоматический редирект /register → /register/
)

# Подключаем API-роутеры
app.include_router(register_router, prefix="/register", tags=["register"])
app.include_router(search_router, prefix="/search", tags=["search"])

# Статические файлы
app.mount("/static", StaticFiles(directory="app/static"), name="static")

# Jinja2 шаблоны
templates = Jinja2Templates(directory="app/templates")


@app.on_event("startup")
async def startup_event():
    get_face_app()  # инициализация модели при старте


@app.get("/", response_class=HTMLResponse)
async def home(request: Request):
    return templates.TemplateResponse("index.html", {"request": request})


# Тестовый эндпоинт (оставляем без изменений)
@app.post("/test-upload")
async def test_upload(file: UploadFile = File(...)):
    # ... (весь код без изменений)
    pass
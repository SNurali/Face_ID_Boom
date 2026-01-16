# app/main.py
from fastapi import FastAPI

from app.api.router_register import router as register_router
from app.api.router_search import router as search_router
# позже добавим другие роутеры, например:
# from app.api.router_verify import router as verify_router
# from app.api.router_health import router as health_router

app = FastAPI(
    title="Face ID Boom",
    description="Система распознавания лиц нового поколения — Grok-powered",
    version="0.6.0 — clickhouse edition"
)

app.include_router(register_router, prefix="/register", tags=["register"])
app.include_router(search_router, prefix="/search", tags=["search"])
# Пример как будет выглядеть добавление нового роутера:
# app.include_router(verify_router, prefix="/verify", tags=["verify"])
# app.include_router(health_router, prefix="/health", tags=["health"])


@app.on_event("startup")
async def startup_event():
    from app.dependencies import get_face_app
    get_face_app()  # инициализация при старте
# Face ID Boom

Система распознавания лиц нового поколения — **Grok-powered**  
Регистрация по фото → извлечение эмбеддинга → хранение в векторной БД → быстрый поиск

**Версия:** 0.6.0 — ClickHouse + Qdrant edition  
**Статус:** активно разрабатывается (январь 2026)

## Основные возможности

- Асинхронный API на **FastAPI**
- Строгий пайплайн обработки фото: детекция + качество (blur, det_score, face_size) + извлечение эмбеддинга
- Выбор лучшего фото при повторной регистрации одного человека
- Сохранение обрезанного лица на диск (crop по bbox)
- Поддержка ClickHouse (метаданные) + Qdrant (векторный поиск)
- Docker-compose ready (ClickHouse + Qdrant)
- Гибкая структура: schemas → services → repositories → dependencies

## Технологии

- **Backend**: FastAPI, Python 3.11+
- **Face models**: insightface / arcface (через face_app)
- **Векторные БД**: Qdrant + ClickHouse (Array(Float32))
- **Хранение фото**: локальный диск → план на S3/MinIO
- **Инфраструктура**: docker-compose, ulimits для ClickHouse

## Быстрый старт

```bash
# 1. Запустить БД
docker compose up -d

# 2. Установить зависимости
pip install -r requirements.txt

# 3. Запустить приложение
uvicorn app.main:app --reload
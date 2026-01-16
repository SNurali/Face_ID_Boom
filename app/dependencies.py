# app/dependencies.py
from fastapi import Depends, FastAPI
from insightface.app import FaceAnalysis
from app.services.database import get_clickhouse_client  # позже добавим

face_app = None

def get_face_app():
    global face_app
    if face_app is None:
        face_app = FaceAnalysis(name='buffalo_l', providers=['CPUExecutionProvider'])
        face_app.prepare(ctx_id=0)
    return face_app

def get_db_client():
    return get_clickhouse_client()
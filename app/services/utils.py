# app/services/utils.py
from uuid import uuid4

def new_uuid() -> str:
    """Генерирует новый UUID в строковом формате"""
    return str(uuid4())
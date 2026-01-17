# app/schemas/register.py

from pydantic import BaseModel
from typing import Optional


class RegisterInput(BaseModel):
    # Обязательные данные
    photos_base64: str
    full_name: str
    passport: str
    sex: int  # 1 или 2

    # Дополнительные
    citizenship: Optional[str] = None
    birth_date: Optional[str] = None

    # Виза (опционально)
    visa_type: Optional[str] = None
    visa_number: Optional[str] = None
    entry_date: Optional[str] = None
    exit_date: Optional[str] = None

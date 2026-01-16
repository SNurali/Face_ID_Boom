# app/schemas/register.py
from pydantic import BaseModel
from typing import List, Optional

class RegisterInput(BaseModel):
    photos_base64: List[str]          # массив base64-фото (1–5)
    full_name: str
    passport: str
    citizen: Optional[int] = None
    citizen_sgb: Optional[int] = None
    date_of_birth: Optional[str] = None  # "YYYY-MM-DD"
    sex: Optional[int] = None            # 1 = муж, 2 = жен
    visa_type: Optional[str] = None
    visa_number: Optional[str] = None
    visa_organ: Optional[str] = None
    visa_date_from: Optional[str] = None
    visa_date_to: Optional[str] = None
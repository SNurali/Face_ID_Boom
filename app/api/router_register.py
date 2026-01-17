# app/api/router_register.py

from fastapi import APIRouter, HTTPException, Depends, Body, Request
from pydantic import BaseModel, Field, field_validator, ValidationError as PydanticValidationError
from typing import Optional, Union
import traceback
import json
from datetime import datetime

from app.schemas.register import RegisterInput
from app.utils.validation import validate_all_register_fields, ValidationError
from app.services.provider_ingest_service import ProviderIngestService
from app.dependencies import get_face_app
from app.repositories.faceid_repo import FaceIdRepo

router = APIRouter()

# 🔧 ФЛАГ: включать/выключать строгую бизнес-валидацию
ENABLE_STRICT_VALIDATION = False   # ← ВРЕМЕННО ОТКЛЮЧЕНО


def get_ingest_service(face_app=Depends(get_face_app)):
    repo = FaceIdRepo()
    return ProviderIngestService(repo, face_app)


# =========================
# Входная модель от фронта
# =========================
class WebRegisterInput(BaseModel):
    photos_base64: Optional[str] = Field(None, description="Base64 фото из фронта")
    full_name: Optional[str] = Field(None, description="ФИО")
    passport: Optional[str] = Field(None, description="Номер паспорта")
    gender: Optional[Union[str, int]] = Field(
        None, description="Пол: 1 или 2 (строкой или числом)"
    )
    citizenship: Optional[str] = None
    birth_date: Optional[str] = None
    visa_type: Optional[str] = None
    visa_number: Optional[str] = None
    entry_date: Optional[str] = None
    exit_date: Optional[str] = None

    model_config = {
        "extra": "ignore",
        "strict": False,   # ⛔ не душим типами
    }

    @field_validator("gender", mode="before")
    @classmethod
    def normalize_gender(cls, v):
        if v is None:
            return None
        return str(v)


# =========================
# Роут регистрации
# =========================
@router.post("")
async def register_person(
    request: Request,
    raw_body: dict = Body(...),
    service: ProviderIngestService = Depends(get_ingest_service),
):
    timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S.%f")[:-3]
    log_prefix = f"[{timestamp}] REGISTER "

    print(f"\n{log_prefix}══════════════════════════════════════════════")

    # 1. Сырой JSON
    try:
        print(json.dumps(raw_body, indent=2, ensure_ascii=False))
    except Exception:
        pass

    # 2. Парсинг (Pydantic остаётся)
    try:
        input_data = WebRegisterInput(**raw_body)
    except PydanticValidationError as ve:
        raise HTTPException(422, detail=ve.errors())

    # 3. Минимальные проверки (ОСТАВЛЯЕМ)
    try:
        if not input_data.photos_base64:
            raise ValueError("photos_base64 обязательно")

        if not input_data.full_name or not input_data.full_name.strip():
            raise ValueError("full_name обязательно")

        if not input_data.passport or not input_data.passport.strip():
            raise ValueError("passport обязательно")

        # Пол оставляем обязательным
        if input_data.gender is None:
            raise ValueError("Пол обязателен (1 или 2)")

        sex = int(input_data.gender)
        if sex not in (1, 2):
            raise ValueError("Пол должен быть 1 или 2")

        register_data = RegisterInput(
            photos_base64=input_data.photos_base64,
            full_name=input_data.full_name.strip(),
            passport=input_data.passport.strip(),
            sex=sex,
            citizenship=input_data.citizenship,
            birth_date=input_data.birth_date,
            visa_type=input_data.visa_type,
            visa_number=input_data.visa_number,
            entry_date=input_data.entry_date,
            exit_date=input_data.exit_date,
        )

    except ValueError as ve:
        raise HTTPException(400, detail=str(ve))

    # 4. ❌/✅ Кастомная бизнес-валидация (ПЕДАНТ)
    if ENABLE_STRICT_VALIDATION:
        try:
            validate_all_register_fields(register_data)
        except ValidationError as ve:
            raise HTTPException(
                status_code=400,
                detail=f"{ve.field or 'general'}: {ve.message}",
            )
    else:
        print(f"{log_prefix}⚠️ STRICT VALIDATION DISABLED")

    # 5. Сохранение
    try:
        person_id = await service.ingest(register_data)
        return {
            "status": "ok",
            "person_id": person_id,
            "data": register_data.model_dump(),
        }
    except Exception as e:
        traceback.print_exc()
        raise HTTPException(500, detail=str(e))

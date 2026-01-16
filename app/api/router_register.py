# app/api/router_register.py
from fastapi import APIRouter, HTTPException, Depends
from app.schemas.register import RegisterInput
from app.utils.validation import validate_all_register_fields, ValidationError
from app.services.provider_ingest_service import ProviderIngestService
from app.dependencies import get_face_app
from app.repositories.faceid_repo import FaceIdRepo
router = APIRouter()

def get_ingest_service(face_app = Depends(get_face_app)):
    repo = FaceIdRepo()  # без None — используем реальный клиент
    return ProviderIngestService(repo, face_app)

@router.post("/")
async def register_person(
    input: RegisterInput,
    service: ProviderIngestService = Depends(get_ingest_service)
):
    try:
        validate_all_register_fields(input)
        person_id = await service.ingest(input)
        return {
            "status": "ok",
            "message": "Зарегистрировано успешно",
            "person_id": person_id
        }
    except ValidationError as e:
        raise HTTPException(400, detail=f"{e.field or 'error'}: {e.message}")
    except Exception as e:
        raise HTTPException(500, detail=str(e))
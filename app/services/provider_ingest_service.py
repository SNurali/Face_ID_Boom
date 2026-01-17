from dataclasses import dataclass
from typing import Optional, List
import os
import uuid
import base64
import asyncio
import numpy as np
import cv2

from app.schemas.register import RegisterInput
from app.repositories.faceid_repo import FaceIdRepo
from app.services.face_pipeline import get_face_embedding_strict
from app.services.utils import new_uuid


# ────────────────────────────────────────────────
# Константы статусов embedding
# ────────────────────────────────────────────────
EMB_OK = 1
EMB_NONE = 0
EMB_FAILED = 2

IMAGES_DIR = "images/persons"
os.makedirs(IMAGES_DIR, exist_ok=True)


# ────────────────────────────────────────────────
# DTO результата обработки фото
# ────────────────────────────────────────────────
@dataclass
class PhotoResult:
    face_url: Optional[str] = None
    embedding: Optional[List[float]] = None
    embedding_status: int = EMB_NONE
    det_score: float = 0.0
    blur: float = 0.0
    face_size: int = 0
    faces_found: int = 0


def quality_score(p: PhotoResult) -> float:
    """
    Итоговый скор качества фото (используется при сравнении снимков)
    """
    return (
        (p.det_score * 100.0)
        + (min(p.blur, 300.0) * 0.2)
        + (min(p.face_size, 200) * 0.5)
    )


# ────────────────────────────────────────────────
# Основной ingest-сервис
# ────────────────────────────────────────────────
class ProviderIngestService:
    def __init__(self, repo: FaceIdRepo, face_app):
        self.repo = repo
        self.face_app = face_app

    # ────────────────────────────────────────────
    # Обработка фото
    # ────────────────────────────────────────────
    async def process_photo(self, input: RegisterInput) -> PhotoResult:
        if not input.photos_base64:
            return PhotoResult(embedding_status=EMB_NONE)

        try:
            photo_b64 = input.photos_base64

            if "," in photo_b64:
                _, photo_b64 = photo_b64.split(",", 1)

            img_bytes = base64.b64decode(photo_b64)
            nparr = np.frombuffer(img_bytes, np.uint8)
            img = cv2.imdecode(nparr, cv2.IMREAD_COLOR)

            if img is None:
                raise ValueError("Не удалось декодировать изображение")

            result = await asyncio.to_thread(
                get_face_embedding_strict,
                img,
                self.face_app,
                min_det_score=0.60,
                min_face_size=80,
                min_blur=60.0,
            )

            if result is None:
                print("Фото не прошло quality gates")
                return PhotoResult(embedding_status=EMB_FAILED)

            # сохраняем кроп лица
            tmp_id = str(uuid.uuid4())
            face_filename = f"{tmp_id}.jpg"
            face_path = os.path.join(IMAGES_DIR, face_filename)

            x1, y1, x2, y2 = result.meta.bbox
            crop = img[int(y1):int(y2), int(x1):int(x2)]
            cv2.imwrite(face_path, crop, [int(cv2.IMWRITE_JPEG_QUALITY), 85])

            return PhotoResult(
                face_url=face_path,
                embedding=result.embedding,
                embedding_status=EMB_OK,
                det_score=result.meta.det_score,
                blur=result.meta.blur,
                face_size=result.meta.face_size,
                faces_found=result.meta.faces_found,
            )

        except Exception as e:
            print(f"Ошибка обработки фото: {str(e)}")
            return PhotoResult(embedding_status=EMB_FAILED)

    # ────────────────────────────────────────────
    # INGEST (РЕГИСТРАЦИЯ)
    # ────────────────────────────────────────────
    async def ingest(self, input: RegisterInput) -> str:
        person_id = str(new_uuid())

        photo_result = await self.process_photo(input)

        # 🔥 ГЛАВНОЕ ИСПРАВЛЕНИЕ:
        # если фото не прошло quality gates — НЕ сохраняем запись
        if photo_result.embedding_status != EMB_OK or not photo_result.embedding:
            raise ValueError("Фото не прошло проверку качества. Регистрация отклонена.")

        snapshot = {
            "person_id": person_id,
            "full_name": input.full_name,
            "passport": input.passport,
            "sex": input.sex,
            "citizenship": input.citizenship,
            "birth_date": input.birth_date,
            "visa_type": input.visa_type,
            "visa_number": input.visa_number,
            "entry_date": input.entry_date,
            "exit_date": input.exit_date,

            # face / embedding
            "embedding": photo_result.embedding,
            "face_url": photo_result.face_url,
            "embedding_status": photo_result.embedding_status,
            "det_score": photo_result.det_score,
            "blur": photo_result.blur,
            "face_size": photo_result.face_size,
            "faces_found": photo_result.faces_found,
        }

        self.repo.insert_document_snapshot(snapshot)

        return person_id

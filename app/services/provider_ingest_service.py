from dataclasses import dataclass
from typing import Optional
import os
import uuid
import base64
import asyncio
import numpy as np
import cv2

from app.schemas.register import RegisterInput
from app.repositories.faceid_repo import FaceIdRepo
from app.services.face_pipeline import get_face_embedding_strict
from app.services.utils import new_uuid  # создадим позже

EMB_OK = 1
EMB_NONE = 0
EMB_FAILED = 2


@dataclass
class PhotoResult:
    face_url: Optional[str] = None
    polygons: list[float] = None  # TODO: переименовать в embedding или embedding_vector
    embedding_status: int = EMB_NONE
    det_score: float = 0.0
    blur: float = 0.0
    face_size: int = 0
    faces_found: int = 0


def quality_score(p: PhotoResult) -> float:
    return (p.det_score * 100.0) + (min(p.blur, 300.0) * 0.2) + (min(p.face_size, 200) * 0.5)


IMAGES_DIR = "images/persons"


class ProviderIngestService:
    def __init__(self, repo: FaceIdRepo, face_app):
        self.repo = repo
        self.face_app = face_app

        # Создаём директорию один раз при инициализации сервиса
        os.makedirs(IMAGES_DIR, exist_ok=True)

    async def process_photo(self, input: RegisterInput) -> PhotoResult:
        if not input.photos_base64 or len(input.photos_base64) == 0:
            return PhotoResult(embedding_status=EMB_NONE)

        photo_b64 = input.photos_base64[0]  # берём первое фото

        try:
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
                min_blur=60.0
            )

            if result is None:
                print("Фото не прошло quality gates")
                return PhotoResult(embedding_status=EMB_FAILED)

            # Сохраняем обрезанное лицо
            person_id_temp = str(uuid.uuid4())  # временный ID, позже заменишь на настоящий
            face_filename = f"{person_id_temp}.jpg"
            face_path = os.path.join("images/persons", face_filename)

            x1, y1, x2, y2 = result.meta.bbox
            crop = img[int(y1):int(y2), int(x1):int(x2)]
            cv2.imwrite(face_path, crop, [int(cv2.IMWRITE_JPEG_QUALITY), 85])

            print(f"Сохранено фото лица: {face_path}")

            return PhotoResult(
                face_url=face_path,  # путь на диске (можно потом сделать URL)
                polygons=result.embedding,
                embedding_status=EMB_OK,
                det_score=result.meta.det_score,
                blur=result.meta.blur,
                face_size=result.meta.face_size,
                faces_found=result.meta.faces_found
            )

        except Exception as e:
            print(f"Ошибка обработки фото: {str(e)}")
            return PhotoResult(embedding_status=EMB_FAILED)

    def choose_best_photo(self, new_photo: PhotoResult, old_photo: PhotoResult) -> PhotoResult:
        if old_photo.embedding_status != EMB_OK:
            return new_photo

        new_q = quality_score(new_photo)
        old_q = quality_score(old_photo)

        if new_q + 5.0 < old_q:
            return old_photo

        return new_photo

    async def ingest(self, input: RegisterInput) -> str:
        person_id = self.repo.get_person_id_by_sgb(input.citizen_sgb or 0) or str(new_uuid())

        old_best = self.repo.get_latest_face_payload(person_id) or PhotoResult()

        new_photo = await self.process_photo(input)

        best_photo = self.choose_best_photo(new_photo, old_best)

        # Сохраняем snapshot (заглушка — позже расширим)
        snapshot = {
            "person_id": person_id,
            "full_name": input.full_name,
            "passport": input.passport,
            "citizen": input.citizen,
            "date_of_birth": input.date_of_birth,
            "det_score": best_photo.det_score,
            "blur": best_photo.blur,
            "face_size": best_photo.face_size,
            "faces_found": best_photo.faces_found,
            # очень рекомендуется добавить:
            # "face_url": best_photo.face_url,
            # "embedding_status": best_photo.embedding_status,
        }
        self.repo.insert_document_snapshot(snapshot)

        return person_id
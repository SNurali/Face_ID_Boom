from typing import Dict, Any, List
import base64
import numpy as np
import cv2
import asyncio

from app.services.face_pipeline import get_face_embedding_strict
from app.repositories.faceid_repo import FaceIdRepo


class SearchService:
    def __init__(self, repo: FaceIdRepo, face_app):
        self.repo = repo
        self.face_app = face_app

    async def search_by_image_b64(
        self,
        image_b64: str,
        top_k: int = 5,
        threshold: float = 0.6,
    ) -> Dict[str, Any]:
        """
        Поиск человека по фото (base64)
        """

        if not image_b64:
            return {
                "status": "error",
                "message": "photos_base64 пустой",
                "matches": [],
            }

        try:
            # Убираем data:image/...;base64,
            if "," in image_b64:
                _, image_b64 = image_b64.split(",", 1)

            img_bytes = base64.b64decode(image_b64)
            nparr = np.frombuffer(img_bytes, np.uint8)
            img = cv2.imdecode(nparr, cv2.IMREAD_COLOR)

            if img is None:
                raise ValueError("Не удалось декодировать изображение")

            # Получаем embedding для поиска
            result = await asyncio.to_thread(
                get_face_embedding_strict,
                img,
                self.face_app,
                min_det_score=0.45,
                min_face_size=60,
                min_blur=40.0,
            )

            if result is None or not result.embedding:
                return {
                    "status": "ok",
                    "message": "Лицо не прошло quality gates",
                    "matches": [],
                }

            query_embedding = np.array(result.embedding, dtype=np.float32)

            # 🔒 ЗАЩИТА: NaN / Inf в embedding запроса
            if np.any(np.isnan(query_embedding)) or np.any(np.isinf(query_embedding)):
                return {
                    "status": "ok",
                    "message": "Embedding запроса некорректен",
                    "matches": [],
                }

            q_norm = np.linalg.norm(query_embedding)
            if q_norm == 0.0:
                return {
                    "status": "ok",
                    "message": "Embedding запроса нулевой",
                    "matches": [],
                }

            # Забираем кандидатов из БД
            candidates = self.repo.get_all_face_embeddings()

            matches: List[Dict[str, Any]] = []

            for c in candidates:
                emb = c.get("embedding")
                if not emb:
                    continue

                db_embedding = np.array(emb, dtype=np.float32)

                # 🔒 ЗАЩИТА: NaN / Inf в embedding из БД
                if np.any(np.isnan(db_embedding)) or np.any(np.isinf(db_embedding)):
                    continue

                d_norm = np.linalg.norm(db_embedding)
                if d_norm == 0.0:
                    continue

                score = float(
                    np.dot(query_embedding, db_embedding) / (q_norm * d_norm)
                )

                # 🔒 ФИНАЛЬНАЯ ЗАЩИТА
                if not np.isfinite(score):
                    continue

                if score >= threshold:
                    matches.append(
                        {
                            # --- Идентификация ---
                            "person_id": c.get("person_id"),
                            "full_name": c.get("full_name"),
                            "passport": c.get("passport"),

                            # --- Доп. данные ---
                            "citizenship": c.get("citizenship"),
                            "birth_date": c.get("birth_date"),
                            "visa_type": c.get("visa_type"),
                            "visa_number": c.get("visa_number"),
                            "entry_date": c.get("entry_date"),
                            "exit_date": c.get("exit_date"),

                            # --- Face данные ---
                            "face_url": c.get("face_url"),

                            # --- Схожесть (ВСЕГДА число) ---
                            "similarity": round(score * 100, 2),
                        }
                    )

            # Сортируем по убыванию схожести
            matches.sort(key=lambda x: x["similarity"], reverse=True)

            return {
                "status": "ok",
                "message": "Поиск выполнен",
                "matches": matches[:top_k],
            }

        except Exception as e:
            print(f"Ошибка поиска: {str(e)}")
            return {
                "status": "error",
                "message": str(e),
                "matches": [],
            }

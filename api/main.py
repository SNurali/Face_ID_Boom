from fastapi import FastAPI, HTTPException
from insightface.app import FaceAnalysis
import base64
from pydantic import BaseModel
from typing import Optional, List
import numpy as np
import cv2
from datetime import datetime
import chromadb

app = FastAPI(
    title="Face ID Boom",
    description="Система распознавания лиц нового поколения — JPG-Style Production-powered, лучше конкурентов",
    version="0.6.1 — Chroma + multi-template"
)

# Инициализация InsightFace
face_app = FaceAnalysis(name='buffalo_l', providers=['CPUExecutionProvider'])
face_app.prepare(ctx_id=0)

# Качество фото
MIN_DET_SCORE = 0.60
MIN_FACE_SIZE = 80
MIN_BLUR_SCORE = 60.0

# Chroma
chroma_client = chromadb.PersistentClient(path="./chroma_db")
collection = chroma_client.get_or_create_collection(
    name="face_id_boom",
    metadata={"hnsw:space": "cosine"}
)

class RegisterInput(BaseModel):
    photos_base64: List[str] = []  # массив фото (1–5)
    photo_base64: Optional[str] = None  # совместимость с single photo
    full_name: str
    passport: str
    citizen: Optional[int] = None
    date_of_birth: Optional[str] = None

class SearchInput(BaseModel):
    photo_base64: str
    top_k: Optional[int] = 5
    threshold: Optional[float] = 0.35

def extract_best_embedding(img: np.ndarray) -> Optional[np.ndarray]:
    faces = face_app.get(img)
    if not faces:
        return None

    best_face = None
    best_score = -1

    for face in faces:
        bbox = face.bbox.astype(int)
        x1, y1, x2, y2 = bbox
        face_w, face_h = x2 - x1, y2 - y1
        face_size = min(face_w, face_h)

        if face_w > 0 and face_h > 0:
            crop = img[y1:y2, x1:x2]
            gray = cv2.cvtColor(crop, cv2.COLOR_BGR2GRAY)
            blur_var = cv2.Laplacian(gray, cv2.CV_64F).var()
        else:
            blur_var = 0.0

        if (float(face.det_score) >= MIN_DET_SCORE and
            face_size >= MIN_FACE_SIZE and
            blur_var >= MIN_BLUR_SCORE and
            face.det_score > best_score):
            best_score = face.det_score
            best_face = face

    return best_face.embedding if best_face else None

@app.get("/")
async def root():
    return {"message": "Face ID Boom запущен! 🚀 JPG-Style Prodution 😈"}

@app.post("/register")
async def register_person(input: RegisterInput):
    try:
        # Совместимость: если single photo, преобразуем в массив
        photos = input.photos_base64
        if input.photo_base64 and not photos:
            photos = [input.photo_base64]

        if not 1 <= len(photos) <= 5:
            raise HTTPException(400, "Отправьте от 1 до 5 фото")

        embeddings = []
        for idx, photo_b64 in enumerate(photos):
            img_bytes = base64.b64decode(photo_b64)
            nparr = np.frombuffer(img_bytes, np.uint8)
            img = cv2.imdecode(nparr, cv2.IMREAD_COLOR)

            if img is None:
                raise HTTPException(400, f"Не удалось декодировать фото #{idx+1}")

            emb = extract_best_embedding(img)
            if emb is None:
                raise HTTPException(400, f"Фото #{idx+1} не прошло контроль качества")

            embeddings.append(emb)

        # Усредняем эмбеддинги
        avg_embedding = np.mean(embeddings, axis=0)
        num_templates = len(embeddings)

        # Получаем следующий ID
        count = collection.count()
        point_id = str(count + 1)

        payload = {
            "full_name": input.full_name.strip(),
            "passport": input.passport.strip(),
            "citizen": input.citizen,
            "date_of_birth": input.date_of_birth,
            "registered_at": datetime.now().isoformat(),
            "num_templates": num_templates
        }

        collection.add(
            ids=[point_id],
            embeddings=[avg_embedding.tolist()],
            metadatas=[payload],
            documents=[input.full_name]
        )

        return {
            "status": "registered",
            "point_id": point_id,
            "full_name": input.full_name,
            "passport": input.passport,
            "num_templates": num_templates
        }

    except Exception as e:
        raise HTTPException(500, str(e))

@app.post("/search")
async def search_faces(input: SearchInput):
    try:
        img_bytes = base64.b64decode(input.photo_base64)
        nparr = np.frombuffer(img_bytes, np.uint8)
        img = cv2.imdecode(nparr, cv2.IMREAD_COLOR)

        if img is None:
            raise HTTPException(400, "Не удалось декодировать изображение")

        query_embedding = extract_best_embedding(img)
        if query_embedding is None:
            raise HTTPException(400, "Нет подходящего лица (качество не прошло)")

        search_result = collection.query(
            query_embeddings=[query_embedding.tolist()],
            n_results=input.top_k,
            include=["metadatas", "distances"]
        )

        matches = []
        for idx in range(len(search_result["ids"][0])):
            payload = search_result["metadatas"][0][idx] or {}
            distance = search_result["distances"][0][idx]
            confidence = (1.0 - distance) * 100

            matches.append({
                "point_id": search_result["ids"][0][idx],
                "full_name": payload.get("full_name"),
                "passport": payload.get("passport"),
                "citizen": payload.get("citizen"),
                "date_of_birth": payload.get("date_of_birth"),
                "distance": round(distance, 4),
                "confidence": round(confidence, 2),
                "registered_at": payload.get("registered_at"),
                "num_templates": payload.get("num_templates", 1)
            })

        # Фильтруем по порогу
        filtered_matches = [m for m in matches if m["distance"] <= input.threshold]

        return {
            "status": "ok",
            "query_quality_passed": True,
            "total_matches": len(filtered_matches),
            "matches": filtered_matches,
            "raw_matches_count": len(matches),  # для понимания, сколько нашлось до фильтра
            "threshold_used": input.threshold
        }

    except Exception as e:
        raise HTTPException(500, str(e))

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000, reload=True)
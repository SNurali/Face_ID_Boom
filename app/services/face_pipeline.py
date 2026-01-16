# app/services/face_pipeline.py
from __future__ import annotations
from dataclasses import dataclass
from typing import Optional, Tuple

import cv2
import numpy as np
from insightface.app import FaceAnalysis

EMB_SIZE = 512

@dataclass
class FaceMeta:
    det_score: float
    bbox: Tuple[int, int, int, int]
    face_size: int
    blur: float
    faces_found: int

@dataclass
class FaceEmbeddingResult:
    embedding: list[float]
    meta: FaceMeta

def _blur_score(image_bgr: np.ndarray) -> float:
    gray = cv2.cvtColor(image_bgr, cv2.COLOR_BGR2GRAY)
    return float(cv2.Laplacian(gray, cv2.CV_64F).var())

def _clamp_bbox(b: Tuple[float, float, float, float], w: int, h: int) -> Tuple[int, int, int, int]:
    x1, y1, x2, y2 = map(int, b)
    return (
        max(0, min(x1, w - 1)),
        max(0, min(y1, h - 1)),
        max(0, min(x2, w)),
        max(0, min(y2, h))
    )

def add_margin(image: np.ndarray, margin_ratio: float = 0.05) -> np.ndarray:
    h, w = image.shape[:2]
    top = bottom = int(h * margin_ratio)
    left = right = int(w * margin_ratio)
    color = [255, 255, 255]
    return cv2.copyMakeBorder(image, top, bottom, left, right,
                              borderType=cv2.BORDER_CONSTANT, value=color)

def get_face_embedding_strict(
    image_bgr: np.ndarray,
    face_app: FaceAnalysis,
    *,
    min_det_score: float = 0.60,
    min_face_size: int = 80,
    min_blur: float = 60.0
) -> Optional[FaceEmbeddingResult]:
    """
    Извлекает лучшее лицо с жёсткими проверками качества.
    Возвращает embedding + метаданные или None, если качество не прошло.
    """
    image_bgr = add_margin(image_bgr)
    faces = face_app.get(image_bgr)
    if not faces:
        return None

    best_face = None
    best_score = -1.0

    h, w = image_bgr.shape[:2]

    for face in faces:
        det_score = float(face.det_score)
        bbox_raw = face.bbox
        bbox = _clamp_bbox(bbox_raw, w, h)

        x1, y1, x2, y2 = bbox
        face_w, face_h = x2 - x1, y2 - y1
        face_size = min(face_w, face_h)

        if face_w <= 0 or face_h <= 0:
            continue

        crop = image_bgr[y1:y2, x1:x2]
        blur = _blur_score(crop)

        if (det_score >= min_det_score and
            face_size >= min_face_size and
            blur >= min_blur and
            det_score > best_score):
            best_score = det_score
            best_face = face

    if best_face is None:
        return None

    embedding = best_face.normed_embedding.tolist()
    if len(embedding) != EMB_SIZE:
        return None

    meta = FaceMeta(
        det_score=best_score,
        bbox=bbox,
        face_size=face_size,
        blur=blur,
        faces_found=len(faces)
    )

    return FaceEmbeddingResult(embedding=embedding, meta=meta)
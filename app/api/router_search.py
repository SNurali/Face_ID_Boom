# app/api/router_search.py

from fastapi import APIRouter, HTTPException, Depends, Body
from pydantic import BaseModel
from typing import Optional

from app.dependencies import get_face_app
from app.repositories.faceid_repo import FaceIdRepo
from app.services.search_service import SearchService

router = APIRouter()   # ← БЕЗ prefix


class SearchRequest(BaseModel):
    photos_base64: str
    threshold: Optional[float] = 0.6


@router.post("")
async def search_person(
    data: SearchRequest = Body(...),
    face_app=Depends(get_face_app),
):
    service = SearchService(
        repo=FaceIdRepo(),
        face_app=face_app,
    )

    return await service.search_by_image_b64(
        image_b64=data.photos_base64,
        threshold=data.threshold,
    )

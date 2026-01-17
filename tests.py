import json
from datetime import datetime

from fastapi import Body, Depends

from app.api.router_register import WebRegisterInput, router, get_ingest_service
from app.schemas.register import RegisterInput
from app.services.provider_ingest_service import ProviderIngestService


@router.post("")
async def register_person(
        raw_body: dict = Body(...),
        service: ProviderIngestService = Depends(get_ingest_service)
):
    print("\n" + "═" * 120)
    print(f"[{datetime.now().strftime('%Y-%m-%d %H:%M:%S')}] POST /register")

    # 1. Что реально пришло
    print("Полученный JSON:")
    print(json.dumps(raw_body, indent=2, ensure_ascii=False))

    # 2. Что ожидает WebRegisterInput
    print("\nОжидаемая структура WebRegisterInput:")
    print(json.dumps(WebRegisterInput.model_json_schema(), indent=2, ensure_ascii=False))

    # 3. Что ожидает RegisterInput (если используешь её дальше)
    print("\nОжидаемая структура RegisterInput:")
    print(json.dumps(RegisterInput.model_json_schema(), indent=2, ensure_ascii=False))

    print("═" * 120 + "\n")

    # Если хочешь продолжить обработку — раскомментируй
    # try:
    #     input_data = WebRegisterInput(**raw_body)
    #     register_data = RegisterInput(...)
    #     ...
    # except Exception as e:
    #     print("Ошибка парсинга:", str(e))
    #     raise HTTPException(422, detail=str(e))

    return {
        "status": "диагностика",
        "received": raw_body,
        "web_schema": WebRegisterInput.model_json_schema(),
        "register_schema": RegisterInput.model_json_schema()
    }
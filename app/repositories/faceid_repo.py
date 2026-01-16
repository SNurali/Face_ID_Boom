from typing import Optional, Dict, Any
from uuid import uuid4
from app.services.database import get_clickhouse_client

class FaceIdRepo:
    def __init__(self):
        self.client = get_clickhouse_client()  # теперь клиент берётся автоматически

    def get_person_id_by_sgb(self, sgb_person_id: int) -> Optional[str]:
        # Пока заглушка — позже заменим на реальный ClickHouse-запрос
        return str(uuid4())  # временно генерируем новый

    def insert_person(self, person_id: str) -> None:
        print(f"Inserted person {person_id}")

    def upsert_sgb_map(self, sgb_person_id: int, person_id: str, is_active: int = 1) -> None:
        print(f"Mapped sgb {sgb_person_id} → person {person_id}")

    def get_latest_face_payload(self, person_id: str) -> Optional[Dict[str, Any]]:
        # Заглушка — вернём старые метрики или None
        return None  # пока нет данных

    def insert_document_snapshot(self, row: Dict[str, Any]) -> None:
        print("Inserted document snapshot:", row)

    def insert_border_event(self, row: Dict[str, Any]) -> None:
        print("Inserted border event:", row)
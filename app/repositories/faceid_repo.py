from typing import Optional, Dict, Any, List
from uuid import uuid4
from app.services.database import get_clickhouse_client


class FaceIdRepo:
    def __init__(self):
        self.client = get_clickhouse_client()

    # ────────────────────────────────────────────────
    # Legacy / заглушки (оставляем)
    # ────────────────────────────────────────────────
    def get_person_id_by_sgb(self, sgb_person_id: int) -> Optional[str]:
        return None

    def insert_person(self, person_id: str) -> None:
        print(f"Inserted person {person_id}")

    def upsert_sgb_map(
        self,
        sgb_person_id: int,
        person_id: str,
        is_active: int = 1,
    ) -> None:
        print(f"Mapped sgb {sgb_person_id} → person {person_id}")

    # ────────────────────────────────────────────────
    # Используется при ingest
    # ────────────────────────────────────────────────
    def get_latest_face_payload(self, person_id: str) -> Optional[Dict[str, Any]]:
        query = """
        SELECT
            person_id,
            embedding,
            full_name,
            passport,
            face_url
        FROM face_snapshots
        WHERE person_id = %(person_id)s
        ORDER BY created_at DESC
        LIMIT 1
        """
        rows = self.client.execute(query, {"person_id": person_id})
        if not rows:
            return None

        row = rows[0]
        return {
            "person_id": row[0],
            "embedding": row[1],
            "full_name": row[2],
            "passport": row[3],
            "face_url": row[4],
        }

    def insert_document_snapshot(self, row: Dict[str, Any]) -> None:
        query = """
                INSERT INTO face_id_boom.face_snapshots
                (person_id, \
                 full_name, \
                 passport, \
                 sex, \
                 citizenship, \
                 birth_date, \
                 visa_type, \
                 visa_number, \
                 entry_date, \
                 exit_date, \
                 face_url, \
                 embedding, \
                 embedding_status, \
                 det_score, \
                 blur, \
                 face_size, \
                 faces_found)
                VALUES \
                """

        self.client.execute(
            query,
            [
                (
                    row.get("person_id"),
                    row.get("full_name"),
                    row.get("passport"),
                    row.get("sex"),
                    row.get("citizenship"),
                    row.get("birth_date"),
                    row.get("visa_type"),
                    row.get("visa_number"),
                    row.get("entry_date"),
                    row.get("exit_date"),
                    row.get("face_url"),
                    row.get("embedding"),
                    row.get("embedding_status"),
                    row.get("det_score"),
                    row.get("blur"),
                    row.get("face_size"),
                    row.get("faces_found"),
                )
            ],
        )

        print("Inserted document snapshot:", row.get("person_id"))

    def insert_border_event(self, row: Dict[str, Any]) -> None:
        print("Inserted border event:", row)

    # ────────────────────────────────────────────────
    # 🔥 КЛЮЧЕВОЙ МЕТОД ДЛЯ SEARCH
    # ────────────────────────────────────────────────
    def get_all_face_embeddings(self):
        query = """
                SELECT person_id, \
                       full_name, \
                       passport, \
                       citizenship, \
                       birth_date, \
                       visa_type, \
                       visa_number, \
                       entry_date, \
                       exit_date, \
                       face_url, \
                       embedding
                FROM face_id_boom.face_snapshots
                WHERE embedding IS NOT NULL \
                """
        rows = self.client.execute(query)

        results = []

        for r in rows:
            results.append(
                {
                    "person_id": r[0],
                    "full_name": r[1],
                    "passport": r[2],
                    "citizenship": r[3],
                    "birth_date": r[4],
                    "visa_type": r[5],
                    "visa_number": r[6],
                    "entry_date": r[7],
                    "exit_date": r[8],
                    "face_url": r[9],
                    "embedding": r[10],
                }
            )

        return results


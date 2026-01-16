# db_init.py
from app.services.database import get_clickhouse_client

client = get_clickhouse_client()

client.execute("""
CREATE TABLE IF NOT EXISTS person_documents_v2 (
    id String,
    person_id String,
    citizen UInt32,
    citizen_sgb UInt32,
    dtb Date32,
    passport String,
    passport_expired Date32,
    sex UInt8,
    full_name String,
    face_url String,
    polygons Array(Float32),
    embedding_status UInt8,
    det_score Float32,
    blur Float32,
    face_size UInt32,
    faces_found UInt32,
    version DateTime DEFAULT now()
) ENGINE = ReplacingMergeTree(version)
ORDER BY (person_id, version);
""")

client.execute("""
CREATE TABLE IF NOT EXISTS person_borders_v2 (
    id String,
    border_id UInt64,
    person_id String,
    reg_date DateTime,
    direction_country UInt32,
    direction_country_sgb UInt32,
    visa_type String,
    visa_number String,
    visa_organ String,
    visa_date_from Date32,
    visa_date_to Date32,
    action UInt8,
    kpp String,
    version DateTime DEFAULT now()
) ENGINE = ReplacingMergeTree(version)
ORDER BY (person_id, border_id, action, version);
""")

client.execute("""
CREATE TABLE IF NOT EXISTS person_sgb_map_v2 (
    sgb_person_id UInt64,
    person_id String,
    is_active UInt8 DEFAULT 1,
    version DateTime DEFAULT now()
) ENGINE = ReplacingMergeTree(version)
ORDER BY (sgb_person_id, version);
""")

print("Таблицы созданы успешно")
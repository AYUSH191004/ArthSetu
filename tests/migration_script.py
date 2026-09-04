from sqlalchemy import create_engine, text

engine = create_engine(
    "postgresql+psycopg2://arthsetu_admin:pgadmin%4012345@localhost:5432/arthsetu"
)

with engine.connect() as conn:
    sample = conn.execute(text("""
        SELECT id, normalized_payload
        FROM source_record
        LIMIT 3
    """)).fetchall()

    for row in sample:
        print(type(row[1]), row[1])
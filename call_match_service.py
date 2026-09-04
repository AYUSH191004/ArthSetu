import json
from uuid import UUID
from backend.app.db.session import SessionLocal
from backend.app.services.matching_engine import process_source_record

session = SessionLocal()
source_id = UUID('1e1c1b18-2da9-449d-a69b-f722fbf44916')
try:
    res = process_source_record(db=session, source_record_id=source_id)
    print(json.dumps({"service_result": res}, indent=2, default=str))
except Exception as e:
    print(json.dumps({"error": str(e)}, indent=2))
finally:
    session.close()

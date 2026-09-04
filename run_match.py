import json
from fastapi.testclient import TestClient
from backend.app.main import app

client = TestClient(app)

sr_id = "1e1c1b18-2da9-449d-a69b-f722fbf44916"
resp = client.post(f"/api/v1/api/matching/process/{sr_id}")
try:
    body = resp.json()
except Exception:
    body = resp.text
print(json.dumps({"path": f"/api/v1/api/matching/process/{sr_id}", "status_code": resp.status_code, "body": body}, indent=2, default=str))

import json
from fastapi.testclient import TestClient
from backend.app.main import app

client = TestClient(app)

requests = [
    ("GET", "/api/v1/api/reviews/", {}),
    ("GET", "/api/v1/api/analytics/summary", {}),
    ("GET", "/api/v1/api/analytics/districts", {}),
    ("GET", "/api/v1/api/analytics/trends", {}),
    ("GET", "/api/v1/api/dashboard/", {}),
    ("GET", "/api/v1/api/businesses/search", {"q": "test"}),
    ("GET", "/api/v1/api/businesses/UBID_NOT_EXISTS", {}),
    ("GET", "/api/v1/api/business/search", {"q": "test"}),
    ("POST", "/api/v1/api/status/run-all", {}),
    ("GET", "/api/v1/api/status/UBID_NOT_EXISTS", {}),
    ("POST", "/api/v1/api/matching/process/00000000-0000-0000-0000-000000000000", {}),
]

results = []
for method, path, params in requests:
    try:
        if method == "GET":
            r = client.get(path, params=params)
        else:
            r = client.post(path, json=params)
    except Exception as e:
        results.append({"path": path, "error": str(e)})
        continue

    try:
        body = r.json()
    except Exception:
        body = r.text

    results.append({"path": path, "status_code": r.status_code, "body": body})

print(json.dumps(results, indent=2, default=str))

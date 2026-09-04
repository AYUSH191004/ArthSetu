# ArthSetu API Contract (v1)

Base URL: `http://localhost:8000`
Prefix: `/api/v1`
Interactive docs: `http://localhost:8000/docs`

All enum values are **lower_snake_case** strings (`active`, `dormant`, `closed`,
`unknown`, `open`, `approved`, `rejected`, `auto_link`, `review`, `manual`).

## Authentication

Every endpoint **except `GET /health` and `POST /auth/login`** requires a
`Authorization: Bearer <token>` header. Missing/expired token → `401`;
insufficient role → `403`.

Roles (each includes the ones below it): **admin** > **reviewer** > **viewer**.

| Capability | Minimum role |
|---|---|
| Read dashboard / search / profiles / analytics / audit | viewer |
| Recompute a business status (`GET /status/{ubid}`) | reviewer |
| Approve / reject a review case | reviewer |
| Batch status recompute (`POST /status/run-all`) | admin |
| Trigger matching (`POST /matching/process/...`) | admin |
| User management (`/auth/users*`) | admin |

`POST /api/v1/auth/login` — form-encoded (`application/x-www-form-urlencoded`):
```
username=admin&password=...
```
```json
{ "access_token": "eyJ...", "token_type": "bearer", "expires_in": 28800,
  "user": { "id": "...", "username": "admin", "full_name": "System Administrator",
            "email": null, "role": "admin", "is_active": true, "created_at": "..." } }
```

`GET /api/v1/auth/me` → the `user` object above.
`POST /api/v1/auth/change-password` → `{ "current_password": "...", "new_password": "..." }` → `204`.

**Admin only:**
`GET /api/v1/auth/users` → `[UserOut, ...]`
`POST /api/v1/auth/users` → `{ username, full_name, email?, role, password }` → `201 UserOut`
`PATCH /api/v1/auth/users/{id}` → `{ full_name?, email?, role?, is_active? }` → `UserOut`
`POST /api/v1/auth/users/{id}/reset-password` → `{ "new_password": "..." }` → `UserOut`

Seeded demo accounts: `admin` / `arthsetu-admin`, `reviewer` / `arthsetu-review`,
`reviewer2` / `arthsetu-review`, `officer` / `arthsetu-view`.

---

## Health

`GET /api/v1/health`  (public)
```json
{ "status": "ok", "service": "ArthSetu", "version": "1.0.0",
  "environment": "development", "database": "connected" }
```

## Dashboard

`GET /api/v1/dashboard`
```json
{ "total_businesses": 140, "active": 90, "dormant": 20, "closed": 30,
  "unknown": 0, "pending_reviews": 151, "total_links": 346,
  "auto_match_rate": 56.36 }
```

## Analytics

`GET /api/v1/analytics/summary` → `{ total_businesses, active, dormant, closed, unknown }`

`GET /api/v1/analytics/trends` → `[{ "month": "2026-07", "events": 212 }, ...]`

`GET /api/v1/analytics/districts` →
```json
[{ "district": "Ludhiana", "total": 25, "active": 19,
   "dormant": 3, "closed": 3, "unknown": 0 }, ...]
```

## Business

`GET /api/v1/business/search?q=&status=&district=&limit=25&offset=0`
```json
{ "total": 12, "limit": 25, "offset": 0,
  "items": [{ "ubid": "UBID000019", "business_name": "Singh Auto Works",
              "status": "active", "district": "Mandi Gobindgarh",
              "pan": "FKBJZ2744X", "gstin": null }] }
```

`GET /api/v1/business/{ubid}`  (404 if unknown)
```json
{ "ubid": "UBID000019", "business_name": "Singh Auto Works",
  "status": "active", "pan": "...", "gstin": null,
  "district": "Mandi Gobindgarh", "sector": "Restaurant",
  "linked_records_count": 4,
  "linked_records": [{ "link_id": "...", "source_record_id": "...",
    "source_system": "Commercial Consumer Ledger", "department": "Electricity Board",
    "external_id": "85c45579-303", "extracted_name": "Singh Auto Wrks",
    "confidence": 0.84, "decision": "review" }],
  "matching_evidence": [{ "signal": "Best link confidence", "value": "84%" }],
  "timeline": [{ "date": "2026-08-22T08:29:15Z", "event": "power_usage", "score": 0.85 }],
  "status_history": [{ "date": "2026-09-04T08:29:16Z", "status": "active", "confidence": 0.735 }] }
```

## Review Queue

`GET /api/v1/reviews?status=open&limit=25&offset=0`
```json
{ "total": 151, "limit": 25, "offset": 0,
  "items": [{ "review_id": "...", "source_record_id": "...",
    "candidate_entity_id": "...", "candidate_name": "Gupta Traders",
    "status": "open", "confidence": 0.56,
    "evidence": { "candidate_name": "Gupta Traders", "confidence": 0.56,
                  "reasons": ["Partial name similarity", "PAN missing on source record"] },
    "notes": "Confidence 0.56. Manual verification required.",
    "reviewer_id": null, "created_at": "2026-09-04T08:29:16Z", "decided_at": null }] }
```

`POST /api/v1/reviews/{review_id}/approve`  (reviewer role)
`POST /api/v1/reviews/{review_id}/reject`  (reviewer role)
- No body. The reviewer is taken from the bearer token and recorded in the audit trail.
- Approve confirms the proposed link (creates/promotes an `entity_record_link`,
  decision `manual`) and writes an audit row. Reject leaves the record separate.
```json
{ "message": "Review approved and link confirmed", "review_id": "...",
  "status": "approved", "linked_entity_id": "...", "link_id": "..." }
```

## Status Engine

`GET /api/v1/status/{ubid}`  — recomputes + persists a snapshot, returns:
```json
{ "business_entity_id": "...", "ubid_code": "UBID000019", "status": "ACTIVE",
  "confidence": 0.735, "reasons": ["POWER_USAGE: base=0.82, age=13d, decay=1.0, score=0.82", ...] }
```
`POST /api/v1/status/run-all` — batch recompute; returns processed/failed/active/dormant/closed counts.

## Matching

`POST /api/v1/matching/process/{source_record_id}`  (404 on bad id)
```json
{ "decision": "REVIEW", "confidence": 0.73,
  "business_entity_id": "...", "reasons": ["PAN exact match", "Name similarity 0.9"] }
```

## Audit

`GET /api/v1/audit?entity_type=&entity_id=&action=&limit=50&offset=0`
```json
{ "total": 486, "limit": 50, "offset": 0,
  "items": [{ "id": "...", "actor_type": "system", "actor_id": null,
    "entity_type": "business_entity", "entity_id": "...", "action": "STATUS_UPDATED",
    "before_state": null, "after_state": { "status": "active", "confidence": 0.72, "reasons": [...] },
    "created_at": "2026-09-04T08:29:16Z" }] }
```

---

## Running the backend

```bash
python -m venv .venv
.venv\Scripts\activate            # Windows
pip install -r backend/requirements.txt

python -m backend.seed_dev --reset   # build a local SQLite dataset
python -m uvicorn backend.app.main:app --reload
```

DB defaults to `sqlite:///./arthsetu_dev.db`. Override with `DATABASE_URL`
(e.g. Postgres) in `backend/.env`. Schema is managed by Alembic
(`alembic upgrade head`); the dev seeder also creates tables directly.

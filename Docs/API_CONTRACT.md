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
| Corrections (split / status override / reassign / undo) | reviewer |
| Batch status recompute (`POST /status/run-all`) | admin |
| Trigger matching (`POST /matching/process/...`) | admin |
| Import records (`POST /ingest/csv`, `/ingest/records`, `/ingest/process-pending`) | admin |
| List source systems / pending count / template | viewer |
| Background jobs (`/jobs*`) | admin |
| Matching weights & calibration (`/matching/weights`, `/matching/calibration`) | admin |
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

`GET /api/v1/business/search?q=&status=&district=&pin=&limit=25&offset=0`
(`q` also matches address text; `pin` is an exact 6-digit filter)
```json
{ "total": 12, "limit": 25, "offset": 0,
  "items": [{ "ubid": "UBID000019", "business_name": "Singh Auto Works",
              "status": "active", "district": "Mandi Gobindgarh",
              "pin_code": "147301", "pan": "FKBJZ2744X", "gstin": null }] }
```

`GET /api/v1/business/{ubid}`  (404 if unknown)
```json
{ "ubid": "UBID000019", "business_name": "Singh Auto Works",
  "status": "active", "pan": "...", "gstin": null,
  "address": "Plot 42, Focal Point 3, Ludhiana, Punjab", "pin_code": "141001",
  "district": "Mandi Gobindgarh", "sector": "Restaurant",
  "linked_records_count": 4,
  "linked_records": [{ "link_id": "...", "source_record_id": "...",
    "source_system": "Commercial Consumer Ledger", "department": "Electricity Board",
    "external_id": "85c45579-303", "extracted_name": "Singh Auto Wrks",
    "extracted_address": "SINGH AUTO WRKS FOCAL POINT LUDHIANA", "extracted_pin": "141001",
    "confidence": 0.84, "decision": "review" }],
  "matching_evidence": [{ "signal": "Address similarity 0.9", "value": "Address similarity 0.9" }],
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

## Corrections  (reviewer role — reversible graph edits)

`GET  /api/v1/corrections?limit=30&offset=0` → paged history of every correction,
each with `reversible` / `undone` flags and a `summary`.

`POST /api/v1/corrections/links/{link_id}/split`
`{ "reason": "...", "mode": "reopen_review" | "new_entity" }` — unlinks a source
record from a business: back to the review queue, or into its own identity.

`POST /api/v1/corrections/entities/{ubid}/status-override`
`{ "status": "active|dormant|closed", "reason": "..." }` — pins the lifecycle
status. The engine keeps recording its opinion in snapshots but stops changing
`status` until the pin is cleared.
`POST /api/v1/corrections/entities/{ubid}/status-override/clear` — unpin + recompute.

`POST /api/v1/corrections/events/{event_id}/reassign`
`{ "target_ubid": "UBID000123", "reason": "..." }` — moves an activity event to a
different business; both entities' statuses are recomputed.

`POST /api/v1/corrections/undo/{audit_id}` — reverses any of the above (and
approve/reject); refuses a second undo of the same action.
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
`POST /api/v1/status/run-all`  (admin) — queues a batch recompute as a
background job (see **Background Jobs** below) instead of blocking the
request → `202` + a `Job`. Poll `GET /jobs/{id}`; its `result` has the same
`processed/failed/active/dormant/closed` shape the old synchronous response
used to return directly.

## Matching

`POST /api/v1/matching/process/{source_record_id}`  (404 on bad id)
```json
{ "decision": "REVIEW", "confidence": 0.73, "business_entity_id": "...",
  "reasons": ["Name similarity 0.98", "Address similarity 0.9", "PIN code match (141001)"] }
```

Signals & weights (score is capped at 1.0) — **admin-tunable**, no longer
fixed constants (defaults shown):

| Signal | Weight | Notes |
|---|---|---|
| GSTIN exact | 0.60 | unique government id — definitive on its own |
| PAN exact | 0.55 | derived from GSTIN when the PAN field is blank |
| Name similarity | 0.42 × score | token-sort fuzzy ratio |
| Address similarity | 0.28 × score | token-set ratio, filler words removed |
| PIN code exact | 0.12 | only counts when name similarity ≥ 0.35 |

`decision` is `AUTO_LINK` at ≥ `auto_link_threshold` (0.92), `REVIEW` at ≥
`review_threshold` (0.70), otherwise `NEW_ENTITY`. A strong name + address +
PIN match reaches `REVIEW` but never `AUTO_LINK` without an id anchor.

`GET /api/v1/matching/weights`  (admin) → the eight tunable values above
plus `updated_by` / `updated_at`.
`PUT /api/v1/matching/weights`  (admin) — partial update, e.g.
`{ "review_threshold": 0.65 }`; each field is `0..1`.

`GET /api/v1/matching/calibration`  (admin) — reviewer-feedback calibration:
buckets review cases by confidence range and shows the approve/reject split
in each, plus which evidence signals appear most in decided cases. Decision
support for tuning the weights above, not auto-tuning.
```json
{ "weights": { "...": "..." },
  "buckets": [{ "label": "0.80 - 0.89", "total": 109, "approved": 1,
                "rejected": 0, "pending": 108, "approve_rate": 1.0 }],
  "signals": [{ "signal": "Name", "approved": 1, "rejected": 0 }],
  "sample_size": 157 }
```

## Ingestion

`GET /api/v1/ingest/source-systems` → `[{ code, name, department, record_count }]`
`GET /api/v1/ingest/pending` → `{ "pending": 157 }` (records not linked and not in review)
`GET /api/v1/ingest/template` → a sample CSV (`text/csv`)

`POST /api/v1/ingest/csv`  (admin, `multipart/form-data`)
- `file` — the CSV; `source_system_code` — e.g. `LABOUR`; `process` — bool (default true)
- Headers are matched loosely: `name` / `firm_name` / `trade_name` / `consumer_name`…,
  `pan`, `gstin`, `address`, `pin` / `pincode`, `external_id` / `registration_no`…
  Unrecognised columns are kept in `raw_payload`. Missing `external_id` → a content hash
  (so re-imports dedupe).
- Row creation is synchronous; if `process` is true, matching those rows is
  queued as a `csv_match` background job (see below) instead of blocking the
  upload — a large batch no longer holds the request open.

`POST /api/v1/ingest/records`  (admin, JSON) — same shape, same job behaviour.
```json
{ "source_system_code": "LABOUR", "process": true,
  "records": [{ "name": "Punjab Steel Works", "pan": "ABCDE1234F",
                "address": "Focal Point, Ludhiana", "pin": "141001" }] }
```

Both return an ingestion report:
```json
{ "source_system": "LABOUR", "rows_read": 120, "created": 118,
  "skipped_duplicates": 2, "errors": [{ "row": 44, "error": "missing business name" }],
  "matching": null, "job_id": "..." }
```
`matching` is populated inline only if the job already finished by response
time (small batches, or `JOBS_SYNC=1`); otherwise poll `GET /jobs/{job_id}`.

`POST /api/v1/ingest/process-pending?limit=1000`  (admin) — queues a
`process_pending` job over every unresolved source record → `202` + a `Job`.
Its `result` is `{ processed, auto_link, review, new_entity, failed }`.

---

## Background Jobs  (admin — see job_runner.py)

Batch status recompute and bulk matching run off the request thread on a
small in-process worker pool — no external queue/broker, just a DB-tracked
`Job` row so callers get a pollable status and an audit trail. Endpoints
that queue one return `202` with the `Job` below immediately; poll it.

`GET  /api/v1/jobs?job_type=&status=&limit=25&offset=0` → paged job history.
`GET  /api/v1/jobs/{id}` → one job (404 if unknown).
```json
{ "id": "...", "job_type": "status_run_all", "status": "succeeded",
  "payload": {}, "result": { "processed": 148, "failed": 0, "active": 65,
  "dormant": 25, "closed": 58, "errors": [] }, "error": null,
  "created_by": "admin", "created_at": "...", "started_at": "...",
  "finished_at": "..." }
```
`status` is `pending` → `running` → `succeeded` / `failed`. `job_type` is
one of `status_run_all`, `process_pending`, `csv_match`.

---

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

## Running with Docker

```bash
docker compose up --build
```
Brings up Postgres, the API (`alembic upgrade head` runs on container start)
on `:8000`, and the frontend behind nginx on `:8080` (nginx proxies `/api/`
to the backend container, so the SPA needs no CORS config). With no `.env`
file this runs in `APP_ENV=development` with insecure demo defaults, so it
works out of the box for a trial. On first boot, if the `user_account`
table is empty, the API creates one admin account from
`BOOTSTRAP_ADMIN_USERNAME` / `BOOTSTRAP_ADMIN_PASSWORD` (default
`admin` / `arthsetu-admin`) — that's the login for a fresh container.
Load the synthetic demo dataset on top of it if you want one:
```bash
docker compose exec backend python -m backend.seed_dev --reset
```

**For a real deployment**, copy `.env.docker.example` to `.env` (repo root)
and fill in `SECRET_KEY`, `BOOTSTRAP_ADMIN_PASSWORD`, and `POSTGRES_PASSWORD`,
then set `APP_ENV=production`. The backend refuses to start in production
with the default secret key or bootstrap password still in place — a
deliberate fail-fast guard (`backend/app/core/config.py`), not a bug, so
double-check `docker compose logs backend` if the container exits
immediately. Hardening baked into the images:
- backend and frontend containers run as non-root users
- both have `HEALTHCHECK`s wired into compose's `depends_on: condition: service_healthy`
- Postgres isn't published to the host — only reachable from the backend over the compose network
- CPU/memory limits and `restart: unless-stopped` on every service
- nginx: security headers (`X-Frame-Options`, `X-Content-Type-Options`, etc.), gzip, `server_tokens off`, immutable caching on hashed assets, `no-cache` on `index.html`

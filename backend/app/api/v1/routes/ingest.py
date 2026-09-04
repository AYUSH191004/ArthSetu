# ============================================================
# FILE: backend/app/api/v1/routes/ingest.py
# ============================================================

from __future__ import annotations

from typing import Annotated

from fastapi import APIRouter, Depends, File, Form, HTTPException, Query, UploadFile
from fastapi.responses import PlainTextResponse
from sqlalchemy import func
from sqlalchemy.orm import Session

from backend.app.api.deps import require_admin
from backend.app.db.session import get_db
from backend.app.db.models.source_record import SourceRecord
from backend.app.db.models.source_system import SourceSystem
from backend.app.schemas import (
    IngestionReportOut,
    IngestRequest,
    PendingCountResponse,
    ProcessPendingResponse,
    SourceSystemOut,
)
from backend.app.services import ingestion

router = APIRouter()

DbSession = Annotated[Session, Depends(get_db)]

MAX_UPLOAD_BYTES = 8 * 1024 * 1024  # 8 MB


@router.get("/source-systems", response_model=list[SourceSystemOut])
def list_source_systems(db: DbSession):
    counts = dict(
        db.query(SourceRecord.source_system_id, func.count(SourceRecord.id))
        .group_by(SourceRecord.source_system_id)
        .all()
    )
    return [
        SourceSystemOut(
            code=s.code,
            name=s.name,
            department=s.department,
            record_count=int(counts.get(s.id, 0)),
        )
        for s in db.query(SourceSystem).order_by(SourceSystem.code).all()
    ]


@router.get("/pending", response_model=PendingCountResponse)
def pending(db: DbSession):
    return PendingCountResponse(pending=ingestion.pending_count(db))


@router.get(
    "/template",
    response_class=PlainTextResponse,
    responses={200: {"content": {"text/csv": {}}}},
)
def csv_template():
    return PlainTextResponse(
        ingestion.CSV_TEMPLATE,
        media_type="text/csv",
        headers={"Content-Disposition": 'attachment; filename="arthsetu_import_template.csv"'},
    )


@router.post(
    "/csv",
    response_model=IngestionReportOut,
    dependencies=[Depends(require_admin)],
)
async def ingest_csv(
    db: DbSession,
    source_system_code: Annotated[str, Form()],
    file: Annotated[UploadFile, File()],
    process: Annotated[bool, Form()] = True,
):
    raw = await file.read()
    if len(raw) > MAX_UPLOAD_BYTES:
        raise HTTPException(status_code=413, detail="File exceeds 8 MB limit")
    if not raw.strip():
        raise HTTPException(status_code=400, detail="Empty file")

    rows = ingestion.parse_csv(raw)
    if not rows:
        raise HTTPException(status_code=400, detail="No data rows found in CSV")

    try:
        report = ingestion.ingest_rows(db, source_system_code, rows, process)
    except ValueError as exc:
        raise HTTPException(status_code=404, detail=str(exc))
    return report.as_dict()


@router.post(
    "/records",
    response_model=IngestionReportOut,
    dependencies=[Depends(require_admin)],
)
def ingest_records(body: IngestRequest, db: DbSession):
    rows = [
        {
            "external_id": r.external_id or "",
            "name": r.name,
            "pan": r.pan or "",
            "gstin": r.gstin or "",
            "address": r.address or "",
            "pin": r.pin or "",
            "_extra": {},
        }
        for r in body.records
    ]
    try:
        report = ingestion.ingest_rows(
            db, body.source_system_code, rows, body.process
        )
    except ValueError as exc:
        raise HTTPException(status_code=404, detail=str(exc))
    return report.as_dict()


@router.post(
    "/process-pending",
    response_model=ProcessPendingResponse,
    dependencies=[Depends(require_admin)],
)
def process_pending(
    db: DbSession,
    limit: int = Query(default=1000, ge=1, le=5000),
):
    return ingestion.process_pending(db, limit=limit)

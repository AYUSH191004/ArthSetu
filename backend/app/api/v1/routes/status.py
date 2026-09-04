# ============================================================
# FILE: backend/app/api/v1/routes/status.py
# ============================================================

from time import perf_counter

from fastapi import APIRouter, Depends, HTTPException, status as http_status
from sqlalchemy.orm import Session

from backend.app.db.session import get_db
from backend.app.db.models.business_entity import BusinessEntity
from backend.app.schemas import StatusResultResponse, StatusRunAllResponse
from backend.app.services.status_engine import infer_business_status

router = APIRouter()


@router.get("/{ubid}", response_model=StatusResultResponse)
def get_status(ubid: str, db: Session = Depends(get_db)):
    entity = (
        db.query(BusinessEntity)
        .filter(BusinessEntity.ubid_code == ubid)
        .first()
    )
    if not entity:
        raise HTTPException(status_code=404, detail="Business not found")

    return infer_business_status(db=db, business_entity_id=entity.id)


@router.post(
    "/run-all",
    response_model=StatusRunAllResponse,
    status_code=http_status.HTTP_200_OK,
)
def run_all_status(db: Session = Depends(get_db)):
    """Batch-recompute status for every business (admin / nightly / demo)."""

    started = perf_counter()
    rows = db.query(BusinessEntity).all()

    processed = failed = active = dormant = closed = 0
    errors = []

    for entity in rows:
        try:
            result = infer_business_status(db=db, business_entity_id=entity.id)
            processed += 1
            current = result["status"]
            if current == "ACTIVE":
                active += 1
            elif current == "DORMANT":
                dormant += 1
            elif current == "CLOSED":
                closed += 1
        except Exception as exc:  # noqa: BLE001
            db.rollback()
            failed += 1
            errors.append(
                {
                    "business_id": str(entity.id),
                    "ubid": entity.ubid_code,
                    "error": str(exc),
                }
            )

    return StatusRunAllResponse(
        message="Status recomputation completed",
        processed=processed,
        failed=failed,
        active=active,
        dormant=dormant,
        closed=closed,
        duration_seconds=round(perf_counter() - started, 2),
        errors=errors[:10],
    )

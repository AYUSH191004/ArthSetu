# ============================================================
# FILE: backend/app/api/v1/routes/matching.py
# ============================================================

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

from backend.app.db.session import get_db
from backend.app.schemas import MatchingResultResponse
from backend.app.services.matching_engine import process_source_record

router = APIRouter()


@router.post("/process/{source_record_id}", response_model=MatchingResultResponse)
def run_matching(source_record_id: str, db: Session = Depends(get_db)):
    try:
        return process_source_record(db=db, source_record_id=source_record_id)
    except ValueError as exc:
        raise HTTPException(status_code=404, detail=str(exc))

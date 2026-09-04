# ============================================================
# FILE: backend/app/api/v1/routes/audit.py
# ============================================================

from fastapi import APIRouter, Depends, Query
from sqlalchemy import func
from sqlalchemy.orm import Session

from backend.app.db.session import get_db
from backend.app.db.models.audit_log import AuditLog
from backend.app.schemas import AuditEntry, AuditListResponse

router = APIRouter()


def _enum_value(value) -> str:
    return value.value if hasattr(value, "value") else str(value)


@router.get("", response_model=AuditListResponse)
@router.get("/", response_model=AuditListResponse, include_in_schema=False)
def list_audit(
    db: Session = Depends(get_db),
    entity_type: str | None = Query(default=None),
    entity_id: str | None = Query(default=None),
    action: str | None = Query(default=None),
    limit: int = Query(default=50, ge=1, le=200),
    offset: int = Query(default=0, ge=0),
):
    query = db.query(AuditLog)
    if entity_type:
        query = query.filter(AuditLog.entity_type == entity_type)
    if entity_id:
        query = query.filter(AuditLog.entity_id == entity_id)
    if action:
        query = query.filter(AuditLog.action == action)

    total = query.with_entities(func.count(AuditLog.id)).scalar() or 0

    rows = (
        query.order_by(AuditLog.created_at.desc())
        .limit(limit)
        .offset(offset)
        .all()
    )

    return AuditListResponse(
        total=int(total),
        limit=limit,
        offset=offset,
        items=[
            AuditEntry(
                id=str(r.id),
                actor_type=_enum_value(r.actor_type),
                actor_id=r.actor_id,
                entity_type=r.entity_type,
                entity_id=r.entity_id,
                action=r.action,
                before_state=r.before_state,
                after_state=r.after_state,
                created_at=r.created_at,
            )
            for r in rows
        ],
    )

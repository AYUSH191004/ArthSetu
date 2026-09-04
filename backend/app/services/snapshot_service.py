# ============================================================
# FILE: backend/app/services/snapshot_service.py
# ============================================================

from __future__ import annotations

from sqlalchemy.orm import Session

from backend.app.db.models.status_snapshot import StatusSnapshot
from backend.app.db.models.audit_log import AuditLog
from backend.app.db.enums import AuditActorEnum


def _enum_value(value) -> str:
    return value.value if hasattr(value, "value") else str(value)


def save_status_snapshot(
    db: Session,
    business_entity_id: str,
    status,
    confidence: float,
    reasons: list[str],
) -> None:
    """Persist the latest status inference plus an audit row."""

    snapshot = StatusSnapshot(
        business_entity_id=business_entity_id,
        status=status,
        confidence=confidence,
        reasons=reasons,
    )
    db.add(snapshot)

    db.add(
        AuditLog(
            actor_type=AuditActorEnum.SYSTEM,
            actor_id=None,
            entity_type="business_entity",
            entity_id=str(business_entity_id),
            action="STATUS_UPDATED",
            before_state=None,
            after_state={
                "status": _enum_value(status),
                "confidence": confidence,
                "reasons": reasons,
            },
        )
    )

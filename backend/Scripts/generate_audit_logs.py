# backend/Scripts/generate_audit_logs.py

from backend.app.db.session import SessionLocal

from backend.app.db.models.audit_log import AuditLog
from backend.app.db.models.entity_record_link import EntityRecordLink
from backend.app.db.models.review_case import ReviewCase
from backend.app.db.models.status_snapshot import StatusSnapshot

from backend.app.db.enums import AuditActorEnum

import random


def seed_audit_logs(db):
    existing = db.query(AuditLog).count()

    if existing > 0:
        print(f"[✓] Audit logs already seeded: {existing}")
        return

    created = 0

    # -----------------------------------
    # SYSTEM: link decisions
    # -----------------------------------
    links = db.query(EntityRecordLink).limit(300).all()

    for link in links:
        row = AuditLog(
            actor_type=AuditActorEnum.SYSTEM,
            actor_id=None,
            entity_type="entity_record_link",
            entity_id=str(link.id),
            action="AUTO_LINK_EVALUATED",
            before_state=None,
            after_state={
                "confidence": link.confidence,
                "decision": str(link.decision),
            },
        )
        db.add(row)
        created += 1

    # -----------------------------------
    # SYSTEM: status snapshots
    # -----------------------------------
    snaps = db.query(StatusSnapshot).limit(300).all()

    for snap in snaps:
        row = AuditLog(
            actor_type=AuditActorEnum.SYSTEM,
            actor_id=None,
            entity_type="status_snapshot",
            entity_id=str(snap.id),
            action="STATUS_INFERRED",
            before_state=None,
            after_state={
                "status": str(snap.status),
                "confidence": snap.confidence,
            },
        )
        db.add(row)
        created += 1

    # -----------------------------------
    # REVIEWER actions
    # -----------------------------------
    reviews = db.query(ReviewCase).limit(80).all()

    for case in reviews:
        action = random.choice(
            ["REVIEW_APPROVED", "REVIEW_REJECTED"]
        )

        row = AuditLog(
            actor_type=AuditActorEnum.REVIEWER,
            actor_id=f"reviewer_{random.randint(1,8)}",
            entity_type="review_case",
            entity_id=str(case.id),
            action=action,
            before_state={
                "status": str(case.status)
            },
            after_state={
                "status": action
            },
        )
        db.add(row)
        created += 1

    # -----------------------------------
    # ADMIN corrections
    # -----------------------------------
    for i in range(25):
        row = AuditLog(
            actor_type=AuditActorEnum.USER,
            actor_id=f"admin_{random.randint(1,3)}",
            entity_type="business_entity",
            entity_id=f"manual_{i}",
            action="DATA_CORRECTION",
            before_state={"pan": None},
            after_state={"pan": "UPDATED"},
        )
        db.add(row)
        created += 1

    db.commit()

    print(f"[✓] Audit logs seeded. Created: {created}")


if __name__ == "__main__":
    db = SessionLocal()
    try:
        seed_audit_logs(db)
    finally:
        db.close()
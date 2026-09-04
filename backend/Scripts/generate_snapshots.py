# backend/Scripts/generate_snapshots.py

from backend.app.db.session import SessionLocal

from backend.app.db.models.status_snapshot import StatusSnapshot
from backend.app.db.models.business_entity import BusinessEntity
from backend.app.db.models.activity_event import ActivityEvent

from backend.app.db.enums import EntityStatusEnum

from datetime import datetime, timedelta


RECENT_DAYS = 60
STALE_DAYS = 180


def infer_status(events):
    now = datetime.utcnow()

    # No activity at all
    if not events:
        return EntityStatusEnum.CLOSED, 0.93

    recent_cutoff = now - timedelta(days=RECENT_DAYS)
    stale_cutoff = now - timedelta(days=STALE_DAYS)

    # Strong recent activity
    recent_positive = [
        e for e in events
        if e.created_at >= recent_cutoff and e.score >= 0.60
    ]

    if recent_positive:
        conf = min(0.98, 0.80 + len(recent_positive) * 0.02)
        return EntityStatusEnum.ACTIVE, round(conf, 2)

    # Some activity but not recent
    semi_recent = [
        e for e in events
        if e.created_at >= stale_cutoff
    ]

    if semi_recent:
        return EntityStatusEnum.DORMANT, 0.79

    # Very old / inactive
    return EntityStatusEnum.CLOSED, 0.88


def seed_snapshots(db):
    existing = db.query(StatusSnapshot).count()

    if existing > 0:
        print(f"[✓] Snapshots already seeded: {existing}")
        return

    businesses = db.query(BusinessEntity).all()

    created = 0

    for entity in businesses:
        events = (
            db.query(ActivityEvent)
            .filter(
                ActivityEvent.business_entity_id == entity.id
            )
            .all()
        )

        status, confidence = infer_status(events)

        snap = StatusSnapshot(
            business_entity_id=entity.id,
            status=status,
            confidence=confidence,
        )

        # sync latest status
        entity.status = status

        db.add(snap)
        created += 1

    db.commit()

    print(f"[✓] Snapshots seeded. Created: {created}")


if __name__ == "__main__":
    db = SessionLocal()
    try:
        seed_snapshots(db)
    finally:
        db.close()
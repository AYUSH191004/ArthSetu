# backend/Scripts/generate_activity.py

from backend.app.db.session import SessionLocal

from backend.app.db.models.activity_event import ActivityEvent
from backend.app.db.models.business_entity import BusinessEntity

from backend.app.db.enums import EventTypeEnum

from datetime import datetime, timedelta
import random


def random_date(days_back):
    return datetime.utcnow() - timedelta(
        days=random.randint(0, days_back)
    )


def make_event(entity_id, event_type, score):
    row = ActivityEvent(
        business_entity_id=entity_id,
        event_type=event_type,
        score=score,
        payload={
            "generated": True,
            "source": "synthetic_seed"
        },
    )
    row.created_at = random_date(365)
    return row


def seed_activity(db):
    existing = db.query(ActivityEvent).count()

    if existing > 0:
        print(f"[✓] Activity already seeded: {existing}")
        return

    businesses = db.query(BusinessEntity).all()

    created = 0

    for entity in businesses:

        roll = random.random()

        # ---------------------------
        # ACTIVE (65%)
        # ---------------------------
        if roll < 0.65:
            events_count = random.randint(8, 16)

            choices = [
                (EventTypeEnum.GST_FILED, 0.95),
                (EventTypeEnum.LICENSE_RENEWED, 0.90),
                (EventTypeEnum.POWER_USAGE, 0.80),
                (EventTypeEnum.INSPECTION, 0.70),
            ]

        # ---------------------------
        # DORMANT (25%)
        # ---------------------------
        elif roll < 0.90:
            events_count = random.randint(2, 5)

            choices = [
                (EventTypeEnum.POWER_USAGE, 0.45),
                (EventTypeEnum.INSPECTION, 0.35),
            ]

        # ---------------------------
        # CLOSED (10%)
        # ---------------------------
        else:
            events_count = random.randint(0, 2)

            choices = [
                (EventTypeEnum.INSPECTION, 0.10),
            ]

        for _ in range(events_count):
            ev_type, score = random.choice(choices)

            row = make_event(entity.id, ev_type, score)

            db.add(row)
            created += 1

    db.commit()

    print(f"[✓] Activity events seeded. Created: {created}")


if __name__ == "__main__":
    db = SessionLocal()
    try:
        seed_activity(db)
    finally:
        db.close()
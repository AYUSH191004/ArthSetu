# backend/Scripts/generate_reviews.py

from backend.app.db.session import SessionLocal

from backend.app.db.models.review_case import ReviewCase
from backend.app.db.models.entity_record_link import EntityRecordLink

from backend.app.db.enums import (
    LinkDecisionEnum,
    ReviewCaseStatusEnum,
)


def seed_review_cases(db):
    existing = db.query(ReviewCase).count()

    if existing > 0:
        print(f"[✓] Review cases already seeded: {existing}")
        return

    review_links = (
        db.query(EntityRecordLink)
        .filter(
            EntityRecordLink.decision
            == LinkDecisionEnum.REVIEWED
        )
        .all()
    )

    created = 0

    for link in review_links:
        case = ReviewCase(
            source_record_id=link.source_record_id,
            status=ReviewCaseStatusEnum.OPEN,
            notes=(
                f"Confidence {link.confidence}. "
                f"Manual verification required."
            ),
        )

        db.add(case)
        created += 1

    db.commit()

    print(f"[✓] Review cases seeded. Created: {created}")


if __name__ == "__main__":
    db = SessionLocal()
    try:
        seed_review_cases(db)
    finally:
        db.close()
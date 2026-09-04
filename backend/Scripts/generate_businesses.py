# backend/Scripts/generate_businesses.py

from backend.app.db.session import SessionLocal
from backend.app.db.models.business_entity import BusinessEntity
from backend.app.db.enums import EntityStatusEnum

from backend.Scripts.seed_master import (
    generate_business_name,
    normalize_name,
    generate_pan,
    generate_gstin,
    ubid,
)

import random


TOTAL_BUSINESSES = 300


def seed_businesses(db):
    existing_count = db.query(BusinessEntity).count()

    if existing_count >= TOTAL_BUSINESSES:
        print(f"[✓] Businesses already seeded: {existing_count}")
        return

    created = 0

    for i in range(existing_count + 1, TOTAL_BUSINESSES + 1):
        name = generate_business_name()
        norm = normalize_name(name)

        # realistic missingness
        pan = generate_pan() if random.random() < 0.70 else None
        gstin = generate_gstin(pan) if pan and random.random() < 0.55 else None

        entity = BusinessEntity(
            ubid_code=ubid(i),
            legal_name=name,
            normalized_name=norm,
            pan=pan,
            gstin=gstin,
            status=EntityStatusEnum.UNKNOWN,
        )

        db.add(entity)
        created += 1

    db.commit()

    print(f"[✓] Businesses seeded. Created: {created}")


if __name__ == "__main__":
    db = SessionLocal()
    try:
        seed_businesses(db)
    finally:
        db.close()
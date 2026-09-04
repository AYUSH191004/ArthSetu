# backend/Scripts/generate_source_records.py

from backend.app.db.session import SessionLocal
from backend.app.db.models.source_record import SourceRecord
from backend.app.db.models.source_system import SourceSystem
from backend.app.db.models.business_entity import BusinessEntity

from backend.Scripts.seed_master import (
    noisy_name,
    generate_address,
    normalize_name,
)

import random
import uuid


TARGET_MIN = 750


def make_payload(system_code, entity, dirty_name):
    if system_code == "LABOUR":
        return {
            "name": dirty_name,
            "employees": random.randint(3, 50),
            "owner": entity.legal_name.split()[0],
        }

    elif system_code == "MUNICIPAL":
        return {
            "trade_name": dirty_name,
            "license_type": random.choice(["Retail", "Food", "Commercial"]),
            "shop_area_sqft": random.randint(150, 3000),
        }

    elif system_code == "POLLUTION":
        return {
            "unit_name": dirty_name,
            "risk_category": random.choice(["Green", "Orange", "Red"]),
            "consent_status": random.choice(["Valid", "Pending"]),
        }

    elif system_code == "POWER":
        return {
            "consumer_name": dirty_name,
            "load_kw": round(random.uniform(2, 55), 2),
            "tariff": "Commercial",
        }

    return {}


def seed_source_records(db):
    existing = db.query(SourceRecord).count()
    if existing >= TARGET_MIN:
        print(f"[✓] Source records already seeded: {existing}")
        return

    systems = db.query(SourceSystem).all()
    businesses = db.query(BusinessEntity).all()

    created = 0

    for entity in businesses:
        # each business appears in 1 to 4 systems
        assigned = random.sample(systems, random.randint(1, 4))

        for system in assigned:
            dirty_name = noisy_name(entity.legal_name)

            payload = make_payload(system.code, entity, dirty_name)

            record = SourceRecord(
                source_system_id=system.id,
                external_id=str(uuid.uuid4())[:12],
                raw_payload=payload,
                normalized_payload={
                    "name": normalize_name(dirty_name)
                },
                extracted_name=dirty_name,
                extracted_pan=entity.pan if random.random() < 0.70 else None,
                extracted_gstin=entity.gstin if random.random() < 0.55 else None,
            )

            db.add(record)
            created += 1

    db.commit()

    total = db.query(SourceRecord).count()
    print(f"[✓] Source records seeded. Created: {created}, Total: {total}")


if __name__ == "__main__":
    db = SessionLocal()
    try:
        seed_source_records(db)
    finally:
        db.close()
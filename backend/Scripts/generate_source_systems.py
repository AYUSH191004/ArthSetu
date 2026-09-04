# scripts/generate_source_systems.py

from backend.app.db.session import SessionLocal
from backend.app.db.models.source_system import SourceSystem


SYSTEMS = [
    {
        "code": "LABOUR",
        "name": "Shops Registration Portal",
        "department": "Labour Department",
    },
    {
        "code": "MUNICIPAL",
        "name": "Trade License Registry",
        "department": "Municipal Department",
    },
    {
        "code": "POLLUTION",
        "name": "Consent Monitoring System",
        "department": "Pollution Control Board",
    },
    {
        "code": "POWER",
        "name": "Commercial Consumer Ledger",
        "department": "Electricity Board",
    },
]


def seed_source_systems(db):
    created = 0

    for row in SYSTEMS:
        existing = (
            db.query(SourceSystem)
            .filter(SourceSystem.code == row["code"])
            .first()
        )

        if existing:
            existing.name = row["name"]
            existing.department = row["department"]
        else:
            db.add(SourceSystem(**row))
            created += 1

    db.commit()

    print(f"[✓] Source systems seeded. Created: {created}")


if __name__ == "__main__":
    db = SessionLocal()
    try:
        seed_source_systems(db)
    finally:
        db.close()
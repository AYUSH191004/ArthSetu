# backend/Scripts/load_seed.py

from backend.app.db.session import SessionLocal

from backend.app.db.models.source_system import SourceSystem
from backend.app.db.models.business_entity import BusinessEntity
from backend.app.db.models.source_record import SourceRecord
from backend.app.db.models.entity_record_link import EntityRecordLink
from backend.app.db.models.review_case import ReviewCase
from backend.app.db.models.activity_event import ActivityEvent
from backend.app.db.models.status_snapshot import StatusSnapshot
from backend.app.db.models.audit_log import AuditLog

from backend.Scripts.generate_source_systems import seed_source_systems
from backend.Scripts.generate_businesses import seed_businesses
from backend.Scripts.generate_source_records import seed_source_records
from backend.Scripts.generate_links import seed_links
from backend.Scripts.generate_reviews import seed_review_cases
from backend.Scripts.generate_activity import seed_activity
from backend.Scripts.generate_snapshots import seed_snapshots
from backend.Scripts.generate_audit_logs import seed_audit_logs


def print_counts(db):
    print("\n========== FINAL DATASET ==========")
    print("Source Systems :", db.query(SourceSystem).count())
    print("Businesses     :", db.query(BusinessEntity).count())
    print("Source Records :", db.query(SourceRecord).count())
    print("Links          :", db.query(EntityRecordLink).count())
    print("Review Cases   :", db.query(ReviewCase).count())
    print("Activity Events:", db.query(ActivityEvent).count())
    print("Snapshots      :", db.query(StatusSnapshot).count())
    print("Audit Logs     :", db.query(AuditLog).count())
    print("==================================\n")


def main():
    db = SessionLocal()

    try:
        print("\n[1/8] Seeding source systems...")
        seed_source_systems(db)

        print("[2/8] Seeding businesses...")
        seed_businesses(db)

        print("[3/8] Seeding source records...")
        seed_source_records(db)

        print("[4/8] Seeding links...")
        seed_links(db)

        print("[5/8] Seeding review cases...")
        seed_review_cases(db)

        print("[6/8] Seeding activity events...")
        seed_activity(db)

        print("[7/8] Seeding snapshots...")
        seed_snapshots(db)

        print("[8/8] Seeding audit logs...")
        seed_audit_logs(db)

        print_counts(db)

    finally:
        db.close()


if __name__ == "__main__":
    main()
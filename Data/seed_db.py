from datetime import datetime, timedelta
from backend.app.db.session import engine, SessionLocal
from backend.app.db.base import Base
from backend.app.db.models.business_entity import BusinessEntity
from backend.app.db.models.activity_event import ActivityEvent
from backend.app.db.models.review_case import ReviewCase
from backend.app.db.models.source_system import SourceSystem
from backend.app.db.models.source_record import SourceRecord
from backend.app.db.models.entity_record_link import EntityRecordLink
from backend.app.db.enums import (
    EntityStatusEnum,
    ReviewCaseStatusEnum,
    EventTypeEnum,
    LinkDecisionEnum,
)

# Create tables
Base.metadata.create_all(engine)

session = SessionLocal()

# Create source system
ss = session.query(SourceSystem).filter_by(code="SAMPLE_SYS").first()
if not ss:
    ss = SourceSystem(code="SAMPLE_SYS", name="Sample System", department="Demo")
    session.add(ss)
    session.flush()

# Create source record
sr = session.query(SourceRecord).filter_by(external_id="ext-1").first()
if not sr:
    sr = SourceRecord(
        source_system_id=ss.id,
        external_id="ext-1",
        raw_payload={"name": "Sample Business"},
        normalized_payload={"address": "123 Demo St", "pin_code": "141001"},
        extracted_name="Sample Business",
        extracted_pan="ABCDE1234F",
        extracted_gstin="27ABCDE1234F1Z5",
    )
    session.add(sr)
    session.flush()

# Create business entity
be = session.query(BusinessEntity).filter_by(ubid_code="UBID_SAMPLE").first()
if not be:
    be = BusinessEntity(
        ubid_code="UBID_SAMPLE",
        legal_name="Sample Business",
        normalized_name="sample business",
        pan="ABCDE1234F",
        gstin="27ABCDE1234F1Z5",
        status=EntityStatusEnum.ACTIVE,
    )
    session.add(be)
    session.flush()

# Create activity events
if not session.query(ActivityEvent).filter_by(business_entity_id=be.id).first():
    ev1 = ActivityEvent(
        business_entity_id=be.id,
        event_type=EventTypeEnum.GST_FILED,
        score=0.9,
        payload={"note": "GST filed"},
        created_at=datetime.utcnow() - timedelta(days=10),
    )
    ev2 = ActivityEvent(
        business_entity_id=be.id,
        event_type=EventTypeEnum.INSPECTION,
        score=0.4,
        payload={"note": "Inspection"},
        created_at=datetime.utcnow() - timedelta(days=200),
    )
    session.add_all([ev1, ev2])

# Create audit/link
if not session.query(EntityRecordLink).filter_by(source_record_id=sr.id).first():
    link = EntityRecordLink(
        source_record_id=sr.id,
        business_entity_id=be.id,
        confidence=0.95,
        decision=LinkDecisionEnum.AUTO,
        explanation=["Seeded link"],
    )
    session.add(link)

# Create review case
if not session.query(ReviewCase).filter_by(source_record_id=sr.id).first():
    rc = ReviewCase(
        source_record_id=sr.id,
        status=ReviewCaseStatusEnum.OPEN,
        notes="Seeded review case",
    )
    session.add(rc)

session.commit()
print("Seeding complete")
session.close()

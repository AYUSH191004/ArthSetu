"""Import every model so SQLAlchemy registers all tables on Base.metadata."""

from backend.app.db.models.user import User
from backend.app.db.models.source_system import SourceSystem
from backend.app.db.models.source_record import SourceRecord
from backend.app.db.models.business_entity import BusinessEntity
from backend.app.db.models.entity_record_link import EntityRecordLink
from backend.app.db.models.review_case import ReviewCase
from backend.app.db.models.activity_event import ActivityEvent
from backend.app.db.models.status_snapshot import StatusSnapshot
from backend.app.db.models.audit_log import AuditLog

__all__ = [
    "User",
    "SourceSystem",
    "SourceRecord",
    "BusinessEntity",
    "EntityRecordLink",
    "ReviewCase",
    "ActivityEvent",
    "StatusSnapshot",
    "AuditLog",
]

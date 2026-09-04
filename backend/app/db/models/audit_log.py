from sqlalchemy import String, JSON
from sqlalchemy.orm import mapped_column

from backend.app.db.base import Base
from backend.app.db.enums import AuditActorEnum
from backend.app.db.mixins import UUIDPKMixin, TimestampMixin
from backend.app.db.types import str_enum


class AuditLog(Base, UUIDPKMixin, TimestampMixin):
    __tablename__ = "audit_log"

    actor_type = mapped_column(str_enum(AuditActorEnum, "auditactorenum"))
    actor_id = mapped_column(String(100), nullable=True)

    entity_type = mapped_column(String(100), index=True)
    entity_id = mapped_column(String(100), index=True)
    action = mapped_column(String(100))

    before_state = mapped_column(JSON)
    after_state = mapped_column(JSON)

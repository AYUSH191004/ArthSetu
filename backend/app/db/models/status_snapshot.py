from sqlalchemy import ForeignKey, Float, JSON
from sqlalchemy.orm import mapped_column

from backend.app.db.base import Base
from backend.app.db.enums import EntityStatusEnum
from backend.app.db.mixins import UUIDPKMixin, TimestampMixin
from backend.app.db.types import str_enum


class StatusSnapshot(Base, UUIDPKMixin, TimestampMixin):
    __tablename__ = "status_snapshot"

    business_entity_id = mapped_column(
        ForeignKey("business_entity.id"), index=True
    )
    status = mapped_column(str_enum(EntityStatusEnum, "entitystatusenum"))
    confidence = mapped_column(Float)
    reasons = mapped_column(JSON, nullable=True)

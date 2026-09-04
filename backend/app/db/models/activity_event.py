from sqlalchemy import ForeignKey, Float, JSON, DateTime
from sqlalchemy.orm import relationship, mapped_column

from backend.app.db.base import Base
from backend.app.db.enums import EventTypeEnum
from backend.app.db.mixins import UUIDPKMixin, TimestampMixin
from backend.app.db.types import str_enum


class ActivityEvent(Base, UUIDPKMixin, TimestampMixin):
    __tablename__ = "activity_event"

    business_entity_id = mapped_column(
        ForeignKey("business_entity.id"), index=True
    )
    event_type = mapped_column(str_enum(EventTypeEnum, "eventtypeenum"), index=True)
    score = mapped_column(Float)

    # Real-world date the event happened (falls back to created_at if unset).
    occurred_at = mapped_column(DateTime(timezone=True), nullable=True)

    payload = mapped_column(JSON)

    business_entity = relationship("BusinessEntity", back_populates="activities")

    @property
    def event_date(self):
        return self.occurred_at or self.created_at

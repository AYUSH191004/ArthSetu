from sqlalchemy import ForeignKey, Text, Float, JSON, String, DateTime
from sqlalchemy.orm import mapped_column

from backend.app.db.base import Base
from backend.app.db.enums import ReviewCaseStatusEnum
from backend.app.db.mixins import UUIDPKMixin, TimestampMixin
from backend.app.db.types import str_enum


class ReviewCase(Base, UUIDPKMixin, TimestampMixin):
    __tablename__ = "review_case"

    source_record_id = mapped_column(
        ForeignKey("source_record.id"), index=True
    )

    # Candidate entity the matcher proposed linking this record to.
    candidate_entity_id = mapped_column(
        ForeignKey("business_entity.id"), nullable=True, index=True
    )

    status = mapped_column(
        str_enum(ReviewCaseStatusEnum, "reviewcasestatusenum"),
        default=ReviewCaseStatusEnum.OPEN,
        index=True,
    )

    confidence = mapped_column(Float, nullable=True)
    evidence = mapped_column(JSON, nullable=True)
    notes = mapped_column(Text, nullable=True)

    reviewer_id = mapped_column(String(100), nullable=True)
    decided_at = mapped_column(DateTime(timezone=True), nullable=True)

from datetime import datetime

from sqlalchemy import JSON, DateTime, String
from sqlalchemy.orm import Mapped, mapped_column

from backend.app.db.base import Base
from backend.app.db.enums import JobStatusEnum, JobTypeEnum
from backend.app.db.mixins import UUIDPKMixin, TimestampMixin
from backend.app.db.types import str_enum


class Job(Base, UUIDPKMixin, TimestampMixin):
    """A unit of long-running work executed off the request thread."""

    __tablename__ = "job"

    job_type = mapped_column(str_enum(JobTypeEnum, "jobtypeenum"), index=True)
    status = mapped_column(
        str_enum(JobStatusEnum, "jobstatusenum"),
        default=JobStatusEnum.PENDING,
        index=True,
    )

    payload = mapped_column(JSON, nullable=True)
    result = mapped_column(JSON, nullable=True)
    error = mapped_column(String(2000), nullable=True)

    created_by = mapped_column(String(100), nullable=True)

    started_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
    finished_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)

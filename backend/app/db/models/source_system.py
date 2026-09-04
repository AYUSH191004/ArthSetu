from sqlalchemy import String
from sqlalchemy.orm import Mapped, mapped_column, relationship
from backend.app.db.base import Base
from backend.app.db.mixins import UUIDPKMixin, TimestampMixin

class SourceSystem(Base, UUIDPKMixin, TimestampMixin):
    __tablename__ = "source_system"

    code: Mapped[str] = mapped_column(String(50), unique=True, index=True)
    name: Mapped[str] = mapped_column(String(255))
    department: Mapped[str] = mapped_column(String(255))

    records = relationship("SourceRecord", back_populates="source_system")
from datetime import datetime

from sqlalchemy import DateTime, Integer, String, func
from sqlalchemy.orm import Mapped, mapped_column

from app.database import Base


class MigrationRecord(Base):
    __tablename__ = "migration_records"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    asset_number: Mapped[str] = mapped_column(String(20), unique=True, index=True)
    polygon: Mapped[str | None] = mapped_column(String(50))
    data_prep_date: Mapped[datetime | None] = mapped_column(DateTime)
    status: Mapped[str] = mapped_column(String(20), default="pending")
    # pending → uploaded → parsed → converted → exported → complete
    notes: Mapped[str | None] = mapped_column(String(500))
    updated_at: Mapped[datetime] = mapped_column(DateTime, server_default=func.now(), onupdate=func.now())

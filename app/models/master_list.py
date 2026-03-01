from sqlalchemy import Integer, String, Text
from sqlalchemy.orm import Mapped, mapped_column

from app.database import Base


class MasterIntersection(Base):
    __tablename__ = "master_intersections"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    asset_number: Mapped[str] = mapped_column(String(20), index=True)
    polygon: Mapped[str | None] = mapped_column(String(50))
    location: Mapped[str | None] = mapped_column(String(200))
    phases_json: Mapped[str | None] = mapped_column(Text)  # JSON: {phase: {yellow, red_clear}}

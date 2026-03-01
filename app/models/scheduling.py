from sqlalchemy import Integer, String, ForeignKey
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.database import Base


class TODSchedule(Base):
    __tablename__ = "tod_schedules"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    intersection_id: Mapped[int] = mapped_column(ForeignKey("intersections.id"))
    bank: Mapped[int] = mapped_column(Integer)
    event_index: Mapped[int] = mapped_column(Integer)
    hour: Mapped[int] = mapped_column(Integer)
    minute: Mapped[int] = mapped_column(Integer)
    day_of_week: Mapped[str] = mapped_column(String(10))  # e.g. "_23456_"
    plan_number: Mapped[int] = mapped_column(Integer)

    intersection: Mapped["Intersection"] = relationship(back_populates="tod_schedules")


class HolidayEvent(Base):
    __tablename__ = "holiday_events"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    intersection_id: Mapped[int] = mapped_column(ForeignKey("intersections.id"))
    event_index: Mapped[int] = mapped_column(Integer)
    month: Mapped[int] = mapped_column(Integer)
    day: Mapped[int] = mapped_column(Integer)
    plan_number: Mapped[int] = mapped_column(Integer)

    intersection: Mapped["Intersection"] = relationship(back_populates="holiday_events")

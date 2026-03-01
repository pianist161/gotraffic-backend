from sqlalchemy import Float, Integer, String, Boolean, ForeignKey
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.database import Base


class Detector(Base):
    __tablename__ = "detectors"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    intersection_id: Mapped[int] = mapped_column(ForeignKey("intersections.id"))
    detector_number: Mapped[int] = mapped_column(Integer)
    phase_assignment: Mapped[int | None] = mapped_column(Integer)
    delay: Mapped[float] = mapped_column(Float, default=0.0)
    extend: Mapped[float] = mapped_column(Float, default=0.0)
    call_type: Mapped[str | None] = mapped_column(String(20))
    lock: Mapped[bool] = mapped_column(Boolean, default=False)

    intersection: Mapped["Intersection"] = relationship(back_populates="detectors")


class Overlap(Base):
    __tablename__ = "overlaps"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    intersection_id: Mapped[int] = mapped_column(ForeignKey("intersections.id"))
    overlap_letter: Mapped[str] = mapped_column(String(5))
    parent_phases: Mapped[str | None] = mapped_column(String(50))
    yellow_change: Mapped[float] = mapped_column(Float, default=0.0)
    red_clear: Mapped[float] = mapped_column(Float, default=0.0)

    intersection: Mapped["Intersection"] = relationship(back_populates="overlaps")


class PreemptionConfig(Base):
    __tablename__ = "preemption_configs"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    intersection_id: Mapped[int] = mapped_column(ForeignKey("intersections.id"))
    preempt_number: Mapped[int] = mapped_column(Integer)
    input_number: Mapped[int | None] = mapped_column(Integer)
    delay: Mapped[float] = mapped_column(Float, default=0.0)
    minimum_duration: Mapped[float] = mapped_column(Float, default=0.0)
    track_green_phases: Mapped[str | None] = mapped_column(String(50))
    dwell_green_phases: Mapped[str | None] = mapped_column(String(50))
    exit_phases: Mapped[str | None] = mapped_column(String(50))

    intersection: Mapped["Intersection"] = relationship(back_populates="preemption_configs")

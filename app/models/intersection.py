from datetime import datetime

from sqlalchemy import DateTime, Float, Integer, String, Boolean, ForeignKey, func
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.database import Base


class Intersection(Base):
    __tablename__ = "intersections"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    asset_number: Mapped[str] = mapped_column(String(20), unique=True, index=True)
    location_name: Mapped[str | None] = mapped_column(String(200))
    street_name_1: Mapped[str | None] = mapped_column(String(100))
    street_name_2: Mapped[str | None] = mapped_column(String(100))
    section: Mapped[str | None] = mapped_column(String(255))
    equipment_type: Mapped[str | None] = mapped_column(String(50))
    cabinet_type: Mapped[str | None] = mapped_column(String(50))
    drop_address: Mapped[str | None] = mapped_column(String(10))
    has_preemption: Mapped[bool] = mapped_column(Boolean, default=False)
    uploaded_filename: Mapped[str | None] = mapped_column(String(255))
    uploaded_at: Mapped[datetime] = mapped_column(DateTime, server_default=func.now())

    # System config (page 8)
    max_off_minutes: Mapped[float | None] = mapped_column(Float)
    max_on_minutes: Mapped[float | None] = mapped_column(Float)
    detector_chatter: Mapped[float | None] = mapped_column(Float)
    zone_address: Mapped[float | None] = mapped_column(Float)
    comm_address: Mapped[float | None] = mapped_column(Float)
    transition_type: Mapped[float | None] = mapped_column(Float)

    # Relationships
    phase_movements: Mapped[list["PhaseMovement"]] = relationship(back_populates="intersection", cascade="all, delete-orphan")
    zone_assignments: Mapped[list["ZoneAssignment"]] = relationship(back_populates="intersection", cascade="all, delete-orphan")
    phase_timings: Mapped[list["PhaseTiming"]] = relationship(back_populates="intersection", cascade="all, delete-orphan")
    coordination_plans: Mapped[list["CoordinationPlan"]] = relationship(back_populates="intersection", cascade="all, delete-orphan")
    tod_schedules: Mapped[list["TODSchedule"]] = relationship(back_populates="intersection", cascade="all, delete-orphan")
    holiday_events: Mapped[list["HolidayEvent"]] = relationship(back_populates="intersection", cascade="all, delete-orphan")
    detectors: Mapped[list["Detector"]] = relationship(back_populates="intersection", cascade="all, delete-orphan")
    overlaps: Mapped[list["Overlap"]] = relationship(back_populates="intersection", cascade="all, delete-orphan")
    preemption_configs: Mapped[list["PreemptionConfig"]] = relationship(back_populates="intersection", cascade="all, delete-orphan")
    comments: Mapped[list["IntersectionComment"]] = relationship(back_populates="intersection", cascade="all, delete-orphan")
    fdot_overrides: Mapped[list["FdotOverride"]] = relationship(back_populates="intersection", cascade="all, delete-orphan")
    split_overrides: Mapped[list["SplitOverride"]] = relationship(back_populates="intersection", cascade="all, delete-orphan")


class PhaseMovement(Base):
    __tablename__ = "phase_movements"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    intersection_id: Mapped[int] = mapped_column(ForeignKey("intersections.id"))
    phase_number: Mapped[int] = mapped_column(Integer)
    movement: Mapped[str | None] = mapped_column(String(50))
    protected: Mapped[bool] = mapped_column(Boolean, default=False)

    intersection: Mapped["Intersection"] = relationship(back_populates="phase_movements")


class ZoneAssignment(Base):
    __tablename__ = "zone_assignments"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    intersection_id: Mapped[int] = mapped_column(ForeignKey("intersections.id"))
    category: Mapped[str] = mapped_column(String(50))
    zone: Mapped[str | None] = mapped_column(String(100))

    intersection: Mapped["Intersection"] = relationship(back_populates="zone_assignments")


class IntersectionComment(Base):
    __tablename__ = "intersection_comments"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    intersection_id: Mapped[int] = mapped_column(ForeignKey("intersections.id"))
    text: Mapped[str] = mapped_column(String(2000))
    category: Mapped[str] = mapped_column(String(20), default="general")  # general, phase, plan
    created_at: Mapped[datetime] = mapped_column(DateTime, server_default=func.now())

    intersection: Mapped["Intersection"] = relationship(back_populates="comments")

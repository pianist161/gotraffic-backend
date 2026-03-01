from datetime import datetime

from sqlalchemy import Boolean, DateTime, Float, Integer, String, ForeignKey, func
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.database import Base


class PhaseTiming(Base):
    __tablename__ = "phase_timings"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    intersection_id: Mapped[int] = mapped_column(ForeignKey("intersections.id"))
    bank: Mapped[int] = mapped_column(Integer)  # 1, 2, or 3
    phase_number: Mapped[int] = mapped_column(Integer)  # 1-8
    ped_walk: Mapped[float] = mapped_column(Float, default=0.0)
    ped_fdw: Mapped[float] = mapped_column(Float, default=0.0)
    min_green: Mapped[float] = mapped_column(Float, default=0.0)
    veh_extension: Mapped[float] = mapped_column(Float, default=0.0)
    max_limit_1: Mapped[float] = mapped_column(Float, default=0.0)
    max_limit_2: Mapped[float] = mapped_column(Float, default=0.0)
    yellow_change: Mapped[float] = mapped_column(Float, default=0.0)
    red_clear: Mapped[float] = mapped_column(Float, default=0.0)

    intersection: Mapped["Intersection"] = relationship(back_populates="phase_timings")


class CoordinationPlan(Base):
    __tablename__ = "coordination_plans"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    intersection_id: Mapped[int] = mapped_column(ForeignKey("intersections.id"))
    plan_number: Mapped[int] = mapped_column(Integer)  # 1-30
    cycle_length: Mapped[float] = mapped_column(Float, default=0.0)
    offset: Mapped[float] = mapped_column(Float, default=0.0)

    # Raw BiTrans ForceOff values
    phase1_force_off: Mapped[float] = mapped_column(Float, default=0.0)
    phase2_force_off: Mapped[float] = mapped_column(Float, default=0.0)
    phase3_force_off: Mapped[float] = mapped_column(Float, default=0.0)
    phase4_force_off: Mapped[float] = mapped_column(Float, default=0.0)
    phase5_force_off: Mapped[float] = mapped_column(Float, default=0.0)
    phase6_force_off: Mapped[float] = mapped_column(Float, default=0.0)
    phase7_force_off: Mapped[float] = mapped_column(Float, default=0.0)
    phase8_force_off: Mapped[float] = mapped_column(Float, default=0.0)

    # Computed SEPAC splits
    sepac_split1: Mapped[float | None] = mapped_column(Float)
    sepac_split2: Mapped[float | None] = mapped_column(Float)
    sepac_split3: Mapped[float | None] = mapped_column(Float)
    sepac_split4: Mapped[float | None] = mapped_column(Float)
    sepac_split5: Mapped[float | None] = mapped_column(Float)
    sepac_split6: Mapped[float | None] = mapped_column(Float)
    sepac_split7: Mapped[float | None] = mapped_column(Float)
    sepac_split8: Mapped[float | None] = mapped_column(Float)

    sync_phases: Mapped[str | None] = mapped_column(String(50))
    lag_phases: Mapped[str | None] = mapped_column(String(50))
    converted: Mapped[bool] = mapped_column(Boolean, default=False)

    intersection: Mapped["Intersection"] = relationship(back_populates="coordination_plans")


class FdotOverride(Base):
    __tablename__ = "fdot_overrides"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    intersection_id: Mapped[int] = mapped_column(ForeignKey("intersections.id"))
    phase_number: Mapped[int] = mapped_column(Integer)  # 1-8
    bank: Mapped[int] = mapped_column(Integer)  # 1-3
    field_name: Mapped[str] = mapped_column(String(30))  # yellow_change, red_clear, ped_fdw
    original_value: Mapped[float] = mapped_column(Float, default=0.0)
    fdot_value: Mapped[float] = mapped_column(Float, default=0.0)

    intersection: Mapped["Intersection"] = relationship(back_populates="fdot_overrides")


class SplitOverride(Base):
    __tablename__ = "split_overrides"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    intersection_id: Mapped[int] = mapped_column(ForeignKey("intersections.id"))
    plan_number: Mapped[int] = mapped_column(Integer)
    phase_number: Mapped[int] = mapped_column(Integer)  # 1-8
    original_value: Mapped[float] = mapped_column(Float, default=0.0)
    override_value: Mapped[float] = mapped_column(Float, default=0.0)
    reason: Mapped[str | None] = mapped_column(String(500))
    created_at: Mapped[datetime] = mapped_column(DateTime, server_default=func.now())

    intersection: Mapped["Intersection"] = relationship(back_populates="split_overrides")

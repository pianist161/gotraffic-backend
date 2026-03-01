"""Timing data endpoints — phase timing, coordination plans, TOD, detectors, overlaps, preemption."""

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

from app.database import get_db
from app.models.intersection import Intersection
from app.models.timing import PhaseTiming, CoordinationPlan
from app.models.scheduling import TODSchedule
from app.models.hardware import Detector, Overlap, PreemptionConfig
from app.schemas.timing import (
    PhaseTimingSchema, CoordinationPlanSchema, TODScheduleSchema,
    DetectorSchema, OverlapSchema, PreemptionSchema,
)

router = APIRouter()


def _get_intersection_id(db: Session, asset: str) -> int:
    intersection = db.query(Intersection.id).filter(
        Intersection.asset_number == asset
    ).first()
    if not intersection:
        raise HTTPException(404, f"Intersection {asset} not found")
    return intersection.id


@router.get("/{asset}/phase-timing")
def get_phase_timing(asset: str, db: Session = Depends(get_db)):
    iid = _get_intersection_id(db, asset)
    timings = db.query(PhaseTiming).filter(
        PhaseTiming.intersection_id == iid
    ).order_by(PhaseTiming.bank, PhaseTiming.phase_number).all()
    return [PhaseTimingSchema.model_validate(t) for t in timings]


@router.get("/{asset}/coordination-plans")
def get_coordination_plans(asset: str, db: Session = Depends(get_db)):
    iid = _get_intersection_id(db, asset)
    plans = db.query(CoordinationPlan).filter(
        CoordinationPlan.intersection_id == iid
    ).order_by(CoordinationPlan.plan_number).all()
    return [CoordinationPlanSchema.model_validate(p) for p in plans]


@router.get("/{asset}/tod-schedule")
def get_tod_schedule(asset: str, db: Session = Depends(get_db)):
    iid = _get_intersection_id(db, asset)
    schedules = db.query(TODSchedule).filter(
        TODSchedule.intersection_id == iid
    ).order_by(TODSchedule.bank, TODSchedule.event_index).all()
    return [TODScheduleSchema.model_validate(s) for s in schedules]


@router.get("/{asset}/detectors")
def get_detectors(asset: str, db: Session = Depends(get_db)):
    iid = _get_intersection_id(db, asset)
    detectors = db.query(Detector).filter(
        Detector.intersection_id == iid
    ).order_by(Detector.detector_number).all()
    return [DetectorSchema.model_validate(d) for d in detectors]


@router.get("/{asset}/overlaps")
def get_overlaps(asset: str, db: Session = Depends(get_db)):
    iid = _get_intersection_id(db, asset)
    overlaps = db.query(Overlap).filter(
        Overlap.intersection_id == iid
    ).order_by(Overlap.overlap_letter).all()
    return [OverlapSchema.model_validate(o) for o in overlaps]


@router.get("/{asset}/preemption")
def get_preemption(asset: str, db: Session = Depends(get_db)):
    iid = _get_intersection_id(db, asset)
    preempts = db.query(PreemptionConfig).filter(
        PreemptionConfig.intersection_id == iid
    ).order_by(PreemptionConfig.preempt_number).all()
    return [PreemptionSchema.model_validate(p) for p in preempts]

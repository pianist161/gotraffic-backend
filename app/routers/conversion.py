"""Conversion endpoints — run conversion, get results, validate, override splits."""

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

from app.database import get_db
from app.models.intersection import Intersection
from app.models.timing import PhaseTiming, CoordinationPlan, SplitOverride
from app.models.migration import MigrationRecord
from app.schemas.conversion import SplitOverrideRequest, SplitOverrideSchema, SplitResetRequest
from app.services.conversion_engine import compute_sepac_splits, compute_min_splits, compute_min_splits_without_peds, validate_splits

router = APIRouter()


@router.post("/{asset}/run")
def run_conversion(asset: str, db: Session = Depends(get_db)):
    """Run or re-run ForceOff → SEPAC conversion for all active plans."""
    intersection = db.query(Intersection).filter(
        Intersection.asset_number == asset
    ).first()
    if not intersection:
        raise HTTPException(404, f"Intersection {asset} not found")

    plans = db.query(CoordinationPlan).filter(
        CoordinationPlan.intersection_id == intersection.id,
        CoordinationPlan.cycle_length > 0,
    ).all()

    if not plans:
        raise HTTPException(404, "No active coordination plans found")

    converted = 0
    for plan in plans:
        splits = compute_sepac_splits(plan)
        for key, val in splits.items():
            setattr(plan, key, val)
        plan.converted = True
        converted += 1

    # Update migration status
    migration = db.query(MigrationRecord).filter(
        MigrationRecord.asset_number == asset
    ).first()
    if migration:
        migration.status = "converted"

    db.commit()

    return {
        "asset_number": asset,
        "plans_converted": converted,
        "message": f"Converted {converted} plans",
    }


@router.get("/{asset}/results")
def get_conversion_results(asset: str, db: Session = Depends(get_db)):
    """Get SEPAC split results for all converted plans."""
    intersection = db.query(Intersection).filter(
        Intersection.asset_number == asset
    ).first()
    if not intersection:
        raise HTTPException(404, f"Intersection {asset} not found")

    plans = db.query(CoordinationPlan).filter(
        CoordinationPlan.intersection_id == intersection.id,
        CoordinationPlan.cycle_length > 0,
    ).order_by(CoordinationPlan.plan_number).all()

    results = []
    for p in plans:
        results.append({
            "plan_number": p.plan_number,
            "cycle_length": round(p.cycle_length, 1),
            "offset": round(p.offset, 1),
            "force_offs": {f"ph{i}": round(getattr(p, f"phase{i}_force_off"), 1) for i in range(1, 9)},
            "sepac_splits": {f"ph{i}": round(getattr(p, f"sepac_split{i}") or 0.0, 1) for i in range(1, 9)},
            "converted": p.converted,
        })

    return {"asset_number": asset, "plans": results}


@router.get("/{asset}/min-splits")
def get_min_splits(asset: str, bank: int = 1, db: Session = Depends(get_db)):
    """Get minimum split calculations for each phase."""
    intersection = db.query(Intersection).filter(
        Intersection.asset_number == asset
    ).first()
    if not intersection:
        raise HTTPException(404, f"Intersection {asset} not found")

    timings = db.query(PhaseTiming).filter(
        PhaseTiming.intersection_id == intersection.id,
    ).all()

    min_splits_with_peds = compute_min_splits(timings, bank=bank)
    min_splits_no_peds = compute_min_splits_without_peds(timings, bank=bank)

    # Include component breakdown
    bank_timings = {t.phase_number: t for t in timings if t.bank == bank}
    results = []
    for phase_num in range(1, 9):
        t = bank_timings.get(phase_num)
        if not t:
            results.append({
                "phase": phase_num,
                "min_split_with_peds": 0,
                "min_split_without_peds": 0,
                "components": {},
            })
            continue

        components = {
            "min_green": round(t.min_green, 1),
            "ped_walk": round(t.ped_walk, 1),
            "ped_fdw": round(t.ped_fdw, 1),
            "yellow_change": round(t.yellow_change, 1),
            "red_clear": round(t.red_clear, 1),
        }

        results.append({
            "phase": phase_num,
            "min_split_with_peds": round(min_splits_with_peds[phase_num], 1),
            "min_split_without_peds": round(min_splits_no_peds[phase_num], 1),
            "components": components,
        })

    return {"asset_number": asset, "bank": bank, "min_splits": results}


@router.get("/{asset}/validation")
def validate_conversion(asset: str, plan_number: int = 0, db: Session = Depends(get_db)):
    """Validate SEPAC splits against minimum requirements."""
    intersection = db.query(Intersection).filter(
        Intersection.asset_number == asset
    ).first()
    if not intersection:
        raise HTTPException(404, f"Intersection {asset} not found")

    timings = db.query(PhaseTiming).filter(
        PhaseTiming.intersection_id == intersection.id,
    ).all()

    plan_query = db.query(CoordinationPlan).filter(
        CoordinationPlan.intersection_id == intersection.id,
        CoordinationPlan.cycle_length > 0,
    )
    if plan_number > 0:
        plan_query = plan_query.filter(CoordinationPlan.plan_number == plan_number)

    plans = plan_query.order_by(CoordinationPlan.plan_number).all()
    min_splits = compute_min_splits(timings, bank=1)

    all_validations = []
    for plan in plans:
        sepac_splits = {f"sepac_split{i}": round(getattr(plan, f"sepac_split{i}") or 0.0, 1) for i in range(1, 9)}
        validations = validate_splits(sepac_splits, min_splits)
        all_validations.append({
            "plan_number": plan.plan_number,
            "cycle_length": plan.cycle_length,
            "validations": validations,
        })

    return {"asset_number": asset, "plans": all_validations}


# --- Split Override Endpoints ---

@router.patch("/{asset}/splits")
def override_splits(asset: str, body: SplitOverrideRequest, db: Session = Depends(get_db)):
    """Manually override SEPAC split values for a plan."""
    intersection = db.query(Intersection).filter(
        Intersection.asset_number == asset
    ).first()
    if not intersection:
        raise HTTPException(404, f"Intersection {asset} not found")

    plan = db.query(CoordinationPlan).filter(
        CoordinationPlan.intersection_id == intersection.id,
        CoordinationPlan.plan_number == body.plan_number,
    ).first()
    if not plan:
        raise HTTPException(404, f"Plan {body.plan_number} not found")

    for phase_num, new_value in body.overrides.items():
        if phase_num < 1 or phase_num > 8:
            raise HTTPException(400, f"Invalid phase number: {phase_num}")

        attr = f"sepac_split{phase_num}"
        original = getattr(plan, attr) or 0.0

        # Log the override
        db.add(SplitOverride(
            intersection_id=intersection.id,
            plan_number=body.plan_number,
            phase_number=phase_num,
            original_value=original,
            override_value=new_value,
            reason=body.reason,
        ))

        # Apply the override
        setattr(plan, attr, new_value)

    db.commit()
    return {"message": f"Updated {len(body.overrides)} split(s) for plan {body.plan_number}"}


@router.get("/{asset}/overrides")
def get_split_overrides(asset: str, db: Session = Depends(get_db)):
    """Get split override history for an intersection."""
    intersection = db.query(Intersection).filter(
        Intersection.asset_number == asset
    ).first()
    if not intersection:
        raise HTTPException(404, f"Intersection {asset} not found")

    overrides = db.query(SplitOverride).filter(
        SplitOverride.intersection_id == intersection.id,
    ).order_by(SplitOverride.created_at.desc()).all()

    return [
        {
            "id": o.id,
            "plan_number": o.plan_number,
            "phase_number": o.phase_number,
            "original_value": o.original_value,
            "override_value": o.override_value,
            "reason": o.reason,
            "created_at": str(o.created_at),
        }
        for o in overrides
    ]


@router.post("/{asset}/reset-splits")
def reset_splits(asset: str, body: SplitResetRequest, db: Session = Depends(get_db)):
    """Reset split overrides back to auto-computed values."""
    intersection = db.query(Intersection).filter(
        Intersection.asset_number == asset
    ).first()
    if not intersection:
        raise HTTPException(404, f"Intersection {asset} not found")

    plan_query = db.query(CoordinationPlan).filter(
        CoordinationPlan.intersection_id == intersection.id,
        CoordinationPlan.cycle_length > 0,
    )
    if body.plan_number is not None:
        plan_query = plan_query.filter(CoordinationPlan.plan_number == body.plan_number)

    plans = plan_query.all()
    if not plans:
        raise HTTPException(404, "No matching plans found")

    reset_count = 0
    for plan in plans:
        splits = compute_sepac_splits(plan)
        for key, val in splits.items():
            setattr(plan, key, val)
        plan.converted = True
        reset_count += 1

    db.commit()
    return {"message": f"Reset splits for {reset_count} plan(s)", "plans_reset": reset_count}

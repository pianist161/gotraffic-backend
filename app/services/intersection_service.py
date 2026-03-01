"""Service layer for persisting parsed BiTrans data to the database."""

import json
import logging

from sqlalchemy.orm import Session

from app.models.intersection import Intersection, PhaseMovement, ZoneAssignment
from app.models.master_list import MasterIntersection
from app.models.timing import PhaseTiming, CoordinationPlan, FdotOverride
from app.models.scheduling import TODSchedule, HolidayEvent
from app.models.hardware import Detector, Overlap, PreemptionConfig
from app.models.migration import MigrationRecord
from app.parsers.bitrans_parser import ParseResult
from app.services.conversion_engine import compute_sepac_splits

logger = logging.getLogger(__name__)


def persist_parse_result(db: Session, result: ParseResult, filename: str) -> Intersection:
    """Save a full BiTrans parse result to the database.

    If the asset already exists, it will be replaced (delete + re-insert).
    """
    asset = result.intersection.get("asset_number")
    if not asset:
        raise ValueError("No asset number found in parsed data")

    # Delete existing if present
    existing = db.query(Intersection).filter(Intersection.asset_number == asset).first()
    if existing:
        db.delete(existing)
        db.flush()

    # Create intersection
    intersection = Intersection(
        asset_number=asset,
        location_name=result.intersection.get("location_name"),
        street_name_1=result.intersection.get("street_name_1"),
        street_name_2=result.intersection.get("street_name_2"),
        section=result.intersection.get("section"),
        equipment_type=result.intersection.get("equipment_type"),
        cabinet_type=result.intersection.get("cabinet_type"),
        drop_address=result.intersection.get("drop_address"),
        has_preemption=result.intersection.get("has_preemption", False),
        uploaded_filename=filename,
        max_off_minutes=result.intersection.get("max_off_minutes"),
        max_on_minutes=result.intersection.get("max_on_minutes"),
        detector_chatter=result.intersection.get("detector_chatter"),
        zone_address=result.intersection.get("zone_address"),
        comm_address=result.intersection.get("comm_address"),
        transition_type=result.intersection.get("transition_type"),
    )
    db.add(intersection)
    db.flush()

    # Phase movements
    for pm in result.intersection.get("phase_movements", []):
        db.add(PhaseMovement(
            intersection_id=intersection.id,
            phase_number=pm["phase_number"],
            movement=pm["movement"],
            protected=pm["protected"],
        ))

    # Zone assignments
    for za in result.intersection.get("zone_assignments", []):
        db.add(ZoneAssignment(
            intersection_id=intersection.id,
            category=za["category"],
            zone=za["zone"],
        ))

    # Phase timings
    for pt in result.phase_timings:
        db.add(PhaseTiming(
            intersection_id=intersection.id,
            bank=pt["bank"],
            phase_number=pt["phase_number"],
            ped_walk=pt["ped_walk"],
            ped_fdw=pt["ped_fdw"],
            min_green=pt["min_green"],
            veh_extension=pt["veh_extension"],
            max_limit_1=pt["max_limit_1"],
            max_limit_2=pt["max_limit_2"],
            yellow_change=pt["yellow_change"],
            red_clear=pt["red_clear"],
        ))
    db.flush()

    # Apply FDOT overrides from Master Intersection List
    _apply_fdot_overrides(db, intersection.id, asset)

    # Coordination plans (with auto-conversion)
    for cp in result.coordination_plans:
        plan = CoordinationPlan(
            intersection_id=intersection.id,
            plan_number=cp["plan_number"],
            cycle_length=cp["cycle_length"],
            offset=cp["offset"],
            phase1_force_off=cp["phase1_force_off"],
            phase2_force_off=cp["phase2_force_off"],
            phase3_force_off=cp["phase3_force_off"],
            phase4_force_off=cp["phase4_force_off"],
            phase5_force_off=cp["phase5_force_off"],
            phase6_force_off=cp["phase6_force_off"],
            phase7_force_off=cp["phase7_force_off"],
            phase8_force_off=cp["phase8_force_off"],
            sync_phases=cp.get("sync_phases"),
            lag_phases=cp.get("lag_phases"),
        )
        db.add(plan)
        db.flush()

        # Auto-convert if cycle length > 0
        if plan.cycle_length > 0:
            splits = compute_sepac_splits(plan)
            plan.sepac_split1 = splits["sepac_split1"]
            plan.sepac_split2 = splits["sepac_split2"]
            plan.sepac_split3 = splits["sepac_split3"]
            plan.sepac_split4 = splits["sepac_split4"]
            plan.sepac_split5 = splits["sepac_split5"]
            plan.sepac_split6 = splits["sepac_split6"]
            plan.sepac_split7 = splits["sepac_split7"]
            plan.sepac_split8 = splits["sepac_split8"]
            plan.converted = True

    # TOD schedules
    for ts in result.tod_schedules:
        db.add(TODSchedule(
            intersection_id=intersection.id,
            bank=ts["bank"],
            event_index=ts["event_index"],
            hour=ts["hour"],
            minute=ts["minute"],
            day_of_week=ts["day_of_week"],
            plan_number=ts["plan_number"],
        ))

    # Holiday events
    for he in result.holiday_events:
        db.add(HolidayEvent(
            intersection_id=intersection.id,
            event_index=he["event_index"],
            month=he["month"],
            day=he["day"],
            plan_number=he.get("plan_number", 0),
        ))

    # Detectors
    for d in result.detectors:
        db.add(Detector(
            intersection_id=intersection.id,
            detector_number=d["detector_number"],
            phase_assignment=d.get("phase_assignment"),
            delay=d.get("delay", 0),
            extend=d.get("extend", 0),
            call_type=d.get("call_type"),
            lock=d.get("lock", False),
        ))

    # Overlaps
    for o in result.overlaps:
        db.add(Overlap(
            intersection_id=intersection.id,
            overlap_letter=o["overlap_letter"],
            parent_phases=o.get("parent_phases"),
            yellow_change=o.get("yellow_change", 0),
            red_clear=o.get("red_clear", 0),
        ))

    # Preemption configs
    for pc in result.preemption_configs:
        db.add(PreemptionConfig(
            intersection_id=intersection.id,
            preempt_number=pc["preempt_number"],
            input_number=pc.get("input_number"),
            delay=pc.get("delay", 0),
            minimum_duration=pc.get("minimum_duration", 0),
            track_green_phases=pc.get("track_green_phases"),
            dwell_green_phases=pc.get("dwell_green_phases"),
            exit_phases=pc.get("exit_phases"),
        ))

    # Create or update migration record
    migration = db.query(MigrationRecord).filter(
        MigrationRecord.asset_number == asset
    ).first()
    if not migration:
        migration = MigrationRecord(asset_number=asset, status="parsed")
        db.add(migration)
    else:
        migration.status = "parsed"

    # Mark as converted if we auto-converted
    active_plans = [p for p in result.coordination_plans if p["cycle_length"] > 0]
    if active_plans:
        migration.status = "converted"

    db.commit()
    db.refresh(intersection)
    return intersection


def _apply_fdot_overrides(db: Session, intersection_id: int, asset_number: str) -> None:
    """Apply FDOT Yellow/Red/PED overrides from Master Intersection List.

    Looks up the asset in the master_intersections table. If found and
    phases_json contains FDOT data, overrides yellow_change, red_clear,
    and ped_fdw for all 3 banks of phase timing. Logs each override to
    the fdot_overrides table for diff tracking.
    """
    master = db.query(MasterIntersection).filter(
        MasterIntersection.asset_number == asset_number
    ).first()

    if not master or not master.phases_json:
        logger.debug("No FDOT data for asset %s", asset_number)
        return

    try:
        fdot_phases = json.loads(master.phases_json)
    except (json.JSONDecodeError, TypeError):
        logger.warning("Invalid phases_json for asset %s", asset_number)
        return

    if not fdot_phases:
        return

    # Clear existing FDOT override records for re-upload
    db.query(FdotOverride).filter(
        FdotOverride.intersection_id == intersection_id
    ).delete()

    # Get all PhaseTiming records for this intersection
    timings = db.query(PhaseTiming).filter(
        PhaseTiming.intersection_id == intersection_id
    ).all()

    overrides_applied = 0
    for timing in timings:
        phase_key = str(timing.phase_number)
        if phase_key not in fdot_phases:
            continue

        fdot = fdot_phases[phase_key]
        fdot_yellow = fdot.get("yellow")
        fdot_red = fdot.get("red_clear")
        fdot_ped = fdot.get("ped_clear")

        if fdot_yellow is not None and fdot_yellow > 0:
            db.add(FdotOverride(
                intersection_id=intersection_id,
                phase_number=timing.phase_number,
                bank=timing.bank,
                field_name="yellow_change",
                original_value=timing.yellow_change,
                fdot_value=fdot_yellow,
            ))
            timing.yellow_change = fdot_yellow
            overrides_applied += 1

        if fdot_red is not None and fdot_red > 0:
            db.add(FdotOverride(
                intersection_id=intersection_id,
                phase_number=timing.phase_number,
                bank=timing.bank,
                field_name="red_clear",
                original_value=timing.red_clear,
                fdot_value=fdot_red,
            ))
            timing.red_clear = fdot_red
            overrides_applied += 1

        if fdot_ped is not None and fdot_ped > 0:
            db.add(FdotOverride(
                intersection_id=intersection_id,
                phase_number=timing.phase_number,
                bank=timing.bank,
                field_name="ped_fdw",
                original_value=timing.ped_fdw,
                fdot_value=fdot_ped,
            ))
            timing.ped_fdw = fdot_ped
            overrides_applied += 1

    if overrides_applied:
        logger.info("Applied %d FDOT overrides for asset %s",
                     overrides_applied, asset_number)

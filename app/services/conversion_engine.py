"""ForceOff → SEPAC split conversion algorithm.

BiTrans stores cumulative ForceOff points; SEPAC needs individual phase splits.

Ring A: Ph1(left) → Ph2(through) ‖ Ph3(left) → Ph4(through)
Ring B: Ph5(left) → Ph6(through) ‖ Ph7(left) → Ph8(through)

VBA SEPAC Split formulas (from Calculated Split Times sheet):
  Ph1 = IF(FO1=0, 0, IF(FO3+FO4=0, IF(FO8=0, FO1-FO7, FO1-FO8), IF(FO4=0, FO1-FO3, FO1-FO4)))
  Ph2 = IF(CL=0, 0, IF(FO3+FO4=0, IF(FO1=0, CL-S7-S8, CL-FO1), IF(FO1=0, CL-S3-S4, CL-FO1)))
  Ph3 = IF(FO3=0, 0, FO3)
  Ph4 = IF(FO4=0, 0, IF(FO3=0, FO4, FO4-FO3))
  Ph5 = IF(FO5=0, 0, IF(FO7+FO8=0, IF(FO4=0, FO5-FO3, FO5-FO4), IF(FO8=0, FO5-FO7, FO5-FO8)))
  Ph6 = IF(CL=0, 0, IF(FO7+FO8=0, IF(FO5=0, CL-S3-S4, CL-FO5), IF(FO5=0, CL-S7-S8, CL-FO5)))
  Ph7 = IF(FO7=0, 0, FO7)
  Ph8 = IF(FO8=0, 0, IF(FO7=0, FO8, FO8-FO7))

Min Split formulas (VBA):
  Without PEDs: MinGreen + Yellow + RedClear + 1
  With PEDs: MAX(MinGreen, Walk+FDW) + Yellow + RedClear + 1
"""

from app.models.timing import CoordinationPlan, PhaseTiming


def compute_sepac_splits(plan: CoordinationPlan) -> dict[str, float]:
    """Compute SEPAC splits from BiTrans ForceOff values.

    Matches VBA Calculated Split Times formulas exactly.
    Returns dict with keys sepac_split1..sepac_split8.
    """
    cl = plan.cycle_length
    fo = {
        1: plan.phase1_force_off,
        2: plan.phase2_force_off,
        3: plan.phase3_force_off,
        4: plan.phase4_force_off,
        5: plan.phase5_force_off,
        6: plan.phase6_force_off,
        7: plan.phase7_force_off,
        8: plan.phase8_force_off,
    }

    if cl <= 0:
        return {f"sepac_split{i}": 0.0 for i in range(1, 9)}

    splits = {}

    # Phase 3: direct (barrier 2 start, Ring A)
    splits["sepac_split3"] = fo[3] if fo[3] > 0 else 0.0

    # Phase 4: barrier 2 remainder, Ring A
    if fo[4] <= 0:
        splits["sepac_split4"] = 0.0
    elif fo[3] <= 0:
        splits["sepac_split4"] = fo[4]
    else:
        splits["sepac_split4"] = fo[4] - fo[3]

    # Phase 7: direct (barrier 2 start, Ring B)
    splits["sepac_split7"] = fo[7] if fo[7] > 0 else 0.0

    # Phase 8: barrier 2 remainder, Ring B
    if fo[8] <= 0:
        splits["sepac_split8"] = 0.0
    elif fo[7] <= 0:
        splits["sepac_split8"] = fo[8]
    else:
        splits["sepac_split8"] = fo[8] - fo[7]

    # Phase 1: left-turn, barrier 1, Ring A
    # VBA: IF(FO1=0, 0, IF(FO3+FO4=0, IF(FO8=0, FO1-FO7, FO1-FO8), IF(FO4=0, FO1-FO3, FO1-FO4)))
    if fo[1] <= 0:
        splits["sepac_split1"] = 0.0
    elif fo[3] + fo[4] == 0:
        # No barrier 2 on Ring A — use Ring B barrier 2
        if fo[8] <= 0:
            splits["sepac_split1"] = fo[1] - fo[7] if fo[7] > 0 else fo[1]
        else:
            splits["sepac_split1"] = fo[1] - fo[8]
    else:
        if fo[4] <= 0:
            splits["sepac_split1"] = fo[1] - fo[3]
        else:
            splits["sepac_split1"] = fo[1] - fo[4]

    # Phase 2: through, barrier 1, Ring A
    # VBA: IF(CL=0, 0, IF(FO3+FO4=0, IF(FO1=0, CL-S7-S8, CL-FO1), IF(FO1=0, CL-S3-S4, CL-FO1)))
    if cl <= 0:
        splits["sepac_split2"] = 0.0
    elif fo[3] + fo[4] == 0:
        if fo[1] <= 0:
            splits["sepac_split2"] = cl - splits["sepac_split7"] - splits["sepac_split8"]
        else:
            splits["sepac_split2"] = cl - fo[1]
    else:
        if fo[1] <= 0:
            splits["sepac_split2"] = cl - splits["sepac_split3"] - splits["sepac_split4"]
        else:
            splits["sepac_split2"] = cl - fo[1]

    # Phase 5: left-turn, barrier 1, Ring B
    # VBA: IF(FO5=0, 0, IF(FO7+FO8=0, IF(FO4=0, FO5-FO3, FO5-FO4), IF(FO8=0, FO5-FO7, FO5-FO8)))
    if fo[5] <= 0:
        splits["sepac_split5"] = 0.0
    elif fo[7] + fo[8] == 0:
        # No barrier 2 on Ring B — use Ring A barrier 2
        if fo[4] <= 0:
            splits["sepac_split5"] = fo[5] - fo[3] if fo[3] > 0 else fo[5]
        else:
            splits["sepac_split5"] = fo[5] - fo[4]
    else:
        if fo[8] <= 0:
            splits["sepac_split5"] = fo[5] - fo[7]
        else:
            splits["sepac_split5"] = fo[5] - fo[8]

    # Phase 6: through, barrier 1, Ring B
    # VBA: IF(CL=0, 0, IF(FO7+FO8=0, IF(FO5=0, CL-S3-S4, CL-FO5), IF(FO5=0, CL-S7-S8, CL-FO5)))
    if cl <= 0:
        splits["sepac_split6"] = 0.0
    elif fo[7] + fo[8] == 0:
        if fo[5] <= 0:
            splits["sepac_split6"] = cl - splits["sepac_split3"] - splits["sepac_split4"]
        else:
            splits["sepac_split6"] = cl - fo[5]
    else:
        if fo[5] <= 0:
            splits["sepac_split6"] = cl - splits["sepac_split7"] - splits["sepac_split8"]
        else:
            splits["sepac_split6"] = cl - fo[5]

    # Round to 1 decimal to avoid floating point artifacts
    return {k: round(v, 1) for k, v in splits.items()}


def compute_min_splits_without_peds(phase_timings: list[PhaseTiming], bank: int = 1) -> dict[int, float]:
    """Compute minimum split times WITHOUT pedestrian timing.

    VBA formula: MinGreen + Yellow + RedClear + 1
    (same for all phases — left-turn and through)
    """
    bank_timings = {t.phase_number: t for t in phase_timings if t.bank == bank}
    min_splits = {}

    for phase_num in range(1, 9):
        t = bank_timings.get(phase_num)
        if not t:
            min_splits[phase_num] = 0.0
            continue
        min_splits[phase_num] = round(t.min_green + t.yellow_change + t.red_clear + 1, 1)

    return min_splits


def compute_min_splits(phase_timings: list[PhaseTiming], bank: int = 1) -> dict[int, float]:
    """Compute minimum split times WITH pedestrian timing.

    VBA formula:
      All phases: MAX(MinGreen, Walk+FDW) + Yellow + RedClear + 1
    """
    bank_timings = {t.phase_number: t for t in phase_timings if t.bank == bank}
    min_splits = {}

    for phase_num in range(1, 9):
        t = bank_timings.get(phase_num)
        if not t:
            min_splits[phase_num] = 0.0
            continue

        ped_total = t.ped_walk + t.ped_fdw
        green_component = max(t.min_green, ped_total)
        min_splits[phase_num] = round(green_component + t.yellow_change + t.red_clear + 1, 1)

    return min_splits


def validate_splits(sepac_splits: dict[str, float],
                    min_splits: dict[int, float]) -> list[dict]:
    """Validate SEPAC splits against minimum split requirements.

    Returns list of validation results per phase.
    """
    results = []
    for phase_num in range(1, 9):
        key = f"sepac_split{phase_num}"
        split_val = sepac_splits.get(key, 0.0)
        min_val = min_splits.get(phase_num, 0.0)

        if split_val == 0.0 and min_val == 0.0:
            status = "inactive"
        elif split_val >= min_val:
            status = "pass"
        else:
            status = "fail"

        results.append({
            "phase": phase_num,
            "sepac_split": split_val,
            "min_split": min_val,
            "difference": round(split_val - min_val, 1),
            "status": status,
        })

    return results

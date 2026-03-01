"""Parse Page 2 of 8 — Phase timing (3 banks) + Coordination plans 1-15."""

import xlrd

from app.utils.xls_helpers import safe_float, safe_str


# Phase timing rows and their parameter names
TIMING_ROWS = {
    5: "ped_walk",
    6: "ped_fdw",
    7: "min_green",
    10: "veh_extension",
    13: "max_limit_1",
    14: "max_limit_2",
    19: "yellow_change",
    20: "red_clear",
}

# Bank column offsets: bank -> start_col (phases 1-8 are at start_col+0 to start_col+7)
BANK_COLS = {1: 3, 2: 12, 3: 21}

# Coordination plan columns for plans 1-15
PLAN_COLS_PAGE2 = {
    1: 3, 2: 5, 3: 7, 4: 9, 5: 11, 6: 13, 7: 15,
    8: 17, 9: 19, 10: 21, 11: 23, 12: 25, 13: 27, 14: 29, 15: 30,
}

# Coordination row offsets (rows 26-38)
COORD_ROWS = {
    "cycle_length": 26,
    "phase1_force_off": 27,
    "phase2_force_off": 28,
    "phase3_force_off": 29,
    "phase4_force_off": 30,
    "phase5_force_off": 31,
    "phase6_force_off": 32,
    "phase7_force_off": 33,
    "phase8_force_off": 34,
    "offset": 36,
    "sync_phases": 37,
    "lag_phases": 38,
}


def parse_phase_timing(sheet: xlrd.sheet.Sheet) -> list[dict]:
    """Parse 3 banks x 8 phases of timing parameters."""
    timings = []
    for bank, start_col in BANK_COLS.items():
        for phase_idx in range(8):
            col = start_col + phase_idx
            phase_num = phase_idx + 1
            entry = {"bank": bank, "phase_number": phase_num}
            for row, param_name in TIMING_ROWS.items():
                entry[param_name] = safe_float(sheet, row, col)
            timings.append(entry)
    return timings


def parse_coordination_plans_1_15(sheet: xlrd.sheet.Sheet) -> list[dict]:
    """Parse coordination plans 1-15 from Page 2."""
    plans = []
    for plan_num, col in PLAN_COLS_PAGE2.items():
        cycle_length = safe_float(sheet, COORD_ROWS["cycle_length"], col)
        plan = {
            "plan_number": plan_num,
            "cycle_length": cycle_length,
            "phase1_force_off": safe_float(sheet, COORD_ROWS["phase1_force_off"], col),
            "phase2_force_off": safe_float(sheet, COORD_ROWS["phase2_force_off"], col),
            "phase3_force_off": safe_float(sheet, COORD_ROWS["phase3_force_off"], col),
            "phase4_force_off": safe_float(sheet, COORD_ROWS["phase4_force_off"], col),
            "phase5_force_off": safe_float(sheet, COORD_ROWS["phase5_force_off"], col),
            "phase6_force_off": safe_float(sheet, COORD_ROWS["phase6_force_off"], col),
            "phase7_force_off": safe_float(sheet, COORD_ROWS["phase7_force_off"], col),
            "phase8_force_off": safe_float(sheet, COORD_ROWS["phase8_force_off"], col),
            "offset": safe_float(sheet, COORD_ROWS["offset"], col),
            "sync_phases": safe_str(sheet, COORD_ROWS["sync_phases"], col),
            "lag_phases": safe_str(sheet, COORD_ROWS["lag_phases"], col),
        }
        plans.append(plan)
    return plans


def parse_page2(sheet: xlrd.sheet.Sheet) -> dict:
    return {
        "phase_timings": parse_phase_timing(sheet),
        "coordination_plans_1_15": parse_coordination_plans_1_15(sheet),
    }

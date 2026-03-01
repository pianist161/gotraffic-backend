"""Parse Page 3 of 8 — Coordination plans 16-30."""

import xlrd

from app.utils.xls_helpers import safe_float, safe_str

# Plan columns for plans 16-30 on Page 3
PLAN_COLS_PAGE3 = {
    16: 3, 17: 4, 18: 6, 19: 8, 20: 10, 21: 11, 22: 12,
    23: 13, 24: 14, 25: 15, 26: 16, 27: 17, 28: 18, 29: 19, 30: 20,
}

# Row offsets on Page 3 (same structure as Page 2 but starting at row 4)
COORD_ROWS_P3 = {
    "cycle_length": 4,
    "phase1_force_off": 5,
    "phase2_force_off": 6,
    "phase3_force_off": 7,
    "phase4_force_off": 8,
    "phase5_force_off": 9,
    "phase6_force_off": 10,
    "phase7_force_off": 11,
    "phase8_force_off": 12,
    "offset": 14,
    "sync_phases": 15,
    "lag_phases": 16,
}


def parse_coordination_plans_16_30(sheet: xlrd.sheet.Sheet) -> list[dict]:
    """Parse coordination plans 16-30 from Page 3."""
    plans = []
    for plan_num, col in PLAN_COLS_PAGE3.items():
        cycle_length = safe_float(sheet, COORD_ROWS_P3["cycle_length"], col)
        plan = {
            "plan_number": plan_num,
            "cycle_length": cycle_length,
            "phase1_force_off": safe_float(sheet, COORD_ROWS_P3["phase1_force_off"], col),
            "phase2_force_off": safe_float(sheet, COORD_ROWS_P3["phase2_force_off"], col),
            "phase3_force_off": safe_float(sheet, COORD_ROWS_P3["phase3_force_off"], col),
            "phase4_force_off": safe_float(sheet, COORD_ROWS_P3["phase4_force_off"], col),
            "phase5_force_off": safe_float(sheet, COORD_ROWS_P3["phase5_force_off"], col),
            "phase6_force_off": safe_float(sheet, COORD_ROWS_P3["phase6_force_off"], col),
            "phase7_force_off": safe_float(sheet, COORD_ROWS_P3["phase7_force_off"], col),
            "phase8_force_off": safe_float(sheet, COORD_ROWS_P3["phase8_force_off"], col),
            "offset": safe_float(sheet, COORD_ROWS_P3["offset"], col),
            "sync_phases": safe_str(sheet, COORD_ROWS_P3["sync_phases"], col),
            "lag_phases": safe_str(sheet, COORD_ROWS_P3["lag_phases"], col),
        }
        plans.append(plan)
    return plans


def parse_page3(sheet: xlrd.sheet.Sheet) -> dict:
    return {
        "coordination_plans_16_30": parse_coordination_plans_16_30(sheet),
    }

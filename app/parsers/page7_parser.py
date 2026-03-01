"""Parse Page 7 of 8 — Preemption configurations."""

import xlrd

from app.utils.xls_helpers import safe_float, safe_str


def _parse_preempt_table(sheet: xlrd.sheet.Sheet, start_row: int, table_num: int) -> list[dict]:
    """Parse a preemption special event table.

    Each table has 16 rows (0-F) with preemption event data.
    Columns: 2=Clear, 3=Time, 4=PedCall, 5=Hold, 6=Advance,
             7=ForceOff, 8=VehicleCall, 9=PermitPhases, 10=PedOmit, 11=Output
    """
    preempts = []
    for i in range(16):
        row = start_row + i
        if row >= sheet.nrows:
            break

        time_val = safe_float(sheet, row, 3)
        force_off = safe_str(sheet, row, 7)
        vehicle_call = safe_str(sheet, row, 8)
        permit_phases = safe_str(sheet, row, 9)
        ped_omit = safe_str(sheet, row, 10)

        # Only include entries that have meaningful data
        has_data = (
            time_val > 0 or
            force_off.replace("_", "") != "" or
            vehicle_call.replace("_", "") != ""
        )

        if has_data:
            preempts.append({
                "preempt_number": table_num,
                "input_number": i,
                "delay": time_val,
                "minimum_duration": 0.0,
                "track_green_phases": force_off,
                "dwell_green_phases": vehicle_call,
                "exit_phases": permit_phases,
            })

    return preempts


def parse_page7(sheet: xlrd.sheet.Sheet) -> dict:
    # Table 1: rows 5-20
    preempts_t1 = _parse_preempt_table(sheet, 5, table_num=1)

    # Table 2: rows 25-40
    preempts_t2 = _parse_preempt_table(sheet, 25, table_num=2)

    # Preempt timing values (right side of page)
    timing = {}
    timing_labels = {
        5: "rr1_delay", 6: "rr1_clear",
        7: "ev_a_delay", 8: "ev_a_clear",
        9: "ev_b_delay", 10: "ev_b_clear",
        11: "ev_c_delay", 12: "ev_c_clear",
        13: "ev_d_delay", 14: "ev_d_clear",
        15: "rr2_delay", 16: "rr2_clear",
    }
    for row, name in timing_labels.items():
        timing[name] = safe_float(sheet, row, 15)

    return {
        "preemption_configs": preempts_t1 + preempts_t2,
        "preemption_timing": timing,
    }

"""Parse Page 5 of 8 — Detectors + Overlaps."""

import xlrd

from app.utils.xls_helpers import safe_float, safe_str, safe_int


def _parse_detectors(sheet: xlrd.sheet.Sheet) -> list[dict]:
    """Parse detector entries from two detector banks on Page 5."""
    detectors = []

    # Detector bank 1: rows 5-20 (indices 0-F)
    # col3=C1 Pin Number, col4=Attributes, col5=Phase(s), col6=Assign, col8=Delay, col9=Carryover
    for i in range(16):
        row = 5 + i
        pin_number = safe_int(sheet, row, 3)
        if pin_number == 0:
            continue

        attributes = safe_str(sheet, row, 4)
        phases = safe_str(sheet, row, 5)
        assign = safe_str(sheet, row, 6)
        delay = safe_float(sheet, row, 8)
        carryover = safe_float(sheet, row, 9)

        # Determine phase assignment from phases string
        phase_assignment = None
        for ch in phases:
            if ch.isdigit() and ch != '_':
                phase_assignment = int(ch)
                break

        # Determine call type from attributes
        call_type = "vehicle"
        if '2' in attributes:  # attribute bit 2 = ped call
            call_type = "pedestrian"
        if '5' in attributes:  # attribute bit 5 = extension
            call_type = "extension"

        detectors.append({
            "detector_number": i + 1,
            "phase_assignment": phase_assignment,
            "delay": delay,
            "extend": carryover,
            "call_type": call_type,
            "lock": False,
        })

    # Detector bank 2: rows 26-41
    for i in range(16):
        row = 26 + i
        if row >= sheet.nrows:
            break
        pin_number = safe_int(sheet, row, 3)
        if pin_number == 0:
            continue

        phases = safe_str(sheet, row, 5)
        delay = safe_float(sheet, row, 8)
        carryover = safe_float(sheet, row, 9)
        attributes = safe_str(sheet, row, 4)

        phase_assignment = None
        for ch in phases:
            if ch.isdigit() and ch != '_':
                phase_assignment = int(ch)
                break

        call_type = "vehicle"
        if '2' in attributes:
            call_type = "pedestrian"

        detectors.append({
            "detector_number": 16 + i + 1,
            "phase_assignment": phase_assignment,
            "delay": delay,
            "extend": carryover,
            "call_type": call_type,
            "lock": False,
        })

    return detectors


def _parse_overlaps(sheet: xlrd.sheet.Sheet) -> list[dict]:
    """Parse overlap assignments from Page 5."""
    overlaps = []
    overlap_letters = ["A", "B", "C", "D", "E", "F", "G", "H"]
    overlap_cols = {
        "A": 12, "B": 13, "C": 14, "D": 15,
        "E": 16, "F": 17, "G": 18, "H": 19,
    }

    for letter in overlap_letters:
        col = overlap_cols[letter]
        # Row 5: Load Switch Number
        load_switch = safe_int(sheet, 5, col)

        # Row 6: Veh Set 1 parent phases
        veh_set_1 = safe_str(sheet, 6, col)

        # Rows 19/20: Yellow Change / Red Clear
        yellow = safe_float(sheet, 19, col)
        red_clear = safe_float(sheet, 20, col)

        # Build parent phases string from veh set 1
        parent_phases = veh_set_1 if veh_set_1.replace("_", "") else ""

        if load_switch > 0 or parent_phases:
            overlaps.append({
                "overlap_letter": letter,
                "parent_phases": parent_phases,
                "yellow_change": yellow,
                "red_clear": red_clear,
            })

    return overlaps


def parse_page5(sheet: xlrd.sheet.Sheet) -> dict:
    return {
        "detectors": _parse_detectors(sheet),
        "overlaps": _parse_overlaps(sheet),
    }

"""Parse Page 8 of 8 — System configuration."""

import xlrd

from app.utils.xls_helpers import safe_float, safe_str


def parse_page8(sheet: xlrd.sheet.Sheet) -> dict:
    """Parse system configuration parameters."""

    # Right side of Page 8 has config parameters
    # Row 18: Max OFF (minutes)
    max_off = safe_float(sheet, 18, 11)
    # Row 19: Max ON (minutes)
    max_on = safe_float(sheet, 19, 11)
    # Row 20: Detector Chatter
    detector_chatter = safe_float(sheet, 20, 11)
    # Row 23: Zone Address
    zone_address = safe_float(sheet, 23, 11)
    # Row 25: Comm Address
    comm_address = safe_float(sheet, 25, 11)
    # Row 34: Transition Type
    transition_type = safe_float(sheet, 34, 11)

    # Flash/startup from Page 5 right side (rows 34-36)
    # Actually these are on Page 5 — page 8 has different config
    # Config timers from page 8:
    # Red Revert is at row 35 col 15 on page 5, but let's grab from page 8 if available

    return {
        "system_config": {
            "max_off_minutes": max_off,
            "max_on_minutes": max_on,
            "detector_chatter": detector_chatter,
            "zone_address": zone_address,
            "comm_address": comm_address,
            "transition_type": transition_type,
        }
    }

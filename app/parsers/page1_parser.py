"""Parse Page 1 of 8 — Intersection metadata, movements, zones."""

import xlrd

from app.utils.xls_helpers import safe_str, safe_float, safe_int


def parse_page1(sheet: xlrd.sheet.Sheet) -> dict:
    """Return intersection metadata dict from Page 1."""

    asset_raw = safe_float(sheet, 3, 10)
    asset_number = str(int(asset_raw)) if asset_raw else None

    location_name = safe_str(sheet, 3, 2)
    section = safe_str(sheet, 5, 2)
    preemption_raw = safe_str(sheet, 9, 2)
    has_preemption = preemption_raw.lower() == "yes"
    equipment_type = safe_str(sheet, 12, 2)

    cabinet_raw = safe_float(sheet, 13, 2)
    cabinet_type = str(int(cabinet_raw)) if cabinet_raw else safe_str(sheet, 13, 2)

    drop_raw = safe_float(sheet, 16, 2)
    drop_address = str(int(drop_raw)) if drop_raw else safe_str(sheet, 16, 2)

    # Phase movements (rows 7-14, phases 1-8)
    phase_movements = []
    for i, row_idx in enumerate(range(7, 15)):
        phase_num = i + 1
        movement = safe_str(sheet, row_idx, 6)
        if movement:
            phase_movements.append({
                "phase_number": phase_num,
                "movement": movement,
                "protected": phase_num in (1, 3, 5, 7),  # odd = left-turn = protected
            })

    # Overlap assignments (rows 7-14, col 8)
    overlaps_page1 = []
    for i, row_idx in enumerate(range(7, 15)):
        letter = safe_str(sheet, row_idx, 8)
        if letter:
            overlaps_page1.append({"overlap_number": i + 1, "overlap_letter": letter})

    # Zone assignments (rows 33-38)
    zone_categories = [
        (33, "Engineering"),
        (34, "Maintenance"),
        (35, "Systems"),
        (36, "Electronic Shop"),
        (37, "Municipality"),
        (38, "Controller Type"),
    ]
    zone_assignments = []
    for row_idx, category in zone_categories:
        zone_val = safe_str(sheet, row_idx, 2)
        if zone_val:
            zone_assignments.append({"category": category, "zone": zone_val})

    # Extract street names from location
    street_name_1 = ""
    street_name_2 = ""
    if location_name and "&" in location_name:
        parts = location_name.split("&")
        street_name_1 = parts[0].strip()
        street_name_2 = parts[1].strip() if len(parts) > 1 else ""
    elif location_name and "/" in location_name:
        parts = location_name.split("/")
        street_name_1 = parts[0].strip()
        street_name_2 = parts[1].strip() if len(parts) > 1 else ""

    return {
        "asset_number": asset_number,
        "location_name": location_name,
        "street_name_1": street_name_1,
        "street_name_2": street_name_2,
        "section": section,
        "equipment_type": equipment_type,
        "cabinet_type": cabinet_type,
        "drop_address": drop_address,
        "has_preemption": has_preemption,
        "phase_movements": phase_movements,
        "zone_assignments": zone_assignments,
    }

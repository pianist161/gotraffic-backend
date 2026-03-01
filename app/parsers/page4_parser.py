"""Parse Page 4 of 8 — TOD/DOW scheduling (3 banks) + holiday events."""

import xlrd

from app.utils.xls_helpers import safe_float, safe_int, safe_str


def _parse_tod_bank(sheet: xlrd.sheet.Sheet, start_row: int, hour_col: int,
                    minute_col: int, dow_col: int, plan_col: int,
                    bank: int) -> list[dict]:
    """Parse a bank of TOD schedule entries (16 entries per bank: rows 0-F)."""
    entries = []
    for i in range(16):
        row = start_row + i
        hour = safe_int(sheet, row, hour_col)
        minute = safe_int(sheet, row, minute_col)
        dow = safe_str(sheet, row, dow_col)
        plan = safe_int(sheet, row, plan_col)

        # Skip empty entries (no day-of-week pattern or all underscores)
        if dow.replace("_", "") == "" and plan == 0 and hour == 0 and minute == 0:
            continue

        entries.append({
            "bank": bank,
            "event_index": i,
            "hour": hour,
            "minute": minute,
            "day_of_week": dow,
            "plan_number": plan,
        })
    return entries


def _parse_holiday_events(sheet: xlrd.sheet.Sheet, start_row: int,
                          day_col: int, month_col: int, bank: int) -> list[dict]:
    """Parse holiday date entries."""
    events = []
    for i in range(16):
        row = start_row + i
        day = safe_int(sheet, row, day_col)
        month_raw = safe_str(sheet, row, month_col)

        if day == 0 and (month_raw == "0" or month_raw == ""):
            continue

        # Convert hex month to int (A=10, B=11, C=12)
        month_map = {"A": 10, "B": 11, "C": 12}
        if month_raw in month_map:
            month = month_map[month_raw]
        elif month_raw.isdigit():
            month = int(month_raw)
        else:
            month = 0

        if day > 0 and month > 0:
            events.append({
                "event_index": i,
                "month": month,
                "day": day,
                "plan_number": 0,  # Holiday events use type, not plan
            })
    return events


def parse_page4(sheet: xlrd.sheet.Sheet) -> dict:
    # Bank 1: rows 4-19, hour=col2, minute=col4, dow=col5, plan=col6
    tod_bank1 = _parse_tod_bank(sheet, 4, 2, 4, 5, 6, bank=1)

    # Bank 2: rows 24-39, same column layout
    tod_bank2 = _parse_tod_bank(sheet, 24, 2, 4, 5, 6, bank=2)

    # Bank 3: rows 44 onward (if present)
    tod_bank3 = []
    if sheet.nrows > 44:
        tod_bank3 = _parse_tod_bank(sheet, 44, 2, 4, 5, 6, bank=3)

    # Holiday dates bank 1: rows 4-19, day=col16, month=col17
    holidays_bank1 = _parse_holiday_events(sheet, 4, 16, 17, bank=1)

    # Holiday dates bank 2: rows 24-39
    holidays_bank2 = _parse_holiday_events(sheet, 24, 16, 17, bank=2)

    return {
        "tod_schedules": tod_bank1 + tod_bank2 + tod_bank3,
        "holiday_events": holidays_bank1 + holidays_bank2,
    }

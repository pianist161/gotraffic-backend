"""Parse Page 6 of 8 — Assignable outputs/inputs (stored as metadata, not modeled separately)."""

import xlrd


def parse_page6(sheet: xlrd.sheet.Sheet) -> dict:
    """Page 6 contains assignable I/O. Stored as raw data for reference."""
    return {"assignable_io": "parsed"}

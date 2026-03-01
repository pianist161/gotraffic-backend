"""Helpers for reading BiTrans XLS cell values safely."""

import xlrd


def safe_float(sheet: xlrd.sheet.Sheet, row: int, col: int, default: float = 0.0) -> float:
    try:
        val = sheet.cell_value(row, col)
        if isinstance(val, (int, float)):
            return float(val)
        if isinstance(val, str):
            val = val.strip()
            if val == '' or val == '-':
                return default
            return float(val)
        return default
    except (IndexError, ValueError):
        return default


def safe_str(sheet: xlrd.sheet.Sheet, row: int, col: int, default: str = "") -> str:
    try:
        val = sheet.cell_value(row, col)
        if isinstance(val, float):
            if val == int(val):
                return str(int(val))
            return str(val)
        return str(val).strip() if val else default
    except (IndexError, ValueError):
        return default


def safe_int(sheet: xlrd.sheet.Sheet, row: int, col: int, default: int = 0) -> int:
    try:
        val = sheet.cell_value(row, col)
        if isinstance(val, (int, float)):
            return int(val)
        if isinstance(val, str) and val.strip().isdigit():
            return int(val.strip())
        return default
    except (IndexError, ValueError):
        return default


def extract_asset_from_header(sheet: xlrd.sheet.Sheet) -> str | None:
    """Extract asset number from the standard header row (row 0 or row 3)."""
    # Try row 0 header string: "INTERSECTION: ... Asset: 2401 ..."
    header = safe_str(sheet, 0, 0)
    if 'Asset:' in header:
        parts = header.split('Asset:')
        if len(parts) > 1:
            asset = parts[1].strip().split()[0]
            return asset
    # Try Page 1 specific location (row 3, col 10)
    val = safe_float(sheet, 3, 10)
    if val > 0:
        return str(int(val))
    return None

"""BiTrans XLS orchestrator — parses all 8 pages and returns structured data."""

from pathlib import Path

import xlrd

from app.parsers.page1_parser import parse_page1
from app.parsers.page2_parser import parse_page2
from app.parsers.page3_parser import parse_page3
from app.parsers.page4_parser import parse_page4
from app.parsers.page5_parser import parse_page5
from app.parsers.page6_parser import parse_page6
from app.parsers.page7_parser import parse_page7
from app.parsers.page8_parser import parse_page8


class ParseResult:
    def __init__(self):
        self.intersection: dict = {}
        self.phase_timings: list[dict] = []
        self.coordination_plans: list[dict] = []
        self.tod_schedules: list[dict] = []
        self.holiday_events: list[dict] = []
        self.detectors: list[dict] = []
        self.overlaps: list[dict] = []
        self.preemption_configs: list[dict] = []
        self.warnings: list[str] = []


def parse_bitrans_xls(file_path: str | Path) -> ParseResult:
    """Parse a complete BiTrans XLS export file.

    Args:
        file_path: Path to the .xls file

    Returns:
        ParseResult with all parsed data and any warnings
    """
    result = ParseResult()
    wb = xlrd.open_workbook(str(file_path))

    sheet_map = {s: wb.sheet_by_name(s) for s in wb.sheet_names()}

    def get_sheet(page_name: str):
        if page_name in sheet_map:
            return sheet_map[page_name]
        result.warnings.append(f"Sheet '{page_name}' not found")
        return None

    # Page 1 — Intersection metadata
    sheet1 = get_sheet("Page 1 of 8")
    if sheet1:
        result.intersection = parse_page1(sheet1)
    else:
        result.warnings.append("Critical: Page 1 missing, cannot identify intersection")
        return result

    # Page 2 — Phase timing + coordination plans 1-15
    sheet2 = get_sheet("Page 2 of 8")
    if sheet2:
        p2 = parse_page2(sheet2)
        result.phase_timings = p2["phase_timings"]
        result.coordination_plans = p2["coordination_plans_1_15"]

    # Page 3 — Coordination plans 16-30
    sheet3 = get_sheet("Page 3 of 8")
    if sheet3:
        p3 = parse_page3(sheet3)
        result.coordination_plans.extend(p3["coordination_plans_16_30"])

    # Page 4 — TOD scheduling
    sheet4 = get_sheet("Page 4 of 8")
    if sheet4:
        p4 = parse_page4(sheet4)
        result.tod_schedules = p4["tod_schedules"]
        result.holiday_events = p4["holiday_events"]

    # Page 5 — Detectors + overlaps
    sheet5 = get_sheet("Page 5 of 8")
    if sheet5:
        p5 = parse_page5(sheet5)
        result.detectors = p5["detectors"]
        result.overlaps = p5["overlaps"]

    # Page 6 — Assignable I/O (minimal data extraction)
    sheet6 = get_sheet("Page 6 of 8")
    if sheet6:
        parse_page6(sheet6)

    # Page 7 — Preemption
    sheet7 = get_sheet("Page 7 of 8")
    if sheet7:
        p7 = parse_page7(sheet7)
        result.preemption_configs = p7["preemption_configs"]

    # Page 8 — System config
    sheet8 = get_sheet("Page 8 of 8")
    if sheet8:
        p8 = parse_page8(sheet8)
        sys_cfg = p8["system_config"]
        result.intersection["max_off_minutes"] = sys_cfg.get("max_off_minutes")
        result.intersection["max_on_minutes"] = sys_cfg.get("max_on_minutes")
        result.intersection["detector_chatter"] = sys_cfg.get("detector_chatter")
        result.intersection["zone_address"] = sys_cfg.get("zone_address")
        result.intersection["comm_address"] = sys_cfg.get("comm_address")
        result.intersection["transition_type"] = sys_cfg.get("transition_type")

    # Validation
    if not result.intersection.get("asset_number"):
        result.warnings.append("Could not extract asset number")
    if not result.phase_timings:
        result.warnings.append("No phase timing data found")
    if not result.coordination_plans:
        result.warnings.append("No coordination plans found")

    active_plans = [p for p in result.coordination_plans if p["cycle_length"] > 0]
    if active_plans:
        result.warnings.append(f"Found {len(active_plans)} active coordination plans")

    return result

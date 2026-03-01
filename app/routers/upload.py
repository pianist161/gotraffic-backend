"""Upload endpoints for BiTrans XLS and master list XLSM files."""

import shutil
from pathlib import Path
from typing import List

from fastapi import APIRouter, Depends, File, HTTPException, UploadFile
from sqlalchemy.orm import Session

from app.config import settings
from app.database import get_db
from app.models.master_list import MasterIntersection
from app.parsers.bitrans_parser import parse_bitrans_xls
from app.parsers.master_list_parser import parse_master_list
from app.services.intersection_service import persist_parse_result

router = APIRouter()


@router.post("/bitrans")
def upload_bitrans(file: UploadFile = File(...), db: Session = Depends(get_db)):
    """Upload a BiTrans XLS export file, parse, convert, and persist."""
    if not file.filename:
        raise HTTPException(400, "No file provided")

    suffix = Path(file.filename).suffix.lower()
    if suffix not in (".xls", ".xlsx"):
        raise HTTPException(400, f"Invalid file type: {suffix}. Expected .xls or .xlsx")

    # Save uploaded file
    dest = settings.UPLOAD_DIR / file.filename
    with open(dest, "wb") as f:
        shutil.copyfileobj(file.file, f)

    # Parse
    try:
        result = parse_bitrans_xls(dest)
    except Exception as e:
        raise HTTPException(422, f"Failed to parse file: {str(e)}")

    if not result.intersection.get("asset_number"):
        raise HTTPException(422, "Could not extract asset number from file")

    # Persist
    try:
        intersection = persist_parse_result(db, result, file.filename)
    except Exception as e:
        raise HTTPException(500, f"Failed to save data: {str(e)}")

    active_plans = [p for p in result.coordination_plans if p["cycle_length"] > 0]

    return {
        "message": "File uploaded and parsed successfully",
        "asset_number": intersection.asset_number,
        "location": intersection.location_name,
        "phase_timings_count": len(result.phase_timings),
        "active_plans_count": len(active_plans),
        "detectors_count": len(result.detectors),
        "overlaps_count": len(result.overlaps),
        "warnings": result.warnings,
    }


@router.post("/batch")
def upload_batch(files: List[UploadFile] = File(...), db: Session = Depends(get_db)):
    """Upload multiple BiTrans XLS files at once."""
    results = []
    successful = 0
    failed = 0

    for file in files:
        entry = {"filename": file.filename, "asset_number": None, "status": "failed", "error": None}

        if not file.filename:
            entry["error"] = "No filename"
            failed += 1
            results.append(entry)
            continue

        suffix = Path(file.filename).suffix.lower()
        if suffix not in (".xls", ".xlsx"):
            entry["error"] = f"Invalid file type: {suffix}"
            failed += 1
            results.append(entry)
            continue

        # Save uploaded file
        dest = settings.UPLOAD_DIR / file.filename
        try:
            with open(dest, "wb") as f:
                shutil.copyfileobj(file.file, f)
        except Exception as e:
            entry["error"] = f"Failed to save: {str(e)}"
            failed += 1
            results.append(entry)
            continue

        # Parse
        try:
            result = parse_bitrans_xls(dest)
        except Exception as e:
            entry["error"] = f"Parse error: {str(e)}"
            failed += 1
            results.append(entry)
            continue

        asset = result.intersection.get("asset_number")
        if not asset:
            entry["error"] = "Could not extract asset number"
            failed += 1
            results.append(entry)
            continue

        entry["asset_number"] = asset

        # Persist
        try:
            persist_parse_result(db, result, file.filename)
            entry["status"] = "success"
            successful += 1
        except Exception as e:
            entry["error"] = f"Save error: {str(e)}"
            failed += 1

        results.append(entry)

    return {
        "total": len(files),
        "successful": successful,
        "failed": failed,
        "results": results,
    }


@router.post("/master-list")
def upload_master_list(file: UploadFile = File(...), db: Session = Depends(get_db)):
    """Upload a master list XLSM file."""
    if not file.filename:
        raise HTTPException(400, "No file provided")

    suffix = Path(file.filename).suffix.lower()
    if suffix not in (".xlsm", ".xlsx", ".xls"):
        raise HTTPException(400, f"Invalid file type: {suffix}")

    dest = settings.UPLOAD_DIR / file.filename
    with open(dest, "wb") as f:
        shutil.copyfileobj(file.file, f)

    try:
        entries = parse_master_list(dest)
    except Exception as e:
        raise HTTPException(422, f"Failed to parse master list: {str(e)}")

    if not entries:
        raise HTTPException(422, "No entries found in master list")

    # Clear existing master list
    db.query(MasterIntersection).delete()

    # Insert new entries
    for entry in entries:
        db.add(MasterIntersection(
            asset_number=entry["asset_number"],
            polygon=entry.get("polygon"),
            location=entry.get("location"),
            phases_json=entry.get("phases_json"),
        ))

    db.commit()

    return {
        "message": "Master list uploaded successfully",
        "entries_count": len(entries),
    }

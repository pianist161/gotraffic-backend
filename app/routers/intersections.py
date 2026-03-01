"""CRUD endpoints for intersections."""

from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.orm import Session, joinedload

from app.database import get_db
from app.models.intersection import Intersection, IntersectionComment
from app.models.migration import MigrationRecord
from app.models.timing import FdotOverride, PhaseTiming, CoordinationPlan
from app.schemas.intersection import IntersectionSummary, IntersectionDetail, CommentCreate, CommentSchema
from app.schemas.timing import FdotOverrideSchema

router = APIRouter()


@router.get("/compare")
def compare_intersections(
    assets: str = Query(..., description="Comma-separated asset numbers (2-3)"),
    db: Session = Depends(get_db),
):
    """Compare 2-3 intersections side-by-side."""
    asset_list = [a.strip() for a in assets.split(",") if a.strip()]
    if len(asset_list) < 2 or len(asset_list) > 3:
        raise HTTPException(400, "Provide 2-3 asset numbers separated by commas")

    results = []
    for asset in asset_list:
        intersection = db.query(Intersection).filter(
            Intersection.asset_number == asset
        ).first()
        if not intersection:
            raise HTTPException(404, f"Intersection {asset} not found")

        timings = db.query(PhaseTiming).filter(
            PhaseTiming.intersection_id == intersection.id,
            PhaseTiming.bank == 1,
        ).order_by(PhaseTiming.phase_number).all()

        plans = db.query(CoordinationPlan).filter(
            CoordinationPlan.intersection_id == intersection.id,
            CoordinationPlan.cycle_length > 0,
        ).order_by(CoordinationPlan.plan_number).all()

        results.append({
            "asset_number": intersection.asset_number,
            "location": intersection.location_name,
            "equipment_type": intersection.equipment_type,
            "phase_timings": [
                {
                    "phase": t.phase_number,
                    "ped_walk": t.ped_walk, "ped_fdw": t.ped_fdw,
                    "min_green": t.min_green, "yellow_change": t.yellow_change,
                    "red_clear": t.red_clear,
                }
                for t in timings
            ],
            "plans": [
                {
                    "plan_number": p.plan_number,
                    "cycle_length": p.cycle_length,
                    "offset": p.offset,
                    "sepac_splits": {
                        f"ph{i}": getattr(p, f"sepac_split{i}") for i in range(1, 9)
                    },
                }
                for p in plans
            ],
        })

    return {"intersections": results}


@router.get("")
def list_intersections(
    search: str = Query("", description="Search by asset, location, or street"),
    polygon: str = Query("", description="Filter by polygon"),
    status: str = Query("", description="Filter by migration status"),
    page: int = Query(1, ge=1),
    per_page: int = Query(20, ge=1, le=100),
    db: Session = Depends(get_db),
):
    query = db.query(Intersection)

    if search:
        like = f"%{search}%"
        query = query.filter(
            (Intersection.asset_number.like(like)) |
            (Intersection.location_name.like(like)) |
            (Intersection.street_name_1.like(like)) |
            (Intersection.street_name_2.like(like))
        )

    if status:
        # Join with migration records to filter by status
        query = query.join(
            MigrationRecord,
            MigrationRecord.asset_number == Intersection.asset_number
        ).filter(MigrationRecord.status == status)

    total = query.count()
    items = query.order_by(Intersection.asset_number).offset(
        (page - 1) * per_page
    ).limit(per_page).all()

    return {
        "items": [IntersectionSummary.model_validate(i) for i in items],
        "total": total,
        "page": page,
        "per_page": per_page,
        "pages": (total + per_page - 1) // per_page,
    }


@router.get("/{asset}")
def get_intersection(asset: str, db: Session = Depends(get_db)):
    intersection = db.query(Intersection).options(
        joinedload(Intersection.phase_movements),
        joinedload(Intersection.zone_assignments),
    ).filter(Intersection.asset_number == asset).first()

    if not intersection:
        raise HTTPException(404, f"Intersection {asset} not found")

    return IntersectionDetail.model_validate(intersection)


@router.delete("/{asset}")
def delete_intersection(asset: str, db: Session = Depends(get_db)):
    intersection = db.query(Intersection).filter(
        Intersection.asset_number == asset
    ).first()
    if not intersection:
        raise HTTPException(404, f"Intersection {asset} not found")

    # Also delete migration record
    db.query(MigrationRecord).filter(
        MigrationRecord.asset_number == asset
    ).delete()

    db.delete(intersection)
    db.commit()
    return {"message": f"Intersection {asset} deleted"}


# --- Comments CRUD ---

@router.post("/{asset}/comments")
def add_comment(asset: str, body: CommentCreate, db: Session = Depends(get_db)):
    intersection = db.query(Intersection).filter(
        Intersection.asset_number == asset
    ).first()
    if not intersection:
        raise HTTPException(404, f"Intersection {asset} not found")

    if body.category not in ("general", "phase", "plan"):
        raise HTTPException(400, "Category must be general, phase, or plan")

    comment = IntersectionComment(
        intersection_id=intersection.id,
        text=body.text,
        category=body.category,
    )
    db.add(comment)
    db.commit()
    db.refresh(comment)
    return CommentSchema.model_validate(comment)


@router.get("/{asset}/comments")
def list_comments(asset: str, db: Session = Depends(get_db)):
    intersection = db.query(Intersection).filter(
        Intersection.asset_number == asset
    ).first()
    if not intersection:
        raise HTTPException(404, f"Intersection {asset} not found")

    comments = db.query(IntersectionComment).filter(
        IntersectionComment.intersection_id == intersection.id
    ).order_by(IntersectionComment.created_at.desc()).all()

    return [CommentSchema.model_validate(c) for c in comments]


@router.delete("/{asset}/comments/{comment_id}")
def delete_comment(asset: str, comment_id: int, db: Session = Depends(get_db)):
    intersection = db.query(Intersection).filter(
        Intersection.asset_number == asset
    ).first()
    if not intersection:
        raise HTTPException(404, f"Intersection {asset} not found")

    comment = db.query(IntersectionComment).filter(
        IntersectionComment.id == comment_id,
        IntersectionComment.intersection_id == intersection.id,
    ).first()
    if not comment:
        raise HTTPException(404, "Comment not found")

    db.delete(comment)
    db.commit()
    return {"message": "Comment deleted"}


# --- FDOT Diff ---

@router.get("/{asset}/fdot-diff")
def get_fdot_diff(asset: str, db: Session = Depends(get_db)):
    intersection = db.query(Intersection).filter(
        Intersection.asset_number == asset
    ).first()
    if not intersection:
        raise HTTPException(404, f"Intersection {asset} not found")

    overrides = db.query(FdotOverride).filter(
        FdotOverride.intersection_id == intersection.id,
    ).order_by(FdotOverride.phase_number, FdotOverride.bank, FdotOverride.field_name).all()

    return [FdotOverrideSchema.model_validate(o) for o in overrides]

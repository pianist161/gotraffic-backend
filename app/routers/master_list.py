"""Master list endpoints."""

from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.orm import Session

from app.database import get_db
from app.models.master_list import MasterIntersection
from app.schemas.master_list import MasterIntersectionSchema

router = APIRouter()


@router.get("")
def list_master_intersections(
    search: str = Query("", description="Search by asset or location"),
    page: int = Query(1, ge=1),
    per_page: int = Query(50, ge=1, le=200),
    db: Session = Depends(get_db),
):
    query = db.query(MasterIntersection)

    if search:
        like = f"%{search}%"
        query = query.filter(
            (MasterIntersection.asset_number.like(like)) |
            (MasterIntersection.location.like(like)) |
            (MasterIntersection.polygon.like(like))
        )

    total = query.count()
    items = query.order_by(MasterIntersection.asset_number).offset(
        (page - 1) * per_page
    ).limit(per_page).all()

    return {
        "items": [MasterIntersectionSchema.model_validate(i) for i in items],
        "total": total,
        "page": page,
        "per_page": per_page,
        "pages": (total + per_page - 1) // per_page,
    }


@router.get("/{asset}")
def get_master_intersection(asset: str, db: Session = Depends(get_db)):
    item = db.query(MasterIntersection).filter(
        MasterIntersection.asset_number == asset
    ).first()
    if not item:
        raise HTTPException(404, f"Asset {asset} not found in master list")
    return MasterIntersectionSchema.model_validate(item)

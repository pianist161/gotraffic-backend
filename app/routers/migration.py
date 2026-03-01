"""Migration tracking endpoints."""

from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.orm import Session

from app.database import get_db
from app.models.migration import MigrationRecord
from app.schemas.migration import MigrationRecordSchema, MigrationStatsSchema, StatusUpdateRequest
from app.services.migration_service import get_migration_stats, update_status

router = APIRouter()


@router.get("/stats")
def migration_stats(db: Session = Depends(get_db)):
    stats = get_migration_stats(db)
    return MigrationStatsSchema(**stats)


@router.get("")
def list_migrations(
    status: str = Query("", description="Filter by status"),
    search: str = Query("", description="Search by asset or polygon"),
    page: int = Query(1, ge=1),
    per_page: int = Query(20, ge=1, le=100),
    db: Session = Depends(get_db),
):
    query = db.query(MigrationRecord)

    if status:
        query = query.filter(MigrationRecord.status == status)
    if search:
        like = f"%{search}%"
        query = query.filter(
            (MigrationRecord.asset_number.like(like)) |
            (MigrationRecord.polygon.like(like))
        )

    total = query.count()
    items = query.order_by(MigrationRecord.asset_number).offset(
        (page - 1) * per_page
    ).limit(per_page).all()

    return {
        "items": [MigrationRecordSchema.model_validate(i) for i in items],
        "total": total,
        "page": page,
        "per_page": per_page,
        "pages": max(1, (total + per_page - 1) // per_page),
    }


@router.patch("/{asset}/status")
def update_migration_status(
    asset: str,
    body: StatusUpdateRequest,
    db: Session = Depends(get_db),
):
    try:
        record = update_status(db, asset, body.status)
    except ValueError as e:
        raise HTTPException(400, str(e))

    if not record:
        raise HTTPException(404, f"Migration record for {asset} not found")

    if body.notes is not None:
        record.notes = body.notes
        db.commit()
        db.refresh(record)

    return MigrationRecordSchema.model_validate(record)

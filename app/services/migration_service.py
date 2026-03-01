"""Migration tracking service."""

from sqlalchemy import func
from sqlalchemy.orm import Session

from app.models.migration import MigrationRecord

VALID_STATUSES = {"pending", "uploaded", "parsed", "converted", "exported", "complete"}


def get_migration_stats(db: Session) -> dict:
    """Get summary counts by migration status."""
    results = db.query(
        MigrationRecord.status,
        func.count(MigrationRecord.id)
    ).group_by(MigrationRecord.status).all()

    stats = {s: 0 for s in VALID_STATUSES}
    total = 0
    for status, count in results:
        stats[status] = count
        total += count
    stats["total"] = total
    return stats


def update_status(db: Session, asset_number: str, new_status: str) -> MigrationRecord | None:
    """Update migration status for an asset."""
    if new_status not in VALID_STATUSES:
        raise ValueError(f"Invalid status: {new_status}")

    record = db.query(MigrationRecord).filter(
        MigrationRecord.asset_number == asset_number
    ).first()
    if not record:
        return None

    record.status = new_status
    db.commit()
    db.refresh(record)
    return record

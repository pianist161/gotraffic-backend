from datetime import datetime
from pydantic import BaseModel


class MigrationRecordSchema(BaseModel):
    id: int
    asset_number: str
    polygon: str | None
    data_prep_date: datetime | None
    status: str
    notes: str | None
    updated_at: datetime

    class Config:
        from_attributes = True


class MigrationStatsSchema(BaseModel):
    total: int
    pending: int
    uploaded: int
    parsed: int
    converted: int
    exported: int
    complete: int


class StatusUpdateRequest(BaseModel):
    status: str
    notes: str | None = None

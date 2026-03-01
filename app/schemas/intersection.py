from datetime import datetime
from pydantic import BaseModel


class PhaseMovementSchema(BaseModel):
    phase_number: int
    movement: str | None
    protected: bool

    class Config:
        from_attributes = True


class ZoneAssignmentSchema(BaseModel):
    category: str
    zone: str | None

    class Config:
        from_attributes = True


class IntersectionSummary(BaseModel):
    id: int
    asset_number: str
    location_name: str | None
    street_name_1: str | None
    street_name_2: str | None
    equipment_type: str | None
    has_preemption: bool
    uploaded_at: datetime

    class Config:
        from_attributes = True


class CommentCreate(BaseModel):
    text: str
    category: str = "general"


class CommentSchema(BaseModel):
    id: int
    text: str
    category: str
    created_at: datetime

    class Config:
        from_attributes = True


class IntersectionDetail(IntersectionSummary):
    section: str | None
    cabinet_type: str | None
    drop_address: str | None
    uploaded_filename: str | None
    max_off_minutes: float | None
    max_on_minutes: float | None
    detector_chatter: float | None
    zone_address: float | None
    comm_address: float | None
    transition_type: float | None
    phase_movements: list[PhaseMovementSchema]
    zone_assignments: list[ZoneAssignmentSchema]

    class Config:
        from_attributes = True

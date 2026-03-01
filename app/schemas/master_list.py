from pydantic import BaseModel


class MasterIntersectionSchema(BaseModel):
    id: int
    asset_number: str
    polygon: str | None
    location: str | None
    phases_json: str | None

    class Config:
        from_attributes = True

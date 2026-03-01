from pydantic import BaseModel


class SplitResult(BaseModel):
    plan_number: int
    cycle_length: float
    offset: float
    sepac_split1: float | None
    sepac_split2: float | None
    sepac_split3: float | None
    sepac_split4: float | None
    sepac_split5: float | None
    sepac_split6: float | None
    sepac_split7: float | None
    sepac_split8: float | None


class MinSplitResult(BaseModel):
    phase: int
    min_split: float
    components: dict


class ValidationResult(BaseModel):
    phase: int
    sepac_split: float
    min_split: float
    difference: float
    status: str  # "pass", "fail", "inactive"


class ConversionResponse(BaseModel):
    asset_number: str
    plans_converted: int
    results: list[SplitResult]


class ValidationResponse(BaseModel):
    asset_number: str
    plan_number: int
    validations: list[ValidationResult]


class SplitOverrideRequest(BaseModel):
    plan_number: int
    overrides: dict[int, float]  # {phase_number: new_split_value}
    reason: str | None = None


class SplitOverrideSchema(BaseModel):
    id: int
    plan_number: int
    phase_number: int
    original_value: float
    override_value: float
    reason: str | None
    created_at: str

    class Config:
        from_attributes = True


class SplitResetRequest(BaseModel):
    plan_number: int | None = None  # None = reset all plans

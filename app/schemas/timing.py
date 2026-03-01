from pydantic import BaseModel


class PhaseTimingSchema(BaseModel):
    bank: int
    phase_number: int
    ped_walk: float
    ped_fdw: float
    min_green: float
    veh_extension: float
    max_limit_1: float
    max_limit_2: float
    yellow_change: float
    red_clear: float

    class Config:
        from_attributes = True


class CoordinationPlanSchema(BaseModel):
    plan_number: int
    cycle_length: float
    offset: float
    phase1_force_off: float
    phase2_force_off: float
    phase3_force_off: float
    phase4_force_off: float
    phase5_force_off: float
    phase6_force_off: float
    phase7_force_off: float
    phase8_force_off: float
    sepac_split1: float | None
    sepac_split2: float | None
    sepac_split3: float | None
    sepac_split4: float | None
    sepac_split5: float | None
    sepac_split6: float | None
    sepac_split7: float | None
    sepac_split8: float | None
    sync_phases: str | None
    lag_phases: str | None
    converted: bool

    class Config:
        from_attributes = True


class TODScheduleSchema(BaseModel):
    bank: int
    event_index: int
    hour: int
    minute: int
    day_of_week: str
    plan_number: int

    class Config:
        from_attributes = True


class DetectorSchema(BaseModel):
    detector_number: int
    phase_assignment: int | None
    delay: float
    extend: float
    call_type: str | None
    lock: bool

    class Config:
        from_attributes = True


class OverlapSchema(BaseModel):
    overlap_letter: str
    parent_phases: str | None
    yellow_change: float
    red_clear: float

    class Config:
        from_attributes = True


class FdotOverrideSchema(BaseModel):
    phase_number: int
    bank: int
    field_name: str
    original_value: float
    fdot_value: float

    class Config:
        from_attributes = True


class PreemptionSchema(BaseModel):
    preempt_number: int
    input_number: int | None
    delay: float
    minimum_duration: float
    track_green_phases: str | None
    dwell_green_phases: str | None
    exit_phases: str | None

    class Config:
        from_attributes = True

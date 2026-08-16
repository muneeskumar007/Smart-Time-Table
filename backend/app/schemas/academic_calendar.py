from datetime import date

from pydantic import BaseModel, Field, field_validator, model_validator

from app.core.constants import DayOfWeek, TermType
from app.schemas.common import RefSummary, TimestampedResponse
from app.utils.time_helpers import is_valid_time_format, time_str_to_minutes


# --- Academic Year ---------------------------------------------------


class AcademicYearCreate(BaseModel):
    name: str = Field(..., min_length=4, max_length=20)
    start_date: date
    end_date: date

    @model_validator(mode="after")
    def dates_are_ordered(self):
        if self.end_date <= self.start_date:
            raise ValueError("End date must be after start date")
        return self


class AcademicYearUpdate(BaseModel):
    name: str | None = Field(None, min_length=4, max_length=20)
    start_date: date | None = None
    end_date: date | None = None
    is_current: bool | None = None


class AcademicYearResponse(TimestampedResponse):
    name: str
    start_date: date
    end_date: date
    is_current: bool


# --- Semester ----------------------------------------------------------


class SemesterCreate(BaseModel):
    name: str = Field(..., min_length=2, max_length=50)
    academic_year_id: str
    term_type: TermType
    start_date: date
    end_date: date

    @model_validator(mode="after")
    def dates_are_ordered(self):
        if self.end_date <= self.start_date:
            raise ValueError("End date must be after start date")
        return self


class SemesterUpdate(BaseModel):
    name: str | None = Field(None, min_length=2, max_length=50)
    start_date: date | None = None
    end_date: date | None = None
    is_current: bool | None = None


class SemesterResponse(TimestampedResponse):
    name: str
    academic_year: RefSummary
    term_type: TermType
    start_date: date
    end_date: date
    is_current: bool


# --- Time Slot -----------------------------------------------------------


class TimeSlotCreate(BaseModel):
    day_of_week: DayOfWeek
    start_time: str = Field(..., description="24-hour HH:MM")
    end_time: str = Field(..., description="24-hour HH:MM")
    label: str | None = Field(None, max_length=50)
    slot_order: int = Field(0, ge=0, le=50)
    is_break: bool = False
    department_id: str | None = None

    @field_validator("start_time", "end_time")
    @classmethod
    def time_format(cls, v: str) -> str:
        if not is_valid_time_format(v):
            raise ValueError("Time must be in 24-hour HH:MM format, e.g. '09:00'")
        return v

    @model_validator(mode="after")
    def end_after_start(self):
        if time_str_to_minutes(self.end_time) <= time_str_to_minutes(self.start_time):
            raise ValueError("End time must be after start time")
        return self


class TimeSlotUpdate(BaseModel):
    day_of_week: DayOfWeek | None = None
    start_time: str | None = None
    end_time: str | None = None
    label: str | None = Field(None, max_length=50)
    slot_order: int | None = Field(None, ge=0, le=50)
    is_break: bool | None = None

    @field_validator("start_time", "end_time")
    @classmethod
    def time_format(cls, v: str | None) -> str | None:
        if v and not is_valid_time_format(v):
            raise ValueError("Time must be in 24-hour HH:MM format, e.g. '09:00'")
        return v


class TimeSlotResponse(TimestampedResponse):
    day_of_week: DayOfWeek
    start_time: str
    end_time: str
    label: str | None
    slot_order: int
    is_break: bool
    department: RefSummary | None = None

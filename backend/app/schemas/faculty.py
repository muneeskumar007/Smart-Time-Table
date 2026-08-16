from datetime import date

from pydantic import BaseModel, EmailStr, Field, field_validator, model_validator

from app.core.constants import EmploymentType
from app.schemas.common import RefSummary, TimestampedResponse
from app.schemas.user import PHONE_PATTERN

COMMON_DESIGNATIONS = [
    "Professor",
    "Associate Professor",
    "Assistant Professor",
    "Senior Lecturer",
    "Lecturer",
    "Lab Instructor",
]


class FacultyCreate(BaseModel):
    employee_code: str = Field(..., min_length=2, max_length=30)
    name: str = Field(..., min_length=2, max_length=150)
    email: EmailStr
    phone: str | None = Field(None, max_length=20)
    designation: str = Field(..., min_length=2, max_length=100)
    department_id: str
    qualification: str | None = Field(None, max_length=100)
    specialization: str | None = Field(None, max_length=200)
    date_of_joining: date
    employment_type: EmploymentType = EmploymentType.PERMANENT
    max_weekly_hours: int = Field(18, ge=1, le=40)
    preferred_slots: list[str] = Field(default_factory=list)
    unavailable_slots: list[str] = Field(default_factory=list)

    @field_validator("phone")
    @classmethod
    def phone_format(cls, v: str | None) -> str | None:
        if v and not PHONE_PATTERN.match(v):
            raise ValueError("Phone number format is invalid")
        return v

    @field_validator("employee_code")
    @classmethod
    def normalise_code(cls, v: str) -> str:
        return v.strip().upper()

    @field_validator("unavailable_slots")
    @classmethod
    def no_overlap_between_preferred_and_unavailable(cls, v, info):
        preferred = info.data.get("preferred_slots") or []
        overlap = set(v) & set(preferred)
        if overlap:
            raise ValueError("A time slot cannot be both preferred and unavailable")
        return v


class FacultyUpdate(BaseModel):
    name: str | None = Field(None, min_length=2, max_length=150)
    phone: str | None = Field(None, max_length=20)
    designation: str | None = Field(None, min_length=2, max_length=100)
    qualification: str | None = Field(None, max_length=100)
    specialization: str | None = Field(None, max_length=200)
    employment_type: EmploymentType | None = None
    max_weekly_hours: int | None = Field(None, ge=1, le=40)
    preferred_slots: list[str] | None = None
    unavailable_slots: list[str] | None = None
    is_active: bool | None = None

    @field_validator("phone")
    @classmethod
    def phone_format(cls, v: str | None) -> str | None:
        if v and not PHONE_PATTERN.match(v):
            raise ValueError("Phone number format is invalid")
        return v

    @model_validator(mode="after")
    def no_overlap_when_both_provided(self):
        if self.preferred_slots is not None and self.unavailable_slots is not None:
            overlap = set(self.preferred_slots) & set(self.unavailable_slots)
            if overlap:
                raise ValueError("A time slot cannot be both preferred and unavailable")
        return self


class FacultyResponse(TimestampedResponse):
    employee_code: str
    name: str
    email: str
    phone: str | None
    designation: str
    department: RefSummary
    qualification: str | None
    specialization: str | None
    date_of_joining: date
    employment_type: EmploymentType
    max_weekly_hours: int
    preferred_slots: list[str] = []
    unavailable_slots: list[str] = []
    is_active: bool

from pydantic import BaseModel, Field, field_validator

from app.schemas.common import RefSummary, TimestampedResponse


class DepartmentCreate(BaseModel):
    name: str = Field(..., min_length=2, max_length=150)
    code: str = Field(..., min_length=2, max_length=20)
    description: str | None = Field(None, max_length=1000)
    established_year: int | None = Field(None, ge=1800, le=2100)

    @field_validator("code")
    @classmethod
    def normalise_code(cls, v: str) -> str:
        return v.strip().upper()

    @field_validator("name")
    @classmethod
    def strip_name(cls, v: str) -> str:
        return v.strip()


class DepartmentUpdate(BaseModel):
    name: str | None = Field(None, min_length=2, max_length=150)
    code: str | None = Field(None, min_length=2, max_length=20)
    description: str | None = Field(None, max_length=1000)
    established_year: int | None = Field(None, ge=1800, le=2100)
    hod_id: str | None = None
    is_active: bool | None = None

    @field_validator("code")
    @classmethod
    def normalise_code(cls, v: str | None) -> str | None:
        return v.strip().upper() if v else v


class DepartmentResponse(TimestampedResponse):
    name: str
    code: str
    description: str | None
    established_year: int | None
    hod: RefSummary | None = None
    is_active: bool
    faculty_count: int = 0
    course_count: int = 0
    section_count: int = 0

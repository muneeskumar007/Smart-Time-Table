from pydantic import BaseModel, Field, field_validator

from app.core.constants import SubjectType
from app.schemas.common import RefSummary, TimestampedResponse

# --- Course --------------------------------------------------------------


class CourseCreate(BaseModel):
    name: str = Field(..., min_length=2, max_length=150)
    code: str = Field(..., min_length=2, max_length=30)
    department_id: str
    duration_years: int = Field(..., ge=1, le=10)
    total_semesters: int = Field(..., ge=1, le=20)
    description: str | None = Field(None, max_length=1000)

    @field_validator("code")
    @classmethod
    def normalise_code(cls, v: str) -> str:
        return v.strip().upper()


class CourseUpdate(BaseModel):
    name: str | None = Field(None, min_length=2, max_length=150)
    duration_years: int | None = Field(None, ge=1, le=10)
    total_semesters: int | None = Field(None, ge=1, le=20)
    description: str | None = Field(None, max_length=1000)
    is_active: bool | None = None


class CourseResponse(TimestampedResponse):
    name: str
    code: str
    department: RefSummary
    duration_years: int
    total_semesters: int
    description: str | None
    is_active: bool


# --- Subject ---------------------------------------------------------------


class SubjectCreate(BaseModel):
    name: str = Field(..., min_length=2, max_length=150)
    code: str = Field(..., min_length=2, max_length=30)
    course_id: str
    semester_number: int = Field(..., ge=1, le=20)
    credits: float = Field(..., ge=0, le=20)
    subject_type: SubjectType = SubjectType.THEORY
    weekly_lecture_hours: int = Field(..., ge=0, le=20)
    weekly_lab_hours: int = Field(0, ge=0, le=20)

    @field_validator("code")
    @classmethod
    def normalise_code(cls, v: str) -> str:
        return v.strip().upper()


class SubjectUpdate(BaseModel):
    name: str | None = Field(None, min_length=2, max_length=150)
    semester_number: int | None = Field(None, ge=1, le=20)
    credits: float | None = Field(None, ge=0, le=20)
    subject_type: SubjectType | None = None
    weekly_lecture_hours: int | None = Field(None, ge=0, le=20)
    weekly_lab_hours: int | None = Field(None, ge=0, le=20)
    is_active: bool | None = None


class SubjectResponse(TimestampedResponse):
    name: str
    code: str
    course: RefSummary
    department_id: str
    semester_number: int
    credits: float
    subject_type: SubjectType
    weekly_lecture_hours: int
    weekly_lab_hours: int
    is_active: bool


# --- Section ----------------------------------------------------------------


class SectionCreate(BaseModel):
    course_id: str
    academic_year_id: str
    semester_id: str
    semester_number: int = Field(..., ge=1, le=20)
    section_name: str = Field(..., min_length=1, max_length=10)
    strength: int = Field(..., ge=1, le=500)
    class_advisor_id: str | None = None
    room_id: str | None = None

    @field_validator("section_name")
    @classmethod
    def normalise(cls, v: str) -> str:
        return v.strip().upper()


class SectionUpdate(BaseModel):
    strength: int | None = Field(None, ge=1, le=500)
    class_advisor_id: str | None = None
    room_id: str | None = None
    is_active: bool | None = None


class SectionResponse(TimestampedResponse):
    course: RefSummary
    academic_year: RefSummary
    semester: RefSummary
    semester_number: int
    department_id: str
    section_name: str
    display_name: str
    strength: int
    class_advisor: RefSummary | None = None
    room: RefSummary | None = None
    is_active: bool

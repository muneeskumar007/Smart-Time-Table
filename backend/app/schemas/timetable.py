from datetime import datetime
from typing import Literal

from pydantic import BaseModel, Field

from app.models.timetable import TimetableStatus
from app.schemas.common import RefSummary


class TimetableEntryResponse(BaseModel):
    id: str = Field(..., description="Stable synthetic id (timeslot_id) so the frontend can key/target one entry")
    timeslot_id: str
    day_of_week: str
    period_label: str | None
    start_time: str
    end_time: str
    subject: RefSummary
    faculty: RefSummary
    room: RefSummary
    is_lab: bool
    remarks: str | None = None


class TimetableResponse(BaseModel):
    id: str
    academic_year: RefSummary
    semester: RefSummary
    department_id: str
    course: RefSummary
    section: RefSummary
    version: int
    status: TimetableStatus
    generated_at: datetime | None
    generated_by: RefSummary | None = None
    published_at: datetime | None
    published_by: RefSummary | None = None
    entries: list[TimetableEntryResponse]
    created_at: datetime
    updated_at: datetime


class TimetableSummaryResponse(BaseModel):
    """Lighter-weight shape for list/history views - omits the full
    entries[] grid, which the detail endpoint returns."""
    id: str
    section: RefSummary
    version: int
    status: TimetableStatus
    entry_count: int
    generated_at: datetime | None
    published_at: datetime | None
    created_at: datetime


class GenerateTimetableRequest(BaseModel):
    section_id: str
    max_solve_seconds: float = Field(20.0, ge=5.0, le=60.0)


class Conflict(BaseModel):
    type: str
    severity: Literal["error", "warning"]
    message: str
    entity: dict | None = None
    day: str | None = None
    period: str | None = None
    possible_solution: str | None = None


class ValidationResult(BaseModel):
    is_valid: bool
    conflicts: list[Conflict]


class GenerateTimetableResponse(BaseModel):
    timetable: TimetableResponse | None
    solver_status: str
    demands_total: int
    demands_scheduled: int
    duration_seconds: float
    conflicts: list[Conflict] = Field(default_factory=list)


# --- Manual editor -------------------------------------------------------


class MoveEntryRequest(BaseModel):
    """Moves one existing entry (identified by its current timeslot) to
    a different timeslot, keeping the same subject/faculty/room."""
    from_timeslot_id: str
    to_timeslot_id: str


class SwapEntriesRequest(BaseModel):
    timeslot_id_a: str
    timeslot_id_b: str


class ReplaceFacultyRequest(BaseModel):
    timeslot_id: str
    new_faculty_id: str


class ReplaceRoomRequest(BaseModel):
    timeslot_id: str
    new_room_id: str


class AddEntryRequest(BaseModel):
    timeslot_id: str
    subject_id: str
    faculty_id: str
    room_id: str
    remarks: str | None = None


class DeleteEntryRequest(BaseModel):
    timeslot_id: str


class RollbackRequest(BaseModel):
    target_timetable_id: str = Field(..., description="The ARCHIVED version to restore as PUBLISHED")

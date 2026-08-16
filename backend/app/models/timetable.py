"""
Timetable models.

A Timetable document is scoped to one Section within one academic
Semester. Its `entries[]` is the actual weekly schedule; `version` and
`status` implement the draft -> generated -> published -> archived
lifecycle (see PUBLISH WORKFLOW in the project brief). Publishing a new
version archives the previously-published one rather than deleting it,
so timetable_service.get_history() can always show what used to be
in effect.
"""
from datetime import datetime
from enum import Enum

from pydantic import BaseModel, Field

from app.models.base import AuditMixin, utcnow


class TimetableStatus(str, Enum):
    DRAFT = "draft"
    GENERATING = "generating"
    GENERATED = "generated"
    PUBLISHED = "published"
    ARCHIVED = "archived"
    FAILED = "failed"


class TimetableEntryModel(BaseModel):
    """One scheduled class meeting. Denormalises day/time/period label
    from the referenced TimeSlot (and subject/faculty/room names are
    resolved at the API layer, not stored here) so an entry is
    self-contained for display, while `timeslot_id`/`room_id`/
    `faculty_id` remain the precise keys conflict-checking groups by."""

    timeslot_id: str
    day_of_week: str
    period_label: str | None = None
    start_time: str
    end_time: str
    subject_id: str
    faculty_id: str
    room_id: str
    is_lab: bool = False
    remarks: str | None = None


class AuditLogEntry(BaseModel):
    action: str  # "generated" | "published" | "rolled_back" | "edited" | "generation_failed"
    actor_id: str
    at: datetime = Field(default_factory=utcnow)
    details: str | None = None


class TimetableModel(AuditMixin):
    academic_year_id: str
    semester_id: str
    department_id: str
    course_id: str
    section_id: str

    version: int = 1
    status: TimetableStatus = TimetableStatus.DRAFT

    generated_at: datetime | None = None
    generated_by: str | None = None
    published_at: datetime | None = None
    published_by: str | None = None

    entries: list[TimetableEntryModel] = Field(default_factory=list)
    audit_log: list[AuditLogEntry] = Field(default_factory=list)


class GenerationLogModel(BaseModel):
    """Canonical shape of a `generation_logs` document - one row per
    solver run, kept even for failed/infeasible attempts so a HOD can
    see why generation didn't work last time without reproducing it."""

    timetable_id: str | None = None
    section_id: str
    triggered_by: str
    started_at: datetime = Field(default_factory=utcnow)
    completed_at: datetime | None = None
    duration_seconds: float | None = None
    solver_status: str | None = None  # "OPTIMAL" | "FEASIBLE" | "INFEASIBLE" | "TIMEOUT" | "ERROR"
    success: bool = False
    demands_total: int = 0
    demands_scheduled: int = 0
    conflict_count: int = 0
    message: str | None = None

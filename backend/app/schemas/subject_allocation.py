from pydantic import BaseModel

from app.schemas.common import RefSummary, TimestampedResponse


class SubjectAllocationCreate(BaseModel):
    subject_id: str
    section_id: str
    faculty_id: str


class SubjectAllocationUpdate(BaseModel):
    """Only the faculty can be reassigned after the fact - subject and
    section define the allocation's identity, so changing either is
    modelled as delete-and-recreate rather than an in-place update."""
    faculty_id: str
    is_active: bool | None = None


class SubjectAllocationResponse(TimestampedResponse):
    subject: RefSummary
    section: RefSummary
    faculty: RefSummary
    department_id: str

    # Computed from Subject.weekly_lecture_hours + weekly_lab_hours and
    # the current timetable's entries referencing this allocation - see
    # the "Modelling note" in models/subject_allocation.py.
    required_hours: int
    allocated_hours: int
    remaining_hours: int
    completion_percentage: float

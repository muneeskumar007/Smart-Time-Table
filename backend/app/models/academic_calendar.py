"""
Academic Year, Semester and Time Slot models.

Grouped in one module because all three describe the institution's
scheduling calendar/grid rather than its people or curriculum - the
same grouping is mirrored in schemas/, repositories/, services/ and
routes/ for this trio.

Modelling note - Semester vs. a Subject's curriculum stage: a `Semester`
document here is a schedulable calendar TERM (e.g. "Odd Semester
2026-27", running Aug-Dec). It is a different concept from
"3rd semester of the B.Tech programme", which is tracked per-Section via
`semester_number` (see models/academic_structure.py::SectionModel) and
per-Subject via `semester_number` (which point in the curriculum a
subject is taught). A Section combines both: which calendar Semester
it's currently running in, and which curriculum stage its students are
at.
"""
from datetime import date

from app.core.constants import DayOfWeek, TermType
from app.models.base import AuditMixin


class AcademicYearModel(AuditMixin):
    name: str  # e.g. "2026-2027"
    start_date: date
    end_date: date
    is_current: bool = False


class SemesterModel(AuditMixin):
    name: str  # e.g. "Odd Semester 2026-27"
    academic_year_id: str
    term_type: TermType
    start_date: date
    end_date: date
    is_current: bool = False


class TimeSlotModel(AuditMixin):
    day_of_week: DayOfWeek
    start_time: str  # "HH:MM", 24-hour
    end_time: str
    label: str | None = None  # e.g. "Period 1"
    slot_order: int = 0
    is_break: bool = False
    # None = a global slot template that applies to every department;
    # set = a department-specific override/addition.
    department_id: str | None = None

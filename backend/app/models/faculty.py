from datetime import date

from pydantic import Field

from app.core.constants import EmploymentType
from app.models.base import AuditMixin


class FacultyModel(AuditMixin):
    """Canonical shape of a `faculty` document - the HR/teaching-staff
    profile. Deliberately independent of `users` (no automatic linked
    login account): a Faculty profile can exist purely as directory/HR
    data, and a login account (role=faculty) is provisioned separately
    via User Management when/if that person needs to sign in. See
    README.md for the reasoning."""

    employee_code: str
    name: str
    email: str
    phone: str | None = None
    designation: str
    department_id: str
    qualification: str | None = None
    specialization: str | None = None
    date_of_joining: date
    employment_type: EmploymentType
    max_weekly_hours: int = 18

    # Added for timetable generation (Master Prompt 3): lists of
    # TimeSlot ids. Optional/default-empty so existing Faculty documents
    # remain valid without a migration - an empty unavailable_slots list
    # simply means "no known constraints yet".
    preferred_slots: list[str] = Field(default_factory=list)
    unavailable_slots: list[str] = Field(default_factory=list)

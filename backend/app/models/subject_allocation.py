from app.models.base import AuditMixin


class SubjectAllocationModel(AuditMixin):
    """Canonical shape of a `subject_allocations` document: "this Faculty
    teaches this Subject to this Section." This is deliberately a
    separate, simpler admin step from timetable generation itself - a
    HOD decides WHO teaches WHAT before the generator decides WHEN/WHERE.
    Without this assignment existing first, the generator has no way to
    know which faculty member a given Subject/Section pairing belongs to.

    Required/allocated/remaining hours and completion percentage
    (explicitly requested tracking fields) are deliberately NOT stored
    here - they're computed on read from Subject.weekly_*_hours and the
    current timetable's entries (see SubjectAllocationService), so they
    can never drift out of sync with the timetable that's actually the
    source of truth for what got scheduled.
    """

    subject_id: str
    section_id: str
    faculty_id: str
    department_id: str  # denormalised from section.department_id

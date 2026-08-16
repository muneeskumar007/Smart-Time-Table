"""
Course, Subject and Section models - the curriculum/programme hierarchy.

Grouped in one module because Subject and Section both depend directly
on Course, and this trio is naturally read/written together. The same
grouping is mirrored in schemas/, repositories/, services/ and routes/.

  Course   - an academic programme, e.g. "B.Tech Computer Science" (4
             years / 8 semesters), owned by a Department.
  Subject  - one subject taught within a Course's curriculum, tagged
             with which curriculum stage (`semester_number`, 1..N) it
             belongs to - e.g. "Data Structures" is semester_number=3
             of the B.Tech CSE course.
  Section  - one actual class/batch, e.g. "CSE-A", combining a Course, a
             calendar Semester (see academic_calendar.py) and a
             `semester_number` for which curriculum stage this batch of
             students is currently at.
"""
from app.core.constants import SubjectType
from app.models.base import AuditMixin


class CourseModel(AuditMixin):
    name: str
    code: str
    department_id: str
    duration_years: int
    total_semesters: int
    description: str | None = None


class SubjectModel(AuditMixin):
    name: str
    code: str
    course_id: str
    department_id: str  # denormalised from course.department_id for faster filtering
    semester_number: int
    credits: float
    subject_type: SubjectType = SubjectType.THEORY
    weekly_lecture_hours: int
    weekly_lab_hours: int = 0


class SectionModel(AuditMixin):
    course_id: str
    academic_year_id: str
    semester_id: str
    semester_number: int
    department_id: str  # denormalised from course.department_id
    section_name: str
    strength: int
    class_advisor_id: str | None = None
    room_id: str | None = None

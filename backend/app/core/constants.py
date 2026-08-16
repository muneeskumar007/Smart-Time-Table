"""
Application-wide constants.

Centralising these avoids "magic strings" scattered across services,
routes and repositories, and gives us one place to change role names,
collection names or default limits.
"""
from enum import Enum


class UserRole(str, Enum):
    """
    The four roles supported in Phase 1.

    Stored on the `users` collection as a plain string (str, Enum) so it
    serialises cleanly to/from MongoDB and JSON without extra converters.
    """
    SUPER_ADMIN = "super_admin"
    HOD = "hod"
    FACULTY = "faculty"
    STUDENT = "student"


# Roles that must belong to exactly one department.
DEPARTMENT_SCOPED_ROLES = {UserRole.HOD, UserRole.FACULTY, UserRole.STUDENT}

# Roles allowed to manage users within their own department (not create
# other HODs/Super Admins - only Super Admin can do that).
DEPARTMENT_USER_MANAGER_ROLES = {UserRole.SUPER_ADMIN, UserRole.HOD}


class EmploymentType(str, Enum):
    PERMANENT = "permanent"
    VISITING = "visiting"
    CONTRACT = "contract"


class SubjectType(str, Enum):
    THEORY = "theory"
    LAB = "lab"
    ELECTIVE = "elective"
    PROJECT = "project"


class RoomType(str, Enum):
    CLASSROOM = "classroom"
    SEMINAR_HALL = "seminar_hall"
    AUDITORIUM = "auditorium"


class TermType(str, Enum):
    ODD = "odd"
    EVEN = "even"


class DayOfWeek(str, Enum):
    MON = "MON"
    TUE = "TUE"
    WED = "WED"
    THU = "THU"
    FRI = "FRI"
    SAT = "SAT"


class Collections:
    """MongoDB collection names - see database/connection.py for indexes."""
    USERS = "users"
    DEPARTMENTS = "departments"
    FACULTY = "faculty"
    COURSES = "courses"
    SUBJECTS = "subjects"
    SECTIONS = "sections"
    ROOMS = "rooms"
    LABORATORIES = "laboratories"
    ACADEMIC_YEARS = "academic_years"
    SEMESTERS = "semesters"
    TIMESLOTS = "timeslots"
    SUBJECT_ALLOCATIONS = "subject_allocations"
    # Timetable module (Master Prompt 3)
    TIMETABLES = "timetables"
    TIMETABLE_VERSIONS = "timetable_versions"
    FACULTY_WORKLOAD = "faculty_workload"
    ROOM_ALLOCATIONS = "room_allocations"
    GENERATION_LOGS = "generation_logs"
    # Reserved for later phases (not written to yet):
    NOTIFICATIONS = "notifications"
    SETTINGS = "settings"


DEFAULT_PAGE = 1
DEFAULT_PAGE_SIZE = 10
MAX_PAGE_SIZE = 100

# Bcrypt-era libraries capped passwords at 72 bytes; Argon2 (what we use)
# has no such limit, but a sane upper bound still protects against
# denial-of-service via absurdly long input.
MIN_PASSWORD_LENGTH = 8
MAX_PASSWORD_LENGTH = 128

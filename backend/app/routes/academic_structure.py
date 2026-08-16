from fastapi import APIRouter, Depends

from app.auth.dependencies import get_current_user, require_roles
from app.core.constants import UserRole
from app.schemas.academic_structure import (
    CourseCreate,
    CourseUpdate,
    SectionCreate,
    SectionUpdate,
    SubjectCreate,
    SubjectUpdate,
)
from app.services.academic_structure_service import CourseService, SectionService, SubjectService
from app.utils.pagination import PaginationParams, get_pagination_params
from app.utils.response import success_response

router = APIRouter(tags=["Academic Structure"])

MANAGER_ROLES = (UserRole.SUPER_ADMIN, UserRole.HOD)

# --- Courses -----------------------------------------------------------

courses_router = APIRouter(prefix="/courses")


@courses_router.get("", response_model=None)
async def list_courses(
    department_id: str | None = None,
    include_inactive: bool = False,
    pagination: PaginationParams = Depends(get_pagination_params),
    current_user: dict = Depends(get_current_user),
):
    items, meta = await CourseService().list_courses(current_user, pagination, department_id, include_inactive)
    return success_response(data=items, meta=meta, message="Courses retrieved successfully")


@courses_router.get("/lookup", response_model=None)
async def lookup_courses(department_id: str | None = None, current_user: dict = Depends(get_current_user)):
    items = await CourseService().list_lookup(current_user, department_id)
    return success_response(data=items, message="Courses retrieved successfully")


@courses_router.get("/{course_id}", response_model=None)
async def get_course(course_id: str, current_user: dict = Depends(get_current_user)):
    course = await CourseService().get_course(current_user, course_id)
    return success_response(data=course, message="Course retrieved successfully")


@courses_router.post("", response_model=None, status_code=201)
async def create_course(payload: CourseCreate, current_user: dict = Depends(require_roles(*MANAGER_ROLES))):
    course = await CourseService().create_course(current_user, payload)
    return success_response(data=course, message="Course created successfully")


@courses_router.patch("/{course_id}", response_model=None)
async def update_course(course_id: str, payload: CourseUpdate, current_user: dict = Depends(require_roles(*MANAGER_ROLES))):
    course = await CourseService().update_course(current_user, course_id, payload)
    return success_response(data=course, message="Course updated successfully")


@courses_router.delete("/{course_id}", response_model=None)
async def delete_course(course_id: str, current_user: dict = Depends(require_roles(*MANAGER_ROLES))):
    await CourseService().delete_course(current_user, course_id)
    return success_response(data=None, message="Course deleted successfully")


@courses_router.post("/{course_id}/restore", response_model=None)
async def restore_course(course_id: str, current_user: dict = Depends(require_roles(*MANAGER_ROLES))):
    course = await CourseService().restore_course(current_user, course_id)
    return success_response(data=course, message="Course restored successfully")


# --- Subjects ------------------------------------------------------------

subjects_router = APIRouter(prefix="/subjects")


@subjects_router.get("", response_model=None)
async def list_subjects(
    course_id: str | None = None,
    include_inactive: bool = False,
    pagination: PaginationParams = Depends(get_pagination_params),
    current_user: dict = Depends(get_current_user),
):
    items, meta = await SubjectService().list_subjects(current_user, pagination, course_id, include_inactive)
    return success_response(data=items, meta=meta, message="Subjects retrieved successfully")


@subjects_router.get("/{subject_id}", response_model=None)
async def get_subject(subject_id: str, current_user: dict = Depends(get_current_user)):
    subject = await SubjectService().get_subject(current_user, subject_id)
    return success_response(data=subject, message="Subject retrieved successfully")


@subjects_router.post("", response_model=None, status_code=201)
async def create_subject(payload: SubjectCreate, current_user: dict = Depends(require_roles(*MANAGER_ROLES))):
    subject = await SubjectService().create_subject(current_user, payload)
    return success_response(data=subject, message="Subject created successfully")


@subjects_router.patch("/{subject_id}", response_model=None)
async def update_subject(
    subject_id: str, payload: SubjectUpdate, current_user: dict = Depends(require_roles(*MANAGER_ROLES))
):
    subject = await SubjectService().update_subject(current_user, subject_id, payload)
    return success_response(data=subject, message="Subject updated successfully")


@subjects_router.delete("/{subject_id}", response_model=None)
async def delete_subject(subject_id: str, current_user: dict = Depends(require_roles(*MANAGER_ROLES))):
    await SubjectService().delete_subject(current_user, subject_id)
    return success_response(data=None, message="Subject deleted successfully")


@subjects_router.post("/{subject_id}/restore", response_model=None)
async def restore_subject(subject_id: str, current_user: dict = Depends(require_roles(*MANAGER_ROLES))):
    subject = await SubjectService().restore_subject(current_user, subject_id)
    return success_response(data=subject, message="Subject restored successfully")


# --- Sections ---------------------------------------------------------------

sections_router = APIRouter(prefix="/sections")


@sections_router.get("", response_model=None)
async def list_sections(
    course_id: str | None = None,
    academic_year_id: str | None = None,
    include_inactive: bool = False,
    pagination: PaginationParams = Depends(get_pagination_params),
    current_user: dict = Depends(get_current_user),
):
    items, meta = await SectionService().list_sections(current_user, pagination, course_id, academic_year_id, include_inactive)
    return success_response(data=items, meta=meta, message="Sections retrieved successfully")


@sections_router.get("/{section_id}", response_model=None)
async def get_section(section_id: str, current_user: dict = Depends(get_current_user)):
    section = await SectionService().get_section(current_user, section_id)
    return success_response(data=section, message="Section retrieved successfully")


@sections_router.post("", response_model=None, status_code=201)
async def create_section(payload: SectionCreate, current_user: dict = Depends(require_roles(*MANAGER_ROLES))):
    section = await SectionService().create_section(current_user, payload)
    return success_response(data=section, message="Section created successfully")


@sections_router.patch("/{section_id}", response_model=None)
async def update_section(
    section_id: str, payload: SectionUpdate, current_user: dict = Depends(require_roles(*MANAGER_ROLES))
):
    section = await SectionService().update_section(current_user, section_id, payload)
    return success_response(data=section, message="Section updated successfully")


@sections_router.delete("/{section_id}", response_model=None)
async def delete_section(section_id: str, current_user: dict = Depends(require_roles(*MANAGER_ROLES))):
    await SectionService().delete_section(current_user, section_id)
    return success_response(data=None, message="Section deleted successfully")


@sections_router.post("/{section_id}/restore", response_model=None)
async def restore_section(section_id: str, current_user: dict = Depends(require_roles(*MANAGER_ROLES))):
    section = await SectionService().restore_section(current_user, section_id)
    return success_response(data=section, message="Section restored successfully")


router.include_router(courses_router)
router.include_router(subjects_router)
router.include_router(sections_router)

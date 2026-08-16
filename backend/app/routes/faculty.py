from fastapi import APIRouter, Depends

from app.auth.dependencies import get_current_user, require_roles
from app.core.constants import UserRole
from app.schemas.faculty import FacultyCreate, FacultyUpdate
from app.services.faculty_service import FacultyService
from app.utils.pagination import PaginationParams, get_pagination_params
from app.utils.response import success_response

router = APIRouter(prefix="/faculty", tags=["Faculty"])

MANAGER_ROLES = (UserRole.SUPER_ADMIN, UserRole.HOD)


@router.get("", response_model=None)
async def list_faculty(
    department_id: str | None = None,
    include_inactive: bool = False,
    pagination: PaginationParams = Depends(get_pagination_params),
    current_user: dict = Depends(get_current_user),
):
    items, meta = await FacultyService().list_faculty(current_user, pagination, department_id, include_inactive)
    return success_response(data=items, meta=meta, message="Faculty retrieved successfully")


@router.get("/lookup", response_model=None)
async def lookup_faculty(department_id: str | None = None, current_user: dict = Depends(get_current_user)):
    items = await FacultyService().list_lookup(current_user, department_id)
    return success_response(data=items, message="Faculty retrieved successfully")


@router.get("/{faculty_id}", response_model=None)
async def get_faculty(faculty_id: str, current_user: dict = Depends(get_current_user)):
    faculty = await FacultyService().get_faculty(current_user, faculty_id)
    return success_response(data=faculty, message="Faculty member retrieved successfully")


@router.post("", response_model=None, status_code=201)
async def create_faculty(payload: FacultyCreate, current_user: dict = Depends(require_roles(*MANAGER_ROLES))):
    faculty = await FacultyService().create_faculty(current_user, payload)
    return success_response(data=faculty, message="Faculty member created successfully")


@router.patch("/{faculty_id}", response_model=None)
async def update_faculty(
    faculty_id: str, payload: FacultyUpdate, current_user: dict = Depends(require_roles(*MANAGER_ROLES))
):
    faculty = await FacultyService().update_faculty(current_user, faculty_id, payload)
    return success_response(data=faculty, message="Faculty member updated successfully")


@router.delete("/{faculty_id}", response_model=None)
async def delete_faculty(faculty_id: str, current_user: dict = Depends(require_roles(*MANAGER_ROLES))):
    await FacultyService().delete_faculty(current_user, faculty_id)
    return success_response(data=None, message="Faculty member deleted successfully")


@router.post("/{faculty_id}/restore", response_model=None)
async def restore_faculty(faculty_id: str, current_user: dict = Depends(require_roles(*MANAGER_ROLES))):
    faculty = await FacultyService().restore_faculty(current_user, faculty_id)
    return success_response(data=faculty, message="Faculty member restored successfully")

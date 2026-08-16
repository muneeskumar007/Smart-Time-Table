from fastapi import APIRouter, Depends

from app.auth.dependencies import get_current_user, require_roles
from app.core.constants import UserRole
from app.schemas.department import DepartmentCreate, DepartmentUpdate
from app.services.department_service import DepartmentService
from app.utils.pagination import PaginationParams, get_pagination_params
from app.utils.response import success_response

router = APIRouter(prefix="/departments", tags=["Departments"])


@router.get("", response_model=None)
async def list_departments(
    include_inactive: bool = False,
    pagination: PaginationParams = Depends(get_pagination_params),
    current_user: dict = Depends(get_current_user),
):
    # Every role may browse departments (needed to populate dropdowns
    # elsewhere in the UI); only Super Admin can create/edit/delete one.
    items, meta = await DepartmentService().list_departments(pagination, include_inactive=include_inactive)
    return success_response(data=items, meta=meta, message="Departments retrieved successfully")


@router.get("/lookup", response_model=None)
async def lookup_departments(current_user: dict = Depends(get_current_user)):
    """Unpaginated {id, name} list for populating dropdowns."""
    items = await DepartmentService().list_all_active()
    return success_response(data=items, message="Departments retrieved successfully")


@router.get("/{department_id}", response_model=None)
async def get_department(department_id: str, current_user: dict = Depends(get_current_user)):
    department = await DepartmentService().get_department(department_id)
    return success_response(data=department, message="Department retrieved successfully")


@router.post("", response_model=None, status_code=201)
async def create_department(payload: DepartmentCreate, current_user: dict = Depends(require_roles(UserRole.SUPER_ADMIN))):
    department = await DepartmentService().create_department(current_user, payload)
    return success_response(data=department, message="Department created successfully")


@router.patch("/{department_id}", response_model=None)
async def update_department(
    department_id: str,
    payload: DepartmentUpdate,
    current_user: dict = Depends(require_roles(UserRole.SUPER_ADMIN)),
):
    department = await DepartmentService().update_department(current_user, department_id, payload)
    return success_response(data=department, message="Department updated successfully")


@router.delete("/{department_id}", response_model=None)
async def delete_department(department_id: str, current_user: dict = Depends(require_roles(UserRole.SUPER_ADMIN))):
    await DepartmentService().delete_department(current_user, department_id)
    return success_response(data=None, message="Department deleted successfully")


@router.post("/{department_id}/restore", response_model=None)
async def restore_department(department_id: str, current_user: dict = Depends(require_roles(UserRole.SUPER_ADMIN))):
    department = await DepartmentService().restore_department(current_user, department_id)
    return success_response(data=department, message="Department restored successfully")

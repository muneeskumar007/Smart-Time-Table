from fastapi import APIRouter, Depends

from app.auth.dependencies import require_roles
from app.core.constants import UserRole
from app.schemas.subject_allocation import SubjectAllocationCreate, SubjectAllocationUpdate
from app.services.subject_allocation_service import SubjectAllocationService
from app.utils.pagination import PaginationParams, get_pagination_params
from app.utils.response import success_response

router = APIRouter(prefix="/subject-allocations", tags=["Subject Allocations"])

MANAGER_ROLES = (UserRole.SUPER_ADMIN, UserRole.HOD)


@router.get("", response_model=None)
async def list_allocations(
    section_id: str | None = None,
    faculty_id: str | None = None,
    pagination: PaginationParams = Depends(get_pagination_params),
    current_user: dict = Depends(require_roles(*MANAGER_ROLES)),
):
    items, meta = await SubjectAllocationService().list_allocations(current_user, pagination, section_id, faculty_id)
    return success_response(data=items, meta=meta, message="Subject allocations retrieved successfully")


@router.get("/{allocation_id}", response_model=None)
async def get_allocation(allocation_id: str, current_user: dict = Depends(require_roles(*MANAGER_ROLES))):
    allocation = await SubjectAllocationService().get_allocation(current_user, allocation_id)
    return success_response(data=allocation, message="Subject allocation retrieved successfully")


@router.post("", response_model=None, status_code=201)
async def create_allocation(payload: SubjectAllocationCreate, current_user: dict = Depends(require_roles(*MANAGER_ROLES))):
    allocation = await SubjectAllocationService().create_allocation(current_user, payload)
    return success_response(data=allocation, message="Subject allocated successfully")


@router.patch("/{allocation_id}", response_model=None)
async def update_allocation(
    allocation_id: str, payload: SubjectAllocationUpdate, current_user: dict = Depends(require_roles(*MANAGER_ROLES))
):
    allocation = await SubjectAllocationService().update_allocation(current_user, allocation_id, payload)
    return success_response(data=allocation, message="Subject allocation updated successfully")


@router.delete("/{allocation_id}", response_model=None)
async def delete_allocation(allocation_id: str, current_user: dict = Depends(require_roles(*MANAGER_ROLES))):
    await SubjectAllocationService().delete_allocation(current_user, allocation_id)
    return success_response(data=None, message="Subject allocation deleted successfully")


@router.post("/{allocation_id}/restore", response_model=None)
async def restore_allocation(allocation_id: str, current_user: dict = Depends(require_roles(*MANAGER_ROLES))):
    allocation = await SubjectAllocationService().restore_allocation(current_user, allocation_id)
    return success_response(data=allocation, message="Subject allocation restored successfully")

from fastapi import APIRouter, Depends

from app.auth.dependencies import get_current_user, require_roles
from app.core.constants import UserRole
from app.schemas.lab import LabCreate, LabUpdate
from app.services.lab_service import LabService
from app.utils.pagination import PaginationParams, get_pagination_params
from app.utils.response import success_response

router = APIRouter(prefix="/labs", tags=["Laboratories"])

MANAGER_ROLES = (UserRole.SUPER_ADMIN, UserRole.HOD)


@router.get("", response_model=None)
async def list_labs(
    department_id: str | None = None,
    include_inactive: bool = False,
    pagination: PaginationParams = Depends(get_pagination_params),
    current_user: dict = Depends(get_current_user),
):
    items, meta = await LabService().list_labs(current_user, pagination, department_id, include_inactive)
    return success_response(data=items, meta=meta, message="Laboratories retrieved successfully")


@router.get("/lookup", response_model=None)
async def lookup_labs(department_id: str | None = None, current_user: dict = Depends(get_current_user)):
    items = await LabService().list_all_active(department_id)
    return success_response(data=items, message="Laboratories retrieved successfully")


@router.get("/{lab_id}", response_model=None)
async def get_lab(lab_id: str, current_user: dict = Depends(get_current_user)):
    lab = await LabService().get_lab(lab_id)
    return success_response(data=lab, message="Laboratory retrieved successfully")


@router.post("", response_model=None, status_code=201)
async def create_lab(payload: LabCreate, current_user: dict = Depends(require_roles(*MANAGER_ROLES))):
    lab = await LabService().create_lab(current_user, payload)
    return success_response(data=lab, message="Laboratory created successfully")


@router.patch("/{lab_id}", response_model=None)
async def update_lab(lab_id: str, payload: LabUpdate, current_user: dict = Depends(require_roles(*MANAGER_ROLES))):
    lab = await LabService().update_lab(current_user, lab_id, payload)
    return success_response(data=lab, message="Laboratory updated successfully")


@router.delete("/{lab_id}", response_model=None)
async def delete_lab(lab_id: str, current_user: dict = Depends(require_roles(*MANAGER_ROLES))):
    await LabService().delete_lab(current_user, lab_id)
    return success_response(data=None, message="Laboratory deleted successfully")


@router.post("/{lab_id}/restore", response_model=None)
async def restore_lab(lab_id: str, current_user: dict = Depends(require_roles(*MANAGER_ROLES))):
    lab = await LabService().restore_lab(current_user, lab_id)
    return success_response(data=lab, message="Laboratory restored successfully")

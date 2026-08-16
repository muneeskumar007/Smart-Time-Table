from fastapi import APIRouter, Depends

from app.auth.dependencies import require_roles
from app.core.constants import UserRole
from app.schemas.user import AdminResetPasswordRequest, UserCreate, UserUpdate
from app.services.user_service import UserService
from app.utils.pagination import PaginationParams, get_pagination_params
from app.utils.response import success_response

router = APIRouter(prefix="/users", tags=["Users"])

MANAGER_ROLES = (UserRole.SUPER_ADMIN, UserRole.HOD)


@router.get("", response_model=None)
async def list_users(
    role: str | None = None,
    include_inactive: bool = False,
    pagination: PaginationParams = Depends(get_pagination_params),
    current_user: dict = Depends(require_roles(*MANAGER_ROLES)),
):
    items, meta = await UserService().list_users(current_user, pagination, role_filter=role, include_inactive=include_inactive)
    return success_response(data=items, meta=meta, message="Users retrieved successfully")


@router.post("", response_model=None, status_code=201)
async def create_user(payload: UserCreate, current_user: dict = Depends(require_roles(*MANAGER_ROLES))):
    user = await UserService().create_user(current_user, payload)
    return success_response(data=user, message="User created successfully")


@router.get("/{user_id}", response_model=None)
async def get_user(user_id: str, current_user: dict = Depends(require_roles(*MANAGER_ROLES))):
    user = await UserService().get_user(current_user, user_id)
    return success_response(data=user, message="User retrieved successfully")


@router.patch("/{user_id}", response_model=None)
async def update_user(user_id: str, payload: UserUpdate, current_user: dict = Depends(require_roles(*MANAGER_ROLES))):
    user = await UserService().update_user(current_user, user_id, payload)
    return success_response(data=user, message="User updated successfully")


@router.delete("/{user_id}", response_model=None)
async def delete_user(user_id: str, current_user: dict = Depends(require_roles(*MANAGER_ROLES))):
    await UserService().delete_user(current_user, user_id)
    return success_response(data=None, message="User deleted successfully")


@router.post("/{user_id}/restore", response_model=None)
async def restore_user(user_id: str, current_user: dict = Depends(require_roles(*MANAGER_ROLES))):
    user = await UserService().restore_user(current_user, user_id)
    return success_response(data=user, message="User restored successfully")


@router.post("/{user_id}/reset-password", response_model=None)
async def reset_user_password(
    user_id: str,
    payload: AdminResetPasswordRequest,
    current_user: dict = Depends(require_roles(*MANAGER_ROLES)),
):
    await UserService().admin_reset_password(current_user, user_id, payload)
    return success_response(data=None, message="Password reset successfully")

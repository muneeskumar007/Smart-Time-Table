from fastapi import APIRouter, Depends

from app.auth.dependencies import get_current_user, require_roles
from app.core.constants import UserRole
from app.schemas.room import RoomCreate, RoomUpdate
from app.services.room_service import RoomService
from app.utils.pagination import PaginationParams, get_pagination_params
from app.utils.response import success_response

router = APIRouter(prefix="/rooms", tags=["Rooms"])


@router.get("", response_model=None)
async def list_rooms(
    room_type: str | None = None,
    include_inactive: bool = False,
    pagination: PaginationParams = Depends(get_pagination_params),
    current_user: dict = Depends(get_current_user),
):
    items, meta = await RoomService().list_rooms(pagination, room_type, include_inactive)
    return success_response(data=items, meta=meta, message="Rooms retrieved successfully")


@router.get("/lookup", response_model=None)
async def lookup_rooms(current_user: dict = Depends(get_current_user)):
    items = await RoomService().list_all_active()
    return success_response(data=items, message="Rooms retrieved successfully")


@router.get("/{room_id}", response_model=None)
async def get_room(room_id: str, current_user: dict = Depends(get_current_user)):
    room = await RoomService().get_room(room_id)
    return success_response(data=room, message="Room retrieved successfully")


@router.post("", response_model=None, status_code=201)
async def create_room(payload: RoomCreate, current_user: dict = Depends(require_roles(UserRole.SUPER_ADMIN))):
    room = await RoomService().create_room(current_user, payload)
    return success_response(data=room, message="Room created successfully")


@router.patch("/{room_id}", response_model=None)
async def update_room(room_id: str, payload: RoomUpdate, current_user: dict = Depends(require_roles(UserRole.SUPER_ADMIN))):
    room = await RoomService().update_room(current_user, room_id, payload)
    return success_response(data=room, message="Room updated successfully")


@router.delete("/{room_id}", response_model=None)
async def delete_room(room_id: str, current_user: dict = Depends(require_roles(UserRole.SUPER_ADMIN))):
    await RoomService().delete_room(current_user, room_id)
    return success_response(data=None, message="Room deleted successfully")


@router.post("/{room_id}/restore", response_model=None)
async def restore_room(room_id: str, current_user: dict = Depends(require_roles(UserRole.SUPER_ADMIN))):
    room = await RoomService().restore_room(current_user, room_id)
    return success_response(data=room, message="Room restored successfully")

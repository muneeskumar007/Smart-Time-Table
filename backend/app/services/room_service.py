from app.core.constants import Collections
from app.core.exceptions import DuplicateException, ValidationException
from app.database.connection import get_database
from app.models.room import RoomModel
from app.repositories.room_repository import RoomRepository
from app.schemas.room import RoomCreate, RoomResponse, RoomUpdate
from app.utils.pagination import PaginationParams, build_meta


class RoomService:
    def __init__(self):
        self.repo = RoomRepository()

    async def list_rooms(self, pagination: PaginationParams, room_type: str | None = None, include_inactive: bool = False):
        filter_ = {"room_type": room_type} if room_type else None
        docs, total = await self.repo.list_paginated(pagination, extra_filter=filter_, include_inactive=include_inactive)
        items = [RoomResponse(**doc) for doc in docs]
        return items, build_meta(pagination, total)

    async def list_all_active(self) -> list[dict]:
        return await self.repo.list_all({"is_active": True})

    async def get_room(self, room_id: str) -> RoomResponse:
        doc = await self.repo.get_by_id_or_404(room_id)
        return RoomResponse(**doc)

    async def create_room(self, current_user: dict, payload: RoomCreate) -> RoomResponse:
        if await self.repo.find_by_number(payload.room_number):
            raise DuplicateException(f"Room '{payload.room_number}' already exists")
        model = RoomModel(**payload.model_dump())
        doc = await self.repo.insert(model.model_dump(mode="json"), actor_id=current_user["id"])
        return RoomResponse(**doc)

    async def update_room(self, current_user: dict, room_id: str, payload: RoomUpdate) -> RoomResponse:
        await self.repo.get_by_id_or_404(room_id)
        update_data = payload.model_dump(exclude_unset=True, mode="json")
        doc = await self.repo.update(room_id, update_data, actor_id=current_user["id"])
        return RoomResponse(**doc)

    async def delete_room(self, current_user: dict, room_id: str) -> None:
        await self.repo.get_by_id_or_404(room_id)
        db = get_database()
        if await db[Collections.SECTIONS].count_documents({"room_id": room_id, "is_active": True}, limit=1):
            raise ValidationException("This room is assigned to one or more sections. Reassign them first.")
        await self.repo.soft_delete(room_id, actor_id=current_user["id"])

    async def restore_room(self, current_user: dict, room_id: str) -> RoomResponse:
        doc = await self.repo.restore(room_id, actor_id=current_user["id"])
        return RoomResponse(**doc)

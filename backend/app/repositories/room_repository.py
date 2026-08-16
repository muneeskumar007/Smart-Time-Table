from app.core.constants import Collections
from app.database.connection import get_database
from app.repositories.base_repository import BaseRepository


class RoomRepository(BaseRepository):
    sortable_fields = {"room_number", "capacity", "building", "created_at"}
    default_sort_field = "room_number"
    searchable_fields = ["room_number", "building", "floor"]
    entity_name = "Room"

    def __init__(self):
        super().__init__(get_database()[Collections.ROOMS])

    async def find_by_number(self, room_number: str) -> dict | None:
        return await self.find_one({"room_number": room_number.strip().upper()})

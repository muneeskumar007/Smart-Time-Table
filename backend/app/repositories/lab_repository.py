from app.core.constants import Collections
from app.database.connection import get_database
from app.repositories.base_repository import BaseRepository


class LabRepository(BaseRepository):
    sortable_fields = {"lab_name", "room_number", "capacity", "created_at"}
    default_sort_field = "lab_name"
    searchable_fields = ["lab_name", "room_number", "building"]
    entity_name = "Laboratory"

    def __init__(self):
        super().__init__(get_database()[Collections.LABORATORIES])

    async def find_by_room_number(self, room_number: str) -> dict | None:
        return await self.find_one({"room_number": room_number.strip().upper()})

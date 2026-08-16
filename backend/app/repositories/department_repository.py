from app.core.constants import Collections
from app.database.connection import get_database
from app.repositories.base_repository import BaseRepository


class DepartmentRepository(BaseRepository):
    sortable_fields = {"name", "code", "established_year", "created_at", "updated_at"}
    default_sort_field = "name"
    searchable_fields = ["name", "code", "description"]
    entity_name = "Department"

    def __init__(self):
        super().__init__(get_database()[Collections.DEPARTMENTS])

    async def find_by_code(self, code: str) -> dict | None:
        return await self.find_one({"code": code.strip().upper()})

    async def find_by_name(self, name: str) -> dict | None:
        return await self.find_one({"name": name.strip()})

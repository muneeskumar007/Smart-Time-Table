from app.core.constants import Collections
from app.database.connection import get_database
from app.repositories.base_repository import BaseRepository


class SubjectAllocationRepository(BaseRepository):
    sortable_fields = {"created_at", "updated_at"}
    default_sort_field = "created_at"
    searchable_fields = []
    entity_name = "Subject allocation"

    def __init__(self):
        super().__init__(get_database()[Collections.SUBJECT_ALLOCATIONS])

    async def find_duplicate(self, subject_id: str, section_id: str) -> dict | None:
        return await self.find_one({"subject_id": subject_id, "section_id": section_id, "is_active": True})

    async def find_by_faculty(self, faculty_id: str, active_only: bool = True) -> list[dict]:
        filter_ = {"faculty_id": faculty_id}
        if active_only:
            filter_["is_active"] = True
        return await self.list_all(filter_, limit=200)

    async def find_by_section(self, section_id: str, active_only: bool = True) -> list[dict]:
        filter_ = {"section_id": section_id}
        if active_only:
            filter_["is_active"] = True
        return await self.list_all(filter_, limit=200)

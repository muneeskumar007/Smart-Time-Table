from app.core.constants import Collections
from app.database.connection import get_database
from app.repositories.base_repository import BaseRepository


class FacultyRepository(BaseRepository):
    sortable_fields = {"name", "employee_code", "designation", "date_of_joining", "created_at", "updated_at"}
    default_sort_field = "name"
    searchable_fields = ["name", "employee_code", "email", "designation", "specialization"]
    entity_name = "Faculty member"

    def __init__(self):
        super().__init__(get_database()[Collections.FACULTY])

    async def find_by_email(self, email: str) -> dict | None:
        return await self.find_one({"email": email.strip().lower()})

    async def find_by_employee_code(self, employee_code: str) -> dict | None:
        return await self.find_one({"employee_code": employee_code.strip().upper()})

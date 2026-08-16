from app.core.constants import Collections
from app.database.connection import get_database
from app.repositories.base_repository import BaseRepository


class CourseRepository(BaseRepository):
    sortable_fields = {"name", "code", "duration_years", "created_at"}
    default_sort_field = "name"
    searchable_fields = ["name", "code", "description"]
    entity_name = "Course"

    def __init__(self):
        super().__init__(get_database()[Collections.COURSES])

    async def find_by_code(self, code: str) -> dict | None:
        return await self.find_one({"code": code.strip().upper()})


class SubjectRepository(BaseRepository):
    sortable_fields = {"name", "code", "semester_number", "credits", "created_at"}
    default_sort_field = "semester_number"
    searchable_fields = ["name", "code"]
    entity_name = "Subject"

    def __init__(self):
        super().__init__(get_database()[Collections.SUBJECTS])

    async def find_by_code(self, code: str) -> dict | None:
        return await self.find_one({"code": code.strip().upper()})


class SectionRepository(BaseRepository):
    sortable_fields = {"section_name", "semester_number", "strength", "created_at"}
    default_sort_field = "section_name"
    searchable_fields = ["section_name"]
    entity_name = "Section"

    def __init__(self):
        super().__init__(get_database()[Collections.SECTIONS])

    async def find_duplicate(self, course_id: str, academic_year_id: str, semester_id: str, section_name: str) -> dict | None:
        return await self.find_one(
            {
                "course_id": course_id,
                "academic_year_id": academic_year_id,
                "semester_id": semester_id,
                "section_name": section_name.strip().upper(),
            }
        )

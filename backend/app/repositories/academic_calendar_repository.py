from app.core.constants import Collections
from app.database.connection import get_database
from app.repositories.base_repository import BaseRepository
from app.utils.time_helpers import time_str_to_minutes


class AcademicYearRepository(BaseRepository):
    sortable_fields = {"name", "start_date", "end_date", "created_at"}
    default_sort_field = "start_date"
    searchable_fields = ["name"]
    entity_name = "Academic year"

    def __init__(self):
        super().__init__(get_database()[Collections.ACADEMIC_YEARS])

    async def find_by_name(self, name: str) -> dict | None:
        return await self.find_one({"name": name.strip()})

    async def unset_current(self) -> None:
        await self.collection.update_many({"is_current": True}, {"$set": {"is_current": False}})


class SemesterRepository(BaseRepository):
    sortable_fields = {"name", "start_date", "end_date", "created_at"}
    default_sort_field = "start_date"
    searchable_fields = ["name"]
    entity_name = "Semester"

    def __init__(self):
        super().__init__(get_database()[Collections.SEMESTERS])

    async def find_by_year_and_term(self, academic_year_id: str, term_type: str) -> dict | None:
        return await self.find_one({"academic_year_id": academic_year_id, "term_type": term_type})

    async def unset_current(self) -> None:
        await self.collection.update_many({"is_current": True}, {"$set": {"is_current": False}})


class TimeSlotRepository(BaseRepository):
    sortable_fields = {"day_of_week", "start_time", "slot_order", "created_at"}
    default_sort_field = "slot_order"
    searchable_fields = ["label"]
    entity_name = "Time slot"

    def __init__(self):
        super().__init__(get_database()[Collections.TIMESLOTS])

    async def find_overlapping(
        self, department_id: str | None, day_of_week: str, start_minutes: int, end_minutes: int, exclude_id: str | None = None
    ) -> list[dict]:
        """Any existing slot in the same scope (same department_id -
        including the shared `None` global scope - and same day) whose
        [start, end) range intersects the given range. Queried directly
        against the collection (rather than through list_paginated) since
        every candidate is needed for the overlap math, not one page."""
        from app.repositories.base_repository import serialize_doc

        cursor = self.collection.find({"department_id": department_id, "day_of_week": day_of_week})
        candidates = [serialize_doc(d) for d in await cursor.to_list(length=200)]

        overlapping = []
        for slot in candidates:
            if exclude_id and slot["id"] == exclude_id:
                continue
            s_start = time_str_to_minutes(slot["start_time"])
            s_end = time_str_to_minutes(slot["end_time"])
            if start_minutes < s_end and s_start < end_minutes:
                overlapping.append(slot)
        return overlapping

from app.core.constants import Collections
from app.database.connection import get_database
from app.models.timetable import TimetableStatus
from app.repositories.base_repository import BaseRepository, serialize_doc


class TimetableRepository(BaseRepository):
    sortable_fields = {"version", "created_at", "updated_at", "published_at"}
    default_sort_field = "created_at"
    searchable_fields = []
    entity_name = "Timetable"

    def __init__(self):
        super().__init__(get_database()[Collections.TIMETABLES])

    async def find_latest_for_section(self, section_id: str, exclude_archived: bool = True) -> dict | None:
        filter_ = {"section_id": section_id}
        if exclude_archived:
            filter_["status"] = {"$ne": TimetableStatus.ARCHIVED.value}
        doc = await self.collection.find_one(filter_, sort=[("version", -1)])
        return serialize_doc(doc)

    async def find_published_for_section(self, section_id: str) -> dict | None:
        doc = await self.collection.find_one({"section_id": section_id, "status": TimetableStatus.PUBLISHED.value})
        return serialize_doc(doc)

    async def find_history_for_section(self, section_id: str, limit: int = 50) -> list[dict]:
        cursor = self.collection.find({"section_id": section_id}).sort("version", -1).limit(limit)
        docs = await cursor.to_list(length=limit)
        return [serialize_doc(d) for d in docs]

    async def find_next_version(self, section_id: str) -> int:
        latest = await self.collection.find_one({"section_id": section_id}, sort=[("version", -1)])
        return (latest["version"] + 1) if latest else 1

    async def find_occupied_faculty_slots(self, academic_year_id: str, semester_id: str, exclude_section_id: str | None = None) -> set[tuple[str, str]]:
        """Every (faculty_id, timeslot_id) pair already committed to a
        schedule elsewhere in this academic term - used so generating
        one section's timetable respects faculty already booked by
        another section's published/generated timetable."""
        filter_ = {
            "academic_year_id": academic_year_id,
            "semester_id": semester_id,
            "status": {"$in": [TimetableStatus.GENERATED.value, TimetableStatus.PUBLISHED.value]},
        }
        if exclude_section_id:
            filter_["section_id"] = {"$ne": exclude_section_id}
        cursor = self.collection.find(filter_, {"entries": 1})
        occupied = set()
        async for doc in cursor:
            for entry in doc.get("entries", []):
                occupied.add((entry["faculty_id"], entry["timeslot_id"]))
        return occupied

    async def find_occupied_room_slots(self, academic_year_id: str, semester_id: str, exclude_section_id: str | None = None) -> set[tuple[str, str]]:
        filter_ = {
            "academic_year_id": academic_year_id,
            "semester_id": semester_id,
            "status": {"$in": [TimetableStatus.GENERATED.value, TimetableStatus.PUBLISHED.value]},
        }
        if exclude_section_id:
            filter_["section_id"] = {"$ne": exclude_section_id}
        cursor = self.collection.find(filter_, {"entries": 1})
        occupied = set()
        async for doc in cursor:
            for entry in doc.get("entries", []):
                occupied.add((entry["room_id"], entry["timeslot_id"]))
        return occupied

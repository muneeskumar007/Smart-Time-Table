"""
Faculty workload.

Deliberately computed on read rather than maintained as a continuously
synced `faculty_workload` document per faculty - see the modelling note
in models/subject_allocation.py for the same reasoning applied here.
generation_logs and each Timetable's own audit_log already give an
after-the-fact history; this service answers "what is true right now."
"""
from pydantic import BaseModel

from app.auth.dependencies import ensure_department_access
from app.core.constants import Collections
from app.database.connection import get_database
from app.repositories.academic_structure_repository import SubjectRepository
from app.repositories.faculty_repository import FacultyRepository
from app.repositories.subject_allocation_repository import SubjectAllocationRepository
from app.schemas.common import RefSummary


class FacultyWorkloadResponse(BaseModel):
    faculty: RefSummary
    max_weekly_hours: int
    lecture_hours: int
    lab_hours: int
    assigned_hours: int
    remaining_hours: int
    is_overloaded: bool
    subject_count: int


class WorkloadService:
    async def get_faculty_workload(self, current_user: dict, faculty_id: str) -> FacultyWorkloadResponse:
        faculty = await FacultyRepository().get_by_id_or_404(faculty_id)
        ensure_department_access(current_user, faculty["department_id"])
        return await self._compute(faculty)

    async def list_department_workload(self, current_user: dict, department_id: str) -> list[FacultyWorkloadResponse]:
        ensure_department_access(current_user, department_id)
        faculty_members = await FacultyRepository().list_all({"department_id": department_id, "is_active": True})
        return [await self._compute(f) for f in faculty_members]

    async def _compute(self, faculty: dict) -> FacultyWorkloadResponse:
        allocations = await SubjectAllocationRepository().find_by_faculty(faculty["id"])

        lecture_hours = 0
        lab_hours = 0
        for allocation in allocations:
            subject = await SubjectRepository().find_by_id(allocation["subject_id"])
            if not subject:
                continue
            lecture_hours += subject.get("weekly_lecture_hours", 0)
            lab_hours += subject.get("weekly_lab_hours", 0)

        assigned = lecture_hours + lab_hours
        max_hours = faculty["max_weekly_hours"]

        return FacultyWorkloadResponse(
            faculty=RefSummary(id=faculty["id"], name=faculty["name"]),
            max_weekly_hours=max_hours,
            lecture_hours=lecture_hours,
            lab_hours=lab_hours,
            assigned_hours=assigned,
            remaining_hours=max(max_hours - assigned, 0),
            is_overloaded=assigned > max_hours,
            subject_count=len(allocations),
        )


class RoomAllocationResponse(BaseModel):
    room: RefSummary
    room_type: str
    capacity: int
    occupied_slot_count: int
    total_slot_count: int
    occupied_timeslot_ids: list[str]


class RoomAllocationService:
    """Computed the same way as workload: derived from the currently
    active (generated/published) timetables rather than a separately
    synced `room_allocations` collection."""

    async def get_room_allocation(self, room_id: str, academic_year_id: str, semester_id: str) -> RoomAllocationResponse:
        db = get_database()

        room = await db[Collections.ROOMS].find_one({"_id": _oid(room_id)})
        room_type = "classroom"
        if room is None:
            room = await db[Collections.LABORATORIES].find_one({"_id": _oid(room_id)})
            room_type = "laboratory"
        if room is None:
            from app.core.exceptions import NotFoundException

            raise NotFoundException("Room not found")

        total_slots = await db[Collections.TIMESLOTS].count_documents({"is_active": True, "is_break": False})

        cursor = db[Collections.TIMETABLES].find(
            {
                "academic_year_id": academic_year_id,
                "semester_id": semester_id,
                "status": {"$in": ["generated", "published"]},
                "entries.room_id": room_id,
            },
            {"entries": 1},
        )
        occupied_ids: set[str] = set()
        async for doc in cursor:
            for entry in doc.get("entries", []):
                if entry["room_id"] == room_id:
                    occupied_ids.add(entry["timeslot_id"])

        name = room.get("room_number") or room.get("lab_name")
        return RoomAllocationResponse(
            room=RefSummary(id=str(room["_id"]), name=name),
            room_type=room_type,
            capacity=room["capacity"],
            occupied_slot_count=len(occupied_ids),
            total_slot_count=total_slots,
            occupied_timeslot_ids=sorted(occupied_ids),
        )


def _oid(id_str: str):
    from app.repositories.base_repository import to_object_id

    return to_object_id(id_str, "Room")

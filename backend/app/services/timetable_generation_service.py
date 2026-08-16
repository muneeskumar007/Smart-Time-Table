"""
Timetable generation service - the bridge between HTTP/repositories and
the database-free algorithms/ layer. Responsible for the full workflow
documented in the brief: load data -> validate -> build context ->
generate -> validate result -> save.
"""
from datetime import datetime, timezone

from app.algorithms.constraints.base import GenerationContext
from app.algorithms.generator import GenerationResult, TimetableGeneratorEngine
from app.auth.dependencies import ensure_department_access
from app.core.constants import Collections
from app.core.exceptions import ValidationException
from app.database.connection import get_database
from app.models.timetable import AuditLogEntry, GenerationLogModel, TimetableModel, TimetableStatus
from app.repositories.academic_calendar_repository import SemesterRepository
from app.repositories.academic_structure_repository import CourseRepository, SectionRepository, SubjectRepository
from app.repositories.faculty_repository import FacultyRepository
from app.repositories.lab_repository import LabRepository
from app.repositories.room_repository import RoomRepository
from app.repositories.subject_allocation_repository import SubjectAllocationRepository
from app.repositories.timetable_repository import TimetableRepository
from app.schemas.timetable import GenerateTimetableRequest, GenerateTimetableResponse
from app.services.timetable_service import build_timetable_response
from app.utils.logger import get_logger

logger = get_logger("timetable_generation")


class TimetableGenerationService:
    def __init__(self):
        self.repo = TimetableRepository()
        self.engine = TimetableGeneratorEngine()

    async def _load_context(self, section: dict) -> GenerationContext:
        allocations = await SubjectAllocationRepository().find_by_section(section["id"])
        if not allocations:
            raise ValidationException(
                "This section has no subject allocations yet. Assign faculty to subjects "
                "for this section (Subject Allocations) before generating a timetable."
            )

        subject_ids = {a["subject_id"] for a in allocations}
        faculty_ids = {a["faculty_id"] for a in allocations}

        subjects_by_id = {}
        for sid in subject_ids:
            subject = await SubjectRepository().find_by_id(sid)
            if subject and subject["is_active"]:
                subjects_by_id[sid] = subject

        faculty_by_id = {}
        for fid in faculty_ids:
            faculty = await FacultyRepository().find_by_id(fid)
            if faculty and faculty["is_active"]:
                faculty_by_id[fid] = faculty

        active_allocations = [
            a for a in allocations if a["subject_id"] in subjects_by_id and a["faculty_id"] in faculty_by_id
        ]

        db = get_database()
        timeslot_cursor = db[Collections.TIMESLOTS].find(
            {"is_active": True, "$or": [{"department_id": None}, {"department_id": section["department_id"]}]}
        )
        timeslots = [self._serialize(d) async for d in timeslot_cursor]

        classrooms = [
            r for r in await RoomRepository().list_all({"is_active": True}) if r["capacity"] >= section["strength"]
        ]
        labs = [
            l
            for l in await LabRepository().list_all({"department_id": section["department_id"], "is_active": True})
            if l["capacity"] >= section["strength"]
        ]

        occupied_faculty = await self.repo.find_occupied_faculty_slots(
            section["academic_year_id"], section["semester_id"], exclude_section_id=section["id"]
        )
        occupied_rooms = await self.repo.find_occupied_room_slots(
            section["academic_year_id"], section["semester_id"], exclude_section_id=section["id"]
        )

        return self.engine.build_context(
            section=section,
            allocations=active_allocations,
            subjects_by_id=subjects_by_id,
            faculty_by_id=faculty_by_id,
            timeslots=timeslots,
            classrooms=classrooms,
            labs=labs,
            externally_occupied_faculty=occupied_faculty,
            externally_occupied_rooms=occupied_rooms,
        )

    @staticmethod
    def _serialize(doc: dict) -> dict:
        doc = dict(doc)
        doc["id"] = str(doc.pop("_id"))
        return doc

    async def generate(self, current_user: dict, payload: GenerateTimetableRequest) -> GenerateTimetableResponse:
        section = await SectionRepository().get_by_id_or_404(payload.section_id)
        ensure_department_access(current_user, section["department_id"])
        if not section["is_active"]:
            raise ValidationException("Cannot generate a timetable for an inactive section")

        db = get_database()
        log = GenerationLogModel(section_id=section["id"], triggered_by=current_user["id"])
        log_result = await db[Collections.GENERATION_LOGS].insert_one(log.model_dump())
        log_id = log_result.inserted_id

        # A GENERATING placeholder record makes an in-progress (or
        # crashed-mid-solve) run observable rather than silently absent.
        version = await self.repo.find_next_version(section["id"])
        placeholder = TimetableModel(
            academic_year_id=section["academic_year_id"],
            semester_id=section["semester_id"],
            department_id=section["department_id"],
            course_id=section["course_id"],
            section_id=section["id"],
            version=version,
            status=TimetableStatus.GENERATING,
        )
        placeholder_doc = await self.repo.insert(placeholder.model_dump(mode="json"), actor_id=current_user["id"])

        try:
            ctx = await self._load_context(section)
        except ValidationException as exc:
            await self._mark_failed(placeholder_doc["id"], log_id, str(exc.message))
            raise

        result: GenerationResult = await self.engine.generate(ctx, max_solve_seconds=payload.max_solve_seconds)

        now = datetime.now(timezone.utc)
        if not result.entries:
            await self._mark_failed(placeholder_doc["id"], log_id, result.message, result)
            return GenerateTimetableResponse(
                timetable=None,
                solver_status=result.solver_status,
                demands_total=result.demands_total,
                demands_scheduled=result.demands_scheduled,
                duration_seconds=result.duration_seconds,
                conflicts=result.conflicts,
            )

        status = TimetableStatus.GENERATED if result.success else TimetableStatus.DRAFT
        update_data = {
            "status": status.value,
            "entries": result.entries,
            "generated_at": now,
            "generated_by": current_user["id"],
            "audit_log": [
                *placeholder_doc.get("audit_log", []),
                AuditLogEntry(
                    action="generated",
                    actor_id=current_user["id"],
                    details=f"{result.solver_status}: {result.demands_scheduled}/{result.demands_total} sessions placed",
                ).model_dump(),
            ],
        }
        doc = await self.repo.update(placeholder_doc["id"], update_data, actor_id=current_user["id"])

        await db[Collections.GENERATION_LOGS].update_one(
            {"_id": log_id},
            {
                "$set": {
                    "timetable_id": doc["id"],
                    "completed_at": now,
                    "duration_seconds": result.duration_seconds,
                    "solver_status": result.solver_status,
                    "success": result.success,
                    "demands_total": result.demands_total,
                    "demands_scheduled": result.demands_scheduled,
                    "conflict_count": len(result.conflicts),
                    "message": result.message,
                }
            },
        )

        timetable_response = await build_timetable_response(doc)
        return GenerateTimetableResponse(
            timetable=timetable_response,
            solver_status=result.solver_status,
            demands_total=result.demands_total,
            demands_scheduled=result.demands_scheduled,
            duration_seconds=result.duration_seconds,
            conflicts=result.conflicts,
        )

    async def _mark_failed(self, timetable_id: str, log_id, message: str, result: GenerationResult | None = None) -> None:
        db = get_database()
        await self.repo.update(timetable_id, {"status": TimetableStatus.FAILED.value})
        await db[Collections.GENERATION_LOGS].update_one(
            {"_id": log_id},
            {
                "$set": {
                    "completed_at": datetime.now(timezone.utc),
                    "success": False,
                    "solver_status": result.solver_status if result else "ERROR",
                    "duration_seconds": result.duration_seconds if result else 0.0,
                    "demands_total": result.demands_total if result else 0,
                    "demands_scheduled": 0,
                    "message": message,
                }
            },
        )
        logger.warning("Timetable generation failed for timetable_id=%s: %s", timetable_id, message)

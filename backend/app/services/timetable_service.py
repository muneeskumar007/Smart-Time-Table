"""
Timetable service: read access, and the publish/rollback/history
lifecycle. `build_timetable_response()` is a module-level function
(not a method) specifically so timetable_generation_service.py can reuse
it without instantiating TimetableService or creating a circular import
between the two service modules.
"""
from datetime import datetime, timezone

from app.auth.dependencies import ensure_department_access
from app.core.constants import UserRole
from app.core.exceptions import NotFoundException, ValidationException
from app.models.timetable import AuditLogEntry, TimetableStatus
from app.repositories.academic_calendar_repository import AcademicYearRepository, SemesterRepository
from app.repositories.academic_structure_repository import CourseRepository, SectionRepository, SubjectRepository
from app.repositories.faculty_repository import FacultyRepository
from app.repositories.room_repository import RoomRepository
from app.repositories.lab_repository import LabRepository
from app.repositories.timetable_repository import TimetableRepository
from app.repositories.user_repository import UserRepository
from app.schemas.common import RefSummary
from app.schemas.timetable import TimetableEntryResponse, TimetableResponse, TimetableSummaryResponse
from app.utils.pagination import PaginationParams, build_meta


async def _room_ref(room_id: str) -> RefSummary:
    room = await RoomRepository().find_by_id(room_id)
    if room:
        return RefSummary(id=room["id"], name=room["room_number"])
    lab = await LabRepository().find_by_id(room_id)
    if lab:
        return RefSummary(id=lab["id"], name=f"{lab['lab_name']} ({lab['room_number']})")
    return RefSummary(id=room_id, name="Unknown room")


async def build_timetable_response(doc: dict) -> TimetableResponse:
    year = await AcademicYearRepository().find_by_id(doc["academic_year_id"])
    semester = await SemesterRepository().find_by_id(doc["semester_id"])
    course = await CourseRepository().find_by_id(doc["course_id"])
    section = await SectionRepository().find_by_id(doc["section_id"])

    generated_by = None
    if doc.get("generated_by"):
        u = await UserRepository().find_by_id(doc["generated_by"])
        if u:
            generated_by = RefSummary(id=u["id"], name=u["name"])

    published_by = None
    if doc.get("published_by"):
        u = await UserRepository().find_by_id(doc["published_by"])
        if u:
            published_by = RefSummary(id=u["id"], name=u["name"])

    entries = []
    for entry in doc.get("entries", []):
        subject = await SubjectRepository().find_by_id(entry["subject_id"])
        faculty = await FacultyRepository().find_by_id(entry["faculty_id"])
        room_ref = await _room_ref(entry["room_id"])
        entries.append(
            TimetableEntryResponse(
                id=entry["timeslot_id"],
                timeslot_id=entry["timeslot_id"],
                day_of_week=entry["day_of_week"],
                period_label=entry.get("period_label"),
                start_time=entry["start_time"],
                end_time=entry["end_time"],
                subject=RefSummary(id=subject["id"], name=subject["name"]) if subject else RefSummary(id=entry["subject_id"], name="Unknown"),
                faculty=RefSummary(id=faculty["id"], name=faculty["name"]) if faculty else RefSummary(id=entry["faculty_id"], name="Unknown"),
                room=room_ref,
                is_lab=entry["is_lab"],
                remarks=entry.get("remarks"),
            )
        )
    # Stable reading order: by day-of-week then start time.
    day_order = {"MON": 0, "TUE": 1, "WED": 2, "THU": 3, "FRI": 4, "SAT": 5}
    entries.sort(key=lambda e: (day_order.get(e.day_of_week, 9), e.start_time))

    def ref(obj, name_field="name"):
        return RefSummary(id=obj["id"], name=obj[name_field]) if obj else RefSummary(id="unknown", name="Unknown")

    return TimetableResponse(
        id=doc["id"],
        academic_year=ref(year),
        semester=ref(semester),
        department_id=doc["department_id"],
        course=ref(course),
        section=RefSummary(id=section["id"], name=section["section_name"]) if section else RefSummary(id=doc["section_id"], name="Unknown"),
        version=doc["version"],
        status=doc["status"],
        generated_at=doc.get("generated_at"),
        generated_by=generated_by,
        published_at=doc.get("published_at"),
        published_by=published_by,
        entries=entries,
        created_at=doc["created_at"],
        updated_at=doc["updated_at"],
    )


async def build_summary_response(doc: dict) -> TimetableSummaryResponse:
    section = await SectionRepository().find_by_id(doc["section_id"])
    return TimetableSummaryResponse(
        id=doc["id"],
        section=RefSummary(id=section["id"], name=section["section_name"]) if section else RefSummary(id=doc["section_id"], name="Unknown"),
        version=doc["version"],
        status=doc["status"],
        entry_count=len(doc.get("entries", [])),
        generated_at=doc.get("generated_at"),
        published_at=doc.get("published_at"),
        created_at=doc["created_at"],
    )


class TimetableService:
    def __init__(self):
        self.repo = TimetableRepository()

    # kept as a thin instance method too, so callers already holding a
    # TimetableService instance don't need the module-level import.
    async def _to_response(self, doc: dict) -> TimetableResponse:
        return await build_timetable_response(doc)

    async def get_timetable(self, current_user: dict, timetable_id: str) -> TimetableResponse:
        doc = await self.repo.get_by_id_or_404(timetable_id)
        ensure_department_access(current_user, doc["department_id"])
        return await build_timetable_response(doc)

    async def get_current_for_section(self, current_user: dict, section_id: str) -> TimetableResponse:
        doc = await self.repo.find_latest_for_section(section_id)
        if not doc:
            raise NotFoundException("No timetable has been generated for this section yet")
        ensure_department_access(current_user, doc["department_id"])
        return await build_timetable_response(doc)

    async def get_published_for_section(self, section_id: str) -> TimetableResponse:
        """Unrestricted by department - this is what Students/Faculty
        use to view a published timetable, and publication is what makes
        it visible to them in the first place."""
        doc = await self.repo.find_published_for_section(section_id)
        if not doc:
            raise NotFoundException("No published timetable exists for this section yet")
        return await build_timetable_response(doc)

    async def list_timetables(
        self, current_user: dict, pagination: PaginationParams, section_id: str | None = None, status: str | None = None
    ):
        filter_ = {}
        if current_user["role"] != UserRole.SUPER_ADMIN.value:
            filter_["department_id"] = current_user["department_id"]
        if section_id:
            filter_["section_id"] = section_id
        if status:
            filter_["status"] = status

        docs, total = await self.repo.list_paginated(pagination, extra_filter=filter_, include_inactive=True)
        items = [await build_summary_response(doc) for doc in docs]
        return items, build_meta(pagination, total)

    async def get_history(self, current_user: dict, section_id: str) -> list[TimetableSummaryResponse]:
        docs = await self.repo.find_history_for_section(section_id)
        if docs:
            ensure_department_access(current_user, docs[0]["department_id"])
        return [await build_summary_response(doc) for doc in docs]

    async def publish(self, current_user: dict, timetable_id: str) -> TimetableResponse:
        from app.services.conflict_detection_service import ConflictDetectionService
        from app.services.timetable_generation_service import TimetableGenerationService

        doc = await self.repo.get_by_id_or_404(timetable_id)
        ensure_department_access(current_user, doc["department_id"])

        if doc["status"] not in (TimetableStatus.DRAFT.value, TimetableStatus.GENERATED.value):
            raise ValidationException(f"Only a draft or generated timetable can be published (current status: {doc['status']})")
        if not doc.get("entries"):
            raise ValidationException("This timetable has no entries to publish")

        section = await SectionRepository().get_by_id_or_404(doc["section_id"])
        ctx = await TimetableGenerationService()._load_context(section)
        # The context freshly reloads faculty/rooms, but externally-occupied
        # slots were computed excluding *this* section - correct, since
        # we're validating this section's own entries against everyone else.
        validation = ConflictDetectionService().validate_entries(doc["entries"], ctx)
        if not validation.is_valid:
            raise ValidationException(
                "This timetable has unresolved conflicts and cannot be published. Run validation for details.",
                errors=[{"field": c.type, "message": c.message} for c in validation.conflicts],
            )

        now = datetime.now(timezone.utc)

        previous_published = await self.repo.find_published_for_section(doc["section_id"])
        if previous_published and previous_published["id"] != doc["id"]:
            await self.repo.update(
                previous_published["id"],
                {"status": TimetableStatus.ARCHIVED.value},
                actor_id=current_user["id"],
            )

        updated = await self.repo.update(
            timetable_id,
            {
                "status": TimetableStatus.PUBLISHED.value,
                "published_at": now,
                "published_by": current_user["id"],
                "audit_log": [
                    *doc.get("audit_log", []),
                    AuditLogEntry(action="published", actor_id=current_user["id"]).model_dump(),
                ],
            },
            actor_id=current_user["id"],
        )
        return await build_timetable_response(updated)

    async def rollback(self, current_user: dict, target_timetable_id: str) -> TimetableResponse:
        target = await self.repo.get_by_id_or_404(target_timetable_id)
        ensure_department_access(current_user, target["department_id"])

        if target["status"] != TimetableStatus.ARCHIVED.value:
            raise ValidationException("Only an archived (previously-published) version can be rolled back to")

        current = await self.repo.find_published_for_section(target["section_id"])
        if current:
            await self.repo.update(
                current["id"],
                {"status": TimetableStatus.ARCHIVED.value},
                actor_id=current_user["id"],
            )

        now = datetime.now(timezone.utc)
        restored = await self.repo.update(
            target_timetable_id,
            {
                "status": TimetableStatus.PUBLISHED.value,
                "published_at": now,
                "published_by": current_user["id"],
                "audit_log": [
                    *target.get("audit_log", []),
                    AuditLogEntry(action="rolled_back", actor_id=current_user["id"], details="Restored via rollback").model_dump(),
                ],
            },
            actor_id=current_user["id"],
        )
        return await build_timetable_response(restored)

    async def delete_timetable(self, current_user: dict, timetable_id: str) -> None:
        doc = await self.repo.get_by_id_or_404(timetable_id)
        ensure_department_access(current_user, doc["department_id"])
        if doc["status"] == TimetableStatus.PUBLISHED.value:
            raise ValidationException("Cannot delete a published timetable - archive or roll it back first")
        await self.repo.soft_delete(timetable_id, actor_id=current_user["id"])

    async def validate_timetable(self, current_user: dict, timetable_id: str):
        from app.services.conflict_detection_service import ConflictDetectionService
        from app.services.timetable_generation_service import TimetableGenerationService

        doc = await self.repo.get_by_id_or_404(timetable_id)
        ensure_department_access(current_user, doc["department_id"])

        section = await SectionRepository().get_by_id_or_404(doc["section_id"])
        ctx = await TimetableGenerationService()._load_context(section)
        return ConflictDetectionService().validate_entries(doc.get("entries", []), ctx)

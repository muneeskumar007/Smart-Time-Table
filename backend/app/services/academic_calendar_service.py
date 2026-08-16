from app.auth.dependencies import ensure_department_access
from app.core.constants import UserRole
from app.core.exceptions import DuplicateException, ValidationException
from app.models.academic_calendar import AcademicYearModel, SemesterModel, TimeSlotModel
from app.repositories.academic_calendar_repository import (
    AcademicYearRepository,
    SemesterRepository,
    TimeSlotRepository,
)
from app.repositories.department_repository import DepartmentRepository
from app.utils.time_helpers import time_str_to_minutes
from app.schemas.academic_calendar import (
    AcademicYearCreate,
    AcademicYearResponse,
    AcademicYearUpdate,
    SemesterCreate,
    SemesterResponse,
    SemesterUpdate,
    TimeSlotCreate,
    TimeSlotResponse,
    TimeSlotUpdate,
)
from app.schemas.common import RefSummary
from app.utils.pagination import PaginationParams, build_meta


class AcademicYearService:
    def __init__(self):
        self.repo = AcademicYearRepository()

    async def list_years(self, pagination: PaginationParams, include_inactive: bool = False):
        docs, total = await self.repo.list_paginated(pagination, include_inactive=include_inactive)
        items = [AcademicYearResponse(**doc) for doc in docs]
        return items, build_meta(pagination, total)

    async def list_all_active(self) -> list[dict]:
        return await self.repo.list_all()

    async def get_year(self, year_id: str) -> AcademicYearResponse:
        doc = await self.repo.get_by_id_or_404(year_id)
        return AcademicYearResponse(**doc)

    async def create_year(self, current_user: dict, payload: AcademicYearCreate) -> AcademicYearResponse:
        if await self.repo.find_by_name(payload.name):
            raise DuplicateException(f"An academic year named '{payload.name}' already exists")
        model = AcademicYearModel(**payload.model_dump())
        doc = await self.repo.insert(model.model_dump(mode="json"), actor_id=current_user["id"])
        return AcademicYearResponse(**doc)

    async def update_year(self, current_user: dict, year_id: str, payload: AcademicYearUpdate) -> AcademicYearResponse:
        await self.repo.get_by_id_or_404(year_id)
        update_data = payload.model_dump(exclude_unset=True, mode="json")

        if update_data.get("is_current") is True:
            await self.repo.unset_current()

        doc = await self.repo.update(year_id, update_data, actor_id=current_user["id"])
        return AcademicYearResponse(**doc)

    async def delete_year(self, current_user: dict, year_id: str) -> None:
        await self.repo.get_by_id_or_404(year_id)
        db = SemesterRepository()
        if await db.exists({"academic_year_id": year_id, "is_active": True}):
            raise ValidationException("This academic year still has semesters defined under it. Remove them first.")
        await self.repo.soft_delete(year_id, actor_id=current_user["id"])

    async def restore_year(self, current_user: dict, year_id: str) -> AcademicYearResponse:
        doc = await self.repo.restore(year_id, actor_id=current_user["id"])
        return AcademicYearResponse(**doc)


class SemesterService:
    def __init__(self):
        self.repo = SemesterRepository()

    async def _to_response(self, doc: dict) -> SemesterResponse:
        year = await AcademicYearRepository().find_by_id(doc["academic_year_id"])
        academic_year = RefSummary(id=year["id"], name=year["name"]) if year else RefSummary(id=doc["academic_year_id"], name="Unknown")
        return SemesterResponse(**doc, academic_year=academic_year)

    async def list_semesters(self, pagination: PaginationParams, academic_year_id: str | None = None, include_inactive: bool = False):
        filter_ = {"academic_year_id": academic_year_id} if academic_year_id else None
        docs, total = await self.repo.list_paginated(pagination, extra_filter=filter_, include_inactive=include_inactive)
        items = [await self._to_response(doc) for doc in docs]
        return items, build_meta(pagination, total)

    async def list_all_active(self) -> list[dict]:
        return await self.repo.list_all()

    async def get_semester(self, semester_id: str) -> SemesterResponse:
        doc = await self.repo.get_by_id_or_404(semester_id)
        return await self._to_response(doc)

    async def create_semester(self, current_user: dict, payload: SemesterCreate) -> SemesterResponse:
        year = await AcademicYearRepository().find_by_id(payload.academic_year_id)
        if not year:
            raise ValidationException("The selected academic year does not exist")

        if payload.start_date < year["start_date"] or payload.end_date > year["end_date"]:
            raise ValidationException("Semester dates must fall within the selected academic year's date range")

        if await self.repo.find_by_year_and_term(payload.academic_year_id, payload.term_type.value):
            raise DuplicateException(
                f"A {payload.term_type.value} semester already exists for this academic year"
            )

        model = SemesterModel(**payload.model_dump())
        doc = await self.repo.insert(model.model_dump(mode="json"), actor_id=current_user["id"])
        return await self._to_response(doc)

    async def update_semester(self, current_user: dict, semester_id: str, payload: SemesterUpdate) -> SemesterResponse:
        await self.repo.get_by_id_or_404(semester_id)
        update_data = payload.model_dump(exclude_unset=True, mode="json")

        if update_data.get("is_current") is True:
            await self.repo.unset_current()

        doc = await self.repo.update(semester_id, update_data, actor_id=current_user["id"])
        return await self._to_response(doc)

    async def delete_semester(self, current_user: dict, semester_id: str) -> None:
        await self.repo.get_by_id_or_404(semester_id)
        await self.repo.soft_delete(semester_id, actor_id=current_user["id"])

    async def restore_semester(self, current_user: dict, semester_id: str) -> SemesterResponse:
        doc = await self.repo.restore(semester_id, actor_id=current_user["id"])
        return await self._to_response(doc)


class TimeSlotService:
    def __init__(self):
        self.repo = TimeSlotRepository()

    async def _to_response(self, doc: dict) -> TimeSlotResponse:
        department = None
        if doc.get("department_id"):
            dept = await DepartmentRepository().find_by_id(doc["department_id"])
            if dept:
                department = RefSummary(id=dept["id"], name=dept["name"])
        return TimeSlotResponse(**doc, department=department)

    async def list_slots(self, current_user: dict, pagination: PaginationParams, department_id: str | None = None, include_inactive: bool = False):
        filter_: dict = {}
        if current_user["role"] == UserRole.HOD.value:
            # A HOD sees the shared global slots plus their own department's.
            filter_ = {"$or": [{"department_id": None}, {"department_id": current_user["department_id"]}]}
        elif department_id:
            filter_ = {"department_id": department_id}

        docs, total = await self.repo.list_paginated(pagination, extra_filter=filter_, include_inactive=include_inactive)
        items = [await self._to_response(doc) for doc in docs]
        return items, build_meta(pagination, total)

    async def get_slot(self, slot_id: str) -> TimeSlotResponse:
        doc = await self.repo.get_by_id_or_404(slot_id)
        return await self._to_response(doc)

    async def create_slot(self, current_user: dict, payload: TimeSlotCreate) -> TimeSlotResponse:
        department_id = payload.department_id
        if current_user["role"] == UserRole.HOD.value:
            # A HOD may only create slots scoped to their own department,
            # never a global (department_id=None) template.
            department_id = current_user["department_id"]
        elif department_id:
            department = await DepartmentRepository().find_by_id(department_id)
            if not department:
                raise ValidationException("The selected department does not exist")

        overlap = await self.repo.find_overlapping(
            department_id, payload.day_of_week.value, time_str_to_minutes(payload.start_time), time_str_to_minutes(payload.end_time)
        )
        if overlap:
            raise ValidationException(
                f"This time overlaps with an existing slot ({overlap[0]['start_time']}-{overlap[0]['end_time']})"
            )

        model = TimeSlotModel(**{**payload.model_dump(), "department_id": department_id})
        doc = await self.repo.insert(model.model_dump(mode="json"), actor_id=current_user["id"])
        return await self._to_response(doc)

    async def update_slot(self, current_user: dict, slot_id: str, payload: TimeSlotUpdate) -> TimeSlotResponse:
        existing = await self.repo.get_by_id_or_404(slot_id)
        ensure_department_access(current_user, existing.get("department_id"))

        update_data = payload.model_dump(exclude_unset=True, mode="json")

        new_start = update_data.get("start_time", existing["start_time"])
        new_end = update_data.get("end_time", existing["end_time"])
        new_day = update_data.get("day_of_week", existing["day_of_week"])
        if "start_time" in update_data or "end_time" in update_data or "day_of_week" in update_data:
            if time_str_to_minutes(new_end) <= time_str_to_minutes(new_start):
                raise ValidationException("End time must be after start time")
            overlap = await self.repo.find_overlapping(
                existing.get("department_id"), new_day, time_str_to_minutes(new_start), time_str_to_minutes(new_end), exclude_id=slot_id
            )
            if overlap:
                raise ValidationException(
                    f"This time overlaps with an existing slot ({overlap[0]['start_time']}-{overlap[0]['end_time']})"
                )

        doc = await self.repo.update(slot_id, update_data, actor_id=current_user["id"])
        return await self._to_response(doc)

    async def delete_slot(self, current_user: dict, slot_id: str) -> None:
        existing = await self.repo.get_by_id_or_404(slot_id)
        ensure_department_access(current_user, existing.get("department_id"))
        await self.repo.soft_delete(slot_id, actor_id=current_user["id"])

    async def restore_slot(self, current_user: dict, slot_id: str) -> TimeSlotResponse:
        existing = await self.repo.get_by_id_or_404(slot_id)
        ensure_department_access(current_user, existing.get("department_id"))
        doc = await self.repo.restore(slot_id, actor_id=current_user["id"])
        return await self._to_response(doc)

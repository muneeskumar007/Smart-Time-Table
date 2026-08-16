"""
Subject Allocation service.

This is the "who teaches what to whom" administrative step that must
happen before a timetable can be generated - see the modelling note in
models/subject_allocation.py. The timetable generator (algorithms/) reads
allocations created here as its primary input.
"""
from app.auth.dependencies import ensure_department_access
from app.core.constants import Collections
from app.core.exceptions import DuplicateException, ValidationException
from app.database.connection import get_database
from app.models.subject_allocation import SubjectAllocationModel
from app.repositories.academic_structure_repository import CourseRepository, SectionRepository, SubjectRepository
from app.repositories.faculty_repository import FacultyRepository
from app.repositories.subject_allocation_repository import SubjectAllocationRepository
from app.schemas.common import RefSummary
from app.schemas.subject_allocation import SubjectAllocationCreate, SubjectAllocationResponse, SubjectAllocationUpdate
from app.utils.pagination import PaginationParams, build_meta


def _required_hours(subject: dict) -> int:
    return subject.get("weekly_lecture_hours", 0) + subject.get("weekly_lab_hours", 0)


class SubjectAllocationService:
    def __init__(self):
        self.repo = SubjectAllocationRepository()

    async def _allocated_hours(self, allocation: dict) -> int:
        """Counts sessions in the most recent non-archived timetable for
        this section that belong to this subject+faculty pairing. Source
        of truth is the timetable itself, not a cached counter, so this
        can never drift."""
        db = get_database()
        timetable = await db[Collections.TIMETABLES].find_one(
            {"section_id": allocation["section_id"], "status": {"$ne": "archived"}},
            sort=[("version", -1)],
        )
        if not timetable:
            return 0
        return sum(
            1
            for entry in timetable.get("entries", [])
            if entry.get("subject_id") == allocation["subject_id"] and entry.get("faculty_id") == allocation["faculty_id"]
        )

    async def _to_response(self, doc: dict) -> SubjectAllocationResponse:
        subject = await SubjectRepository().find_by_id(doc["subject_id"])
        section = await SectionRepository().find_by_id(doc["section_id"])
        faculty = await FacultyRepository().find_by_id(doc["faculty_id"])

        subject_ref = RefSummary(id=subject["id"], name=subject["name"]) if subject else RefSummary(id=doc["subject_id"], name="Unknown")
        section_ref = (
            RefSummary(id=section["id"], name=section["section_name"]) if section else RefSummary(id=doc["section_id"], name="Unknown")
        )
        faculty_ref = RefSummary(id=faculty["id"], name=faculty["name"]) if faculty else RefSummary(id=doc["faculty_id"], name="Unknown")

        required = _required_hours(subject) if subject else 0
        allocated = await self._allocated_hours(doc)
        allocated = min(allocated, required) if required else allocated
        remaining = max(required - allocated, 0)
        completion = round((allocated / required) * 100, 1) if required else 0.0

        return SubjectAllocationResponse(
            **doc,
            subject=subject_ref,
            section=section_ref,
            faculty=faculty_ref,
            required_hours=required,
            allocated_hours=allocated,
            remaining_hours=remaining,
            completion_percentage=completion,
        )

    async def list_allocations(
        self, current_user: dict, pagination: PaginationParams, section_id: str | None = None, faculty_id: str | None = None
    ):
        filter_ = {}
        if current_user["role"] != "super_admin":
            filter_["department_id"] = current_user["department_id"]
        if section_id:
            filter_["section_id"] = section_id
        if faculty_id:
            filter_["faculty_id"] = faculty_id

        docs, total = await self.repo.list_paginated(pagination, extra_filter=filter_)
        items = [await self._to_response(doc) for doc in docs]
        return items, build_meta(pagination, total)

    async def get_allocation(self, current_user: dict, allocation_id: str) -> SubjectAllocationResponse:
        doc = await self.repo.get_by_id_or_404(allocation_id)
        ensure_department_access(current_user, doc["department_id"])
        return await self._to_response(doc)

    async def _check_faculty_capacity(self, faculty: dict, new_subject: dict, exclude_allocation_id: str | None = None) -> None:
        """Warns/blocks at allocation time (not just generation time) if
        assigning this subject would push the faculty member over their
        weekly cap, using every OTHER active allocation they already
        hold plus this new one."""
        existing = await self.repo.find_by_faculty(faculty["id"])
        total = new_subject and _required_hours(new_subject) or 0
        for alloc in existing:
            if exclude_allocation_id and alloc["id"] == exclude_allocation_id:
                continue
            subject = await SubjectRepository().find_by_id(alloc["subject_id"])
            if subject:
                total += _required_hours(subject)
        if total > faculty["max_weekly_hours"]:
            raise ValidationException(
                f"Assigning this subject would give {faculty['name']} {total} hours/week, "
                f"exceeding their {faculty['max_weekly_hours']}-hour weekly maximum."
            )

    async def create_allocation(self, current_user: dict, payload: SubjectAllocationCreate) -> SubjectAllocationResponse:
        subject = await SubjectRepository().find_by_id(payload.subject_id)
        if not subject or not subject["is_active"]:
            raise ValidationException("The selected subject does not exist or is inactive")

        section = await SectionRepository().find_by_id(payload.section_id)
        if not section or not section["is_active"]:
            raise ValidationException("The selected section does not exist or is inactive")

        ensure_department_access(current_user, section["department_id"])

        course = await CourseRepository().find_by_id(section["course_id"])
        if not course or subject["course_id"] != course["id"]:
            raise ValidationException("This subject does not belong to the section's course")
        if subject["semester_number"] != section["semester_number"]:
            raise ValidationException(
                f"This subject is for semester {subject['semester_number']}, but the section is in semester {section['semester_number']}"
            )

        faculty = await FacultyRepository().find_by_id(payload.faculty_id)
        if not faculty or not faculty["is_active"]:
            raise ValidationException("The selected faculty member does not exist or is inactive")
        if faculty["department_id"] != section["department_id"]:
            raise ValidationException("The selected faculty member must belong to the section's department")

        if await self.repo.find_duplicate(payload.subject_id, payload.section_id):
            raise DuplicateException("This subject is already allocated to a faculty member for this section")

        await self._check_faculty_capacity(faculty, subject)

        model = SubjectAllocationModel(
            subject_id=payload.subject_id,
            section_id=payload.section_id,
            faculty_id=payload.faculty_id,
            department_id=section["department_id"],
        )
        doc = await self.repo.insert(model.model_dump(), actor_id=current_user["id"])
        return await self._to_response(doc)

    async def update_allocation(
        self, current_user: dict, allocation_id: str, payload: SubjectAllocationUpdate
    ) -> SubjectAllocationResponse:
        existing = await self.repo.get_by_id_or_404(allocation_id)
        ensure_department_access(current_user, existing["department_id"])

        faculty = await FacultyRepository().find_by_id(payload.faculty_id)
        if not faculty or not faculty["is_active"]:
            raise ValidationException("The selected faculty member does not exist or is inactive")
        if faculty["department_id"] != existing["department_id"]:
            raise ValidationException("The selected faculty member must belong to the section's department")

        subject = await SubjectRepository().find_by_id(existing["subject_id"])
        await self._check_faculty_capacity(faculty, subject, exclude_allocation_id=allocation_id)

        update_data = payload.model_dump(exclude_unset=True)
        doc = await self.repo.update(allocation_id, update_data, actor_id=current_user["id"])
        return await self._to_response(doc)

    async def delete_allocation(self, current_user: dict, allocation_id: str) -> None:
        existing = await self.repo.get_by_id_or_404(allocation_id)
        ensure_department_access(current_user, existing["department_id"])
        await self.repo.soft_delete(allocation_id, actor_id=current_user["id"])

    async def restore_allocation(self, current_user: dict, allocation_id: str) -> SubjectAllocationResponse:
        existing = await self.repo.get_by_id_or_404(allocation_id)
        ensure_department_access(current_user, existing["department_id"])
        doc = await self.repo.restore(allocation_id, actor_id=current_user["id"])
        return await self._to_response(doc)

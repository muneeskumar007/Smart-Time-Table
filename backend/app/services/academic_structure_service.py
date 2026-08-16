from app.auth.dependencies import ensure_department_access
from app.core.constants import UserRole
from app.core.exceptions import DuplicateException, ValidationException
from app.models.academic_structure import CourseModel, SectionModel, SubjectModel
from app.repositories.academic_calendar_repository import AcademicYearRepository, SemesterRepository
from app.repositories.academic_structure_repository import CourseRepository, SectionRepository, SubjectRepository
from app.repositories.department_repository import DepartmentRepository
from app.repositories.faculty_repository import FacultyRepository
from app.repositories.room_repository import RoomRepository
from app.schemas.academic_structure import (
    CourseCreate,
    CourseResponse,
    CourseUpdate,
    SectionCreate,
    SectionResponse,
    SectionUpdate,
    SubjectCreate,
    SubjectResponse,
    SubjectUpdate,
)
from app.schemas.common import RefSummary
from app.utils.pagination import PaginationParams, build_meta


def _scope_filter(current_user: dict) -> dict:
    if current_user["role"] == UserRole.SUPER_ADMIN.value:
        return {}
    return {"department_id": current_user["department_id"]}


class CourseService:
    def __init__(self):
        self.repo = CourseRepository()

    async def _to_response(self, doc: dict) -> CourseResponse:
        dept = await DepartmentRepository().find_by_id(doc["department_id"])
        department = RefSummary(id=dept["id"], name=dept["name"]) if dept else RefSummary(id=doc["department_id"], name="Unknown")
        return CourseResponse(**doc, department=department)

    async def list_courses(self, current_user: dict, pagination: PaginationParams, department_id: str | None = None, include_inactive: bool = False):
        filter_ = _scope_filter(current_user)
        if current_user["role"] == UserRole.SUPER_ADMIN.value and department_id:
            filter_ = {**filter_, "department_id": department_id}
        docs, total = await self.repo.list_paginated(pagination, extra_filter=filter_, include_inactive=include_inactive)
        items = [await self._to_response(doc) for doc in docs]
        return items, build_meta(pagination, total)

    async def list_lookup(self, current_user: dict, department_id: str | None = None) -> list[dict]:
        filter_ = _scope_filter(current_user)
        if current_user["role"] == UserRole.SUPER_ADMIN.value and department_id:
            filter_ = {**filter_, "department_id": department_id}
        return await self.repo.list_all({**filter_, "is_active": True})

    async def get_course(self, current_user: dict, course_id: str) -> CourseResponse:
        doc = await self.repo.get_by_id_or_404(course_id)
        ensure_department_access(current_user, doc["department_id"])
        return await self._to_response(doc)

    async def create_course(self, current_user: dict, payload: CourseCreate) -> CourseResponse:
        ensure_department_access(current_user, payload.department_id)

        if not await DepartmentRepository().find_by_id(payload.department_id):
            raise ValidationException("The selected department does not exist")
        if await self.repo.find_by_code(payload.code):
            raise DuplicateException(f"A course with code '{payload.code}' already exists")

        model = CourseModel(**payload.model_dump())
        doc = await self.repo.insert(model.model_dump(), actor_id=current_user["id"])
        return await self._to_response(doc)

    async def update_course(self, current_user: dict, course_id: str, payload: CourseUpdate) -> CourseResponse:
        existing = await self.repo.get_by_id_or_404(course_id)
        ensure_department_access(current_user, existing["department_id"])
        update_data = payload.model_dump(exclude_unset=True)
        doc = await self.repo.update(course_id, update_data, actor_id=current_user["id"])
        return await self._to_response(doc)

    async def delete_course(self, current_user: dict, course_id: str) -> None:
        existing = await self.repo.get_by_id_or_404(course_id)
        ensure_department_access(current_user, existing["department_id"])
        if await SubjectRepository().exists({"course_id": course_id, "is_active": True}):
            raise ValidationException("This course still has subjects defined under it. Remove them first.")
        if await SectionRepository().exists({"course_id": course_id, "is_active": True}):
            raise ValidationException("This course still has sections defined under it. Remove them first.")
        await self.repo.soft_delete(course_id, actor_id=current_user["id"])

    async def restore_course(self, current_user: dict, course_id: str) -> CourseResponse:
        existing = await self.repo.get_by_id_or_404(course_id)
        ensure_department_access(current_user, existing["department_id"])
        doc = await self.repo.restore(course_id, actor_id=current_user["id"])
        return await self._to_response(doc)


class SubjectService:
    def __init__(self):
        self.repo = SubjectRepository()

    async def _to_response(self, doc: dict) -> SubjectResponse:
        course = await CourseRepository().find_by_id(doc["course_id"])
        course_ref = RefSummary(id=course["id"], name=course["name"]) if course else RefSummary(id=doc["course_id"], name="Unknown")
        return SubjectResponse(**doc, course=course_ref)

    async def list_subjects(self, current_user: dict, pagination: PaginationParams, course_id: str | None = None, include_inactive: bool = False):
        filter_ = _scope_filter(current_user)
        if course_id:
            filter_ = {**filter_, "course_id": course_id}
        docs, total = await self.repo.list_paginated(pagination, extra_filter=filter_, include_inactive=include_inactive)
        items = [await self._to_response(doc) for doc in docs]
        return items, build_meta(pagination, total)

    async def get_subject(self, current_user: dict, subject_id: str) -> SubjectResponse:
        doc = await self.repo.get_by_id_or_404(subject_id)
        ensure_department_access(current_user, doc["department_id"])
        return await self._to_response(doc)

    async def create_subject(self, current_user: dict, payload: SubjectCreate) -> SubjectResponse:
        course = await CourseRepository().find_by_id(payload.course_id)
        if not course:
            raise ValidationException("The selected course does not exist")
        ensure_department_access(current_user, course["department_id"])

        if payload.semester_number > course["total_semesters"]:
            raise ValidationException(
                f"Semester {payload.semester_number} is beyond this course's {course['total_semesters']} semesters"
            )
        if await self.repo.find_by_code(payload.code):
            raise DuplicateException(f"A subject with code '{payload.code}' already exists")

        model = SubjectModel(**payload.model_dump(), department_id=course["department_id"])
        doc = await self.repo.insert(model.model_dump(mode="json"), actor_id=current_user["id"])
        return await self._to_response(doc)

    async def update_subject(self, current_user: dict, subject_id: str, payload: SubjectUpdate) -> SubjectResponse:
        existing = await self.repo.get_by_id_or_404(subject_id)
        ensure_department_access(current_user, existing["department_id"])

        update_data = payload.model_dump(exclude_unset=True, mode="json")
        if "semester_number" in update_data:
            course = await CourseRepository().find_by_id(existing["course_id"])
            if course and update_data["semester_number"] > course["total_semesters"]:
                raise ValidationException(
                    f"Semester {update_data['semester_number']} is beyond this course's {course['total_semesters']} semesters"
                )

        doc = await self.repo.update(subject_id, update_data, actor_id=current_user["id"])
        return await self._to_response(doc)

    async def delete_subject(self, current_user: dict, subject_id: str) -> None:
        existing = await self.repo.get_by_id_or_404(subject_id)
        ensure_department_access(current_user, existing["department_id"])
        await self.repo.soft_delete(subject_id, actor_id=current_user["id"])

    async def restore_subject(self, current_user: dict, subject_id: str) -> SubjectResponse:
        existing = await self.repo.get_by_id_or_404(subject_id)
        ensure_department_access(current_user, existing["department_id"])
        doc = await self.repo.restore(subject_id, actor_id=current_user["id"])
        return await self._to_response(doc)


class SectionService:
    def __init__(self):
        self.repo = SectionRepository()

    async def _to_response(self, doc: dict) -> SectionResponse:
        course = await CourseRepository().find_by_id(doc["course_id"])
        year = await AcademicYearRepository().find_by_id(doc["academic_year_id"])
        semester = await SemesterRepository().find_by_id(doc["semester_id"])

        course_ref = RefSummary(id=course["id"], name=course["name"]) if course else RefSummary(id=doc["course_id"], name="Unknown")
        year_ref = RefSummary(id=year["id"], name=year["name"]) if year else RefSummary(id=doc["academic_year_id"], name="Unknown")
        semester_ref = RefSummary(id=semester["id"], name=semester["name"]) if semester else RefSummary(id=doc["semester_id"], name="Unknown")

        advisor_ref = None
        if doc.get("class_advisor_id"):
            advisor = await FacultyRepository().find_by_id(doc["class_advisor_id"])
            if advisor:
                advisor_ref = RefSummary(id=advisor["id"], name=advisor["name"])

        room_ref = None
        if doc.get("room_id"):
            room = await RoomRepository().find_by_id(doc["room_id"])
            if room:
                room_ref = RefSummary(id=room["id"], name=room["room_number"])

        display_name = f"{course_ref.name} - {doc['section_name']} ({year_ref.name})"

        return SectionResponse(
            **doc,
            course=course_ref,
            academic_year=year_ref,
            semester=semester_ref,
            display_name=display_name,
            class_advisor=advisor_ref,
            room=room_ref,
        )

    async def list_sections(
        self,
        current_user: dict,
        pagination: PaginationParams,
        course_id: str | None = None,
        academic_year_id: str | None = None,
        include_inactive: bool = False,
    ):
        filter_ = _scope_filter(current_user)
        if course_id:
            filter_ = {**filter_, "course_id": course_id}
        if academic_year_id:
            filter_ = {**filter_, "academic_year_id": academic_year_id}
        docs, total = await self.repo.list_paginated(pagination, extra_filter=filter_, include_inactive=include_inactive)
        items = [await self._to_response(doc) for doc in docs]
        return items, build_meta(pagination, total)

    async def get_section(self, current_user: dict, section_id: str) -> SectionResponse:
        doc = await self.repo.get_by_id_or_404(section_id)
        ensure_department_access(current_user, doc["department_id"])
        return await self._to_response(doc)

    async def _validate_references(self, payload: SectionCreate | SectionUpdate, course: dict) -> None:
        if payload.class_advisor_id:
            advisor = await FacultyRepository().find_by_id(payload.class_advisor_id)
            if not advisor:
                raise ValidationException("The selected class advisor does not exist")
            if advisor["department_id"] != course["department_id"]:
                raise ValidationException("The class advisor must belong to the same department as the course")
        if payload.room_id and not await RoomRepository().find_by_id(payload.room_id):
            raise ValidationException("The selected room does not exist")

    async def create_section(self, current_user: dict, payload: SectionCreate) -> SectionResponse:
        course = await CourseRepository().find_by_id(payload.course_id)
        if not course:
            raise ValidationException("The selected course does not exist")
        ensure_department_access(current_user, course["department_id"])

        year = await AcademicYearRepository().find_by_id(payload.academic_year_id)
        if not year:
            raise ValidationException("The selected academic year does not exist")

        semester = await SemesterRepository().find_by_id(payload.semester_id)
        if not semester:
            raise ValidationException("The selected semester does not exist")
        if semester["academic_year_id"] != payload.academic_year_id:
            raise ValidationException("The selected semester does not belong to the selected academic year")

        if payload.semester_number > course["total_semesters"]:
            raise ValidationException(
                f"Semester {payload.semester_number} is beyond this course's {course['total_semesters']} semesters"
            )

        await self._validate_references(payload, course)

        if await self.repo.find_duplicate(payload.course_id, payload.academic_year_id, payload.semester_id, payload.section_name):
            raise DuplicateException(
                f"Section '{payload.section_name}' already exists for this course, academic year and semester"
            )

        model = SectionModel(**payload.model_dump(), department_id=course["department_id"])
        doc = await self.repo.insert(model.model_dump(), actor_id=current_user["id"])
        return await self._to_response(doc)

    async def update_section(self, current_user: dict, section_id: str, payload: SectionUpdate) -> SectionResponse:
        existing = await self.repo.get_by_id_or_404(section_id)
        ensure_department_access(current_user, existing["department_id"])

        course = await CourseRepository().find_by_id(existing["course_id"])
        await self._validate_references(payload, course)

        update_data = payload.model_dump(exclude_unset=True)
        doc = await self.repo.update(section_id, update_data, actor_id=current_user["id"])
        return await self._to_response(doc)

    async def delete_section(self, current_user: dict, section_id: str) -> None:
        existing = await self.repo.get_by_id_or_404(section_id)
        ensure_department_access(current_user, existing["department_id"])
        await self.repo.soft_delete(section_id, actor_id=current_user["id"])

    async def restore_section(self, current_user: dict, section_id: str) -> SectionResponse:
        existing = await self.repo.get_by_id_or_404(section_id)
        ensure_department_access(current_user, existing["department_id"])
        doc = await self.repo.restore(section_id, actor_id=current_user["id"])
        return await self._to_response(doc)

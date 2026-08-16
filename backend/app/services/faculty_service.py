from app.auth.dependencies import ensure_department_access
from app.core.constants import UserRole
from app.core.exceptions import DuplicateException, ValidationException
from app.models.faculty import FacultyModel
from app.repositories.department_repository import DepartmentRepository
from app.repositories.faculty_repository import FacultyRepository
from app.schemas.common import RefSummary
from app.schemas.faculty import FacultyCreate, FacultyResponse, FacultyUpdate
from app.utils.pagination import PaginationParams, build_meta


class FacultyService:
    def __init__(self):
        self.repo = FacultyRepository()

    async def _to_response(self, doc: dict) -> FacultyResponse:
        dept = await DepartmentRepository().find_by_id(doc["department_id"])
        department = RefSummary(id=dept["id"], name=dept["name"]) if dept else RefSummary(id=doc["department_id"], name="Unknown")
        return FacultyResponse(**doc, department=department)

    @staticmethod
    def _scope_filter(current_user: dict) -> dict:
        if current_user["role"] == UserRole.SUPER_ADMIN.value:
            return {}
        return {"department_id": current_user["department_id"]}

    async def list_faculty(self, current_user: dict, pagination: PaginationParams, department_id: str | None = None, include_inactive: bool = False):
        filter_ = self._scope_filter(current_user)
        if current_user["role"] == UserRole.SUPER_ADMIN.value and department_id:
            filter_ = {**filter_, "department_id": department_id}
        docs, total = await self.repo.list_paginated(pagination, extra_filter=filter_, include_inactive=include_inactive)
        items = [await self._to_response(doc) for doc in docs]
        return items, build_meta(pagination, total)

    async def get_faculty(self, current_user: dict, faculty_id: str) -> FacultyResponse:
        doc = await self.repo.get_by_id_or_404(faculty_id)
        ensure_department_access(current_user, doc["department_id"])
        return await self._to_response(doc)

    async def create_faculty(self, current_user: dict, payload: FacultyCreate) -> FacultyResponse:
        ensure_department_access(current_user, payload.department_id)

        department = await DepartmentRepository().find_by_id(payload.department_id)
        if not department:
            raise ValidationException("The selected department does not exist")

        if await self.repo.find_by_email(payload.email):
            raise DuplicateException(f"A faculty member with email '{payload.email}' already exists")
        if await self.repo.find_by_employee_code(payload.employee_code):
            raise DuplicateException(f"A faculty member with employee code '{payload.employee_code}' already exists")

        model = FacultyModel(**payload.model_dump())
        doc = await self.repo.insert(model.model_dump(mode="json"), actor_id=current_user["id"])
        return await self._to_response(doc)

    async def update_faculty(self, current_user: dict, faculty_id: str, payload: FacultyUpdate) -> FacultyResponse:
        existing = await self.repo.get_by_id_or_404(faculty_id)
        ensure_department_access(current_user, existing["department_id"])

        update_data = payload.model_dump(exclude_unset=True, mode="json")
        doc = await self.repo.update(faculty_id, update_data, actor_id=current_user["id"])
        return await self._to_response(doc)

    async def delete_faculty(self, current_user: dict, faculty_id: str) -> None:
        existing = await self.repo.get_by_id_or_404(faculty_id)
        ensure_department_access(current_user, existing["department_id"])
        await self.repo.soft_delete(faculty_id, actor_id=current_user["id"])

    async def restore_faculty(self, current_user: dict, faculty_id: str) -> FacultyResponse:
        existing = await self.repo.get_by_id_or_404(faculty_id)
        ensure_department_access(current_user, existing["department_id"])
        doc = await self.repo.restore(faculty_id, actor_id=current_user["id"])
        return await self._to_response(doc)

    async def list_lookup(self, current_user: dict, department_id: str | None = None) -> list[dict]:
        filter_ = self._scope_filter(current_user)
        if current_user["role"] == UserRole.SUPER_ADMIN.value and department_id:
            filter_ = {**filter_, "department_id": department_id}
        filter_ = {**filter_, "is_active": True}
        return await self.repo.list_all(filter_)

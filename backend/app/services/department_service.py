from app.core.constants import Collections
from app.core.exceptions import DuplicateException, ValidationException
from app.database.connection import get_database
from app.models.department import DepartmentModel
from app.repositories.department_repository import DepartmentRepository
from app.repositories.user_repository import UserRepository
from app.schemas.common import RefSummary
from app.schemas.department import DepartmentCreate, DepartmentResponse, DepartmentUpdate
from app.utils.pagination import PaginationParams, build_meta


class DepartmentService:
    def __init__(self):
        self.repo = DepartmentRepository()

    async def _to_response(self, doc: dict, with_counts: bool = True) -> DepartmentResponse:
        hod = None
        if doc.get("hod_id"):
            hod_user = await UserRepository().find_by_id(doc["hod_id"])
            if hod_user:
                hod = RefSummary(id=hod_user["id"], name=hod_user["name"])

        counts = {"faculty_count": 0, "course_count": 0, "section_count": 0}
        if with_counts:
            counts = await self._get_counts(doc["id"])

        return DepartmentResponse(**doc, hod=hod, **counts)

    @staticmethod
    async def _get_counts(department_id: str) -> dict:
        db = get_database()
        faculty_count = await db[Collections.FACULTY].count_documents({"department_id": department_id, "is_active": True})
        course_count = await db[Collections.COURSES].count_documents({"department_id": department_id, "is_active": True})
        section_count = await db[Collections.SECTIONS].count_documents({"department_id": department_id, "is_active": True})
        return {"faculty_count": faculty_count, "course_count": course_count, "section_count": section_count}

    async def list_departments(self, pagination: PaginationParams, include_inactive: bool = False) -> tuple[list[DepartmentResponse], dict]:
        docs, total = await self.repo.list_paginated(pagination, include_inactive=include_inactive)
        items = [await self._to_response(doc) for doc in docs]
        return items, build_meta(pagination, total)

    async def list_all_active(self) -> list[dict]:
        """Lightweight lookup list for dropdowns (id + name only upstream)."""
        return await self.repo.list_all({"is_active": True})

    async def get_department(self, department_id: str) -> DepartmentResponse:
        doc = await self.repo.get_by_id_or_404(department_id)
        return await self._to_response(doc)

    async def create_department(self, current_user: dict, payload: DepartmentCreate) -> DepartmentResponse:
        if await self.repo.find_by_code(payload.code):
            raise DuplicateException(f"A department with code '{payload.code}' already exists")
        if await self.repo.find_by_name(payload.name):
            raise DuplicateException(f"A department named '{payload.name}' already exists")

        model = DepartmentModel(
            name=payload.name,
            code=payload.code,
            description=payload.description,
            established_year=payload.established_year,
        )
        doc = await self.repo.insert(model.model_dump(), actor_id=current_user["id"])
        return await self._to_response(doc, with_counts=False)

    async def update_department(self, current_user: dict, department_id: str, payload: DepartmentUpdate) -> DepartmentResponse:
        existing = await self.repo.get_by_id_or_404(department_id)

        update_data = payload.model_dump(exclude_unset=True)

        if "code" in update_data and update_data["code"] != existing["code"]:
            if await self.repo.find_by_code(update_data["code"]):
                raise DuplicateException(f"A department with code '{update_data['code']}' already exists")

        if "name" in update_data and update_data["name"] != existing["name"]:
            if await self.repo.find_by_name(update_data["name"]):
                raise DuplicateException(f"A department named '{update_data['name']}' already exists")

        if "hod_id" in update_data and update_data["hod_id"]:
            hod_user = await UserRepository().find_by_id(update_data["hod_id"])
            if not hod_user:
                raise ValidationException("The selected HOD user does not exist")
            if hod_user["role"] != "hod":
                raise ValidationException("The selected user does not have the HOD role")
            if hod_user.get("department_id") != department_id:
                raise ValidationException("The selected HOD must belong to this department")

        doc = await self.repo.update(department_id, update_data, actor_id=current_user["id"])
        return await self._to_response(doc)

    async def delete_department(self, current_user: dict, department_id: str) -> None:
        await self.repo.get_by_id_or_404(department_id)
        counts = await self._get_counts(department_id)
        if any(counts.values()):
            raise ValidationException(
                "This department still has faculty, courses or sections assigned to it. "
                "Reassign or remove them before deleting the department."
            )
        await self.repo.soft_delete(department_id, actor_id=current_user["id"])

    async def restore_department(self, current_user: dict, department_id: str) -> DepartmentResponse:
        doc = await self.repo.restore(department_id, actor_id=current_user["id"])
        return await self._to_response(doc)

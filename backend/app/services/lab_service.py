from app.auth.dependencies import ensure_department_access
from app.core.constants import Collections
from app.core.exceptions import DuplicateException, ValidationException
from app.database.connection import get_database
from app.models.lab import LabModel
from app.repositories.department_repository import DepartmentRepository
from app.repositories.lab_repository import LabRepository
from app.schemas.common import RefSummary
from app.schemas.lab import LabCreate, LabResponse, LabUpdate
from app.utils.pagination import PaginationParams, build_meta


class LabService:
    def __init__(self):
        self.repo = LabRepository()

    async def _to_response(self, doc: dict) -> LabResponse:
        dept = await DepartmentRepository().find_by_id(doc["department_id"])
        department = RefSummary(id=dept["id"], name=dept["name"]) if dept else RefSummary(id=doc["department_id"], name="Unknown")
        return LabResponse(**doc, department=department)

    async def list_labs(self, current_user: dict, pagination: PaginationParams, department_id: str | None = None, include_inactive: bool = False):
        filter_ = {}
        if department_id:
            filter_["department_id"] = department_id
        docs, total = await self.repo.list_paginated(pagination, extra_filter=filter_, include_inactive=include_inactive)
        items = [await self._to_response(doc) for doc in docs]
        return items, build_meta(pagination, total)

    async def list_all_active(self, department_id: str | None = None) -> list[dict]:
        filter_ = {"is_active": True}
        if department_id:
            filter_["department_id"] = department_id
        return await self.repo.list_all(filter_)

    async def get_lab(self, lab_id: str) -> LabResponse:
        doc = await self.repo.get_by_id_or_404(lab_id)
        return await self._to_response(doc)

    async def create_lab(self, current_user: dict, payload: LabCreate) -> LabResponse:
        ensure_department_access(current_user, payload.department_id)

        if not await DepartmentRepository().find_by_id(payload.department_id):
            raise ValidationException("The selected department does not exist")
        if await self.repo.find_by_room_number(payload.room_number):
            raise DuplicateException(f"A laboratory with room number '{payload.room_number}' already exists")

        model = LabModel(**payload.model_dump())
        doc = await self.repo.insert(model.model_dump(), actor_id=current_user["id"])
        return await self._to_response(doc)

    async def update_lab(self, current_user: dict, lab_id: str, payload: LabUpdate) -> LabResponse:
        existing = await self.repo.get_by_id_or_404(lab_id)
        ensure_department_access(current_user, existing["department_id"])
        update_data = payload.model_dump(exclude_unset=True)
        doc = await self.repo.update(lab_id, update_data, actor_id=current_user["id"])
        return await self._to_response(doc)

    async def delete_lab(self, current_user: dict, lab_id: str) -> None:
        existing = await self.repo.get_by_id_or_404(lab_id)
        ensure_department_access(current_user, existing["department_id"])
        db = get_database()
        if await db[Collections.SECTIONS].count_documents({"room_id": lab_id, "is_active": True}, limit=1):
            raise ValidationException("This laboratory is assigned to one or more sections. Reassign them first.")
        await self.repo.soft_delete(lab_id, actor_id=current_user["id"])

    async def restore_lab(self, current_user: dict, lab_id: str) -> LabResponse:
        existing = await self.repo.get_by_id_or_404(lab_id)
        ensure_department_access(current_user, existing["department_id"])
        doc = await self.repo.restore(lab_id, actor_id=current_user["id"])
        return await self._to_response(doc)

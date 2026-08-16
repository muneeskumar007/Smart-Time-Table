from app.auth.security import hash_password, verify_password
from app.core.constants import UserRole
from app.core.exceptions import AuthorizationException, DuplicateException, ValidationException
from app.models.user import UserModel
from app.repositories.academic_structure_repository import SectionRepository
from app.repositories.department_repository import DepartmentRepository
from app.repositories.user_repository import UserRepository
from app.schemas.common import RefSummary
from app.schemas.user import (
    AdminResetPasswordRequest,
    ChangePasswordRequest,
    SelfProfileUpdate,
    UserCreate,
    UserResponse,
    UserUpdate,
)
from app.utils.pagination import PaginationParams, build_meta


class UserService:
    def __init__(self):
        self.repo = UserRepository()

    async def _to_response(self, doc: dict) -> UserResponse:
        department = None
        if doc.get("department_id"):
            dept = await DepartmentRepository().find_by_id(doc["department_id"])
            if dept:
                department = RefSummary(id=dept["id"], name=dept["name"])
        section = None
        if doc.get("section_id"):
            sec = await SectionRepository().find_by_id(doc["section_id"])
            if sec:
                section = RefSummary(id=sec["id"], name=sec["section_name"])
        return UserResponse(**doc, department=department, section=section)

    @staticmethod
    def _scope_filter(current_user: dict) -> dict:
        """Super Admin sees everyone; a HOD only ever sees users in their
        own department."""
        if current_user["role"] == UserRole.SUPER_ADMIN.value:
            return {}
        return {"department_id": current_user["department_id"]}

    @staticmethod
    def _assert_can_manage(current_user: dict, target_role: UserRole, target_department_id: str | None) -> None:
        if current_user["role"] == UserRole.SUPER_ADMIN.value:
            return
        if current_user["role"] == UserRole.HOD.value:
            if target_role in (UserRole.SUPER_ADMIN, UserRole.HOD):
                raise AuthorizationException("HODs may only manage Faculty and Student accounts")
            if target_department_id != current_user["department_id"]:
                raise AuthorizationException("You can only manage users within your own department")
            return
        raise AuthorizationException()

    async def list_users(self, current_user: dict, pagination: PaginationParams, role_filter: str | None = None, include_inactive: bool = False):
        filter_ = self._scope_filter(current_user)
        if role_filter:
            filter_ = {**filter_, "role": role_filter}
        docs, total = await self.repo.list_paginated(pagination, extra_filter=filter_, include_inactive=include_inactive)
        items = [await self._to_response(doc) for doc in docs]
        return items, build_meta(pagination, total)

    async def get_user(self, current_user: dict, user_id: str) -> UserResponse:
        doc = await self.repo.get_by_id_or_404(user_id)
        self._assert_can_manage(current_user, UserRole(doc["role"]), doc.get("department_id"))
        return await self._to_response(doc)

    async def create_user(self, current_user: dict, payload: UserCreate) -> UserResponse:
        self._assert_can_manage(current_user, payload.role, payload.department_id)

        if await self.repo.find_by_email(payload.email):
            raise DuplicateException(f"A user with email '{payload.email}' already exists")

        if payload.department_id:
            department = await DepartmentRepository().find_by_id(payload.department_id)
            if not department:
                raise ValidationException("The selected department does not exist")

        if payload.section_id:
            section = await SectionRepository().find_by_id(payload.section_id)
            if not section:
                raise ValidationException("The selected section does not exist")
            if section["department_id"] != payload.department_id:
                raise ValidationException("The selected section must belong to the student's department")

        model = UserModel(
            name=payload.name,
            email=payload.email.strip().lower(),
            password_hash=hash_password(payload.password),
            role=payload.role,
            department_id=payload.department_id,
            section_id=payload.section_id,
            phone=payload.phone,
        )
        doc = await self.repo.insert(model.model_dump(mode="json"), actor_id=current_user["id"])
        return await self._to_response(doc)

    async def update_user(self, current_user: dict, user_id: str, payload: UserUpdate) -> UserResponse:
        existing = await self.repo.get_by_id_or_404(user_id)
        self._assert_can_manage(current_user, UserRole(existing["role"]), existing.get("department_id"))

        update_data = payload.model_dump(exclude_unset=True, mode="json")

        new_role = UserRole(update_data["role"]) if "role" in update_data else UserRole(existing["role"])
        new_department_id = update_data.get("department_id", existing.get("department_id"))
        self._assert_can_manage(current_user, new_role, new_department_id)

        needs_department = new_role in (UserRole.HOD, UserRole.FACULTY, UserRole.STUDENT)
        if needs_department and not new_department_id:
            raise ValidationException(f"A department is required for the '{new_role.value}' role")
        if new_role == UserRole.SUPER_ADMIN and new_department_id:
            raise ValidationException("Super Admin accounts must not be assigned to a department")

        if "department_id" in update_data and update_data["department_id"]:
            department = await DepartmentRepository().find_by_id(update_data["department_id"])
            if not department:
                raise ValidationException("The selected department does not exist")

        if "section_id" in update_data and update_data["section_id"]:
            if new_role != UserRole.STUDENT:
                raise ValidationException("Only Student accounts may be assigned to a section")
            section = await SectionRepository().find_by_id(update_data["section_id"])
            if not section:
                raise ValidationException("The selected section does not exist")
            if section["department_id"] != new_department_id:
                raise ValidationException("The selected section must belong to the student's department")

        doc = await self.repo.update(user_id, update_data, actor_id=current_user["id"])
        return await self._to_response(doc)

    async def delete_user(self, current_user: dict, user_id: str) -> None:
        existing = await self.repo.get_by_id_or_404(user_id)
        self._assert_can_manage(current_user, UserRole(existing["role"]), existing.get("department_id"))

        if existing["id"] == current_user["id"]:
            raise ValidationException("You cannot delete your own account")

        dept_hod = await DepartmentRepository().find_one({"hod_id": user_id})
        if dept_hod:
            raise ValidationException(
                f"This user is set as the HOD of '{dept_hod['name']}'. Unassign them first."
            )

        await self.repo.soft_delete(user_id, actor_id=current_user["id"])

    async def restore_user(self, current_user: dict, user_id: str) -> UserResponse:
        existing = await self.repo.get_by_id_or_404(user_id)
        self._assert_can_manage(current_user, UserRole(existing["role"]), existing.get("department_id"))
        doc = await self.repo.restore(user_id, actor_id=current_user["id"])
        return await self._to_response(doc)

    # --- self-service -------------------------------------------------

    async def get_my_profile(self, current_user: dict) -> UserResponse:
        return await self._to_response(current_user)

    async def update_my_profile(self, current_user: dict, payload: SelfProfileUpdate) -> UserResponse:
        update_data = payload.model_dump(exclude_unset=True)
        doc = await self.repo.update(current_user["id"], update_data, actor_id=current_user["id"])
        return await self._to_response(doc)

    async def change_my_password(self, current_user: dict, payload: ChangePasswordRequest) -> None:
        if not verify_password(payload.current_password, current_user["password_hash"]):
            raise ValidationException("Current password is incorrect")
        new_hash = hash_password(payload.new_password)
        await self.repo.set_password_hash(current_user["id"], new_hash)
        # Changing your password invalidates every other logged-in session
        # as a security precaution.
        await self.repo.clear_all_sessions(current_user["id"])

    async def admin_reset_password(self, current_user: dict, user_id: str, payload: AdminResetPasswordRequest) -> None:
        existing = await self.repo.get_by_id_or_404(user_id)
        self._assert_can_manage(current_user, UserRole(existing["role"]), existing.get("department_id"))
        new_hash = hash_password(payload.new_password)
        await self.repo.set_password_hash(user_id, new_hash)
        await self.repo.clear_all_sessions(user_id)

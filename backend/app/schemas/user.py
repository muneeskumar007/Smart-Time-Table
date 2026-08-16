import re
from datetime import datetime

from pydantic import BaseModel, EmailStr, Field, field_validator, model_validator

from app.core.constants import MAX_PASSWORD_LENGTH, MIN_PASSWORD_LENGTH, UserRole
from app.schemas.common import RefSummary, TimestampedResponse

PHONE_PATTERN = re.compile(r"^\+?[0-9\s\-()]{7,20}$")


def _validate_password_strength(v: str) -> str:
    if len(v) < MIN_PASSWORD_LENGTH:
        raise ValueError(f"Password must be at least {MIN_PASSWORD_LENGTH} characters long")
    if len(v) > MAX_PASSWORD_LENGTH:
        raise ValueError(f"Password must be at most {MAX_PASSWORD_LENGTH} characters long")
    if not re.search(r"[A-Za-z]", v):
        raise ValueError("Password must contain at least one letter")
    if not re.search(r"[0-9]", v):
        raise ValueError("Password must contain at least one number")
    return v


class UserCreate(BaseModel):
    name: str = Field(..., min_length=2, max_length=150)
    email: EmailStr
    password: str
    role: UserRole
    department_id: str | None = None
    section_id: str | None = None
    phone: str | None = Field(None, max_length=20)

    @field_validator("password")
    @classmethod
    def password_strength(cls, v: str) -> str:
        return _validate_password_strength(v)

    @field_validator("phone")
    @classmethod
    def phone_format(cls, v: str | None) -> str | None:
        if v and not PHONE_PATTERN.match(v):
            raise ValueError("Phone number format is invalid")
        return v

    @model_validator(mode="after")
    def department_requirement(self):
        needs_department = self.role in (UserRole.HOD, UserRole.FACULTY, UserRole.STUDENT)
        if needs_department and not self.department_id:
            raise ValueError(f"A department is required for the '{self.role.value}' role")
        if self.role == UserRole.SUPER_ADMIN and self.department_id:
            raise ValueError("Super Admin accounts must not be assigned to a department")
        if self.section_id and self.role != UserRole.STUDENT:
            raise ValueError("Only Student accounts may be assigned to a section")
        return self


class UserUpdate(BaseModel):
    name: str | None = Field(None, min_length=2, max_length=150)
    role: UserRole | None = None
    department_id: str | None = None
    section_id: str | None = None
    phone: str | None = Field(None, max_length=20)
    is_active: bool | None = None

    @field_validator("phone")
    @classmethod
    def phone_format(cls, v: str | None) -> str | None:
        if v and not PHONE_PATTERN.match(v):
            raise ValueError("Phone number format is invalid")
        return v


class SelfProfileUpdate(BaseModel):
    """What a logged-in user may change about their own account - a
    deliberately smaller surface than UserUpdate (no role/department/
    active-status changes here, only what the roles table promises:
    'update profile')."""
    name: str | None = Field(None, min_length=2, max_length=150)
    phone: str | None = Field(None, max_length=20)

    @field_validator("phone")
    @classmethod
    def phone_format(cls, v: str | None) -> str | None:
        if v and not PHONE_PATTERN.match(v):
            raise ValueError("Phone number format is invalid")
        return v


class ChangePasswordRequest(BaseModel):
    current_password: str
    new_password: str

    @field_validator("new_password")
    @classmethod
    def password_strength(cls, v: str) -> str:
        return _validate_password_strength(v)


class AdminResetPasswordRequest(BaseModel):
    """Super Admin / HOD setting a new password for someone else (e.g. a
    forgotten-password recovery flow) - deliberately requires no
    knowledge of the old password, unlike ChangePasswordRequest."""
    new_password: str

    @field_validator("new_password")
    @classmethod
    def password_strength(cls, v: str) -> str:
        return _validate_password_strength(v)


class UserResponse(TimestampedResponse):
    name: str
    email: str
    role: UserRole
    department: RefSummary | None = None
    section: RefSummary | None = None
    phone: str | None
    is_active: bool
    last_login: datetime | None = None

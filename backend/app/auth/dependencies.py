"""
Authentication & authorization dependencies.

    current_user = Depends(get_current_user)                  # any authenticated user
    current_user = Depends(require_roles(UserRole.SUPER_ADMIN))  # role-gated

`current_user` is the plain dict returned by UserRepository (never the
raw password hash's caller-facing shape - see UserResponse for that).
"""
from fastapi import Depends
from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer

from app.auth.jwt_handler import TokenError, decode_token
from app.core.constants import UserRole
from app.core.exceptions import AuthenticationException, AuthorizationException
from app.repositories.user_repository import UserRepository

_bearer_scheme = HTTPBearer(auto_error=False, description="Paste the access token returned by POST /auth/login")


async def get_current_user(
    credentials: HTTPAuthorizationCredentials | None = Depends(_bearer_scheme),
) -> dict:
    if credentials is None or not credentials.credentials:
        raise AuthenticationException("Missing authentication credentials")

    try:
        payload = decode_token(credentials.credentials, expected_type="access")
    except TokenError as exc:
        raise AuthenticationException(str(exc)) from exc

    user = await UserRepository().find_by_id(payload["sub"])
    if user is None:
        raise AuthenticationException("This account no longer exists")
    if not user["is_active"]:
        raise AuthenticationException("This account has been deactivated")

    return user


def require_roles(*allowed_roles: UserRole):
    """Dependency factory: restricts an endpoint to the given roles."""

    async def dependency(current_user: dict = Depends(get_current_user)) -> dict:
        if current_user["role"] not in {role.value for role in allowed_roles}:
            raise AuthorizationException()
        return current_user

    return dependency


def ensure_department_access(current_user: dict, resource_department_id: str | None) -> None:
    """Raise 403 unless the current user is a Super Admin or the resource
    belongs to their own department. Used inside services for entities
    (Faculty, Courses, Subjects, Sections, department-scoped Time Slots)
    that a HOD may only manage within their own department."""
    if current_user["role"] == UserRole.SUPER_ADMIN.value:
        return
    if current_user["role"] == UserRole.HOD.value and current_user.get("department_id") == resource_department_id:
        return
    raise AuthorizationException("You can only manage resources within your own department")

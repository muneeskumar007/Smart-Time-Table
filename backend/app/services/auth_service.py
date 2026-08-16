"""
Authentication service.

Token strategy:
  * Access token: short-lived (default 30 min), returned in the JSON body,
    kept in memory only on the frontend (never persisted to storage) and
    sent as `Authorization: Bearer <token>`.
  * Refresh token: longer-lived (default 7 days, or 30 with "remember
    me"), set as an httpOnly cookie so frontend JS never touches it -
    this is what protects it from theft via XSS. Each refresh token's
    `jti` is recorded in the user's `sessions` list so it can be revoked
    (logout) and is rotated (replaced) on every use, so a stolen refresh
    token that gets used is immediately invalidated for its legitimate
    owner too - a signal worth building alerting on in a later phase.
"""
from datetime import datetime, timezone

from app.auth.jwt_handler import (
    TokenError,
    create_access_token,
    create_refresh_token,
    decode_token,
    generate_refresh_token_id,
)
from app.auth.security import DUMMY_HASH, verify_password
from app.config.settings import get_settings
from app.core.exceptions import AuthenticationException
from app.repositories.user_repository import UserRepository
from app.schemas.auth import LoginRequest, TokenResponse
from app.schemas.user import UserResponse


class AuthService:
    def __init__(self):
        self.repo = UserRepository()
        self.settings = get_settings()

    async def _authenticate(self, email: str, password: str) -> dict:
        user = await self.repo.find_by_email(email)
        if user is None:
            # Still run a hash comparison so response timing doesn't
            # reveal whether the email exists (mitigates account
            # enumeration via timing attacks).
            verify_password(password, DUMMY_HASH)
            raise AuthenticationException("Incorrect email or password")

        if not verify_password(password, user["password_hash"]):
            raise AuthenticationException("Incorrect email or password")

        if not user["is_active"]:
            raise AuthenticationException("This account has been deactivated. Contact your administrator.")

        return user

    async def _to_user_response(self, user: dict) -> UserResponse:
        # Local import avoids a circular dependency (department_service
        # already imports from this auth module's neighbours).
        from app.repositories.department_repository import DepartmentRepository
        from app.schemas.common import RefSummary

        department = None
        if user.get("department_id"):
            dept = await DepartmentRepository().find_by_id(user["department_id"])
            if dept:
                department = RefSummary(id=dept["id"], name=dept["name"])
        return UserResponse(**user, department=department)

    async def _issue_tokens(self, user: dict, remember_me: bool, user_agent: str | None) -> tuple[TokenResponse, str, int]:
        access_token = create_access_token(user["id"], user["role"])
        refresh_token = create_refresh_token(user["id"], user["role"], remember_me=remember_me)
        payload = decode_token(refresh_token, expected_type="refresh")

        days = (
            self.settings.REFRESH_TOKEN_EXPIRE_DAYS_REMEMBER_ME
            if remember_me
            else self.settings.REFRESH_TOKEN_EXPIRE_DAYS
        )
        max_age_seconds = days * 24 * 60 * 60

        session = {
            "jti": payload["jti"],
            "expires_at": datetime.fromtimestamp(payload["exp"], tz=timezone.utc),
            "created_at": datetime.now(timezone.utc),
            "user_agent": (user_agent or "unknown")[:200],
        }
        await self.repo.add_session(user["id"], session, self.settings.MAX_ACTIVE_SESSIONS_PER_USER)

        token_response = TokenResponse(
            access_token=access_token,
            expires_in_minutes=self.settings.ACCESS_TOKEN_EXPIRE_MINUTES,
            user=await self._to_user_response(user),
        )
        return token_response, refresh_token, max_age_seconds

    async def login(self, payload: LoginRequest, user_agent: str | None) -> tuple[TokenResponse, str, int]:
        user = await self._authenticate(payload.email, payload.password)
        await self.repo.set_last_login(user["id"], datetime.now(timezone.utc))
        return await self._issue_tokens(user, payload.remember_me, user_agent)

    async def refresh(self, refresh_token: str, user_agent: str | None) -> tuple[TokenResponse, str, int]:
        try:
            payload = decode_token(refresh_token, expected_type="refresh")
        except TokenError as exc:
            raise AuthenticationException("Your session has expired. Please log in again.") from exc

        user = await self.repo.find_by_id(payload["sub"])
        if user is None or not user["is_active"]:
            raise AuthenticationException("Your session is no longer valid. Please log in again.")

        if not await self.repo.has_session(user["id"], payload["jti"]):
            # Token is validly signed but was already rotated/revoked
            # (logout, password change, or a stolen-token replay).
            raise AuthenticationException("Your session is no longer valid. Please log in again.")

        # Rotate: the old session is atomically swapped for a new one so
        # this exact refresh token cannot be replayed again.
        access_token = create_access_token(user["id"], user["role"])
        remember_me = (payload["exp"] - payload["iat"]) > (self.settings.REFRESH_TOKEN_EXPIRE_DAYS * 24 * 60 * 60)
        new_refresh_token = create_refresh_token(user["id"], user["role"], remember_me=remember_me)
        new_payload = decode_token(new_refresh_token, expected_type="refresh")

        days = self.settings.REFRESH_TOKEN_EXPIRE_DAYS_REMEMBER_ME if remember_me else self.settings.REFRESH_TOKEN_EXPIRE_DAYS
        max_age_seconds = days * 24 * 60 * 60

        new_session = {
            "jti": new_payload["jti"],
            "expires_at": datetime.fromtimestamp(new_payload["exp"], tz=timezone.utc),
            "created_at": datetime.now(timezone.utc),
            "user_agent": (user_agent or "unknown")[:200],
        }
        await self.repo.replace_session(user["id"], payload["jti"], new_session, self.settings.MAX_ACTIVE_SESSIONS_PER_USER)

        token_response = TokenResponse(
            access_token=access_token,
            expires_in_minutes=self.settings.ACCESS_TOKEN_EXPIRE_MINUTES,
            user=await self._to_user_response(user),
        )
        return token_response, new_refresh_token, max_age_seconds

    async def logout(self, refresh_token: str | None) -> None:
        if not refresh_token:
            return
        try:
            payload = decode_token(refresh_token, expected_type="refresh")
        except TokenError:
            # Already invalid/expired - nothing to revoke, and the client
            # is logging out either way, so this is not an error.
            return
        await self.repo.remove_session(payload["sub"], payload["jti"])

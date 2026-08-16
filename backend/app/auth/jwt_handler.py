"""
JWT access & refresh token creation/verification.

IMPORTANT - library choice: the project brief asked for python-jose.
python-jose has had no release since 2021 and has an unpatched CVE
(CVE-2024-33663). FastAPI's own official documentation moved away from
it in favour of PyJWT for exactly this reason. We use PyJWT instead. See
README.md for the full note.
"""
import secrets
import uuid
from datetime import datetime, timedelta, timezone
from typing import Any, Literal

import jwt
from jwt import PyJWTError

from app.config.settings import get_settings

TokenType = Literal["access", "refresh"]


class TokenError(Exception):
    """Raised for any invalid/expired/malformed token. Callers translate
    this into an AuthenticationException (401) - kept separate from that
    exception type so this module has no dependency on FastAPI/core."""


def _create_token(subject: str, role: str, token_type: TokenType, expires_delta: timedelta, extra_claims: dict | None = None) -> str:
    settings = get_settings()
    now = datetime.now(timezone.utc)
    payload: dict[str, Any] = {
        "sub": subject,
        "role": role,
        "type": token_type,
        "iat": now,
        "exp": now + expires_delta,
        "jti": uuid.uuid4().hex,
    }
    if extra_claims:
        payload.update(extra_claims)
    return jwt.encode(payload, settings.JWT_SECRET_KEY, algorithm=settings.JWT_ALGORITHM)


def create_access_token(user_id: str, role: str) -> str:
    settings = get_settings()
    return _create_token(
        subject=user_id,
        role=role,
        token_type="access",
        expires_delta=timedelta(minutes=settings.ACCESS_TOKEN_EXPIRE_MINUTES),
    )


def create_refresh_token(user_id: str, role: str, remember_me: bool = False) -> str:
    settings = get_settings()
    days = settings.REFRESH_TOKEN_EXPIRE_DAYS_REMEMBER_ME if remember_me else settings.REFRESH_TOKEN_EXPIRE_DAYS
    return _create_token(
        subject=user_id,
        role=role,
        token_type="refresh",
        expires_delta=timedelta(days=days),
    )


def decode_token(token: str, expected_type: TokenType) -> dict:
    """Decode and verify a token, checking both the signature/expiry and
    that it is the type of token expected at this call site (an access
    token must never be accepted where a refresh token is required, and
    vice versa)."""
    settings = get_settings()
    try:
        payload = jwt.decode(token, settings.JWT_SECRET_KEY, algorithms=[settings.JWT_ALGORITHM])
    except PyJWTError as exc:
        raise TokenError(f"Invalid or expired token: {exc}") from exc

    if payload.get("type") != expected_type:
        raise TokenError(f"Expected a {expected_type} token")

    return payload


def generate_refresh_token_id() -> str:
    """A random identifier stored alongside a hash of the refresh token in
    the user's session list, so a specific session can be revoked on
    logout without invalidating the user's other logged-in devices."""
    return secrets.token_hex(16)

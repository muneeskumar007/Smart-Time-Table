from fastapi import APIRouter, Depends, Request, Response

from app.auth.dependencies import get_current_user
from app.config.settings import get_settings
from app.core.exceptions import AuthenticationException
from app.middleware.rate_limiter import limiter
from app.schemas.auth import LoginRequest
from app.schemas.user import ChangePasswordRequest, SelfProfileUpdate
from app.services.auth_service import AuthService
from app.services.user_service import UserService
from app.utils.response import success_response

router = APIRouter(prefix="/auth", tags=["Authentication"])

settings = get_settings()
REFRESH_COOKIE_PATH = f"{settings.API_V1_PREFIX}/auth"


def _set_refresh_cookie(response: Response, refresh_token: str, max_age_seconds: int) -> None:
    response.set_cookie(
        key=settings.REFRESH_COOKIE_NAME,
        value=refresh_token,
        max_age=max_age_seconds,
        httponly=True,
        secure=settings.ENVIRONMENT == "production",
        samesite="lax",
        path=REFRESH_COOKIE_PATH,
    )


def _clear_refresh_cookie(response: Response) -> None:
    response.delete_cookie(key=settings.REFRESH_COOKIE_NAME, path=REFRESH_COOKIE_PATH)


@router.post("/login", response_model=None)
@limiter.limit(settings.RATE_LIMIT_LOGIN)
async def login(request: Request, response: Response, payload: LoginRequest):
    token_response, refresh_token, max_age = await AuthService().login(
        payload, user_agent=request.headers.get("user-agent")
    )
    _set_refresh_cookie(response, refresh_token, max_age)
    return success_response(data=token_response, message="Logged in successfully")


@router.post("/refresh", response_model=None)
@limiter.limit(settings.RATE_LIMIT_LOGIN)
async def refresh_token(request: Request, response: Response):
    incoming = request.cookies.get(settings.REFRESH_COOKIE_NAME)
    if not incoming:
        raise AuthenticationException("No active session found. Please log in again.")

    token_response, new_refresh_token, max_age = await AuthService().refresh(
        incoming, user_agent=request.headers.get("user-agent")
    )
    _set_refresh_cookie(response, new_refresh_token, max_age)
    return success_response(data=token_response, message="Session refreshed successfully")


@router.post("/logout", response_model=None)
async def logout(request: Request, response: Response):
    incoming = request.cookies.get(settings.REFRESH_COOKIE_NAME)
    await AuthService().logout(incoming)
    _clear_refresh_cookie(response)
    return success_response(data=None, message="Logged out successfully")


@router.get("/me", response_model=None)
async def get_my_profile(current_user: dict = Depends(get_current_user)):
    profile = await UserService().get_my_profile(current_user)
    return success_response(data=profile, message="Profile retrieved successfully")


@router.patch("/me", response_model=None)
async def update_my_profile(payload: SelfProfileUpdate, current_user: dict = Depends(get_current_user)):
    profile = await UserService().update_my_profile(current_user, payload)
    return success_response(data=profile, message="Profile updated successfully")


@router.post("/me/change-password", response_model=None)
async def change_my_password(payload: ChangePasswordRequest, current_user: dict = Depends(get_current_user)):
    await UserService().change_my_password(current_user, payload)
    return success_response(data=None, message="Password changed successfully. Please log in again.")

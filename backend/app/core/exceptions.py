"""
Custom exception hierarchy + global exception handlers.

Every error response returned by this API - whether raised explicitly by
our own code, thrown by Pydantic validation, or an unexpected 500 - is
normalised to the standard envelope:

    {"success": false, "message": "...", "errors": [...]}

Route handlers should raise one of the exceptions below (never a bare
HTTPException) so the error always carries a consistent shape and status
code. See register_exception_handlers() for how each type is mapped.
"""
import logging
from typing import Any

from fastapi import FastAPI, Request, status
from fastapi.exceptions import RequestValidationError
from fastapi.responses import JSONResponse
from starlette.exceptions import HTTPException as StarletteHTTPException

logger = logging.getLogger("app")


class AppException(Exception):
    """Base class for all handled application errors."""

    def __init__(
        self,
        message: str = "An error occurred",
        status_code: int = status.HTTP_400_BAD_REQUEST,
        errors: list[dict[str, Any]] | None = None,
    ):
        self.message = message
        self.status_code = status_code
        self.errors = errors or []
        super().__init__(message)


class NotFoundException(AppException):
    def __init__(self, message: str = "Resource not found", errors=None):
        super().__init__(message, status.HTTP_404_NOT_FOUND, errors)


class DuplicateException(AppException):
    def __init__(self, message: str = "Resource already exists", errors=None):
        super().__init__(message, status.HTTP_409_CONFLICT, errors)


class ValidationException(AppException):
    """Business-rule validation failures (as opposed to Pydantic's own
    request-shape validation, which is handled separately below)."""

    def __init__(self, message: str = "Validation error", errors=None):
        super().__init__(message, status.HTTP_422_UNPROCESSABLE_ENTITY, errors)


class AuthenticationException(AppException):
    def __init__(self, message: str = "Authentication failed", errors=None):
        super().__init__(message, status.HTTP_401_UNAUTHORIZED, errors)


class AuthorizationException(AppException):
    def __init__(self, message: str = "You do not have permission to perform this action", errors=None):
        super().__init__(message, status.HTTP_403_FORBIDDEN, errors)


class DatabaseException(AppException):
    def __init__(self, message: str = "A database error occurred", errors=None):
        super().__init__(message, status.HTTP_500_INTERNAL_SERVER_ERROR, errors)


def _envelope(message: str, errors: list[Any] | None = None) -> dict:
    return {"success": False, "message": message, "errors": errors or []}


def register_exception_handlers(app: FastAPI) -> None:
    """Wire every exception type this app can raise to the standard envelope."""

    @app.exception_handler(AppException)
    async def handle_app_exception(request: Request, exc: AppException):
        return JSONResponse(status_code=exc.status_code, content=_envelope(exc.message, exc.errors))

    @app.exception_handler(RequestValidationError)
    async def handle_validation_error(request: Request, exc: RequestValidationError):
        field_errors = [
            {
                "field": ".".join(str(loc) for loc in err["loc"] if loc != "body"),
                "message": err["msg"],
            }
            for err in exc.errors()
        ]
        return JSONResponse(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            content=_envelope("Validation error", field_errors),
        )

    @app.exception_handler(StarletteHTTPException)
    async def handle_http_exception(request: Request, exc: StarletteHTTPException):
        # Covers framework-level errors too, e.g. unmatched routes (404) and
        # 405 Method Not Allowed, so every error response - not just the
        # ones we raise ourselves - uses the same envelope.
        message = exc.detail if isinstance(exc.detail, str) else "Request failed"
        return JSONResponse(status_code=exc.status_code, content=_envelope(message))

    @app.exception_handler(Exception)
    async def handle_unexpected_exception(request: Request, exc: Exception):
        # Never leak internals (stack traces, exception messages) to the
        # client for an unanticipated error - log it fully server-side
        # instead and return a generic message.
        logger.exception("Unhandled exception on %s %s", request.method, request.url.path)
        return JSONResponse(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            content=_envelope("An unexpected error occurred. Please try again later."),
        )

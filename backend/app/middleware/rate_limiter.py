"""
Rate limiting via slowapi.

Uses in-memory storage, which is correct for a single backend instance
(local dev, or the single-container Docker Compose setup in this repo).
If you scale the backend horizontally (multiple containers/processes
behind a load balancer), point slowapi at Redis instead so every
instance shares the same counters - see
https://slowapi.readthedocs.io/ for the `storage_uri` option.
"""
from slowapi import Limiter
from slowapi.errors import RateLimitExceeded
from slowapi.util import get_remote_address
from starlette.requests import Request
from starlette.responses import JSONResponse

from app.config.settings import get_settings

settings = get_settings()

limiter = Limiter(key_func=get_remote_address, default_limits=[settings.RATE_LIMIT_DEFAULT])


async def rate_limit_exceeded_handler(request: Request, exc: RateLimitExceeded) -> JSONResponse:
    # Matches the app's standard error envelope, rather than slowapi's
    # default plain-text response.
    return JSONResponse(
        status_code=429,
        content={
            "success": False,
            "message": "Too many requests. Please wait a moment and try again.",
            "errors": [],
        },
        headers={"Retry-After": "60"},
    )

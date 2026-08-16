"""
Application entry point.

Run with: uvicorn app.main:app --reload   (see README.md for full setup)
"""
from contextlib import asynccontextmanager

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from slowapi.errors import RateLimitExceeded
from slowapi.middleware import SlowAPIMiddleware

from app.config.settings import get_settings
from app.core.exceptions import register_exception_handlers
from app.database.connection import close_mongo_connection, connect_to_mongo, ensure_indexes
from app.database.seed import seed_super_admin
from app.middleware.logging_middleware import RequestLoggingMiddleware
from app.middleware.rate_limiter import limiter, rate_limit_exceeded_handler
from app.middleware.security_headers import SecurityHeadersMiddleware
from app.routes import (
    academic_calendar,
    academic_structure,
    auth,
    departments,
    faculty,
    labs,
    rooms,
    subject_allocations,
    timetable,
    users,
)
from app.utils.logger import configure_logging, get_logger
from app.utils.response import success_response

settings = get_settings()
configure_logging(settings.LOG_LEVEL)
logger = get_logger("main")


@asynccontextmanager
async def lifespan(app: FastAPI):
    logger.info("Starting %s (%s)", settings.APP_NAME, settings.ENVIRONMENT)
    await connect_to_mongo()
    await ensure_indexes()
    await seed_super_admin()
    logger.info("Startup complete")
    yield
    logger.info("Shutting down")
    await close_mongo_connection()


app = FastAPI(
    title=settings.APP_NAME,
    version="1.0.0",
    description=(
        "Phase 1: Authentication, User Management, and core master-data CRUD modules. "
        "Phase 3: Subject Allocation, Laboratories, and the Timetable generation engine."
    ),
    lifespan=lifespan,
)

# --- Rate limiting ---------------------------------------------------------
app.state.limiter = limiter
app.add_exception_handler(RateLimitExceeded, rate_limit_exceeded_handler)
app.add_middleware(SlowAPIMiddleware)

# --- CORS --------------------------------------------------------------
app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.cors_origins_list,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# --- Custom middleware (security headers, request logging) -----------------
app.add_middleware(SecurityHeadersMiddleware)
app.add_middleware(RequestLoggingMiddleware)

# --- Standardised error envelope for every exception type ------------------
register_exception_handlers(app)

# --- Routes --------------------------------------------------------------
app.include_router(auth.router, prefix=settings.API_V1_PREFIX)
app.include_router(users.router, prefix=settings.API_V1_PREFIX)
app.include_router(departments.router, prefix=settings.API_V1_PREFIX)
app.include_router(faculty.router, prefix=settings.API_V1_PREFIX)
app.include_router(academic_calendar.router, prefix=settings.API_V1_PREFIX)
app.include_router(rooms.router, prefix=settings.API_V1_PREFIX)
app.include_router(labs.router, prefix=settings.API_V1_PREFIX)
app.include_router(academic_structure.router, prefix=settings.API_V1_PREFIX)
app.include_router(subject_allocations.router, prefix=settings.API_V1_PREFIX)
app.include_router(timetable.router, prefix=settings.API_V1_PREFIX)


@app.get(f"{settings.API_V1_PREFIX}/health", tags=["Health"])
async def health_check():
    """Used by Docker Compose's healthcheck directive and useful for
    manual smoke-testing after deployment."""
    return success_response(data={"status": "healthy", "environment": settings.ENVIRONMENT}, message="Service is running")

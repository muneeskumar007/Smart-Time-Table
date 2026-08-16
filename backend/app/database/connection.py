"""
MongoDB connection lifecycle.

IMPORTANT - driver choice: the project brief asked for Motor. Motor was
formally deprecated on 2026-05-14 (MongoDB's own recommendation is to
migrate to PyMongo's native async API - see
https://www.mongodb.com/docs/languages/python/pymongo-driver/current/reference/migration/).
We use `pymongo.AsyncMongoClient` instead, which is what Motor itself now
tells its users to move to. The API is almost identical
(`AsyncMongoClient` instead of `AsyncIOMotorClient`, same
coroutine/await-based calls), so this does not change the architecture -
see README.md for the full note if you'd rather switch back to Motor.
"""
from pymongo import AsyncMongoClient
from pymongo.asynchronous.database import AsyncDatabase

from app.config.settings import get_settings
from app.core.constants import Collections
from app.utils.logger import get_logger

logger = get_logger("database")

_client: AsyncMongoClient | None = None
_db: AsyncDatabase | None = None


async def connect_to_mongo() -> None:
    global _client, _db
    settings = get_settings()
    _client = AsyncMongoClient(settings.MONGODB_URL, uuidRepresentation="standard")
    _db = _client[settings.MONGODB_DB_NAME]
    # `ping` forces an actual round-trip so connection problems surface at
    # startup with a clear log line, rather than on the first request.
    await _client.admin.command("ping")
    logger.info("Connected to MongoDB database '%s'", settings.MONGODB_DB_NAME)


async def close_mongo_connection() -> None:
    global _client
    if _client is not None:
        await _client.close()
        logger.info("MongoDB connection closed")


def get_database() -> AsyncDatabase:
    if _db is None:
        raise RuntimeError("Database not initialised - connect_to_mongo() must run before use.")
    return _db


async def ensure_indexes() -> None:
    """Create (idempotently) every index the Phase 1 modules rely on.

    create_index() is safe to call on every startup: MongoDB no-ops if an
    identical index already exists. Enforcing uniqueness at the DB level
    (in addition to the application-level checks in each service) guards
    against race conditions under concurrent requests.
    """
    db = get_database()

    await db[Collections.USERS].create_index("email", unique=True)
    await db[Collections.USERS].create_index("role")
    await db[Collections.USERS].create_index("department_id")

    await db[Collections.DEPARTMENTS].create_index("name", unique=True)
    await db[Collections.DEPARTMENTS].create_index("code", unique=True)

    await db[Collections.FACULTY].create_index("email", unique=True)
    await db[Collections.FACULTY].create_index("employee_code", unique=True)
    await db[Collections.FACULTY].create_index("department_id")

    await db[Collections.COURSES].create_index("code", unique=True)
    await db[Collections.COURSES].create_index("department_id")

    await db[Collections.SUBJECTS].create_index("code", unique=True)
    await db[Collections.SUBJECTS].create_index("course_id")
    await db[Collections.SUBJECTS].create_index("department_id")

    await db[Collections.SECTIONS].create_index(
        [("course_id", 1), ("academic_year_id", 1), ("semester_id", 1), ("section_name", 1)],
        unique=True,
    )
    await db[Collections.SECTIONS].create_index("department_id")

    await db[Collections.ROOMS].create_index("room_number", unique=True)

    await db[Collections.LABORATORIES].create_index("room_number", unique=True)
    await db[Collections.LABORATORIES].create_index("department_id")

    await db[Collections.ACADEMIC_YEARS].create_index("name", unique=True)

    await db[Collections.SEMESTERS].create_index(
        [("academic_year_id", 1), ("term_type", 1)], unique=True
    )

    await db[Collections.TIMESLOTS].create_index(
        [("department_id", 1), ("day_of_week", 1), ("start_time", 1)]
    )

    await db[Collections.SUBJECT_ALLOCATIONS].create_index(
        [("subject_id", 1), ("section_id", 1)], unique=True,
        partialFilterExpression={"is_active": True},
    )
    await db[Collections.SUBJECT_ALLOCATIONS].create_index("faculty_id")
    await db[Collections.SUBJECT_ALLOCATIONS].create_index("section_id")

    await db[Collections.TIMETABLES].create_index("section_id")
    await db[Collections.TIMETABLES].create_index([("section_id", 1), ("version", -1)])
    await db[Collections.TIMETABLES].create_index([("academic_year_id", 1), ("semester_id", 1), ("status", 1)])
    await db[Collections.TIMETABLES].create_index("department_id")

    await db[Collections.GENERATION_LOGS].create_index("section_id")
    await db[Collections.GENERATION_LOGS].create_index("started_at")

    logger.info("MongoDB indexes ensured")

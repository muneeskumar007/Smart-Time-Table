"""
First-run bootstrap.

A freshly created database has no users in it, which is a chicken-and-egg
problem (you need a Super Admin to create any other account, but nothing
can create the first Super Admin). On every startup, if the `users`
collection is completely empty, one Super Admin account is created from
the SUPER_ADMIN_* environment variables. This only ever fires once - as
soon as any user document exists, it's skipped on every subsequent
startup.
"""
from app.auth.security import hash_password
from app.config.settings import get_settings
from app.core.constants import UserRole
from app.models.user import UserModel
from app.repositories.user_repository import UserRepository
from app.utils.logger import get_logger

logger = get_logger("seed")


async def seed_super_admin() -> None:
    settings = get_settings()
    repo = UserRepository()

    if await repo.count() > 0:
        return

    model = UserModel(
        name=settings.SUPER_ADMIN_NAME,
        email=settings.SUPER_ADMIN_EMAIL.strip().lower(),
        password_hash=hash_password(settings.SUPER_ADMIN_PASSWORD),
        role=UserRole.SUPER_ADMIN,
        department_id=None,
    )
    await repo.insert(model.model_dump())

    logger.warning(
        "No users existed - created the initial Super Admin account (%s). "
        "Log in and change this password immediately.",
        settings.SUPER_ADMIN_EMAIL,
    )

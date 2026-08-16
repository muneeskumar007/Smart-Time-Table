from datetime import datetime

from pydantic import Field

from app.core.constants import UserRole
from app.models.base import AuditMixin


class UserModel(AuditMixin):
    """Canonical shape of a `users` document.

    `sessions` holds one entry per active login (one per device/browser):
    ``{"jti": str, "expires_at": datetime, "created_at": datetime,
    "user_agent": str | None}``. The `jti` is the JWT ID claim of the
    refresh token issued for that session, letting us revoke a single
    session (logout) or all of them (deactivate user) without needing a
    separate collection. Kept as `list[dict]` rather than a nested
    Pydantic model since it is only ever read/written by auth_service in
    small, direct operations (push/remove one entry).
    """

    name: str
    email: str
    password_hash: str
    role: UserRole
    department_id: str | None = None
    # Added for timetable viewing (Master Prompt 3): which Section a
    # STUDENT-role user belongs to, so "view published timetable" has
    # something to key off. Irrelevant for other roles - left null.
    section_id: str | None = None
    phone: str | None = None
    last_login: datetime | None = None
    sessions: list[dict] = Field(default_factory=list)

from app.core.constants import RoomType
from app.models.base import AuditMixin


class RoomModel(AuditMixin):
    """Canonical shape of a `rooms` document. Phase 1 covers general
    classrooms/seminar halls/auditoria only - dedicated Lab rooms get
    their own `labs` collection and module in a later phase, per the
    project's explicit Phase 1 scope."""

    room_number: str
    building: str | None = None
    floor: str | None = None
    capacity: int
    room_type: RoomType = RoomType.CLASSROOM
    has_projector: bool = False
    has_ac: bool = False

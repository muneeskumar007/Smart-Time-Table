"""
Base building block for MongoDB-facing models.

Design note: we deliberately do NOT give Pydantic models a custom
bson.ObjectId type. MongoDB's ObjectId lives only inside the repository
layer (converted to/from `str` at the boundary - see
repositories/base_repository.py::serialize_doc). Every model, schema and
API response works with plain string ids. This keeps Mongo-specific
types out of the domain/API layer entirely and avoids a whole class of
Pydantic v2 custom-type bugs.
"""
from datetime import datetime, timezone

from pydantic import BaseModel, Field


def utcnow() -> datetime:
    return datetime.now(timezone.utc)


class TimestampMixin(BaseModel):
    created_at: datetime = Field(default_factory=utcnow)
    updated_at: datetime = Field(default_factory=utcnow)


class AuditMixin(TimestampMixin):
    """Adds soft-delete and audit-trail support on top of TimestampMixin.
    Every Phase 1+ entity uses this (not the bare TimestampMixin) so that
    every collection consistently has is_active/deleted_at/created_by/
    updated_by, per the project's data-design requirements. Kept as a
    separate class (rather than folding into TimestampMixin directly) so
    the distinction between "has timestamps" and "is independently
    soft-deletable/audited" stays explicit in the code."""

    is_active: bool = True
    deleted_at: datetime | None = None
    created_by: str | None = None
    updated_by: str | None = None

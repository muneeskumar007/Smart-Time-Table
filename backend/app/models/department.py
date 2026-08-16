from app.models.base import AuditMixin


class DepartmentModel(AuditMixin):
    """Canonical shape of a `departments` document. Services build one of
    these from a validated Create/Update schema (normalising fields such
    as `code`) before handing a plain dict to the repository - the model
    class exists to make that normalisation explicit and typed, not
    because we parse documents back out of Mongo through it (reads go
    through the lighter-weight Response schemas instead)."""

    name: str
    code: str
    description: str | None = None
    established_year: int | None = None
    hod_id: str | None = None

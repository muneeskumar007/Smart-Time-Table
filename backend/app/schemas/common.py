"""Small building blocks shared by multiple schema modules."""
from datetime import datetime

from pydantic import BaseModel, ConfigDict


class TimestampedResponse(BaseModel):
    """Every entity response includes when it was created/last updated
    and by whom (audit trail), plus its soft-delete status."""
    model_config = ConfigDict(from_attributes=True)

    id: str
    created_at: datetime
    updated_at: datetime
    created_by: str | None = None
    updated_by: str | None = None
    is_active: bool = True


class RefSummary(BaseModel):
    """A minimal {id, name} reference used to embed related entities
    (e.g. a Faculty response embedding its Department) without pulling
    in the full related document."""
    id: str
    name: str

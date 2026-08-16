from pydantic import BaseModel, Field, field_validator

from app.schemas.common import RefSummary, TimestampedResponse


class LabCreate(BaseModel):
    lab_name: str = Field(..., min_length=2, max_length=150)
    room_number: str = Field(..., min_length=1, max_length=20)
    building: str | None = Field(None, max_length=100)
    floor: str | None = Field(None, max_length=20)
    capacity: int = Field(..., ge=1, le=300)
    department_id: str
    available_systems: int | None = Field(None, ge=0, le=300)
    has_ac: bool = False

    @field_validator("room_number")
    @classmethod
    def normalise(cls, v: str) -> str:
        return v.strip().upper()


class LabUpdate(BaseModel):
    lab_name: str | None = Field(None, min_length=2, max_length=150)
    building: str | None = Field(None, max_length=100)
    floor: str | None = Field(None, max_length=20)
    capacity: int | None = Field(None, ge=1, le=300)
    available_systems: int | None = Field(None, ge=0, le=300)
    has_ac: bool | None = None
    is_active: bool | None = None


class LabResponse(TimestampedResponse):
    lab_name: str
    room_number: str
    building: str | None
    floor: str | None
    capacity: int
    department: RefSummary
    available_systems: int | None
    has_ac: bool
    is_active: bool

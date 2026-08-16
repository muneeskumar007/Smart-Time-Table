from pydantic import BaseModel, Field, field_validator

from app.core.constants import RoomType
from app.schemas.common import TimestampedResponse


class RoomCreate(BaseModel):
    room_number: str = Field(..., min_length=1, max_length=20)
    building: str | None = Field(None, max_length=100)
    floor: str | None = Field(None, max_length=20)
    capacity: int = Field(..., ge=1, le=1000)
    room_type: RoomType = RoomType.CLASSROOM
    has_projector: bool = False
    has_ac: bool = False

    @field_validator("room_number")
    @classmethod
    def normalise(cls, v: str) -> str:
        return v.strip().upper()


class RoomUpdate(BaseModel):
    building: str | None = Field(None, max_length=100)
    floor: str | None = Field(None, max_length=20)
    capacity: int | None = Field(None, ge=1, le=1000)
    room_type: RoomType | None = None
    has_projector: bool | None = None
    has_ac: bool | None = None
    is_active: bool | None = None


class RoomResponse(TimestampedResponse):
    room_number: str
    building: str | None
    floor: str | None
    capacity: int
    room_type: RoomType
    has_projector: bool
    has_ac: bool
    is_active: bool

from app.models.base import AuditMixin


class LabModel(AuditMixin):
    """Canonical shape of a `laboratories` document. A sibling of Room
    rather than a subtype of it - real institutions track labs
    separately (systems count, department ownership, specialised
    equipment) even though both are "a place you hold a class". Added in
    Master Prompt 3 because lab-type Subjects need lab-type rooms for
    the timetable generator to place them in."""

    lab_name: str
    room_number: str
    building: str | None = None
    floor: str | None = None
    capacity: int
    department_id: str
    available_systems: int | None = None
    has_ac: bool = False

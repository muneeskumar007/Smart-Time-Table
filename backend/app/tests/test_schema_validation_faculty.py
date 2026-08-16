from datetime import date

import pytest
from pydantic import ValidationError

from app.schemas.faculty import FacultyCreate, FacultyUpdate


def _valid_payload(**overrides):
    base = dict(
        employee_code="fac001",
        name="Dr. Asha Rao",
        email="asha.rao@college.edu",
        designation="Associate Professor",
        department_id="dept123",
        date_of_joining=date(2020, 6, 1),
    )
    base.update(overrides)
    return base


class TestFacultyCreate:
    def test_accepts_valid_payload(self):
        faculty = FacultyCreate(**_valid_payload())
        assert faculty.employee_code == "FAC001"  # normalised
        assert faculty.employment_type == "permanent"  # default
        assert faculty.max_weekly_hours == 18  # default

    def test_rejects_invalid_email(self):
        with pytest.raises(ValidationError):
            FacultyCreate(**_valid_payload(email="not-an-email"))

    def test_rejects_invalid_phone_format(self):
        with pytest.raises(ValidationError):
            FacultyCreate(**_valid_payload(phone="abc-not-a-phone"))

    def test_accepts_valid_phone_format(self):
        faculty = FacultyCreate(**_valid_payload(phone="+91 98765 43210"))
        assert faculty.phone == "+91 98765 43210"

    def test_rejects_max_weekly_hours_out_of_bounds(self):
        with pytest.raises(ValidationError):
            FacultyCreate(**_valid_payload(max_weekly_hours=0))
        with pytest.raises(ValidationError):
            FacultyCreate(**_valid_payload(max_weekly_hours=41))

    def test_rejects_slot_marked_both_preferred_and_unavailable(self):
        with pytest.raises(ValidationError, match="cannot be both preferred and unavailable"):
            FacultyCreate(**_valid_payload(preferred_slots=["slot1", "slot2"], unavailable_slots=["slot2", "slot3"]))

    def test_accepts_disjoint_preferred_and_unavailable_slots(self):
        faculty = FacultyCreate(**_valid_payload(preferred_slots=["slot1"], unavailable_slots=["slot2"]))
        assert faculty.preferred_slots == ["slot1"]
        assert faculty.unavailable_slots == ["slot2"]

    def test_rejects_invalid_employment_type(self):
        with pytest.raises(ValidationError):
            FacultyCreate(**_valid_payload(employment_type="freelance"))


class TestFacultyUpdate:
    def test_all_fields_optional(self):
        update = FacultyUpdate()
        assert update.name is None

    def test_rejects_overlapping_slots_when_both_provided(self):
        with pytest.raises(ValidationError, match="cannot be both preferred and unavailable"):
            FacultyUpdate(preferred_slots=["slot1"], unavailable_slots=["slot1"])

    def test_allows_updating_only_preferred_slots(self):
        # unavailable_slots is None (not provided) - the overlap check
        # only applies when *both* are present in the same update.
        update = FacultyUpdate(preferred_slots=["slot1", "slot2"])
        assert update.preferred_slots == ["slot1", "slot2"]
        assert update.unavailable_slots is None

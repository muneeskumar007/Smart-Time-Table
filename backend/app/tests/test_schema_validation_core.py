"""
Schema (Pydantic) validation tests.

These exercise the request-validation layer directly - no database, no
running app required, since Pydantic validation is pure Python. This is
deliberately narrower than a full integration test (it doesn't touch
repositories/services/MongoDB), but it's a real, honestly-scoped test of
"does invalid data actually get rejected, with a clear reason" for every
CRUD module, which is exactly what a database-less test environment can
verify with confidence.
"""
import pytest
from pydantic import ValidationError

from app.schemas.department import DepartmentCreate, DepartmentUpdate
from app.schemas.room import RoomCreate


class TestDepartmentCreate:
    def test_accepts_valid_payload(self):
        dept = DepartmentCreate(name="Computer Science", code="cse", established_year=1998)
        assert dept.name == "Computer Science"
        assert dept.code == "CSE"  # normalised to uppercase

    def test_rejects_missing_name(self):
        with pytest.raises(ValidationError):
            DepartmentCreate(code="CSE")

    def test_rejects_missing_code(self):
        with pytest.raises(ValidationError):
            DepartmentCreate(name="Computer Science")

    def test_rejects_too_short_name(self):
        with pytest.raises(ValidationError):
            DepartmentCreate(name="C", code="CSE")

    def test_rejects_established_year_out_of_range(self):
        with pytest.raises(ValidationError):
            DepartmentCreate(name="Computer Science", code="CSE", established_year=1500)
        with pytest.raises(ValidationError):
            DepartmentCreate(name="Computer Science", code="CSE", established_year=3000)

    def test_code_is_trimmed_and_uppercased(self):
        dept = DepartmentCreate(name="Computer Science", code="  cse  ")
        assert dept.code == "CSE"

    def test_established_year_is_optional(self):
        dept = DepartmentCreate(name="Computer Science", code="CSE")
        assert dept.established_year is None


class TestDepartmentUpdate:
    def test_all_fields_optional(self):
        update = DepartmentUpdate()
        assert update.name is None
        assert update.code is None

    def test_partial_update_normalises_code(self):
        update = DepartmentUpdate(code="ece")
        assert update.code == "ECE"

    def test_rejects_invalid_established_year_even_on_partial_update(self):
        with pytest.raises(ValidationError):
            DepartmentUpdate(established_year=1500)


class TestRoomCreate:
    def test_accepts_valid_payload(self):
        room = RoomCreate(room_number="a-101", capacity=60)
        assert room.room_number == "A-101"
        assert room.room_type == "classroom"  # default

    def test_rejects_zero_or_negative_capacity(self):
        with pytest.raises(ValidationError):
            RoomCreate(room_number="A101", capacity=0)
        with pytest.raises(ValidationError):
            RoomCreate(room_number="A101", capacity=-5)

    def test_rejects_missing_room_number(self):
        with pytest.raises(ValidationError):
            RoomCreate(capacity=60)

    def test_rejects_invalid_room_type(self):
        with pytest.raises(ValidationError):
            RoomCreate(room_number="A101", capacity=60, room_type="not_a_real_type")

    def test_defaults_amenities_to_false(self):
        room = RoomCreate(room_number="A101", capacity=60)
        assert room.has_projector is False
        assert room.has_ac is False

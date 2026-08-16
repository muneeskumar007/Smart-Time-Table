from datetime import date

import pytest
from pydantic import ValidationError

from app.schemas.academic_calendar import AcademicYearCreate, SemesterCreate, TimeSlotCreate


class TestAcademicYearCreate:
    def test_accepts_valid_payload(self):
        year = AcademicYearCreate(name="2026-2027", start_date=date(2026, 6, 1), end_date=date(2027, 5, 31))
        assert year.name == "2026-2027"

    def test_rejects_end_date_before_start_date(self):
        with pytest.raises(ValidationError, match="End date must be after start date"):
            AcademicYearCreate(name="2026-2027", start_date=date(2027, 5, 31), end_date=date(2026, 6, 1))

    def test_rejects_end_date_equal_to_start_date(self):
        with pytest.raises(ValidationError, match="End date must be after start date"):
            AcademicYearCreate(name="2026-2027", start_date=date(2026, 6, 1), end_date=date(2026, 6, 1))

    def test_rejects_name_too_short(self):
        with pytest.raises(ValidationError):
            AcademicYearCreate(name="26", start_date=date(2026, 6, 1), end_date=date(2027, 5, 31))


class TestSemesterCreate:
    def test_accepts_valid_payload(self):
        semester = SemesterCreate(
            name="Odd Semester 2026-27",
            academic_year_id="ay1",
            term_type="odd",
            start_date=date(2026, 8, 1),
            end_date=date(2026, 12, 15),
        )
        assert semester.term_type == "odd"

    def test_rejects_end_before_start(self):
        with pytest.raises(ValidationError, match="End date must be after start date"):
            SemesterCreate(
                name="Odd Semester 2026-27",
                academic_year_id="ay1",
                term_type="odd",
                start_date=date(2026, 12, 15),
                end_date=date(2026, 8, 1),
            )

    def test_rejects_invalid_term_type(self):
        with pytest.raises(ValidationError):
            SemesterCreate(
                name="Odd Semester 2026-27",
                academic_year_id="ay1",
                term_type="summer",
                start_date=date(2026, 8, 1),
                end_date=date(2026, 12, 15),
            )


class TestTimeSlotCreate:
    def _valid(self, **overrides):
        base = dict(day_of_week="MON", start_time="09:00", end_time="10:00")
        base.update(overrides)
        return TimeSlotCreate(**base)

    def test_accepts_valid_payload(self):
        slot = self._valid()
        assert slot.start_time == "09:00"
        assert slot.is_break is False  # default

    def test_rejects_malformed_time_string(self):
        with pytest.raises(ValidationError):
            self._valid(start_time="9:00")  # missing leading zero
        with pytest.raises(ValidationError):
            self._valid(start_time="09:60")  # invalid minutes
        with pytest.raises(ValidationError):
            self._valid(start_time="24:00")  # invalid hour

    def test_rejects_end_time_before_start_time(self):
        with pytest.raises(ValidationError, match="End time must be after start time"):
            self._valid(start_time="10:00", end_time="09:00")

    def test_rejects_end_time_equal_to_start_time(self):
        with pytest.raises(ValidationError, match="End time must be after start time"):
            self._valid(start_time="09:00", end_time="09:00")

    def test_rejects_invalid_day_of_week(self):
        with pytest.raises(ValidationError):
            self._valid(day_of_week="FUNDAY")

    def test_department_id_defaults_to_none_meaning_global(self):
        slot = self._valid()
        assert slot.department_id is None

    def test_accepts_department_scoped_slot(self):
        slot = self._valid(department_id="dept1")
        assert slot.department_id == "dept1"

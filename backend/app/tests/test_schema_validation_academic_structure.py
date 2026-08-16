import pytest
from pydantic import ValidationError

from app.schemas.academic_structure import CourseCreate, SectionCreate, SubjectCreate


class TestCourseCreate:
    def test_accepts_valid_payload(self):
        course = CourseCreate(name="B.Tech CSE", code="btech-cse", department_id="dept1", duration_years=4, total_semesters=8)
        assert course.code == "BTECH-CSE"

    def test_rejects_zero_duration(self):
        with pytest.raises(ValidationError):
            CourseCreate(name="B.Tech CSE", code="BTECH-CSE", department_id="dept1", duration_years=0, total_semesters=8)

    def test_rejects_total_semesters_out_of_bounds(self):
        with pytest.raises(ValidationError):
            CourseCreate(name="B.Tech CSE", code="BTECH-CSE", department_id="dept1", duration_years=4, total_semesters=21)

    def test_rejects_missing_department(self):
        with pytest.raises(ValidationError):
            CourseCreate(name="B.Tech CSE", code="BTECH-CSE", duration_years=4, total_semesters=8)


class TestSubjectCreate:
    def _valid(self, **overrides):
        base = dict(
            name="Data Structures",
            code="cs301",
            course_id="course1",
            semester_number=3,
            credits=4,
            weekly_lecture_hours=3,
        )
        base.update(overrides)
        return SubjectCreate(**base)

    def test_accepts_valid_payload(self):
        subject = self._valid()
        assert subject.code == "CS301"
        assert subject.subject_type == "theory"  # default
        assert subject.weekly_lab_hours == 0  # default

    def test_rejects_negative_credits(self):
        with pytest.raises(ValidationError):
            self._valid(credits=-1)

    def test_rejects_semester_number_out_of_bounds(self):
        with pytest.raises(ValidationError):
            self._valid(semester_number=0)
        with pytest.raises(ValidationError):
            self._valid(semester_number=21)

    def test_accepts_a_subject_with_both_lecture_and_lab_hours(self):
        subject = self._valid(subject_type="lab", weekly_lecture_hours=2, weekly_lab_hours=2)
        assert subject.weekly_lecture_hours == 2
        assert subject.weekly_lab_hours == 2

    def test_rejects_invalid_subject_type(self):
        with pytest.raises(ValidationError):
            self._valid(subject_type="workshop")

    def test_rejects_negative_weekly_hours(self):
        with pytest.raises(ValidationError):
            self._valid(weekly_lecture_hours=-1)


class TestSectionCreate:
    def _valid(self, **overrides):
        base = dict(
            course_id="course1",
            academic_year_id="ay1",
            semester_id="sem1",
            semester_number=3,
            section_name="a",
            strength=60,
        )
        base.update(overrides)
        return SectionCreate(**base)

    def test_accepts_valid_payload_and_normalises_section_name(self):
        section = self._valid()
        assert section.section_name == "A"

    def test_rejects_zero_strength(self):
        with pytest.raises(ValidationError):
            self._valid(strength=0)

    def test_rejects_strength_above_max(self):
        with pytest.raises(ValidationError):
            self._valid(strength=501)

    def test_class_advisor_and_room_are_optional(self):
        section = self._valid()
        assert section.class_advisor_id is None
        assert section.room_id is None

    def test_rejects_section_name_too_long(self):
        with pytest.raises(ValidationError):
            self._valid(section_name="THIS-IS-WAY-TOO-LONG")

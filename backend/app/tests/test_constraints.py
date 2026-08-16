"""
Constraint engine tests. Every HardConstraint.check() method is pure
Python (no MongoDB, no OR-Tools) by design - see the module docstring in
algorithms/constraints/base.py - so these run fast and need no fixtures
beyond a synthetic GenerationContext.
"""
import pytest

from app.algorithms.constraints.base import GenerationContext, SchedulingDemand
from app.algorithms.constraints.hard_constraints import (
    ActiveResourceOnlyConstraint,
    FacultyMaxWeeklyHoursConstraint,
    FacultyNoDoubleBookingConstraint,
    FacultyUnavailabilityConstraint,
    RoomCapacityConstraint,
    RoomNoDoubleBookingConstraint,
    RoomTypeMatchConstraint,
    SubjectWeeklyHoursConstraint,
)


@pytest.fixture
def ctx() -> GenerationContext:
    return GenerationContext(
        section_id="sec1",
        section_name="CSE-A",
        section_strength=60,
        department_id="dept1",
        academic_year_id="ay1",
        semester_id="sem1",
        demands=[
            SchedulingDemand(
                index=0,
                allocation_id="a1",
                subject_id="sub1",
                subject_name="Data Structures",
                subject_code="CS301",
                section_id="sec1",
                faculty_id="f1",
                faculty_name="Dr. Rao",
                faculty_max_weekly_hours=18,
                faculty_preferred_slots=frozenset(),
                faculty_unavailable_slots=frozenset(["t3"]),
                is_lab=False,
                sessions_needed=2,
            )
        ],
        timeslots_by_id={
            "t1": {"id": "t1", "day_of_week": "MON", "start_time": "09:00", "end_time": "10:00", "label": "P1", "is_break": False},
            "t2": {"id": "t2", "day_of_week": "MON", "start_time": "10:00", "end_time": "11:00", "label": "P2", "is_break": False},
            "t3": {"id": "t3", "day_of_week": "TUE", "start_time": "09:00", "end_time": "10:00", "label": "P1", "is_break": False},
        },
        classrooms_by_id={"r1": {"id": "r1", "room_number": "A101", "capacity": 70, "is_active": True}},
        labs_by_id={"l1": {"id": "l1", "lab_name": "CS Lab 1", "capacity": 30, "is_active": True}},
        faculty_by_id={
            "f1": {"id": "f1", "name": "Dr. Rao", "max_weekly_hours": 18, "is_active": True, "unavailable_slots": ["t3"]},
            "f2": {"id": "f2", "name": "Dr. Iyer", "max_weekly_hours": 2, "is_active": True, "unavailable_slots": []},
        },
    )


def _entry(**overrides):
    base = {"faculty_id": "f1", "timeslot_id": "t1", "room_id": "r1", "subject_id": "sub1", "is_lab": False}
    return {**base, **overrides}


class TestFacultyNoDoubleBooking:
    def test_detects_same_faculty_same_slot_twice(self, ctx):
        entries = [_entry(), _entry()]
        conflicts = FacultyNoDoubleBookingConstraint().check(entries, ctx)
        assert len(conflicts) == 1
        assert conflicts[0].type == "faculty_conflict"
        assert conflicts[0].severity == "error"

    def test_allows_same_faculty_different_slots(self, ctx):
        entries = [_entry(timeslot_id="t1"), _entry(timeslot_id="t2")]
        assert FacultyNoDoubleBookingConstraint().check(entries, ctx) == []

    def test_allows_different_faculty_same_slot(self, ctx):
        entries = [_entry(faculty_id="f1"), _entry(faculty_id="f2")]
        assert FacultyNoDoubleBookingConstraint().check(entries, ctx) == []


class TestRoomNoDoubleBooking:
    def test_detects_two_classes_in_same_room_same_slot(self, ctx):
        entries = [_entry(faculty_id="f1"), _entry(faculty_id="f2")]  # same room+slot, different faculty
        conflicts = RoomNoDoubleBookingConstraint().check(entries, ctx)
        assert len(conflicts) == 1
        assert conflicts[0].type == "room_conflict"

    def test_also_catches_lab_double_booking(self, ctx):
        """No separate 'lab conflict' class exists - a lab is a room as
        far as double-booking goes. See the class docstring."""
        entries = [_entry(room_id="l1", is_lab=True, faculty_id="f1"), _entry(room_id="l1", is_lab=True, faculty_id="f2")]
        conflicts = RoomNoDoubleBookingConstraint().check(entries, ctx)
        assert len(conflicts) == 1


class TestFacultyMaxWeeklyHours:
    def test_flags_overload(self, ctx):
        entries = [
            _entry(faculty_id="f2", timeslot_id="t1"),
            _entry(faculty_id="f2", timeslot_id="t2"),
            _entry(faculty_id="f2", timeslot_id="t3"),
        ]
        conflicts = FacultyMaxWeeklyHoursConstraint().check(entries, ctx)
        assert len(conflicts) == 1
        assert conflicts[0].type == "faculty_overload"

    def test_does_not_flag_within_limit(self, ctx):
        entries = [_entry(faculty_id="f2", timeslot_id="t1"), _entry(faculty_id="f2", timeslot_id="t2")]
        assert FacultyMaxWeeklyHoursConstraint().check(entries, ctx) == []


class TestFacultyUnavailability:
    def test_flags_assignment_to_unavailable_slot(self, ctx):
        entries = [_entry(faculty_id="f1", timeslot_id="t3")]
        conflicts = FacultyUnavailabilityConstraint().check(entries, ctx)
        assert len(conflicts) == 1
        assert conflicts[0].type == "faculty_unavailable"

    def test_allows_available_slot(self, ctx):
        entries = [_entry(faculty_id="f1", timeslot_id="t1")]
        assert FacultyUnavailabilityConstraint().check(entries, ctx) == []


class TestSubjectWeeklyHours:
    def test_flags_short_of_required_sessions(self, ctx):
        entries = [_entry(timeslot_id="t1")]  # demand needs 2, only 1 given
        conflicts = SubjectWeeklyHoursConstraint().check(entries, ctx)
        assert len(conflicts) == 1
        assert conflicts[0].type == "missing_subject_hours"

    def test_satisfied_when_count_matches(self, ctx):
        entries = [_entry(timeslot_id="t1"), _entry(timeslot_id="t2")]
        assert SubjectWeeklyHoursConstraint().check(entries, ctx) == []


class TestRoomTypeMatch:
    def test_flags_lab_session_in_classroom(self, ctx):
        entries = [_entry(room_id="r1", is_lab=True)]
        conflicts = RoomTypeMatchConstraint().check(entries, ctx)
        assert len(conflicts) == 1

    def test_flags_lecture_in_lab_room(self, ctx):
        entries = [_entry(room_id="l1", is_lab=False)]
        conflicts = RoomTypeMatchConstraint().check(entries, ctx)
        assert len(conflicts) == 1

    def test_allows_correct_pairing(self, ctx):
        assert RoomTypeMatchConstraint().check([_entry(room_id="r1", is_lab=False)], ctx) == []
        assert RoomTypeMatchConstraint().check([_entry(room_id="l1", is_lab=True)], ctx) == []


class TestRoomCapacity:
    def test_flags_room_smaller_than_section(self, ctx):
        # section_strength=60, lab l1 capacity=30
        entries = [_entry(room_id="l1", is_lab=True)]
        conflicts = RoomCapacityConstraint().check(entries, ctx)
        assert len(conflicts) == 1

    def test_allows_sufficient_capacity(self, ctx):
        entries = [_entry(room_id="r1")]  # capacity 70 >= 60
        assert RoomCapacityConstraint().check(entries, ctx) == []


class TestActiveResourceOnly:
    def test_flags_inactive_faculty(self, ctx):
        ctx.faculty_by_id["f3"] = {"id": "f3", "name": "Retired Prof", "is_active": False, "max_weekly_hours": 10}
        entries = [_entry(faculty_id="f3")]
        conflicts = ActiveResourceOnlyConstraint().check(entries, ctx)
        assert len(conflicts) == 1
        assert conflicts[0].type == "inactive_resource"

    def test_allows_active_faculty(self, ctx):
        assert ActiveResourceOnlyConstraint().check([_entry(faculty_id="f1")], ctx) == []

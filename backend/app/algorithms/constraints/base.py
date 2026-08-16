"""
Constraint engine foundations.

Design goal (per the project brief): "Every scheduling rule must exist
as an individual constraint class... do NOT hardcode rules inside the
generator" and "additional constraints can be added without modifying
existing logic." Concretely, that means:

  * Each rule is one class implementing `HardConstraint` or
    `SoftConstraint` below.
  * The generator (algorithms/generator.py) never contains rule logic
    itself - it just loops over a *list* of constraint instances
    (see constraints/registry.py) and calls `.apply()` on each.
  * Adding a new rule means adding one new class and appending it to the
    registry list - nothing else changes.

Dual-purpose design: every HardConstraint implements both `.apply()`
(adds the rule to the CP-SAT model while *building* a timetable) and
`.check()` (evaluates the same rule against an already-decided list of
entries - a plain Python function with no OR-Tools dependency at all).
`.check()` is what powers the manual editor's "reject invalid edits" and
the standalone POST /timetable/validate endpoint, and is exactly how the
same rule ends up enforced in both places without being written twice.
"""
from abc import ABC, abstractmethod
from dataclasses import dataclass, field

from app.schemas.timetable import Conflict


@dataclass
class SchedulingDemand:
    """"This subject needs N more sessions this week" - one per
    (subject, section, faculty, session-type) combination, derived by
    splitting a SubjectAllocation into its lecture and lab components
    (each needs a different room type, so they can't share one demand).
    """

    index: int
    allocation_id: str
    subject_id: str
    subject_name: str
    subject_code: str
    section_id: str
    faculty_id: str
    faculty_name: str
    faculty_max_weekly_hours: int
    faculty_preferred_slots: frozenset[str]
    faculty_unavailable_slots: frozenset[str]
    is_lab: bool
    sessions_needed: int


@dataclass
class GenerationContext:
    """Everything a constraint needs to know about the world, independent
    of which decision variables the solver ends up creating. Built once
    per generation run by generator.py and passed to every constraint's
    `.apply()`, and reconstructed (more cheaply, without OR-Tools) for
    `.check()` calls from the manual editor."""

    section_id: str
    section_name: str
    section_strength: int
    department_id: str
    academic_year_id: str
    semester_id: str

    demands: list[SchedulingDemand]

    # Eligible resources - already filtered to is_active=True and
    # (for rooms) capacity >= section_strength by the caller, so
    # constraints don't need to re-check basic eligibility themselves.
    timeslots_by_id: dict[str, dict]  # timeslot_id -> {day_of_week, start_time, end_time, label, is_break, ...}
    classrooms_by_id: dict[str, dict]  # room_id -> {room_number, capacity, ...}
    labs_by_id: dict[str, dict]  # lab_id -> {lab_name, capacity, ...}
    faculty_by_id: dict[str, dict]

    # (faculty_id, timeslot_id) / (room_id, timeslot_id) pairs already
    # committed elsewhere this term (other sections' generated/published
    # timetables) - new assignments must avoid these too.
    externally_occupied_faculty: frozenset[tuple[str, str]] = field(default_factory=frozenset)
    externally_occupied_rooms: frozenset[tuple[str, str]] = field(default_factory=frozenset)

    def room_lookup(self, room_id: str) -> dict | None:
        return self.classrooms_by_id.get(room_id) or self.labs_by_id.get(room_id)

    def is_lab_room(self, room_id: str) -> bool:
        return room_id in self.labs_by_id


@dataclass
class ModelVariables:
    """The CP-SAT decision variables plus pre-built indexes over them, so
    constraints don't each have to re-scan every variable to find "all
    sessions this faculty could have at this timeslot". Built once by
    algorithms/cpsat_builder.py."""

    # (demand_index, timeslot_id, room_id) -> BoolVar
    x: dict

    by_demand: dict  # demand_index -> list[(timeslot_id, room_id, var)]
    by_demand_day: dict  # (demand_index, day_of_week) -> list[var]
    by_faculty_timeslot: dict  # (faculty_id, timeslot_id) -> list[var]
    by_room_timeslot: dict  # (room_id, timeslot_id) -> list[var]
    by_faculty: dict  # faculty_id -> list[var]  (every session that faculty could teach, any time/room)
    by_faculty_day: dict  # (faculty_id, day_of_week) -> list[var]
    by_timeslot: dict  # timeslot_id -> list[var]  (every var at this time, any demand/room - i.e. "is this section in class right now")


class HardConstraint(ABC):
    """A rule that MUST hold. If `.apply()`'s additions to the model make
    it infeasible, generation fails outright - see MANDATORY CONSTRAINTS
    in the project brief."""

    #: Machine-readable identifier used in Conflict.type
    key: str = "hard_constraint"
    #: Human-readable name for logs/UI
    name: str = "Hard constraint"

    @abstractmethod
    def apply(self, model, variables: ModelVariables, ctx: GenerationContext) -> None:
        """Add this rule's constraints to the CP-SAT model in place."""

    @abstractmethod
    def check(self, entries: list[dict], ctx: GenerationContext) -> list[Conflict]:
        """Evaluate this rule against a concrete, already-decided list of
        entries (plain dicts shaped like TimetableEntryModel). Returns
        one Conflict per violation found. Must not touch OR-Tools at
        all - this is what lets conflict-checking run standalone (manual
        editor, POST /timetable/validate) without a solver in the loop.
        """


class SoftConstraint(ABC):
    """A preference that shapes solution *quality* but never blocks
    feasibility. Contributes weighted penalty terms to the objective -
    lower is always better, so a "reward" (like using a preferred slot)
    is expressed as a penalty for *not* getting it."""

    key: str = "soft_constraint"
    name: str = "Soft constraint"
    #: Relative importance vs. other soft constraints in the combined objective.
    weight: int = 1

    @abstractmethod
    def penalty_terms(self, model, variables: ModelVariables, ctx: GenerationContext) -> list:
        """Return a list of CP-SAT linear expressions/vars representing
        cost (to be summed and weighted into the objective's Minimize)."""

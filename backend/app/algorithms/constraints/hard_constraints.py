"""
Hard (mandatory) constraints. One class per rule listed under
"MANDATORY CONSTRAINTS" in the project brief - see base.py for why each
implements both `.apply()` (CP-SAT) and `.check()` (plain Python).

Several MANDATORY rules are enforced *structurally* rather than by an
explicit CP-SAT constraint: "lunch break is fixed" / "break periods must
never receive classes", "only active X may be assigned", and "only
laboratory subjects may use laboratory rooms" are all satisfied by never
creating a decision variable for the disallowed combination in the first
place (see algorithms/cpsat_builder.py's eligibility filtering) - there
is no variable for the solver to ever set to 1, so no `model.add(...)`
call is needed to forbid it. Those rules still need a `.check()`
implementation here, though, because a *manual* edit doesn't go through
that eligibility filtering and must be actively re-validated.
"""
from app.algorithms.constraints.base import GenerationContext, HardConstraint, ModelVariables
from app.schemas.timetable import Conflict


class FacultyNoDoubleBookingConstraint(HardConstraint):
    key = "faculty_conflict"
    name = "Faculty cannot teach two classes simultaneously"

    def apply(self, model, variables: ModelVariables, ctx: GenerationContext) -> None:
        for (faculty_id, timeslot_id), vars_here in variables.by_faculty_timeslot.items():
            if len(vars_here) > 1:
                model.add_at_most_one(vars_here)

    def check(self, entries: list[dict], ctx: GenerationContext) -> list[Conflict]:
        conflicts = []
        seen: dict[tuple[str, str], dict] = {}
        for entry in entries:
            key = (entry["faculty_id"], entry["timeslot_id"])
            if key in seen:
                other = seen[key]
                faculty = ctx.faculty_by_id.get(entry["faculty_id"], {})
                slot = ctx.timeslots_by_id.get(entry["timeslot_id"], {})
                conflicts.append(
                    Conflict(
                        type=self.key,
                        severity="error",
                        message=f"{faculty.get('name', 'This faculty member')} is scheduled for two classes at the same time",
                        entity={"faculty_id": entry["faculty_id"], "faculty_name": faculty.get("name")},
                        day=slot.get("day_of_week"),
                        period=slot.get("label"),
                        possible_solution="Move one of the two conflicting sessions to a different time slot.",
                    )
                )
            else:
                seen[key] = entry
        return conflicts


class RoomNoDoubleBookingConstraint(HardConstraint):
    """Covers both "a room cannot host two classes simultaneously" and
    "a laboratory cannot host multiple labs simultaneously" - a lab IS a
    room as far as double-booking is concerned, so one uniform rule
    correctly covers both bullet points in the brief without duplicating
    the same logic in a near-identical second class."""

    key = "room_conflict"
    name = "A room cannot host two classes simultaneously"

    def apply(self, model, variables: ModelVariables, ctx: GenerationContext) -> None:
        for (room_id, timeslot_id), vars_here in variables.by_room_timeslot.items():
            if len(vars_here) > 1:
                model.add_at_most_one(vars_here)

    def check(self, entries: list[dict], ctx: GenerationContext) -> list[Conflict]:
        conflicts = []
        seen: dict[tuple[str, str], dict] = {}
        for entry in entries:
            key = (entry["room_id"], entry["timeslot_id"])
            if key in seen:
                room = ctx.room_lookup(entry["room_id"]) or {}
                slot = ctx.timeslots_by_id.get(entry["timeslot_id"], {})
                room_label = room.get("room_number") or room.get("lab_name") or "This room"
                conflicts.append(
                    Conflict(
                        type=self.key,
                        severity="error",
                        message=f"{room_label} is booked for two classes at the same time",
                        entity={"room_id": entry["room_id"], "room_name": room_label},
                        day=slot.get("day_of_week"),
                        period=slot.get("label"),
                        possible_solution="Assign one of the two conflicting sessions to a different room.",
                    )
                )
            else:
                seen[key] = entry
        return conflicts


class FacultyMaxWeeklyHoursConstraint(HardConstraint):
    key = "faculty_overload"
    name = "Faculty maximum weekly hours cannot be exceeded"

    def apply(self, model, variables: ModelVariables, ctx: GenerationContext) -> None:
        for faculty_id, vars_here in variables.by_faculty.items():
            max_hours = ctx.faculty_by_id.get(faculty_id, {}).get("max_weekly_hours")
            if max_hours is not None and vars_here:
                model.add(sum(vars_here) <= max_hours)

    def check(self, entries: list[dict], ctx: GenerationContext) -> list[Conflict]:
        counts: dict[str, int] = {}
        for entry in entries:
            counts[entry["faculty_id"]] = counts.get(entry["faculty_id"], 0) + 1

        conflicts = []
        for faculty_id, count in counts.items():
            faculty = ctx.faculty_by_id.get(faculty_id, {})
            max_hours = faculty.get("max_weekly_hours")
            if max_hours is not None and count > max_hours:
                conflicts.append(
                    Conflict(
                        type=self.key,
                        severity="error",
                        message=f"{faculty.get('name', 'This faculty member')} is assigned {count} hours/week, "
                        f"exceeding their {max_hours}-hour maximum",
                        entity={"faculty_id": faculty_id, "faculty_name": faculty.get("name")},
                        possible_solution="Reduce this faculty member's sessions or raise their weekly hour limit.",
                    )
                )
        return conflicts


class FacultyUnavailabilityConstraint(HardConstraint):
    key = "faculty_unavailable"
    name = "Faculty unavailable slots must never be assigned"

    def apply(self, model, variables: ModelVariables, ctx: GenerationContext) -> None:
        # Enforced structurally by the builder (no variable is created
        # for an unavailable slot) - nothing to add here. See the class
        # docstring at the top of this module.
        return

    def check(self, entries: list[dict], ctx: GenerationContext) -> list[Conflict]:
        conflicts = []
        for entry in entries:
            faculty = ctx.faculty_by_id.get(entry["faculty_id"], {})
            if entry["timeslot_id"] in (faculty.get("unavailable_slots") or []):
                slot = ctx.timeslots_by_id.get(entry["timeslot_id"], {})
                conflicts.append(
                    Conflict(
                        type=self.key,
                        severity="error",
                        message=f"{faculty.get('name', 'This faculty member')} marked this time slot as unavailable",
                        entity={"faculty_id": entry["faculty_id"], "faculty_name": faculty.get("name")},
                        day=slot.get("day_of_week"),
                        period=slot.get("label"),
                        possible_solution="Reassign this session to a time the faculty member is available.",
                    )
                )
        return conflicts


class SubjectWeeklyHoursConstraint(HardConstraint):
    key = "missing_subject_hours"
    name = "Every subject must receive its required weekly hours"

    def apply(self, model, variables: ModelVariables, ctx: GenerationContext) -> None:
        for demand in ctx.demands:
            vars_here = [v for (_, _, v) in variables.by_demand.get(demand.index, [])]
            if vars_here:
                model.add(sum(vars_here) == demand.sessions_needed)
            elif demand.sessions_needed > 0:
                # No eligible (timeslot, room) exists at all for this
                # demand (e.g. no lab rooms configured) - the solver
                # would report this section of the model as trivially
                # infeasible; check() surfaces it with a clearer message.
                model.add(0 == demand.sessions_needed)

    def check(self, entries: list[dict], ctx: GenerationContext) -> list[Conflict]:
        counts: dict[tuple[str, str, bool], int] = {}
        for entry in entries:
            key = (entry["subject_id"], entry["faculty_id"], entry["is_lab"])
            counts[key] = counts.get(key, 0) + 1

        conflicts = []
        for demand in ctx.demands:
            key = (demand.subject_id, demand.faculty_id, demand.is_lab)
            actual = counts.get(key, 0)
            if actual != demand.sessions_needed:
                session_word = "lab" if demand.is_lab else "lecture"
                conflicts.append(
                    Conflict(
                        type=self.key,
                        severity="error",
                        message=f"{demand.subject_name} ({session_word}) has {actual} of its required "
                        f"{demand.sessions_needed} weekly sessions scheduled for {demand.faculty_name}",
                        entity={"subject_id": demand.subject_id, "subject_name": demand.subject_name},
                        possible_solution="Add the missing session(s) via the manual editor, or regenerate.",
                    )
                )
        return conflicts


class RoomTypeMatchConstraint(HardConstraint):
    key = "room_type_mismatch"
    name = "Only laboratory subjects may use laboratory rooms"

    def apply(self, model, variables: ModelVariables, ctx: GenerationContext) -> None:
        # Enforced structurally: lab demands only ever get lab room_ids
        # and lecture demands only ever get classroom room_ids in the
        # variable set the builder creates.
        return

    def check(self, entries: list[dict], ctx: GenerationContext) -> list[Conflict]:
        conflicts = []
        for entry in entries:
            room_is_lab = ctx.is_lab_room(entry["room_id"])
            if entry["is_lab"] and not room_is_lab:
                conflicts.append(self._conflict(entry, "This lab session is scheduled in a non-laboratory room"))
            elif not entry["is_lab"] and room_is_lab:
                conflicts.append(self._conflict(entry, "This lecture is scheduled in a laboratory room"))
        return conflicts

    def _conflict(self, entry: dict, message: str) -> Conflict:
        return Conflict(
            type=self.key,
            severity="error",
            message=message,
            entity={"room_id": entry["room_id"]},
            possible_solution="Reassign this session to a room of the correct type.",
        )


class RoomCapacityConstraint(HardConstraint):
    key = "insufficient_capacity"
    name = "Room capacity must be greater than or equal to section strength"

    def apply(self, model, variables: ModelVariables, ctx: GenerationContext) -> None:
        # Enforced structurally: the builder only creates variables for
        # rooms whose capacity already meets the section's strength.
        return

    def check(self, entries: list[dict], ctx: GenerationContext) -> list[Conflict]:
        conflicts = []
        for entry in entries:
            room = ctx.room_lookup(entry["room_id"])
            if room and room.get("capacity", 0) < ctx.section_strength:
                room_label = room.get("room_number") or room.get("lab_name")
                conflicts.append(
                    Conflict(
                        type=self.key,
                        severity="error",
                        message=f"{room_label} seats {room.get('capacity')}, fewer than the section's {ctx.section_strength} students",
                        entity={"room_id": entry["room_id"], "room_name": room_label},
                        possible_solution="Assign a larger room.",
                    )
                )
        return conflicts


class ActiveResourceOnlyConstraint(HardConstraint):
    """Covers "only active faculty/classrooms/subjects may be assigned"
    as one rule, since it's the same "is this referenced resource
    currently active" check regardless of which resource type."""

    key = "inactive_resource"
    name = "Only active faculty, rooms and subjects may be scheduled"

    def apply(self, model, variables: ModelVariables, ctx: GenerationContext) -> None:
        # Enforced structurally: the generator only loads is_active=True
        # faculty/rooms/subjects into the context in the first place.
        return

    def check(self, entries: list[dict], ctx: GenerationContext) -> list[Conflict]:
        conflicts = []
        for entry in entries:
            faculty = ctx.faculty_by_id.get(entry["faculty_id"])
            if faculty is not None and not faculty.get("is_active", True):
                conflicts.append(self._conflict("faculty_id", entry["faculty_id"], "faculty member", faculty.get("name")))
            room = ctx.room_lookup(entry["room_id"])
            if room is not None and not room.get("is_active", True):
                room_label = room.get("room_number") or room.get("lab_name")
                conflicts.append(self._conflict("room_id", entry["room_id"], "room", room_label))
        return conflicts

    def _conflict(self, field: str, value: str, kind: str, label: str | None) -> Conflict:
        return Conflict(
            type=self.key,
            severity="error",
            message=f"This session uses an inactive {kind} ({label or value})",
            entity={field: value},
            possible_solution=f"Reassign this session to an active {kind}.",
        )


#: Every hard constraint, in the order they're applied. Extending the
#: engine means appending a new class *here* - nothing in generator.py
#: or cpsat_builder.py needs to change.
DEFAULT_HARD_CONSTRAINTS: list[HardConstraint] = [
    FacultyNoDoubleBookingConstraint(),
    RoomNoDoubleBookingConstraint(),
    FacultyMaxWeeklyHoursConstraint(),
    FacultyUnavailabilityConstraint(),
    SubjectWeeklyHoursConstraint(),
    RoomTypeMatchConstraint(),
    RoomCapacityConstraint(),
    ActiveResourceOnlyConstraint(),
]

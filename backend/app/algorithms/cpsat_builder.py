"""
CP-SAT variable builder.

Turns a GenerationContext into the actual `model.new_bool_var()` decision
variables plus the indexes constraints need (ModelVariables). Several
MANDATORY rules (room type matching, room capacity, faculty
unavailability, active-only resources, breaks excluded) are enforced
right here by simply never creating a variable for the disallowed
combination - see the module docstring in constraints/hard_constraints.py
for why that's a deliberate design choice, not a missing constraint.
"""
from app.algorithms.constraints.base import GenerationContext, ModelVariables


def build_variables(model, ctx: GenerationContext) -> ModelVariables:
    x: dict = {}
    by_demand: dict = {}
    by_demand_day: dict = {}
    by_faculty_timeslot: dict = {}
    by_room_timeslot: dict = {}
    by_faculty: dict = {}
    by_faculty_day: dict = {}
    by_timeslot: dict = {}

    non_break_slots = {tid: slot for tid, slot in ctx.timeslots_by_id.items() if not slot.get("is_break")}

    for demand in ctx.demands:
        eligible_rooms = ctx.labs_by_id if demand.is_lab else ctx.classrooms_by_id
        by_demand[demand.index] = []

        for timeslot_id, slot in non_break_slots.items():
            if timeslot_id in demand.faculty_unavailable_slots:
                continue
            if (demand.faculty_id, timeslot_id) in ctx.externally_occupied_faculty:
                continue

            for room_id in eligible_rooms:
                if (room_id, timeslot_id) in ctx.externally_occupied_rooms:
                    continue

                var = model.new_bool_var(f"x_d{demand.index}_t{timeslot_id}_r{room_id}")
                x[(demand.index, timeslot_id, room_id)] = var

                by_demand[demand.index].append((timeslot_id, room_id, var))
                by_demand_day.setdefault((demand.index, slot["day_of_week"]), []).append(var)
                by_faculty_timeslot.setdefault((demand.faculty_id, timeslot_id), []).append(var)
                by_room_timeslot.setdefault((room_id, timeslot_id), []).append(var)
                by_faculty.setdefault(demand.faculty_id, []).append(var)
                by_faculty_day.setdefault((demand.faculty_id, slot["day_of_week"]), []).append(var)
                by_timeslot.setdefault(timeslot_id, []).append(var)

    return ModelVariables(
        x=x,
        by_demand=by_demand,
        by_demand_day=by_demand_day,
        by_faculty_timeslot=by_faculty_timeslot,
        by_room_timeslot=by_room_timeslot,
        by_faculty=by_faculty,
        by_faculty_day=by_faculty_day,
        by_timeslot=by_timeslot,
    )

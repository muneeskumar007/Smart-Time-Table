"""
Timetable generator engine.

Deliberately has no database/repository dependency at all - it takes
already-loaded plain data in (see build_context) and returns plain data
out (GenerationResult). services/timetable_generation_service.py is the
only thing that talks to both this module and the database, which is
what keeps this module unit-testable without MongoDB and keeps "swap the
solver for something else later" (per the brief: "allow future migration
to AI-assisted optimization without changing the API contract") a change
that's contained entirely to this file and cpsat_builder.py.
"""
import asyncio
import time
from dataclasses import dataclass

from ortools.sat.python import cp_model

from app.algorithms.constraints.base import GenerationContext, SchedulingDemand
from app.algorithms.constraints.registry import get_hard_constraints, get_soft_constraints
from app.algorithms.cpsat_builder import build_variables
from app.schemas.timetable import Conflict

SOLVER_STATUS_NAMES = {
    cp_model.OPTIMAL: "OPTIMAL",
    cp_model.FEASIBLE: "FEASIBLE",
    cp_model.INFEASIBLE: "INFEASIBLE",
    cp_model.MODEL_INVALID: "MODEL_INVALID",
    cp_model.UNKNOWN: "UNKNOWN",
}


@dataclass
class GenerationResult:
    solver_status: str
    success: bool
    entries: list[dict]
    demands_total: int
    demands_scheduled: int
    duration_seconds: float
    conflicts: list[Conflict]
    message: str


class TimetableGeneratorEngine:
    def build_context(
        self,
        *,
        section: dict,
        allocations: list[dict],
        subjects_by_id: dict[str, dict],
        faculty_by_id: dict[str, dict],
        timeslots: list[dict],
        classrooms: list[dict],
        labs: list[dict],
        externally_occupied_faculty: set[tuple[str, str]],
        externally_occupied_rooms: set[tuple[str, str]],
    ) -> GenerationContext:
        demands: list[SchedulingDemand] = []
        index = 0
        for allocation in allocations:
            subject = subjects_by_id.get(allocation["subject_id"])
            faculty = faculty_by_id.get(allocation["faculty_id"])
            if not subject or not faculty:
                continue

            preferred = frozenset(faculty.get("preferred_slots") or [])
            unavailable = frozenset(faculty.get("unavailable_slots") or [])

            for is_lab, hours_field in ((False, "weekly_lecture_hours"), (True, "weekly_lab_hours")):
                sessions_needed = subject.get(hours_field, 0)
                if sessions_needed <= 0:
                    continue
                demands.append(
                    SchedulingDemand(
                        index=index,
                        allocation_id=allocation["id"],
                        subject_id=subject["id"],
                        subject_name=subject["name"],
                        subject_code=subject["code"],
                        section_id=section["id"],
                        faculty_id=faculty["id"],
                        faculty_name=faculty["name"],
                        faculty_max_weekly_hours=faculty["max_weekly_hours"],
                        faculty_preferred_slots=preferred,
                        faculty_unavailable_slots=unavailable,
                        is_lab=is_lab,
                        sessions_needed=sessions_needed,
                    )
                )
                index += 1

        return GenerationContext(
            section_id=section["id"],
            section_name=section["section_name"],
            section_strength=section["strength"],
            department_id=section["department_id"],
            academic_year_id=section["academic_year_id"],
            semester_id=section["semester_id"],
            demands=demands,
            timeslots_by_id={t["id"]: t for t in timeslots},
            classrooms_by_id={r["id"]: r for r in classrooms},
            labs_by_id={l["id"]: l for l in labs},
            faculty_by_id=faculty_by_id,
            externally_occupied_faculty=frozenset(externally_occupied_faculty),
            externally_occupied_rooms=frozenset(externally_occupied_rooms),
        )

    async def generate(self, ctx: GenerationContext, max_solve_seconds: float = 20.0) -> GenerationResult:
        start = time.perf_counter()

        if not ctx.demands:
            return GenerationResult(
                solver_status="NO_DEMANDS",
                success=False,
                entries=[],
                demands_total=0,
                demands_scheduled=0,
                duration_seconds=0.0,
                conflicts=[],
                message="No subject allocations found for this section. Allocate faculty to subjects before generating.",
            )

        model = cp_model.CpModel()
        variables = build_variables(model, ctx)

        hard_constraints = get_hard_constraints()
        for constraint in hard_constraints:
            constraint.apply(model, variables, ctx)

        objective_terms = []
        for soft in get_soft_constraints():
            for term in soft.penalty_terms(model, variables, ctx):
                objective_terms.append(soft.weight * term)
        if objective_terms:
            model.minimize(sum(objective_terms))

        solver = cp_model.CpSolver()
        solver.parameters.max_time_in_seconds = max_solve_seconds
        solver.parameters.num_search_workers = 8

        status = await asyncio.to_thread(solver.solve, model)
        duration = time.perf_counter() - start
        status_name = SOLVER_STATUS_NAMES.get(status, "UNKNOWN")

        if status not in (cp_model.OPTIMAL, cp_model.FEASIBLE):
            return GenerationResult(
                solver_status=status_name,
                success=False,
                entries=[],
                demands_total=len(ctx.demands),
                demands_scheduled=0,
                duration_seconds=duration,
                conflicts=[],
                message=self._infeasibility_message(status_name, ctx),
            )

        entries = self._parse_solution(solver, variables, ctx)

        # Defence in depth: independently re-check the solver's own
        # output against every hard constraint's .check(), even though
        # .apply() should have guaranteed this already - catches any
        # modeling bug rather than silently trusting the solver.
        conflicts: list[Conflict] = []
        for constraint in hard_constraints:
            conflicts.extend(constraint.check(entries, ctx))

        scheduled_count = len(entries)
        expected_count = sum(d.sessions_needed for d in ctx.demands)

        return GenerationResult(
            solver_status=status_name,
            success=len(conflicts) == 0,
            entries=entries,
            demands_total=expected_count,
            demands_scheduled=scheduled_count,
            duration_seconds=duration,
            conflicts=conflicts,
            message="Generated successfully" if not conflicts else "Generated with unresolved conflicts - review before publishing",
        )

    def _parse_solution(self, solver: "cp_model.CpSolver", variables, ctx: GenerationContext) -> list[dict]:
        entries = []
        demand_by_index = {d.index: d for d in ctx.demands}

        for (demand_index, timeslot_id, room_id), var in variables.x.items():
            if solver.value(var) != 1:
                continue
            demand = demand_by_index[demand_index]
            slot = ctx.timeslots_by_id[timeslot_id]
            entries.append(
                {
                    "timeslot_id": timeslot_id,
                    "day_of_week": slot["day_of_week"],
                    "period_label": slot.get("label"),
                    "start_time": slot["start_time"],
                    "end_time": slot["end_time"],
                    "subject_id": demand.subject_id,
                    "faculty_id": demand.faculty_id,
                    "room_id": room_id,
                    "is_lab": demand.is_lab,
                    "remarks": None,
                }
            )
        return entries

    @staticmethod
    def _infeasibility_message(status_name: str, ctx: GenerationContext) -> str:
        if status_name == "INFEASIBLE":
            total_needed = sum(d.sessions_needed for d in ctx.demands)
            available_slots = len([t for t in ctx.timeslots_by_id.values() if not t.get("is_break")])
            hint = (
                f"This section needs {total_needed} sessions/week across {len(ctx.demands)} subject "
                f"requirements, with {available_slots} time slots and "
                f"{len(ctx.classrooms_by_id)} classrooms / {len(ctx.labs_by_id)} labs available. "
                "Check for faculty over-committed elsewhere this term, too few rooms of the right "
                "type/capacity, or faculty unavailability that leaves no valid slot."
            )
            return f"No valid timetable exists with the current constraints. {hint}"
        if status_name == "UNKNOWN":
            return "The solver did not finish within the time limit. Try again with a higher time limit."
        return f"Generation did not produce a usable schedule (solver status: {status_name})."

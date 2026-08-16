"""
Soft (preference) constraints. Each contributes weighted terms to the
objective the solver minimizes - see SoftConstraint.penalty_terms() in
base.py for the exact contract (a term can be a positive "cost to avoid"
or a negative "bonus to chase").

This is a representative, extensible subset covering 4 of the 7 SOFT
CONSTRAINTS bullets in the project brief (with two bullets merged where
they're the same underlying preference - see class docstrings). The
registry pattern below (DEFAULT_SOFT_CONSTRAINTS) is exactly what makes
adding the rest ("balance room utilization" etc.) a one-class,
one-line-registration addition rather than a generator rewrite.
"""
from app.algorithms.constraints.base import GenerationContext, ModelVariables, SoftConstraint


class PreferredSlotPreference(SoftConstraint):
    key = "preferred_slot"
    name = "Prefer faculty preferred slots"
    weight = 3

    def penalty_terms(self, model, variables: ModelVariables, ctx: GenerationContext) -> list:
        terms = []
        for demand in ctx.demands:
            if not demand.faculty_preferred_slots:
                continue
            for timeslot_id, _room_id, var in variables.by_demand.get(demand.index, []):
                if timeslot_id in demand.faculty_preferred_slots:
                    terms.append(-var)  # negative = bonus: reduces the objective when chosen
        return terms


class AvoidSameDayRepetitionPreference(SoftConstraint):
    """Merges two brief bullets that are the same rule in practice:
    "avoid duplicate subject repetition within the same day" and
    "distribute difficult subjects across the week" - both mean "don't
    cluster a demand's sessions onto one day"."""

    key = "same_day_repetition"
    name = "Avoid duplicate subject repetition within the same day"
    weight = 4

    def penalty_terms(self, model, variables: ModelVariables, ctx: GenerationContext) -> list:
        terms = []
        for (demand_index, _day), vars_here in variables.by_demand_day.items():
            if len(vars_here) < 2:
                continue
            excess = model.new_int_var(0, len(vars_here), f"excess_d{demand_index}")
            model.add(excess >= sum(vars_here) - 1)
            terms.append(excess)
        return terms


class MinimizeGapsPreference(SoftConstraint):
    """Covers both "minimize idle periods" and "reduce timetable gaps" -
    penalizes a section having free periods sandwiched between two
    classes on the same day (as opposed to classes simply ending early)."""

    key = "minimize_gaps"
    name = "Minimize idle periods between classes"
    weight = 2

    def penalty_terms(self, model, variables: ModelVariables, ctx: GenerationContext) -> list:
        terms = []
        periods_by_day: dict[str, list[tuple[int, str]]] = {}
        for timeslot_id, slot in ctx.timeslots_by_id.items():
            if slot.get("is_break"):
                continue
            periods_by_day.setdefault(slot["day_of_week"], []).append((slot.get("slot_order", 0), timeslot_id))

        for day, ordered in periods_by_day.items():
            ordered.sort(key=lambda p: p[0])
            if len(ordered) < 3:
                continue  # no room for a "sandwiched" gap with fewer than 3 periods

            occupied = []
            for _order, timeslot_id in ordered:
                vars_here = variables.by_timeslot.get(timeslot_id, [])
                if not vars_here:
                    occupied.append(None)
                    continue
                is_occupied = model.new_bool_var(f"occ_{timeslot_id}")
                model.add(sum(vars_here) >= 1).only_enforce_if(is_occupied)
                model.add(sum(vars_here) == 0).only_enforce_if(~is_occupied)
                occupied.append(is_occupied)

            n = len(ordered)
            first_idx = model.new_int_var(0, n - 1, f"first_{day}")
            last_idx = model.new_int_var(0, n - 1, f"last_{day}")
            any_occupied_vars = [v for v in occupied if v is not None]
            if not any_occupied_vars:
                continue
            has_any = model.new_bool_var(f"has_any_{day}")
            model.add(sum(any_occupied_vars) >= 1).only_enforce_if(has_any)
            model.add(sum(any_occupied_vars) == 0).only_enforce_if(~has_any)

            for i, is_occ in enumerate(occupied):
                if is_occ is None:
                    continue
                model.add(first_idx <= i).only_enforce_if(is_occ)
                model.add(last_idx >= i).only_enforce_if(is_occ)

            span = model.new_int_var(0, n, f"span_{day}")
            model.add(span == last_idx - first_idx + 1).only_enforce_if(has_any)
            model.add(span == 0).only_enforce_if(~has_any)

            occupied_count = model.new_int_var(0, n, f"count_{day}")
            model.add(occupied_count == sum(any_occupied_vars))

            gap = model.new_int_var(0, n, f"gap_{day}")
            model.add(gap >= span - occupied_count)
            terms.append(gap)

        return terms


class BalanceFacultyDailyLoadPreference(SoftConstraint):
    """Covers "balance faculty workload": penalizes a faculty member's
    *peak* single-day load, nudging the solver to spread their sessions
    across the week rather than clustering them (which also indirectly
    softens "avoid long continuous teaching hours" for the common case
    of many same-day sessions being back-to-back)."""

    key = "balance_faculty_load"
    name = "Balance faculty workload across the week"
    weight = 1

    def penalty_terms(self, model, variables: ModelVariables, ctx: GenerationContext) -> list:
        terms = []
        faculty_days: dict[str, list] = {}
        for (faculty_id, _day), vars_here in variables.by_faculty_day.items():
            faculty_days.setdefault(faculty_id, []).append(vars_here)

        for faculty_id, day_groups in faculty_days.items():
            daily_counts = []
            max_possible = 0
            for i, vars_here in enumerate(day_groups):
                if not vars_here:
                    continue
                upper_bound = len(vars_here)
                max_possible = max(max_possible, upper_bound)
                count = model.new_int_var(0, upper_bound, f"load_{faculty_id}_{i}")
                model.add(count == sum(vars_here))
                daily_counts.append(count)
            if len(daily_counts) < 2:
                continue
            peak = model.new_int_var(0, max_possible, f"peak_{faculty_id}")
            model.add_max_equality(peak, daily_counts)
            terms.append(peak)
        return terms


#: Every soft constraint, in the order their terms are added to the
#: objective. Extending the engine (e.g. "balance room utilization")
#: means appending a new class here.
DEFAULT_SOFT_CONSTRAINTS: list[SoftConstraint] = [
    PreferredSlotPreference(),
    AvoidSameDayRepetitionPreference(),
    MinimizeGapsPreference(),
    BalanceFacultyDailyLoadPreference(),
]

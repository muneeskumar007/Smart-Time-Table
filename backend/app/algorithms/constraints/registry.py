"""
The constraint registry - the one place that knows the full list of
active hard/soft constraints. algorithms/generator.py imports only from
here, never from hard_constraints.py or soft_constraints.py directly, so
adding a new rule is always a two-line change (define the class, add it
to one of the lists below) with zero changes anywhere else.
"""
from app.algorithms.constraints.base import HardConstraint, SoftConstraint
from app.algorithms.constraints.hard_constraints import DEFAULT_HARD_CONSTRAINTS
from app.algorithms.constraints.soft_constraints import DEFAULT_SOFT_CONSTRAINTS


def get_hard_constraints() -> list[HardConstraint]:
    return list(DEFAULT_HARD_CONSTRAINTS)


def get_soft_constraints() -> list[SoftConstraint]:
    return list(DEFAULT_SOFT_CONSTRAINTS)

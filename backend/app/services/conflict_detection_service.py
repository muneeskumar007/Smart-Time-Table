"""
Conflict detection service.

Deliberately thin: all the actual rule logic lives in each
HardConstraint's `.check()` method (see algorithms/constraints/), so
this service is just "run every registered rule against this entry list
and collect the results." That's what makes conflict detection at
POST /timetable/validate, pre-publish validation, and every manual edit
all go through the exact same rules the generator itself enforces -
there is no second, parallel implementation to drift out of sync.
"""
from app.algorithms.constraints.base import GenerationContext
from app.algorithms.constraints.registry import get_hard_constraints
from app.schemas.timetable import Conflict, ValidationResult


class ConflictDetectionService:
    def validate_entries(self, entries: list[dict], ctx: GenerationContext) -> ValidationResult:
        conflicts: list[Conflict] = []
        for constraint in get_hard_constraints():
            conflicts.extend(constraint.check(entries, ctx))
        return ValidationResult(is_valid=len(conflicts) == 0, conflicts=conflicts)

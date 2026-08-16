"""Single source of truth for "HH:MM" time-string handling, used by Time
Slot validation (schemas), overlap detection (repository) and update
validation (service) - previously duplicated across two of those, which
is exactly the kind of drift-prone repetition this module exists to
prevent."""
import re

TIME_PATTERN = re.compile(r"^([01]\d|2[0-3]):([0-5]\d)$")


def is_valid_time_format(value: str) -> bool:
    return bool(TIME_PATTERN.match(value))


def time_str_to_minutes(value: str) -> int:
    hours, minutes = value.split(":")
    return int(hours) * 60 + int(minutes)

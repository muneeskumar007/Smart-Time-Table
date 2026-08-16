"""
Centralised logging setup.

Call configure_logging() once at startup (see main.py). Every module then
gets its logger via get_logger(__name__) and inherits the same handler
and formatting, so logs stay consistent whether they come from auth,
CRUD operations, or the timetable engine added in a later phase.
"""
import logging
import sys


def configure_logging(level: str = "INFO") -> None:
    root = logging.getLogger("app")
    root.setLevel(level.upper())

    if root.handlers:
        # Avoid duplicate handlers if configure_logging() is called twice
        # (e.g. under a reloader).
        return

    handler = logging.StreamHandler(sys.stdout)
    formatter = logging.Formatter(
        fmt="%(asctime)s | %(levelname)-8s | %(name)s | %(message)s",
        datefmt="%Y-%m-%d %H:%M:%S",
    )
    handler.setFormatter(formatter)
    root.addHandler(handler)
    root.propagate = False


def get_logger(name: str) -> logging.Logger:
    return logging.getLogger(f"app.{name}")

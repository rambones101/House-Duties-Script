"""
House Duties Scheduler Package

A modular chore scheduling system with persistent state tracking,
fairness algorithms, and deck-based organization.
"""

__version__ = "1.2.0"

# Import all public APIs for backward compatibility
from .models import TaskTemplate, Occurrence
from .utils import (
    DOW,
    most_recent_sunday,
    parse_start_sunday,
    week_start_for,
    dt_on,
    unique_sorted_days,
    week_index_from_anchor
)
from .state import (
    load_state,
    save_state,
    get_anchor_sunday,
    load_brothers,
    load_categories,
    load_constraints,
    DEFAULT_CONSTRAINTS
)
from .output import (
    write_csv,
    write_json,
    print_schedule_by_deck,
    DECK_ORDER
)
from .templates import build_templates, default_severity_for
from .assignment import assign_chores, is_banned, preference_bonus
from .bonus import choose_bonus_tasks_for_week, stable_int_from_strings
from .scheduler import occurrences_from_templates

__all__ = [
    "__version__",
    # Models
    "TaskTemplate",
    "Occurrence",
    # Utils
    "DOW",
    "most_recent_sunday",
    "parse_start_sunday",
    "week_start_for",
    "dt_on",
    "unique_sorted_days",
    "week_index_from_anchor",
    # State
    "load_state",
    "save_state",
    "get_anchor_sunday",
    "load_brothers",
    "load_categories",
    "load_constraints",
    "DEFAULT_CONSTRAINTS",
    # Output
    "write_csv",
    "write_json",
    "print_schedule_by_deck",
    "DECK_ORDER",
    # Templates
    "build_templates",
    "default_severity_for",
    # Assignment
    "assign_chores",
    "is_banned",
    "preference_bonus",
    # Bonus
    "choose_bonus_tasks_for_week",
    "stable_int_from_strings",
    # Scheduler
    "occurrences_from_templates",
]

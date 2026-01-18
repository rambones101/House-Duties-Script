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

__all__ = [
    "__version__",
    "TaskTemplate",
    "Occurrence",
    "DOW",
    "most_recent_sunday",
    "parse_start_sunday",
    "week_start_for",
    "dt_on",
    "unique_sorted_days",
    "week_index_from_anchor",
    "load_state",
    "save_state",
    "get_anchor_sunday",
    "load_brothers",
    "load_categories",
    "load_constraints",
    "DEFAULT_CONSTRAINTS",
    "write_csv",
    "write_json",
    "print_schedule_by_deck",
    "DECK_ORDER",
]

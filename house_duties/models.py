"""Data models for House Duties Scheduler."""
from dataclasses import dataclass
from datetime import datetime
from typing import List, Optional


@dataclass(frozen=True)
class TaskTemplate:
    """Template defining a recurring chore."""
    key: str
    label: str
    deck: str           # Deck name for grouping (Zero/First/Second/Third/Other)
    category: str       # k&m, bathrooms, floors, laundry, common, other
    people_needed: int
    cadence: str        # "weekly", "biweekly", "n_per_week"
    days_of_week: Optional[List[int]] = None
    times_per_week: Optional[int] = None
    preferred_days: Optional[List[int]] = None
    severity: int = 3
    effort_multiplier: float = 1.0
    flexible_2_3x: bool = False


@dataclass
class Occurrence:
    """A specific instance of a task on a particular date."""
    task_key: str
    task_label: str
    deck: str
    category: str
    people_needed: int
    due_dt: datetime
    week_index: int
    weight: float

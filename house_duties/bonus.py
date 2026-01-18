"""Bonus third cleaning selection for flexible 2-3x/week tasks."""
from typing import List, Dict, Any
import hashlib
from .models import TaskTemplate


def week_capacity_allows_bonus(house_size: int, min_roster: int = 14) -> bool:
    """Check if roster size is large enough to support bonus 3rd cleanings."""
    return house_size >= min_roster


def stable_int_from_strings(*parts: str) -> int:
    """Generate deterministic integer from string inputs for reproducible randomness."""
    combined = "|".join(str(p) for p in parts)
    digest = hashlib.md5(combined.encode("utf-8")).hexdigest()
    return int(digest[:8], 16)


def choose_bonus_tasks_for_week(
    templates: List[TaskTemplate],
    anchor_sunday: str,
    week_index: int,
    roster_size: int,
    bonus_counts: Dict[str, int],
    seed_offset: int = 0,
    min_roster: int = 14
) -> List[str]:
    """
    Select which flexible_2_3x tasks get a bonus 3rd cleaning this week.
    
    Uses deterministic selection based on:
    - anchor_sunday: Ensures consistency across runs for same week
    - week_index: Varies selection week-to-week
    - roster_size: Part of seed for stability
    - seed_offset: Optional seed variation
    
    Priority order: bathrooms > floors > common areas
    Among same category, tasks with lower bonus_counts are favored.
    
    Returns:
        List of task_keys that get bonus 3rd cleaning
    """
    if not week_capacity_allows_bonus(roster_size, min_roster):
        return []
    
    # Filter eligible tasks
    eligible = [t for t in templates if t.flexible_2_3x]
    if not eligible:
        return []
    
    # Priority categories
    category_priority = {
        "bathrooms": 3,
        "floors": 2,
        "common": 1,
        "k&m": 1,
        "laundry": 0,
        "other": 0
    }
    
    # Sort by: priority desc, bonus_count asc, then stable hash
    def sort_key(t: TaskTemplate):
        priority = category_priority.get(t.category, 0)
        count = bonus_counts.get(t.key, 0)
        # Stable tie-breaker
        seed_val = stable_int_from_strings(anchor_sunday, str(week_index), t.key, str(seed_offset))
        return (-priority, count, seed_val)
    
    eligible.sort(key=sort_key)
    
    # Select top 40% (minimum 1, maximum 3)
    num_to_pick = max(1, min(3, len(eligible) * 2 // 5))
    selected = [t.key for t in eligible[:num_to_pick]]
    
    return selected

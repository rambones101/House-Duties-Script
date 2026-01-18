"""Assignment logic for distributing chores to brothers with fairness algorithms."""
from typing import List, Dict, Tuple, Any, Set
from collections import defaultdict
import random
from .models import Occurrence
from .utils import DOW


def normalize_set(x) -> Set[str]:
    return set(s.strip() for s in x) if isinstance(x, (list, set)) else set()


def is_banned(brother: str, occ: Occurrence, constraints: Dict[str, Any]) -> bool:
    """Check if a brother is banned from a specific task or category."""
    cat_bans = constraints.get("brother_category_bans", {}).get(brother, [])
    task_bans = constraints.get("brother_task_bans", {}).get(brother, [])
    return occ.category in cat_bans or occ.task_key in task_bans


def preference_bonus(brother: str, category: str, constraints: Dict[str, Any]) -> float:
    """Return bonus (negative = better score) if brother prefers this category."""
    prefs = constraints.get("brother_preferred_categories", {}).get(brother, [])
    return -0.35 if category in prefs else 0.0


def assign_chores(
    occs: List[Occurrence],
    brothers: List[str],
    constraints: Dict[str, Any],
    state: Dict[str, Any],
    random_seed: int = 42
) -> Tuple[List[Dict[str, Any]], Dict[str, Any]]:
    """
    Assign brothers to chores using fairness-based greedy algorithm.
    
    Returns:
        Tuple of (schedule_items, updated_state)
    
    Assignment scoring factors (lower is better):
    - Base load: Brother's cumulative task weight (severity × effort_multiplier)
    - Repeat penalty: Same task history × 1.50
    - Recent penalty: Same task last week × 0.60
    - Day penalty: Same-day task count × 0.75
    - Preference: -0.35 bonus for preferred categories
    - Jitter: Small random value for tie-breaking
    """
    random.seed(random_seed)

    # Constants
    REPEAT_TASK_PENALTY = 1.50
    SAME_DAY_PENALTY = 0.75
    RECENT_WEEK_PENALTY = 0.60
    PREFERENCE_BONUS = -0.35

    # Extract constraints
    exempt_all = normalize_set(constraints.get("exempt_all", []))
    on_call_only = normalize_set(constraints.get("on_call_only", []))
    max_per_day = constraints.get("max_per_brother_per_day", 2)
    max_per_week = constraints.get("max_per_brother_per_week", 5)

    # Build active pool
    normal_pool = [b for b in brothers if b not in exempt_all and b not in on_call_only]
    backup_pool = list(on_call_only)

    # Load history
    brother_task_counts = state.get("brother_task_counts", {})
    last_week_tasks = state.get("brother_last_week_tasks", {})
    this_week_tasks = defaultdict(list)

    # Brother cumulative load
    brother_loads = defaultdict(float)

    # Track assignments by day for same-day penalty
    brother_day_counts = defaultdict(lambda: defaultdict(int))

    schedule = []

    for occ in occs:
        assigned = []
        day_str = occ.due_dt.strftime("%A")

        for _ in range(occ.people_needed):
            pool = normal_pool if normal_pool else backup_pool
            if not pool:
                assigned.append("NO_ONE_AVAILABLE")
                continue

            # Score each brother
            candidates = []
            for bro in pool:
                # Hard constraints
                if is_banned(bro, occ, constraints):
                    continue

                week_count = len(this_week_tasks[bro])
                if week_count >= max_per_week:
                    continue

                day_count = brother_day_counts[bro][occ.due_dt.date()]
                if day_count >= max_per_day:
                    continue

                # Fairness scoring
                base_load = brother_loads[bro]
                
                hist_count = brother_task_counts.get(bro, {}).get(occ.task_key, 0)
                run_count = sum(1 for t in this_week_tasks[bro] if t == occ.task_key)
                repeat_pen = (hist_count + run_count) * REPEAT_TASK_PENALTY
                
                last_week_count = sum(1 for t in last_week_tasks.get(bro, []) if t == occ.task_key)
                recent_pen = last_week_count * RECENT_WEEK_PENALTY
                
                day_pen = day_count * SAME_DAY_PENALTY
                
                pref = preference_bonus(bro, occ.category, constraints)
                
                jitter = random.random() * 0.01

                score = base_load + repeat_pen + recent_pen + day_pen + pref + jitter
                candidates.append((score, bro))

            if not candidates:
                # No one in pool is eligible
                assigned.append("UNASSIGNED")
                continue

            # Pick lowest score
            candidates.sort()
            _, chosen = candidates[0]
            assigned.append(chosen)

            # Update tracking
            brother_loads[chosen] += occ.weight
            this_week_tasks[chosen].append(occ.task_key)
            brother_day_counts[chosen][occ.due_dt.date()] += 1

        # Record assignment
        schedule.append({
            "due": occ.due_dt.isoformat(),
            "deck": occ.deck,
            "task_key": occ.task_key,
            "task": occ.task_label,
            "category": occ.category,
            "people_needed": occ.people_needed,
            "assigned": assigned,
            "weight_total": occ.weight * len(assigned)
        })

    # Update persistent state
    for bro, tasks in this_week_tasks.items():
        for tk in tasks:
            brother_task_counts.setdefault(bro, {})
            brother_task_counts[bro][tk] = brother_task_counts[bro].get(tk, 0) + 1

    state["brother_task_counts"] = brother_task_counts
    state["brother_last_week_tasks"] = dict(this_week_tasks)

    return schedule, state

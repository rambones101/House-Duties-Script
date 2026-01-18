"""
Fraternity House Chore Scheduler (Deck-Organized Output)
- Weekly Sunday runner
- Persistent rotation (biweekly parity + bonus 3rd cleans)
- Constraints / opt-outs
- OUTPUT grouped by DECK (Zero/First/Second/Third) then by Day

Run:
  python chore_scheduler.py

Inputs:
- brothers.txt
- constraints.json (optional)

Outputs:
- schedule.csv (includes deck column)
- schedule.json
- prints deck-organized schedule to terminal
- chore_state.json (persistent rotation + anti-repeat history)
"""

from __future__ import annotations

from dataclasses import dataclass
from datetime import date, datetime, timedelta, time
from typing import List, Dict, Tuple, Optional, Any, Set
import csv
import json
import random
from collections import defaultdict
import os
import hashlib
import logging
import sys
import argparse
from pathlib import Path

# Import validation module
try:
    from house_duties.validation import validate_all, validate_brothers, ValidationError
except ImportError:
    logger = logging.getLogger(__name__)
    logger.warning("Validation module not available - skipping validation")
    validate_all = None
    validate_brothers = None
    ValidationError = ValueError

__version__ = "1.3.0"

# =========================
# CONFIG — EDIT THIS PART
# =========================

ROSTER_FILE = "brothers.txt"
CONSTRAINTS_FILE = "constraints.json"  # optional
CATEGORIES_FILE = "brother_categories.json"  # optional - for pairing rules

# If "", auto-detect most recent Sunday from today (recommended)
START_SUNDAY = ""

WEEKS_TO_GENERATE = 1

# Brasso cadence per deck: "weekly" or "biweekly"
BRASSO_CADENCE_SECOND_DECK = "biweekly"
BRASSO_CADENCE_THIRD_DECK = "biweekly"

DEFAULT_DUE_TIMES = {
    "k&m": time(23, 59),
    "bathrooms": time(23, 59),
    "floors": time(23, 59),
    "laundry": time(23, 59),
    "common": time(23, 59),
    "other": time(23, 59),
}

SEVERITY_OVERRIDES: Dict[str, int] = {
    # "FD_KM_SUN": 5,
}

# --- "2–3x/week" policy ---
BONUS_THIRD_CLEANING_MIN_ROSTER = 14
BONUS_THIRD_CLEANING_MAX_TASK_SHARE = 0.50
BONUS_PRIORITY = {
    "bathrooms": 3,
    "floors": 2,
    "common": 1,
    "laundry": 0,
    "k&m": 0,
    "other": 0,
}
BASE_2X_DAYS_DEFAULT = [2, 4]  # tues, Thu
BONUS_3RD_DAY_DEFAULT = 5      # Fri

STATE_FILE = "chore_state.json"

# Fairness tuning
REPEAT_TASK_PENALTY = 1.50
SAME_DAY_STACK_PENALTY = 0.75
RECENT_WEEK_PENALTY = 0.60

RANDOM_SEED = 42

# Deck ordering for display
DECK_ORDER = ["Zero Deck", "First Deck", "Second Deck", "Third Deck", "Other"]

# =========================
# INTERNALS — DON'T EDIT
# =========================

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s',
    handlers=[
        logging.StreamHandler(sys.stdout),
        logging.FileHandler('house_duties.log', mode='a')
    ]
)
logger = logging.getLogger(__name__)

DOW = ["Sun", "Mon", "Tue", "Wed", "Thu", "Fri", "Sat"]


@dataclass(frozen=True)
class TaskTemplate:
    key: str
    label: str
    deck: str           # NEW: deck name for grouping
    category: str
    people_needed: int
    cadence: str  # "weekly", "biweekly", "n_per_week"
    days_of_week: Optional[List[int]] = None
    times_per_week: Optional[int] = None
    preferred_days: Optional[List[int]] = None
    severity: int = 3
    effort_multiplier: float = 1.0
    flexible_2_3x: bool = False


@dataclass
class Occurrence:
    task_key: str
    task_label: str
    deck: str
    category: str
    people_needed: int
    due_dt: datetime
    week_index: int
    weight: float


# -------------------------
# Dates / week helpers
# -------------------------

def most_recent_sunday(d: date) -> date:
    days_since_sun = (d.weekday() + 1) % 7
    return d - timedelta(days=days_since_sun)

def parse_start_sunday(s: str) -> date:
    if s.strip() == "":
        return most_recent_sunday(date.today())
    return date.fromisoformat(s)

def week_start_for(start_sunday: date, week_index: int) -> date:
    return start_sunday + timedelta(days=7 * week_index)

def dt_on(week_start: date, dow_index: int, due_t: time) -> datetime:
    return datetime.combine(week_start + timedelta(days=dow_index), due_t)

def unique_sorted_days(days: List[int]) -> List[int]:
    return sorted(set(days))


# -------------------------
# State (persistent)
# -------------------------

def load_state(filepath: str) -> Dict[str, Any]:
    """Load persistent state from JSON file with error handling."""
    if not os.path.exists(filepath):
        logger.info(f"State file '{filepath}' not found. Starting with empty state.")
        return {}
    try:
        with open(filepath, "r", encoding="utf-8") as f:
            state = json.load(f)
            logger.info(f"Loaded state from '{filepath}'")
            return state
    except json.JSONDecodeError as e:
        logger.error(f"Invalid JSON in state file '{filepath}': {e}")
        logger.warning("Starting with empty state. Previous state will be backed up.")
        # Backup corrupted file
        backup_path = f"{filepath}.corrupt.bak"
        try:
            os.rename(filepath, backup_path)
            logger.info(f"Corrupted state backed up to '{backup_path}'")
        except OSError:
            pass
        return {}
    except Exception as e:
        logger.error(f"Error reading state file '{filepath}': {e}")
        raise

def save_state(filepath: str, state: Dict[str, Any]) -> None:
    """Save persistent state to JSON file with error handling and backup."""
    try:
        # Validate state before saving
        if not isinstance(state, dict):
            raise ValueError(f"State must be a dictionary, got {type(state)}")
        
        # Create backup of existing state
        if os.path.exists(filepath):
            backup_path = f"{filepath}.bak"
            try:
                with open(filepath, "r", encoding="utf-8") as f:
                    backup_state = json.load(f)
                with open(backup_path, "w", encoding="utf-8") as f:
                    json.dump(backup_state, f, indent=2)
                logger.debug(f"Created backup at '{backup_path}'")
            except Exception as e:
                logger.warning(f"Could not create backup: {e}")
        
        # Write new state
        with open(filepath, "w", encoding="utf-8") as f:
            json.dump(state, f, indent=2)
        logger.info(f"Saved state to '{filepath}'")
    except Exception as e:
        logger.error(f"Error saving state to '{filepath}': {e}")
        raise

def get_anchor_sunday(state: Dict[str, Any], current_sunday: date) -> date:
    anchor = state.get("anchor_sunday")
    if anchor:
        return date.fromisoformat(anchor)
    state["anchor_sunday"] = current_sunday.isoformat()
    return current_sunday

def week_index_from_anchor(anchor_sunday: date, current_sunday: date) -> int:
    return (current_sunday - anchor_sunday).days // 7


# -------------------------
# Roster
# -------------------------

def load_brothers(filepath: str) -> List[str]:
    """Load brother roster from file with validation and error handling."""
    if not os.path.exists(filepath):
        logger.error(f"Roster file '{filepath}' not found")
        raise FileNotFoundError(
            f"Missing roster file: {filepath}\n"
            "Create brothers.txt with one brother name per line."
        )
    
    try:
        brothers: List[str] = []
        with open(filepath, "r", encoding="utf-8") as f:
            for line_num, line in enumerate(f, 1):
                name = line.strip()
                if name and not name.startswith("#"):
                    # Validate name
                    if len(name) > 100:
                        logger.warning(f"Line {line_num}: Name too long (truncating): {name[:50]}...")
                        name = name[:100]
                    if not name.replace(' ', '').replace('-', '').replace("'", '').isalnum():
                        logger.warning(f"Line {line_num}: Name contains unusual characters: {name}")
                    brothers.append(name)
        
        if not brothers:
            logger.error(f"Roster file '{filepath}' is empty or contains only comments")
            raise ValueError("Roster file is empty. Add at least one brother name.")
        
        # Remove duplicates while preserving order
        seen = set()
        out = []
        for b in brothers:
            if b not in seen:
                out.append(b)
                seen.add(b)
            else:
                logger.warning(f"Duplicate brother name removed: {b}")
        
        logger.info(f"Loaded {len(out)} brothers from '{filepath}'")
        return out
    
    except UnicodeDecodeError as e:
        logger.error(f"File encoding error in '{filepath}': {e}")
        raise ValueError(f"Could not read '{filepath}'. Ensure it's saved as UTF-8 text.") from e
    except Exception as e:
        logger.error(f"Error loading brothers from '{filepath}': {e}")
        raise


def load_categories(filepath: str) -> Dict[str, List[str]]:
    """Load brother categories for pairing rules with error handling."""
    if not os.path.exists(filepath):
        logger.debug(f"Categories file '{filepath}' not found. Using empty categories.")
        return {"actives": [], "junior_actives": []}
    
    try:
        with open(filepath, "r", encoding="utf-8") as f:
            data = json.load(f)
        
        # Validate structure
        if not isinstance(data, dict):
            logger.warning(f"Invalid categories file format. Expected dict, got {type(data)}")
            return {"actives": [], "junior_actives": []}
        
        # Ensure all values are lists
        for key, value in data.items():
            if not isinstance(value, list):
                logger.warning(f"Category '{key}' is not a list, converting")
                data[key] = list(value) if hasattr(value, '__iter__') else []
        
        logger.info(f"Loaded categories from '{filepath}'")
        return data
    
    except json.JSONDecodeError as e:
        logger.error(f"Invalid JSON in categories file '{filepath}': {e}")
        return {"actives": [], "junior_actives": []}
    except Exception as e:
        logger.error(f"Error loading categories from '{filepath}': {e}")
        return {"actives": [], "junior_actives": []}


# -------------------------
# Constraints / opt-outs
# -------------------------

DEFAULT_CONSTRAINTS = {
    "exempt_all": [],
    "on_call_only": [],
    "max_per_brother_per_week": None,
    "max_per_brother_per_day": None,
    "min_per_brother_per_week": None,
    "brother_category_bans": {},
    "brother_task_bans": {},
    "brother_preferred_categories": {},
}

def load_constraints(filepath: str) -> Dict[str, Any]:
    """Load constraints file with validation and error handling."""
    if not os.path.exists(filepath):
        logger.debug(f"Constraints file '{filepath}' not found. Using defaults.")
        return DEFAULT_CONSTRAINTS.copy()
    
    try:
        with open(filepath, "r", encoding="utf-8") as f:
            data = json.load(f)
        
        if not isinstance(data, dict):
            logger.warning(f"Invalid constraints format. Expected dict, got {type(data)}")
            return DEFAULT_CONSTRAINTS.copy()
        
        merged = DEFAULT_CONSTRAINTS.copy()
        merged.update(data or {})
        
        # Validate numeric constraints
        for key in ['max_per_brother_per_week', 'max_per_brother_per_day', 'min_per_brother_per_week']:
            if key in merged and merged[key] is not None:
                try:
                    merged[key] = int(merged[key])
                    if merged[key] < 0:
                        logger.warning(f"Constraint '{key}' is negative, ignoring")
                        merged[key] = None
                except (ValueError, TypeError):
                    logger.warning(f"Invalid value for '{key}', ignoring")
                    merged[key] = None
        
        logger.info(f"Loaded constraints from '{filepath}'")
        return merged
    
    except json.JSONDecodeError as e:
        logger.error(f"Invalid JSON in constraints file '{filepath}': {e}")
        logger.warning("Using default constraints")
        return DEFAULT_CONSTRAINTS.copy()
    except Exception as e:
        logger.error(f"Error loading constraints from '{filepath}': {e}")
        return DEFAULT_CONSTRAINTS.copy()

def normalize_set(x) -> Set[str]:
    return set([str(v).strip() for v in (x or []) if str(v).strip()])

def is_banned(brother: str, occ: Occurrence, constraints: Dict[str, Any]) -> bool:
    cat_bans = constraints.get("brother_category_bans", {}).get(brother, []) or []
    task_bans = constraints.get("brother_task_bans", {}).get(brother, []) or []
    return (occ.category in set(cat_bans)) or (occ.task_key in set(task_bans))

def preference_bonus(brother: str, category: str, constraints: Dict[str, Any]) -> float:
    prefs = constraints.get("brother_preferred_categories", {}).get(brother, []) or []
    return -0.35 if category in set(prefs) else 0.0


# -------------------------
# Severity defaults
# -------------------------

def default_severity_for(label: str, category: str) -> int:
    if label.lower() == "k&m":
        return 5
    if category == "bathrooms":
        return 4
    if category == "floors":
        return 3
    if category == "laundry":
        return 2
    if category == "common":
        return 3
    return 3


# -------------------------
# Bonus selection (rotating)
# -------------------------

def week_capacity_allows_bonus(house_size: int) -> bool:
    return house_size >= BONUS_THIRD_CLEANING_MIN_ROSTER

def stable_int_from_strings(*parts: str) -> int:
    h = hashlib.sha256("||".join(parts).encode("utf-8")).hexdigest()
    return int(h[:12], 16)

def choose_bonus_tasks_for_week(templates: List[TaskTemplate],
                                house_size: int,
                                anchor_sunday: date,
                                current_sunday: date,
                                brothers: List[str],
                                state: Dict[str, Any]) -> set[str]:
    flex = [t for t in templates if t.flexible_2_3x]
    if not flex or not week_capacity_allows_bonus(house_size):
        return set()

    max_bonus = int(round(len(flex) * BONUS_THIRD_CLEANING_MAX_TASK_SHARE))
    if max_bonus <= 0:
        return set()

    bonus_counts: Dict[str, int] = state.setdefault("bonus_counts", {})
    for t in flex:
        bonus_counts.setdefault(t.key, 0)

    roster_sig = ",".join(sorted(brothers))
    widx = week_index_from_anchor(anchor_sunday, current_sunday)
    seed_val = stable_int_from_strings(str(anchor_sunday), str(widx), roster_sig, str(RANDOM_SEED))
    rng = random.Random(seed_val)

    scored = []
    for t in flex:
        count = int(bonus_counts.get(t.key, 0))
        catp = BONUS_PRIORITY.get(t.category, 0)
        scored.append((count, -catp, -t.severity, t.key))
    scored.sort()

    pool = [k for *_, k in scored[: max_bonus * 2]]
    rng.shuffle(pool)
    bonus = set(pool[:max_bonus])

    for k in bonus:
        bonus_counts[k] = int(bonus_counts.get(k, 0)) + 1

    return bonus


# -------------------------
# Task templates (your chores)
# -------------------------

def build_templates() -> List[TaskTemplate]:
    templates: List[TaskTemplate] = []

    def add(key, deck, label, category, people, cadence,
            days=None, times_per_week=None, preferred_days=None,
            severity=None, effort_multiplier=1.0, flexible_2_3x=False):
        sev = severity if severity is not None else default_severity_for(label, category)
        sev = SEVERITY_OVERRIDES.get(key, SEVERITY_OVERRIDES.get(label, sev))
        templates.append(TaskTemplate(
            key=key,
            deck=deck,
            label=label,
            category=category,
            people_needed=people,
            cadence=cadence,
            days_of_week=days,
            times_per_week=times_per_week,
            preferred_days=preferred_days,
            severity=sev,
            effort_multiplier=effort_multiplier,
            flexible_2_3x=flexible_2_3x
        ))

    # -------- Zero Deck --------
    add("ZD_RATSKELLER_FLOOR", "Zero Deck", "Ratskeller Sweep+Mop", "floors", 2,
        "n_per_week", times_per_week=2, preferred_days=BASE_2X_DAYS_DEFAULT,
        effort_multiplier=1.1, flexible_2_3x=True)

    add("ZD_GAMEX_FLOOR", "Zero Deck", "Game Room + X-Room Sweep+Mop", "floors", 2,
        "n_per_week", times_per_week=2, preferred_days=BASE_2X_DAYS_DEFAULT,
        effort_multiplier=1.1, flexible_2_3x=True)

    add("ZD_LAUNDRY", "Zero Deck", "Laundry Room Clean", "laundry", 1,
        "weekly", days=[6], effort_multiplier=1.0)

    # -------- First Deck --------
    add("FD_KM_SUN", "First Deck", "k&m", "k&m", 3, "weekly", days=[0], effort_multiplier=1.2)
    add("FD_KM_MON", "First Deck", "k&m", "k&m", 2, "weekly", days=[1], effort_multiplier=1.1)
    add("FD_KM_TUE", "First Deck", "k&m", "k&m", 2, "weekly", days=[2], effort_multiplier=1.1)
    add("FD_KM_WED", "First Deck", "k&m", "k&m", 2, "weekly", days=[3], effort_multiplier=1.1)
    add("FD_KM_THU", "First Deck", "k&m", "k&m", 2, "weekly", days=[4], effort_multiplier=1.1)

    add("FD_LIVING_FLOOR", "First Deck", "Living Room Sweep+Mop", "floors", 2,
        "n_per_week", times_per_week=2, preferred_days=BASE_2X_DAYS_DEFAULT,
        effort_multiplier=1.05, flexible_2_3x=True)

    add("FD_DINING_FLOOR", "First Deck", "Dining Room Sweep+Mop", "floors", 2,
        "n_per_week", times_per_week=2, preferred_days=BASE_2X_DAYS_DEFAULT,
        effort_multiplier=1.05, flexible_2_3x=True)

    # -------- Second Deck --------
    add("SD_HALL_FLOOR", "Second Deck", "Hallway Sweep+Mop", "floors", 2,
        "n_per_week", times_per_week=2, preferred_days=BASE_2X_DAYS_DEFAULT, flexible_2_3x=True)

    add("SD_SINKS", "Second Deck", "Sinks Clean/Sweep Bathroom", "bathrooms", 1,
        "n_per_week", times_per_week=2, preferred_days=BASE_2X_DAYS_DEFAULT, flexible_2_3x=True)

    add("SD_TOILETS", "Second Deck", "Toilets Clean/Mop Bathroom", "bathrooms", 1,
        "n_per_week", times_per_week=2, preferred_days=BASE_2X_DAYS_DEFAULT, flexible_2_3x=True)

    add("SD_SHOWERS", "Second Deck", "Showers Clean", "bathrooms", 2,
        "weekly", days=[6], effort_multiplier=1.2)

    add("SD_STAIRS_FLOOR", "Second Deck", "Stairs Sweep+Mop", "floors", 2,
        "n_per_week", times_per_week=2, preferred_days=BASE_2X_DAYS_DEFAULT,
        effort_multiplier=1.1, flexible_2_3x=True)

    add("SD_LROOM", "Second Deck", "L-Room Clean", "common", 1, "weekly", days=[6])
    add("SD_LIBRARY", "Second Deck", "Library Clean", "common", 1, "weekly", days=[6])
    # add("SD_WINDOW_FRAMES", "Second Deck", "Window Frames Clean", "common", 1, "weekly", days=[6])

    if BRASSO_CADENCE_SECOND_DECK == "biweekly":
        add("SD_BRASSO", "Second Deck", "Brasso", "other", 1, "biweekly", days=[6], severity=3)
    else:
        add("SD_BRASSO", "Second Deck", "Brasso", "other", 1, "weekly", days=[6], severity=3)

    add("SD_BLUE", "Second Deck", "Blue", "other", 1, "biweekly", days=[6], severity=3)

    # -------- Third Deck --------
    add("TD_HALL_FLOOR", "Third Deck", "Hallway Sweep+Mop", "floors", 2,
        "n_per_week", times_per_week=2, preferred_days=BASE_2X_DAYS_DEFAULT, flexible_2_3x=True)

    add("TD_SINKS", "Third Deck", "Sinks Clean/Sweep Bathroom", "bathrooms", 1,
        "n_per_week", times_per_week=2, preferred_days=BASE_2X_DAYS_DEFAULT, flexible_2_3x=True)

    add("TD_TOILETS", "Third Deck", "Toilets Clean/Mop Bathroom", "bathrooms", 1,
        "n_per_week", times_per_week=2, preferred_days=BASE_2X_DAYS_DEFAULT, flexible_2_3x=True)

    add("TD_SHOWERS", "Third Deck", "Showers Clean", "bathrooms", 2,
        "weekly", days=[6], effort_multiplier=1.2)

    add("TD_STAIRS_FLOOR", "Third Deck", "Stairs Sweep+Mop", "floors", 2,
        "n_per_week", times_per_week=2, preferred_days=BASE_2X_DAYS_DEFAULT,
        effort_multiplier=1.1, flexible_2_3x=True)

    if BRASSO_CADENCE_THIRD_DECK == "biweekly":
        add("TD_BRASSO", "Third Deck", "Brasso", "other", 1, "biweekly", days=[6], severity=3)
    else:
        add("TD_BRASSO", "Third Deck", "Brasso", "other", 1, "weekly", days=[6], severity=3)

    add("TD_BLUE", "Third Deck", "Blue", "other", 1, "biweekly", days=[6], severity=3)

    return templates


# -------------------------
# Occurrence expansion
# -------------------------

def occurrences_from_templates(templates: List[TaskTemplate],
                               anchor_sunday: date,
                               current_sunday: date,
                               weeks: int,
                               brothers: List[str],
                               state: Dict[str, Any]) -> List[Occurrence]:
    house_size = len(brothers)
    occs: List[Occurrence] = []

    for w in range(weeks):
        ws = week_start_for(current_sunday, w)
        widx = week_index_from_anchor(anchor_sunday, ws)

        bonus_keys = choose_bonus_tasks_for_week(
            templates=templates,
            house_size=house_size,
            anchor_sunday=anchor_sunday,
            current_sunday=ws,
            brothers=brothers,
            state=state
        )

        for tpl in templates:
            if tpl.cadence == "biweekly" and (widx % 2 == 1):
                continue

            due_t = DEFAULT_DUE_TIMES.get(tpl.category, DEFAULT_DUE_TIMES["other"])

            if tpl.cadence in ("weekly", "biweekly"):
                days = tpl.days_of_week or [6]
                for d in days:
                    due_dt = dt_on(ws, d, due_t)
                    weight = tpl.severity * tpl.effort_multiplier * tpl.people_needed
                    occs.append(Occurrence(tpl.key, tpl.label, tpl.deck, tpl.category, tpl.people_needed, due_dt, widx, weight))

            elif tpl.cadence == "n_per_week":
                times = tpl.times_per_week or 1
                preferred = tpl.preferred_days or BASE_2X_DAYS_DEFAULT
                chosen_days = preferred[:times]

                if tpl.flexible_2_3x and tpl.key in bonus_keys:
                    chosen_days = chosen_days + [BONUS_3RD_DAY_DEFAULT]

                for d in unique_sorted_days(chosen_days):
                    due_dt = dt_on(ws, d, due_t)
                    weight = tpl.severity * tpl.effort_multiplier * tpl.people_needed
                    occs.append(Occurrence(tpl.key, tpl.label, tpl.deck, tpl.category, tpl.people_needed, due_dt, widx, weight))
            else:
                raise ValueError(f"Unknown cadence: {tpl.cadence}")

    occs.sort(key=lambda o: (o.due_dt, -o.weight, o.deck, o.task_label))
    return occs


# -------------------------
# Assignment (constraints + history)
# -------------------------

def assign_chores(occs: List[Occurrence],
                  brothers: List[str],
                  state: Dict[str, Any],
                  constraints: Dict[str, Any],
                  current_sunday: date,
                  categories: Dict[str, List[str]]) -> Dict[str, Any]:
    # random.seed(RANDOM_SEED)  # Disabled for truly random assignments

    exempt_all = normalize_set(constraints.get("exempt_all"))
    on_call_only = normalize_set(constraints.get("on_call_only"))
    
    # Load active categories for pairing rules
    actives_set = set(categories.get("actives", []))

    active = [b for b in brothers if b not in exempt_all]
    if not active:
        raise ValueError("All brothers are exempted this week. Remove someone from exempt_all.")

    normal_pool = [b for b in active if b not in on_call_only]
    on_call_pool = [b for b in active if b in on_call_only]

    hist_task_counts: Dict[str, Dict[str, int]] = state.setdefault("brother_task_counts", {})
    hist_last_week: Dict[str, Dict[str, int]] = state.setdefault("brother_last_week_tasks", {})

    for b in active:
        hist_task_counts.setdefault(b, {})
        hist_last_week.setdefault(b, {})

    total_load = defaultdict(float)
    day_load = defaultdict(lambda: defaultdict(int))
    run_task_counts = defaultdict(lambda: defaultdict(int))
    run_week_count = defaultdict(int)

    max_per_week = constraints.get("max_per_brother_per_week", None)
    max_per_day = constraints.get("max_per_brother_per_day", None)

    schedule_items: List[Dict[str, Any]] = []

    def under_caps(b: str, due_day: date) -> bool:
        if max_per_week is not None and run_week_count[b] >= int(max_per_week):
            return False
        if max_per_day is not None and day_load[b][due_day] >= int(max_per_day):
            return False
        return True

    def base_candidates(occ: Occurrence) -> List[str]:
        c = []
        for b in normal_pool:
            if b in chosen:
                continue
            if is_banned(b, occ, constraints):
                continue
            if not under_caps(b, due_day):
                continue
            c.append(b)
        return c

    def on_call_candidates(occ: Occurrence) -> List[str]:
        c = []
        for b in on_call_pool:
            if b in chosen:
                continue
            if is_banned(b, occ, constraints):
                continue
            if not under_caps(b, due_day):
                continue
            c.append(b)
        return c

    def relaxed_candidates(occ: Occurrence) -> List[str]:
        c = []
        for b in (normal_pool + on_call_pool):
            if b in chosen:
                continue
            if is_banned(b, occ, constraints):
                continue
            c.append(b)
        return c

    for occ in occs:
        due_day = occ.due_dt.date()
        chosen: List[str] = []
        
        # For multi-person tasks, ensure at least 1 active is assigned
        need_active = occ.people_needed >= 2 and actives_set
        has_active = False

        for slot_index in range(occ.people_needed):
            candidates = base_candidates(occ)
            if not candidates:
                candidates = on_call_candidates(occ)
            if not candidates:
                candidates = relaxed_candidates(occ)
            if not candidates:
                raise ValueError(f"No eligible brothers for {occ.task_key} ({occ.task_label}). Check constraints.")
            
            # If this is a multi-person task and we need an active, prioritize them for first slot
            if need_active and not has_active and slot_index == 0:
                active_candidates = [c for c in candidates if c in actives_set]
                if active_candidates:
                    candidates = active_candidates

            def score(b: str) -> float:
                # RANDOM ASSIGNMENT MODE - ignores fairness penalties
                return random.random()

            candidates.sort(key=score)
            pick = candidates[0]
            chosen.append(pick)
            
            # Track if we've assigned an active
            if pick in actives_set:
                has_active = True

            indiv_weight = occ.weight / occ.people_needed
            total_load[pick] += indiv_weight
            day_load[pick][due_day] += 1
            run_task_counts[pick][occ.task_key] += 1
            run_week_count[pick] += 1

        schedule_items.append({
            "task_key": occ.task_key,
            "task": occ.task_label,
            "deck": occ.deck,
            "category": occ.category,
            "due": occ.due_dt.isoformat(sep=" ", timespec="minutes"),
            "people_needed": occ.people_needed,
            "assigned": chosen,
            "weight_total": round(occ.weight, 2),
        })

    new_last_week: Dict[str, Dict[str, int]] = {b: {} for b in active}
    for b in active:
        for task_key, cnt in run_task_counts[b].items():
            hist_task_counts[b][task_key] = int(hist_task_counts[b].get(task_key, 0)) + int(cnt)
            new_last_week[b][task_key] = int(cnt)

    state["brother_task_counts"] = hist_task_counts
    state["brother_last_week_tasks"] = new_last_week
    state["last_run_sunday"] = current_sunday.isoformat()

    return {"schedule_items": schedule_items, "state": state}


# -------------------------
# Output (grouped by deck)
# -------------------------

def deck_sort_key(deck: str) -> int:
    try:
        return DECK_ORDER.index(deck)
    except ValueError:
        return len(DECK_ORDER)

def print_schedule_by_deck(schedule_items: List[Dict[str, Any]],
                           current_sunday: date,
                           anchor_sunday: date,
                           house_size: int):
    week_end = current_sunday + timedelta(days=6)
    widx = week_index_from_anchor(anchor_sunday, current_sunday)

    print(f"\n{'='*60}")
    print(f"HOUSE DUTIES SCHEDULE")
    print(f"{'='*60}")
    print(f"Week: {current_sunday.isoformat()} (Sun) -> {week_end.isoformat()} (Sat)")
    print(f"Roster size: {house_size} brothers")
    print(f"Biweekly parity: week_index={widx} | {'EVEN' if (widx%2==0) else 'ODD'}")
    print(f"{'='*60}\n")

    # Group by due date -> deck -> items
    by_date: Dict[str, Dict[str, List[Dict[str, Any]]]] = defaultdict(lambda: defaultdict(list))
    for item in schedule_items:
        d = item["due"].split(" ")[0]
        by_date[d][item["deck"]].append(item)

    # Iterate through dates in chronological order
    for date_str in sorted(by_date.keys()):
        dt = date.fromisoformat(date_str)
        dow = DOW[(dt.weekday() + 1) % 7]
        
        print(f"\n**{dow} {date_str}**")
        print(f"{'-'*60}")
        
        # Iterate through decks in proper order for this date
        date_decks = by_date[date_str]
        for deck in sorted(date_decks.keys(), key=deck_sort_key):
            print(f"\n\n  {deck}:")
            
            # Sort items by due time, then task name
            for item in sorted(date_decks[deck], key=lambda x: (x["due"], x["task"])):
                due_time = item["due"].split(" ")[1]
                assigned = ", ".join(item["assigned"])
                print(f"    - {item['task']}")
                print(f"      > Assigned: {assigned} ({item['people_needed']} person{'s' if item['people_needed'] > 1 else ''})")
                print()  # Add blank line between tasks
        
        print(f"\n{'='*60}\n")


def write_csv(schedule_items: List[Dict[str, Any]], filepath: str):
    rows = []
    for item in schedule_items:
        rows.append({
            "due": item["due"],
            "deck": item["deck"],
            "task_key": item["task_key"],
            "task": item["task"],
            "category": item["category"],
            "people_needed": item["people_needed"],
            "assigned": ", ".join(item["assigned"]),
            "weight_total": item["weight_total"],
        })
    rows.sort(key=lambda r: (r["deck"], r["due"]))
    with open(filepath, "w", newline="", encoding="utf-8") as f:
        writer = csv.DictWriter(f, fieldnames=[
            "due", "deck", "task_key", "task", "category", "people_needed", "assigned", "weight_total"
        ])
        writer.writeheader()
        writer.writerows(rows)


def write_json(schedule_items: List[Dict[str, Any]], filepath: str):
    """Write schedule to JSON file with error handling."""
    try:
        # Convert datetime objects to ISO format strings
        serializable_items = []
        for item in schedule_items:
            serializable = item.copy()
            if "due_dt" in serializable and isinstance(serializable["due_dt"], datetime):
                serializable["due_dt"] = serializable["due_dt"].isoformat()
            serializable_items.append(serializable)
        
        with open(filepath, "w", encoding="utf-8") as f:
            json.dump(serializable_items, f, indent=2)
        
        logger.info(f"Wrote {len(serializable_items)} schedule items to '{filepath}'")
    
    except Exception as e:
        logger.error(f"Error writing JSON to '{filepath}': {e}")
        raise


# -------------------------
# Command-Line Interface
# -------------------------

def parse_arguments() -> argparse.Namespace:
    """Parse command-line arguments."""
    parser = argparse.ArgumentParser(
        description="House Duties Scheduler - Automated chore assignment system",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  # Basic usage (uses defaults)
  python house_duties.py
  
  # Generate 2 weeks starting from specific date
  python house_duties.py --weeks 2 --start-date 2026-01-19
  
  # Use custom files
  python house_duties.py --roster my_brothers.txt --constraints my_rules.json
  
  # Preview without saving (dry run)
  python house_duties.py --dry-run
  
  # Specify output directory
  python house_duties.py --output-dir ./schedules/
  
  # Verbose logging
  python house_duties.py -v
  
  # Quiet mode (errors only)
  python house_duties.py -q
"""
    )
    
    # Input files
    parser.add_argument(
        '--roster',
        default=ROSTER_FILE,
        help=f'Path to brothers roster file (default: {ROSTER_FILE})'
    )
    parser.add_argument(
        '--constraints',
        default=CONSTRAINTS_FILE,
        help=f'Path to constraints file (default: {CONSTRAINTS_FILE})'
    )
    parser.add_argument(
        '--categories',
        default=CATEGORIES_FILE,
        help=f'Path to categories file (default: {CATEGORIES_FILE})'
    )
    parser.add_argument(
        '--state',
        default=STATE_FILE,
        help=f'Path to state file (default: {STATE_FILE})'
    )
    
    # Schedule generation
    parser.add_argument(
        '--weeks',
        type=int,
        default=WEEKS_TO_GENERATE,
        help=f'Number of weeks to generate (default: {WEEKS_TO_GENERATE})'
    )
    parser.add_argument(
        '--start-date',
        default=START_SUNDAY,
        help='Start date (YYYY-MM-DD). If empty, uses most recent Sunday (default: auto-detect)'
    )
    
    # Output options
    parser.add_argument(
        '--output-dir',
        default='.',
        help='Directory for output files (default: current directory)'
    )
    parser.add_argument(
        '--output-csv',
        help='Custom name for CSV output (default: schedule.csv)'
    )
    parser.add_argument(
        '--output-json',
        help='Custom name for JSON output (default: schedule.json)'
    )
    parser.add_argument(
        '--dry-run',
        action='store_true',
        help='Preview schedule without saving any files'
    )
    parser.add_argument(
        '--no-display',
        action='store_true',
        help='Skip terminal display of schedule'
    )
    parser.add_argument(
        '--ignore-validation-errors',
        action='store_true',
        help='Continue execution even if validation fails (not recommended)'
    )
    
    # Logging
    parser.add_argument(
        '-v', '--verbose',
        action='store_true',
        help='Enable verbose logging (DEBUG level)'
    )
    parser.add_argument(
        '-q', '--quiet',
        action='store_true',
        help='Quiet mode - only show errors'
    )
    parser.add_argument(
        '--log-file',
        default='house_duties.log',
        help='Path to log file (default: house_duties.log)'
    )
    
    # Version
    parser.add_argument(
        '--version',
        action='version',
        version=f'%(prog)s {__version__}'
    )
    
    args = parser.parse_args()
    
    # Validation
    if args.weeks < 1:
        parser.error('--weeks must be at least 1')
    
    if args.start_date:
        try:
            date.fromisoformat(args.start_date)
        except ValueError:
            parser.error(f'Invalid date format: {args.start_date}. Use YYYY-MM-DD')
    
    return args


def configure_logging(args: argparse.Namespace) -> None:
    """Configure logging based on command-line arguments."""
    # Determine log level
    if args.verbose:
        level = logging.DEBUG
    elif args.quiet:
        level = logging.ERROR
    else:
        level = logging.INFO
    
    # Configure handlers
    handlers = [logging.StreamHandler(sys.stdout)]
    
    if not args.dry_run:
        handlers.append(logging.FileHandler(args.log_file, mode='a'))
    
    logging.basicConfig(
        level=level,
        format='%(asctime)s - %(levelname)s - %(message)s',
        handlers=handlers,
        force=True  # Reconfigure if already configured
    )


# -------------------------
# Main
# -------------------------

def main(args: Optional[argparse.Namespace] = None) -> int:
    """Main execution function with comprehensive error handling."""
    if args is None:
        args = parse_arguments()
    
    # Configure logging based on arguments
    configure_logging(args)
    
    # Get logger after configuration
    logger = logging.getLogger(__name__)
    
    try:
        if args.dry_run:
            logger.info("DRY RUN MODE - No files will be saved")
        
        logger.info("="*60)
        logger.info(f"House Duties Scheduler v{__version__}")
        logger.info("="*60)
        
        # Create output directory if needed
        output_dir = Path(args.output_dir)
        if not args.dry_run and not output_dir.exists():
            output_dir.mkdir(parents=True, exist_ok=True)
            logger.info(f"Created output directory: {output_dir}")
        
        # Load input files
        brothers = load_brothers(args.roster)
        constraints = load_constraints(args.constraints)
        categories = load_categories(args.categories)

        # Validate inputs
        logger.info("Validating inputs...")
        try:
            if validate_all is not None:
                # Build templates first for validation
                templates = build_templates()
                
                # Validate all inputs together
                validate_all(
                    brothers=brothers,
                    templates=templates,
                    constraints=constraints,
                    categories=categories if categories else None
                )
                logger.info("✓ All inputs validated successfully")
            else:
                logger.warning("Skipping validation - module not available")
                templates = build_templates()
        except ValidationError as e:
            logger.error(f"Validation failed: {e}")
            if not args.ignore_validation_errors:
                raise
            logger.warning("Continuing with invalid data (--ignore-validation-errors enabled)")
            templates = build_templates()
        except Exception as e:
            logger.error(f"Unexpected error during validation: {e}")
            if not args.ignore_validation_errors:
                raise
            logger.warning("Continuing despite validation error")
            templates = build_templates()

        # Calculate dates
        current_sunday = parse_start_sunday(args.start_date)
        logger.info(f"Generating schedule for {args.weeks} week(s) starting: {current_sunday}")

        # Load and initialize state
        state = load_state(args.state)
        anchor_sunday = get_anchor_sunday(state, current_sunday)
        logger.info(f"Using anchor Sunday: {anchor_sunday}")

        logger.info(f"Built {len(templates)} task templates")

        # Generate occurrences
        occs = occurrences_from_templates(
            templates=templates,
            anchor_sunday=anchor_sunday,
            current_sunday=current_sunday,
            weeks=args.weeks,
            brothers=brothers,
            state=state
        )
        logger.info(f"Generated {len(occs)} task occurrences for {args.weeks} week(s)")

        # Assign chores
        result = assign_chores(
            occs=occs,
            brothers=brothers,
            state=state,
            constraints=constraints,
            current_sunday=current_sunday,
            categories=categories
        )

        schedule_items = result["schedule_items"]
        state = result["state"]
        logger.info(f"Successfully assigned {len(schedule_items)} chores")

        # Calculate house size
        exempt_all = set(constraints.get("exempt_all", []) or [])
        house_size = len([b for b in brothers if b not in exempt_all])
        logger.info(f"Active house size: {house_size} brothers")

        # Display schedule
        if not args.no_display:
            print_schedule_by_deck(schedule_items, current_sunday, anchor_sunday, house_size)

        # Write output files
        if not args.dry_run:
            csv_file = args.output_csv or "schedule.csv"
            json_file = args.output_json or "schedule.json"
            
            csv_path = output_dir / csv_file
            json_path = output_dir / json_file
            
            write_csv(schedule_items, str(csv_path))
            write_json(schedule_items, str(json_path))
            save_state(args.state, state)

            logger.info("="*60)
            logger.info("SUCCESS: Schedule generation completed")
            logger.info(f"Saved: {csv_path}, {json_path}, and {args.state}")
            
            # Generate dashboard if requested
            if args.dashboard:
                try:
                    from house_duties.dashboard import generate_dashboard_html
                    dashboard_path = output_dir / args.dashboard_output
                    generate_dashboard_html(
                        schedule_json_path=str(json_path),
                        output_html_path=str(dashboard_path),
                        title="House Duties Schedule"
                    )
                    logger.info(f"Generated dashboard: {dashboard_path}")
                except ImportError:
                    logger.warning("Dashboard module not available")
                except Exception as e:
                    logger.error(f"Failed to generate dashboard: {e}")
            
            logger.info("="*60)
        else:
            logger.info("="*60)
            logger.info("DRY RUN COMPLETE: No files were modified")
            logger.info("="*60)
        
        # Use ASCII-safe output for Windows terminals
        try:
            print("\n✓ Schedule generation completed successfully!\n")
        except UnicodeEncodeError:
            print("\n[SUCCESS] Schedule generation completed successfully!\n")
        
        return 0
    
    except FileNotFoundError as e:
        logger.error(f"File not found: {e}")
        print(f"\n❌ ERROR: {e}\n", file=sys.stderr)
        return 1
    
    except ValueError as e:
        logger.error(f"Validation error: {e}")
        print(f"\n❌ ERROR: {e}\n", file=sys.stderr)
        return 1
    
    except Exception as e:
        logger.exception("Unexpected error occurred")
        print(f"\n❌ UNEXPECTED ERROR: {e}", file=sys.stderr)
        print("Check house_duties.log for details.\n", file=sys.stderr)
        return 1


if __name__ == "__main__":
    try:
        args = parse_arguments()
        sys.exit(main(args))
    except KeyboardInterrupt:
        print("\n\nInterrupted by user", file=sys.stderr)
        sys.exit(130)

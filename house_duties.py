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
    if not os.path.exists(filepath):
        return {}
    with open(filepath, "r", encoding="utf-8") as f:
        return json.load(f)

def save_state(filepath: str, state: Dict[str, Any]) -> None:
    with open(filepath, "w", encoding="utf-8") as f:
        json.dump(state, f, indent=2)

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
    if not os.path.exists(filepath):
        raise FileNotFoundError(
            f"Missing roster file: {filepath}\n"
            "Create brothers.txt with one brother name per line."
        )
    brothers: List[str] = []
    with open(filepath, "r", encoding="utf-8") as f:
        for line in f:
            name = line.strip()
            if name and not name.startswith("#"):
                brothers.append(name)
    if not brothers:
        raise ValueError("Roster file is empty. Add at least one brother name.")
    seen = set()
    out = []
    for b in brothers:
        if b not in seen:
            out.append(b)
            seen.add(b)
    return out


def load_categories(filepath: str) -> Dict[str, List[str]]:
    """Load brother categories for pairing rules (e.g., actives, junior_actives)"""
    if not os.path.exists(filepath):
        return {"actives": [], "junior_actives": []}
    with open(filepath, "r", encoding="utf-8") as f:
        data = json.load(f)
    return data


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
    if not os.path.exists(filepath):
        return DEFAULT_CONSTRAINTS.copy()
    with open(filepath, "r", encoding="utf-8") as f:
        data = json.load(f)
    merged = DEFAULT_CONSTRAINTS.copy()
    merged.update(data or {})
    return merged

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
    with open(filepath, "w", encoding="utf-8") as f:
        json.dump(schedule_items, f, indent=2)


# -------------------------
# Main
# -------------------------

def main():
    brothers = load_brothers(ROSTER_FILE)
    constraints = load_constraints(CONSTRAINTS_FILE)
    categories = load_categories(CATEGORIES_FILE)

    current_sunday = parse_start_sunday(START_SUNDAY)

    state = load_state(STATE_FILE)
    anchor_sunday = get_anchor_sunday(state, current_sunday)

    templates = build_templates()

    occs = occurrences_from_templates(
        templates=templates,
        anchor_sunday=anchor_sunday,
        current_sunday=current_sunday,
        weeks=WEEKS_TO_GENERATE,
        brothers=brothers,
        state=state
    )

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

    exempt_all = set(constraints.get("exempt_all", []) or [])
    house_size = len([b for b in brothers if b not in exempt_all])

    print_schedule_by_deck(schedule_items, current_sunday, anchor_sunday, house_size)

    write_csv(schedule_items, "schedule.csv")
    write_json(schedule_items, "schedule.json")
    save_state(STATE_FILE, state)

    print("Saved: schedule.csv, schedule.json, and chore_state.json")


if __name__ == "__main__":
    main()

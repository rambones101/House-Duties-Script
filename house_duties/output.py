"""Output formatting for schedules (CSV, JSON, terminal display)."""
import csv
import json
import logging
from datetime import date, datetime
from typing import List, Dict, Any

logger = logging.getLogger(__name__)

# Deck ordering for display
DECK_ORDER = ["Zero Deck", "First Deck", "Second Deck", "Third Deck", "Other"]


def write_csv(schedule_items: List[Dict[str, Any]], filepath: str):
    """Write schedule to CSV file with error handling."""
    try:
        rows = []
        for item in schedule_items:
            rows.append({
                "due": item["due_dt"].strftime("%Y-%m-%d %H:%M"),
                "deck": item["deck"],
                "task_key": item["task_key"],
                "task": item["task_label"],
                "category": item["category"],
                "people_needed": item["people_needed"],
                "assigned": ", ".join(item["assigned"]),
                "weight_total": round(item["weight"], 2)
            })
        rows.sort(key=lambda x: (DECK_ORDER.index(x["deck"]) if x["deck"] in DECK_ORDER else 999, x["due"]))
        
        with open(filepath, "w", newline="", encoding="utf-8") as f:
            writer = csv.DictWriter(f, fieldnames=[
                "due", "deck", "task_key", "task", "category", "people_needed", "assigned", "weight_total"
            ])
            writer.writeheader()
            writer.writerows(rows)
        
        logger.info(f"Wrote {len(rows)} schedule items to '{filepath}'")
    
    except Exception as e:
        logger.error(f"Error writing CSV to '{filepath}': {e}")
        raise


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


def print_schedule_by_deck(schedule_items: List[Dict[str, Any]], 
                          current_sunday: date, 
                          anchor_sunday: date,
                          house_size: int):
    """Print schedule organized by deck and day."""
    from .utils import week_index_from_anchor, DOW
    
    week_index = week_index_from_anchor(anchor_sunday, current_sunday)
    parity = "EVEN" if week_index % 2 == 0 else "ODD"
    
    print("\n" + "=" * 60)
    print("HOUSE DUTIES SCHEDULE")
    print("=" * 60)
    print(f"Week: {current_sunday} (Sun) -> {current_sunday + __import__('datetime').timedelta(days=6)} (Sat)")
    print(f"Roster size: {house_size} brothers")
    print(f"Biweekly parity: week_index={week_index} | {parity}")
    print("=" * 60)
    
    # Group by day then by deck
    by_day: Dict[date, Dict[str, List[Dict[str, Any]]]] = {}
    for item in schedule_items:
        day = item["due_dt"].date()
        if day not in by_day:
            by_day[day] = {}
        deck = item["deck"]
        if deck not in by_day[day]:
            by_day[day][deck] = []
        by_day[day][deck].append(item)
    
    for day in sorted(by_day.keys()):
        dow_name = DOW[day.weekday() if day.weekday() != 6 else 0] if day.weekday() == 6 else DOW[(day.weekday() + 1) % 7]
        print(f"\n\n**{dow_name} {day}**")
        print("-" * 60)
        
        decks_this_day = by_day[day]
        # Sort decks by DECK_ORDER
        sorted_decks = sorted(decks_this_day.keys(), 
                            key=lambda d: DECK_ORDER.index(d) if d in DECK_ORDER else 999)
        
        for deck in sorted_decks:
            print(f"\n\n  {deck}:")
            tasks = decks_this_day[deck]
            for task in tasks:
                assigned_str = ", ".join(task["assigned"])
                people_count = len(task["assigned"])
                print(f"    - {task['task_label']}")
                print(f"      > Assigned: {assigned_str} ({people_count} person{'s' if people_count != 1 else ''})")
                print()
    
    print("\n" + "=" * 60 + "\n")

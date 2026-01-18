"""Core scheduling logic - expands templates into occurrences."""
from typing import List, Dict, Any
from datetime import time, timedelta
from .models import TaskTemplate, Occurrence
from .utils import week_start_for, dt_on, unique_sorted_days, week_index_from_anchor
from .bonus import choose_bonus_tasks_for_week


DEFAULT_DUE_TIME = time(23, 59)


def occurrences_from_templates(
    templates: List[TaskTemplate],
    start_sunday: Any,  # date object
    num_weeks: int,
    anchor_sunday: Any,  # date object
    bonus_counts: Dict[str, int],
    roster_size: int,
    bonus_third_day: List[int] = None,
    min_bonus_roster: int = 14
) -> List[Occurrence]:
    """
    Expand task templates into concrete chore occurrences for the scheduling period.
    
    Handles:
    - Weekly tasks (fixed days)
    - Biweekly tasks (odd/even week parity from anchor)
    - n_per_week tasks (rotating through preferred_days)
    - Bonus 3rd cleanings for flexible_2_3x tasks
    
    Args:
        templates: Task definitions
        start_sunday: First Sunday of scheduling period
        num_weeks: Number of weeks to generate
        anchor_sunday: Reference point for biweekly parity
        bonus_counts: Historical bonus counts for fair rotation
        roster_size: Number of active brothers
        bonus_third_day: Day(s) for bonus 3rd cleaning (default [5] = Friday)
        min_bonus_roster: Minimum roster size to enable bonuses
    
    Returns:
        List of Occurrence objects sorted by due date
    """
    if bonus_third_day is None:
        bonus_third_day = [5]  # Friday
    
    all_occs = []
    
    for week_idx in range(num_weeks):
        week_start = week_start_for(start_sunday, week_idx)
        abs_week_idx = week_index_from_anchor(anchor_sunday, week_start)
        
        # Determine bonus tasks for this week
        bonus_task_keys = choose_bonus_tasks_for_week(
            templates=templates,
            anchor_sunday=str(anchor_sunday),
            week_index=abs_week_idx,
            roster_size=roster_size,
            bonus_counts=bonus_counts,
            min_roster=min_bonus_roster
        )
        
        for tmpl in templates:
            weight = tmpl.severity * tmpl.effort_multiplier
            
            # ----- Weekly cadence -----
            if tmpl.cadence == "weekly":
                if not tmpl.days_of_week:
                    continue
                for dow in unique_sorted_days(tmpl.days_of_week):
                    due_dt = dt_on(week_start, dow, DEFAULT_DUE_TIME)
                    all_occs.append(Occurrence(
                        task_key=tmpl.key,
                        task_label=tmpl.label,
                        deck=tmpl.deck,
                        category=tmpl.category,
                        people_needed=tmpl.people_needed,
                        due_dt=due_dt,
                        week_index=abs_week_idx,
                        weight=weight
                    ))
            
            # ----- Biweekly cadence -----
            elif tmpl.cadence == "biweekly":
                if abs_week_idx % 2 == 0:  # Even weeks only (or adjust logic as needed)
                    if not tmpl.days_of_week:
                        continue
                    for dow in unique_sorted_days(tmpl.days_of_week):
                        due_dt = dt_on(week_start, dow, DEFAULT_DUE_TIME)
                        all_occs.append(Occurrence(
                            task_key=tmpl.key,
                            task_label=tmpl.label,
                            deck=tmpl.deck,
                            category=tmpl.category,
                            people_needed=tmpl.people_needed,
                            due_dt=due_dt,
                            week_index=abs_week_idx,
                            weight=weight
                        ))
            
            # ----- N per week cadence -----
            elif tmpl.cadence == "n_per_week":
                if not tmpl.preferred_days or not tmpl.times_per_week:
                    continue
                
                # Base occurrences (usually 2x/week)
                base_days = unique_sorted_days(tmpl.preferred_days[:tmpl.times_per_week])
                for dow in base_days:
                    due_dt = dt_on(week_start, dow, DEFAULT_DUE_TIME)
                    all_occs.append(Occurrence(
                        task_key=tmpl.key,
                        task_label=tmpl.label,
                        deck=tmpl.deck,
                        category=tmpl.category,
                        people_needed=tmpl.people_needed,
                        due_dt=due_dt,
                        week_index=abs_week_idx,
                        weight=weight
                    ))
                
                # Bonus 3rd occurrence if selected
                if tmpl.key in bonus_task_keys:
                    for dow in unique_sorted_days(bonus_third_day):
                        # Skip if already scheduled on this day
                        if dow not in base_days:
                            due_dt = dt_on(week_start, dow, DEFAULT_DUE_TIME)
                            all_occs.append(Occurrence(
                                task_key=tmpl.key,
                                task_label=tmpl.label + " [BONUS]",
                                deck=tmpl.deck,
                                category=tmpl.category,
                                people_needed=tmpl.people_needed,
                                due_dt=due_dt,
                                week_index=abs_week_idx,
                                weight=weight
                            ))
    
    # Sort by due date
    all_occs.sort(key=lambda o: o.due_dt)
    return all_occs

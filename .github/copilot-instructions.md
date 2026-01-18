# House Duties Scheduler — AI Coding Guide

## Project Overview
Fraternity house chore scheduling system with persistent state, fairness algorithms, and deck-based organization. Weekly runner that assigns chores to brothers while maintaining historical equity and respecting constraints.

## Architecture & Data Flow

### Core Pipeline
1. **Load State** → `chore_state.json` (persistent rotation tracking, anti-repeat history, anchor Sunday)
2. **Build Templates** → Hardcoded task definitions with deck assignments, cadence rules, flexible 2-3x/week flags
3. **Expand Occurrences** → Generate concrete chore instances for the week with bonus task selection
4. **Assign Brothers** → Constraint-based greedy algorithm with fairness penalties
5. **Save Outputs** → `schedule.csv`, `schedule.json`, updated `chore_state.json`

### Key Files
- **[house_duties.py](house_duties.py)**: Single-file application (~750 lines)
- **[brothers.txt](brothers.txt)**: Active roster (one name per line, `#` for comments)
- **[chore_state.json](chore_state.json)**: Persistent state tracking (`anchor_sunday`, `bonus_counts`, `brother_task_counts`, `brother_last_week_tasks`)
- **constraints.json** (optional): Opt-outs, category bans, task bans (see `DEFAULT_CONSTRAINTS` in code)

## Critical Domain Logic

### Biweekly Parity System
Tasks like "Brasso" and "Blue" use `week_index_from_anchor()` to determine odd/even weeks. **Never modify the anchor Sunday** unless intentionally resetting the rotation cycle. Week index 0 = week of anchor Sunday.

### Bonus Third Cleaning (2-3x/week Tasks)
- Tasks marked `flexible_2_3x=True` can get a 3rd cleaning if roster ≥ `BONUS_THIRD_CLEANING_MIN_ROSTER` (default 14)
- Bonus selection uses deterministic seeding: `stable_int_from_strings(anchor_sunday, week_index, roster, seed)` → ensures reproducibility
- Priority: bathrooms > floors > common. Tasks with fewer bonus counts are favored (`bonus_counts` in state)
- Once assigned, increment `bonus_counts[task_key]` to rotate fairly

### Fairness Algorithm (Assignment Scoring)
Brother selection uses tuple sorting: `(base_load + repeat_pen + recent_pen + day_pen + pref, jitter)`

- **Repeat penalty**: `(hist_count + run_count) * 1.50` — discourages same task assignment
- **Recent week penalty**: `last_week_count * 0.60` — avoids back-to-back weeks on same task
- **Same-day stack penalty**: `day_assignments * 0.75` — spreads chores across days
- **Preference bonus**: `-0.35` if brother prefers this category

Lower scores are assigned first. **Don't modify penalties without testing impact on fairness distribution.**

## Task Template Structure

```python
TaskTemplate(
    key="SD_SINKS",                          # Unique identifier
    deck="Second Deck",                       # Zero/First/Second/Third/Other
    label="Sinks Clean/Sweep Bathroom",
    category="bathrooms",                     # k&m, bathrooms, floors, laundry, common, other
    people_needed=2,
    cadence="n_per_week",                     # weekly, biweekly, n_per_week
    times_per_week=2,                         # Only for n_per_week cadence
    preferred_days=[2, 4],                    # 0=Sun, 6=Sat
    severity=4,                               # 1-5, affects fairness weight
    effort_multiplier=1.1,                    # Weight adjustment
    flexible_2_3x=True                        # Enable bonus 3rd cleaning
)
```

### Adding New Tasks
1. Add to `build_templates()` grouped by deck
2. Choose appropriate cadence: `"weekly"` (fixed days), `"biweekly"` (odd/even weeks), `"n_per_week"` (rotating days)
3. Set `flexible_2_3x=True` only for high-traffic areas needing variable frequency
4. Use `BASE_2X_DAYS_DEFAULT` (Tue/Thu) and `BONUS_3RD_DAY_DEFAULT` (Fri) for consistency

## Common Workflows

### Running the Scheduler
```powershell
python house_duties.py
```
No arguments needed. Auto-detects most recent Sunday and generates 1 week (configurable via `WEEKS_TO_GENERATE`).

### Testing Fairness Changes
1. Back up `chore_state.json` 
2. Modify penalty constants at top of file (`REPEAT_TASK_PENALTY`, etc.)
3. Run scheduler multiple times with same roster
4. Analyze `brother_task_counts` distribution in state file
5. Restore backup if results degrade

### Resetting Rotation History
Delete or rename `chore_state.json`. Next run will create fresh state with new `anchor_sunday`.

## Constraints & Opt-Outs

Create `constraints.json` (optional):
```json
{
  "exempt_all": ["BrotherName"],              // Exclude from all chores
  "on_call_only": ["BackupBrother"],          // Use only if normal pool exhausted
  "max_per_brother_per_week": 5,
  "max_per_brother_per_day": 2,
  "brother_category_bans": {
    "John": ["bathrooms", "k&m"]              // Category-level opt-out
  },
  "brother_task_bans": {
    "Jane": ["SD_SINKS", "TD_TOILETS"]        // Specific task opt-out
  },
  "brother_preferred_categories": {
    "Alex": ["floors"]                        // Get -0.35 score bonus
  }
}
```

## Configuration Constants (Top of File)

- `START_SUNDAY`: Leave `""` to auto-detect (recommended)
- `WEEKS_TO_GENERATE`: Typically `1` for weekly runs
- `BRASSO_CADENCE_SECOND_DECK`/`THIRD_DECK`: `"weekly"` or `"biweekly"`
- `DEFAULT_DUE_TIMES`: All chores default to `23:59` (not enforced, display only)
- `BONUS_THIRD_CLEANING_MIN_ROSTER`: Minimum roster size to enable 3rd cleanings (default 14)
- `RANDOM_SEED`: Change to alter tie-breaking randomness (affects assignment distribution)

## Output Format

### Terminal: Deck-Organized Schedule
Groups chores by date → deck (Zero/First/Second/Third order) → tasks with assigned brothers.

### CSV: [schedule.csv](schedule.csv)
Sorted by deck, then due date. Columns: `due, deck, task_key, task, category, people_needed, assigned, weight_total`

### JSON: [schedule.json](schedule.json)
Array of assignment objects. Machine-readable for integrations.

## Common Pitfalls

1. **Never mutate `anchor_sunday` in state file** — breaks biweekly parity tracking
2. **Don't add tasks without deck assignment** — output grouping will fail
3. **Changing `RANDOM_SEED` mid-semester** — alters fairness trajectory; keep constant
4. **Modifying `bonus_counts` manually** — defeats rotation equity; let algorithm manage it
5. **Using `cadence="n_per_week"` without `preferred_days`** — tasks will cluster randomly

## Extending the System

### Adding a New Deck
1. Add deck name to `DECK_ORDER` list
2. Create tasks in `build_templates()` with new deck name
3. Output will automatically group by new deck

### Implementing Skill-Based Assignment
Add `required_skills` field to `TaskTemplate`, update `is_banned()` to check brother skills from constraints file.

### Email/SMS Notifications
Parse `schedule.json` after generation, map brothers to contact info, send reminders using external service.

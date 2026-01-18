# Architecture Documentation

## Overview
The House Duties Scheduler has been refactored from a monolithic 1157-line script into a modular package structure for better maintainability and testability.

## Project Structure

```
House Duties Script/
├── house_duties/              # Main package (new modular structure)
│   ├── __init__.py           # Package exports
│   ├── models.py             # Data structures (TaskTemplate, Occurrence)
│   ├── utils.py              # Date/time utilities
│   ├── state.py              # State management and file I/O
│   └── output.py             # CSV/JSON/terminal formatters
│
├── house_duties_legacy.py     # Original implementation (all functionality)
├── house_duties.py            # Thin wrapper for backward compatibility
│
├── tests/                     # Test suite (54 tests)
│   ├── conftest.py           # Shared pytest fixtures
│   ├── test_bonus.py         # Bonus 3rd cleaning tests
│   ├── test_cli.py           # CLI argument parsing tests
│   ├── test_date_utils.py    # Date utility tests
│   ├── test_loading.py       # File loading and constraints tests
│   └── test_state.py         # State management tests
│
├── brothers.txt               # Active roster
├── chore_state.json          # Persistent state tracking
├── constraints.json          # Opt-outs and preferences (optional)
├── brother_categories.json   # Brother preferences (optional)
├── schedule.csv              # Generated schedule (output)
├── schedule.json             # Generated schedule JSON (output)
│
├── discord_bot.py            # Optional Discord integration
├── requirements.txt          # Python dependencies
├── pytest.ini                # Test configuration
├── README.md                 # User documentation
└── .gitignore                # Git ignore rules
```

## Module Responsibilities

### `house_duties/models.py`
**Purpose:** Core data structures

**Classes:**
- `TaskTemplate`: Task definition (key, label, deck, cadence, people_needed, etc.)
- `Occurrence`: Concrete task instance with due date and assigned brothers

### `house_duties/utils.py`
**Purpose:** Date and time utilities

**Functions:**
- `most_recent_sunday()`: Find most recent Sunday from a given date
- `parse_start_sunday()`: Parse start date string or auto-detect
- `week_start_for()`: Get Sunday for a given date
- `dt_on()`: Create datetime for a specific day of the week
- `unique_sorted_days()`: Get unique days from list of dates
- `week_index_from_anchor()`: Calculate week number from anchor Sunday

### `house_duties/state.py`
**Purpose:** State management and file I/O

**Functions:**
- `load_state()`: Load persistent state from JSON
- `save_state()`: Save state to JSON with backup
- `get_anchor_sunday()`: Get or initialize anchor Sunday
- `load_brothers()`: Load roster from text file
- `load_constraints()`: Load constraints from JSON
- `load_categories()`: Load brother preferences

**State Format:**
```json
{
  "anchor_sunday": "2024-01-07",
  "bonus_counts": {"TASK_KEY": 3},
  "brother_task_counts": {"Brother": {"TASK_KEY": 5}},
  "brother_last_week_tasks": {"Brother": ["TASK_KEY1", "TASK_KEY2"]}
}
```

### `house_duties/output.py`
**Purpose:** Output formatting and file generation

**Functions:**
- `write_csv()`: Generate CSV schedule sorted by deck and date
- `write_json()`: Generate JSON schedule for machine parsing
- `print_schedule_by_deck()`: Terminal display grouped by date and deck

**Output Formats:**
- **CSV:** Deck-sorted, columns: `due, deck, task_key, task, category, people_needed, assigned, weight_total`
- **JSON:** Array of assignment objects with full metadata
- **Terminal:** Human-readable grouped by date → deck → tasks

### `house_duties_legacy.py`
**Purpose:** Original complete implementation

Contains all functions from the original monolithic file:
- `build_templates()`: Hardcoded task definitions
- `occurrences_from_templates()`: Expand templates to concrete instances
- `assign_chores()`: Greedy constraint-based assignment algorithm
- `choose_bonus_tasks_for_week()`: Select bonus 3rd cleanings
- `is_banned()`: Check brother constraints
- `preference_bonus()`: Calculate preference score
- `parse_arguments()`: CLI argument parser
- `main()`: Entry point and orchestration

### `house_duties.py` (Wrapper)
**Purpose:** Backward compatibility and CLI entry point

Imports `main()` from `house_duties_legacy.py` and executes it. This ensures:
- Existing command-line usage works unchanged
- Old imports still function
- Gradual migration path available

## Design Patterns

### Separation of Concerns
- **Models:** Pure data structures with no business logic
- **Utils:** Stateless utility functions
- **State:** File I/O isolated from business logic
- **Output:** Formatting decoupled from assignment algorithm

### Backward Compatibility
- Original functionality preserved in `house_duties_legacy.py`
- Thin wrapper maintains CLI interface
- Tests updated to import from legacy module
- Future: Incrementally migrate functions from legacy to modules

### State Management
- Single source of truth in `chore_state.json`
- Immutable state loading (returns dict, doesn't modify globals)
- Backup before save to prevent data loss
- Anchor Sunday locked for biweekly parity tracking

## Testing Strategy

### Test Coverage (54 tests)
- **Unit tests:** Individual function behavior (`@pytest.mark.unit`)
- **Integration tests:** End-to-end workflows (`@pytest.mark.integration`)

### Test Files
- `test_bonus.py`: Bonus 3rd cleaning logic (10 tests)
- `test_cli.py`: Argument parsing and validation (7 tests)
- `test_date_utils.py`: Date utilities (15 tests)
- `test_loading.py`: File loading and constraints (14 tests)
- `test_state.py`: State management (8 tests)

### Running Tests
```bash
# All tests
pytest tests/

# Quick mode (no output)
pytest tests/ -q

# Unit tests only
pytest tests/ -m unit

# Integration tests only
pytest tests/ -m integration

# Verbose with coverage
pytest tests/ -v --cov=house_duties_legacy
```

## Configuration

### CLI Arguments (15+ options)
```bash
--roster ROSTER              # Default: brothers.txt
--constraints CONSTRAINTS    # Default: constraints.json
--categories CATEGORIES      # Default: brother_categories.json
--state STATE               # Default: chore_state.json
--weeks WEEKS               # Default: 1
--start-date YYYY-MM-DD     # Default: auto-detect most recent Sunday
--output-dir DIR            # Default: current directory
--output-csv FILE           # Default: schedule.csv
--output-json FILE          # Default: schedule.json
--dry-run                   # Preview without saving
--no-display                # Suppress terminal output
-v, --verbose               # Detailed logging
-q, --quiet                 # Minimal output
--log-file FILE             # Log to file
--version                   # Show version (1.1.0)
```

### Constants (house_duties_legacy.py)
```python
START_SUNDAY = ""                          # Auto-detect most recent Sunday
WEEKS_TO_GENERATE = 1                      # Weekly runs
BONUS_THIRD_CLEANING_MIN_ROSTER = 14       # Roster size for bonus cleanings
RANDOM_SEED = 42                           # Assignment tie-breaking

# Fairness penalties (tuple sorting)
REPEAT_TASK_PENALTY = 1.50                 # Same task in history
RECENT_WEEK_PENALTY = 0.60                 # Same task last week
SAME_DAY_STACK_PENALTY = 0.75              # Multiple tasks same day
PREFERENCE_BONUS = -0.35                   # Preferred category
```

## Data Flow

### Weekly Execution Pipeline

1. **Load Inputs**
   - Brothers roster (`brothers.txt`)
   - Persistent state (`chore_state.json`)
   - Constraints (`constraints.json`) [optional]
   - Categories (`brother_categories.json`) [optional]

2. **Build Templates**
   - Hardcoded task definitions by deck
   - Cadence rules (weekly, biweekly, n_per_week)
   - Flexible 2-3x/week flags

3. **Expand Occurrences**
   - Generate concrete instances for the week
   - Select bonus 3rd cleanings (deterministic seeding)
   - Validate against cadence rules

4. **Assign Brothers**
   - Greedy constraint-based algorithm
   - Fairness scoring: `(base_load + repeat_pen + recent_pen + day_pen + pref, jitter)`
   - Respect constraints (exempt, on_call_only, bans, preferences)

5. **Save Outputs**
   - Update `chore_state.json` (rotation tracking, bonus counts)
   - Write `schedule.csv` (deck-sorted)
   - Write `schedule.json` (machine-readable)
   - Display terminal output (grouped by date/deck)

### State Persistence

```
Initial Run:
chore_state.json (empty) → anchor_sunday = today's Sunday
                          → bonus_counts = {}
                          → brother_task_counts = {}

Subsequent Runs:
chore_state.json (loaded) → Use existing anchor_sunday (locked)
                          → Increment bonus_counts for assigned tasks
                          → Update brother_task_counts (history)
                          → Save brother_last_week_tasks (recent penalty)
```

## Extension Points

### Adding New Decks
1. Add deck name to `DECK_ORDER` in `house_duties_legacy.py`
2. Create tasks in `build_templates()` with new deck name
3. Output automatically groups by new deck

### Adding New Task Cadences
1. Add new cadence type in `TaskTemplate` (e.g., `"monthly"`)
2. Implement logic in `occurrences_from_templates()`
3. Update tests in `test_loading.py`

### Custom Fairness Algorithms
Modify penalty constants at top of `house_duties_legacy.py`:
- `REPEAT_TASK_PENALTY`: Discourage same task
- `RECENT_WEEK_PENALTY`: Avoid back-to-back weeks
- `SAME_DAY_STACK_PENALTY`: Spread across days
- `PREFERENCE_BONUS`: Favor preferred categories

Test impact by running multiple weeks and analyzing `brother_task_counts` distribution.

### Integration with External Systems

**Discord Bot:**
- Use `schedule.json` as data source
- Parse assignments and post to channel
- See `discord_bot.py` for reference

**Email Notifications:**
- Parse `schedule.json` after generation
- Map brothers to email addresses
- Send reminders using external service

**Web Dashboard:**
- Serve `schedule.json` via API
- Build frontend to display schedule
- Add interactive preference management

## Upgrade Path

The current structure provides a migration path for future refactoring:

1. **Phase 1 (Current):** Legacy file + package structure
   - All functionality in `house_duties_legacy.py`
   - Thin wrapper for backward compatibility
   - Tests use legacy imports

2. **Phase 2 (Future):** Gradual migration
   - Move `build_templates()` to `house_duties/scheduler.py`
   - Move `assign_chores()` to `house_duties/scheduler.py`
   - Move `parse_arguments()` to `house_duties/cli.py`
   - Update tests to use package imports

3. **Phase 3 (Future):** Full modular
   - Delete `house_duties_legacy.py`
   - All functions in appropriate modules
   - Clean package structure with clear dependencies

## Version History

- **v1.0.0:** Initial monolithic implementation (1157 lines)
- **v1.0.1:** Added error handling and logging framework
- **v1.1.0:** Added CLI arguments (15+ options)
- **v1.1.1:** Added unit test suite (54 tests)
- **v1.1.2:** Modular package structure (current)

## Maintenance Guidelines

### When Adding Tasks
1. Add to `build_templates()` in `house_duties_legacy.py`
2. Group by deck (Zero/First/Second/Third/Other)
3. Choose appropriate cadence
4. Set `flexible_2_3x=True` only for high-traffic areas
5. Test with `--dry-run` before production

### When Modifying Fairness
1. Back up `chore_state.json`
2. Modify penalty constants
3. Run scheduler 4-6 weeks with same roster
4. Analyze `brother_task_counts` distribution
5. Restore backup if results degrade

### When Updating Dependencies
1. Update `requirements.txt`
2. Run `pip install -r requirements.txt`
3. Run full test suite: `pytest tests/`
4. Test CLI: `python house_duties.py --help`
5. Commit changes with dependency version notes

### When Resetting Rotation
Delete `chore_state.json` to start fresh with new anchor Sunday. This resets:
- Biweekly parity tracking
- Bonus rotation counts
- Historical task assignments
- Recent week penalties

**Warning:** Only do this intentionally (e.g., new semester, roster change). Never modify `anchor_sunday` manually.

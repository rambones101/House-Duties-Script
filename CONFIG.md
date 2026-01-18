# Configuration File Guide

The House Duties Scheduler now supports YAML-based configuration! All previously hardcoded constants can be customized in the `config.yaml` file.

## Quick Start

The scheduler will automatically load `config.yaml` from the current directory if it exists. If not found, it uses sensible defaults.

```bash
# Use default config.yaml
python house_duties.py

# Use custom config file
python house_duties.py --config my_config.yaml
```

## Configuration Sections

### Files
Paths to input/output files:

```yaml
files:
  roster: "brothers.txt"           # Active roster
  constraints: "constraints.json"   # Optional opt-outs and bans
  categories: "brother_categories.json"  # Optional preferences
  state: "chore_state.json"        # Persistent state tracking
```

### Scheduling Parameters
Core scheduling behavior:

```yaml
scheduling:
  start_sunday: ""                 # Auto-detect if empty
  weeks_to_generate: 1             # Number of weeks to schedule
  bonus_third_cleaning_min_roster: 14  # Min roster for bonus 3rd cleanings
  bonus_third_cleaning_max_task_share: 0.50  # Max % of tasks getting bonus
  random_seed: 42                  # For deterministic tie-breaking
```

### Task Cadence
Frequency per deck (use "weekly" or "biweekly"):

```yaml
cadence:
  brasso_second_deck: "biweekly"
  brasso_third_deck: "biweekly"
```

### Due Times
Default due times by category (24-hour format):

```yaml
due_times:
  k&m: "23:59"
  bathrooms: "23:59"
  floors: "23:59"
  laundry: "23:59"
  common: "23:59"
  other: "23:59"
```

### Bonus 3rd Cleaning Policy
How bonus third cleanings are selected:

```yaml
bonus:
  base_2x_days: [2, 4]    # Days for base 2x cleanings (0=Sun, 6=Sat)
  bonus_3rd_day: 5        # Day for 3rd cleaning if selected (Friday)
  
  # Priority by category (higher = selected first)
  priority:
    bathrooms: 3
    floors: 2
    common: 1
    laundry: 0
    k&m: 0
    other: 0
```

### Fairness Algorithm
Tune the assignment algorithm:

```yaml
fairness:
  repeat_task_penalty: 1.50      # Penalty for same task assignment
  recent_week_penalty: 0.60      # Penalty for task done last week
  same_day_stack_penalty: 0.75   # Penalty for multiple tasks same day
  preference_bonus: -0.35        # Bonus for preferred categories (negative = good)
```

**How it works:** Brothers are assigned scores when selecting for a task. Lower scores are chosen first:
```
score = (base_load + repeat_pen + recent_pen + day_pen + pref_bonus, random_jitter)
```

**Tuning tips:**
- Increase `repeat_task_penalty` to discourage repeated assignments more strongly
- Increase `recent_week_penalty` to avoid back-to-back weeks on same task
- Increase `same_day_stack_penalty` to spread chores across days
- Make `preference_bonus` more negative to favor preferences more strongly

### Display Settings
Output formatting:

```yaml
display:
  deck_order:
    - "Zero Deck"
    - "First Deck"
    - "Second Deck"
    - "Third Deck"
    - "Other"
```

This controls the order decks appear in terminal output and CSV files.

### Severity Overrides
Override default severity (1-5) for specific tasks:

```yaml
severity_overrides:
  FD_KM_SUN: 5        # k&m Sunday gets severity 5
  TD_TOILETS: 4       # Third Deck toilets get severity 4
```

**Note:** Severity affects fairness calculations. Higher severity = considered "heavier" work.

## Example Custom Configurations

### High-Traffic House (More Frequent Cleaning)
```yaml
scheduling:
  bonus_third_cleaning_min_roster: 12  # Lower threshold for bonus cleanings

bonus:
  base_2x_days: [1, 3, 5]  # Mon, Wed, Fri
  priority:
    bathrooms: 5           # Prioritize bathrooms even more
    floors: 4
```

### Strict Fairness (Minimize Repeats)
```yaml
fairness:
  repeat_task_penalty: 2.50      # Much higher penalty for repeats
  recent_week_penalty: 1.00      # Strong penalty for back-to-back weeks
  same_day_stack_penalty: 1.50   # Discourage multiple tasks per day
```

### Weekly Brasso Schedule
```yaml
cadence:
  brasso_second_deck: "weekly"   # Brasso every week instead of biweekly
  brasso_third_deck: "weekly"
```

### Early Due Times
```yaml
due_times:
  k&m: "12:00"        # k&m due at noon
  bathrooms: "18:00"  # Bathrooms due at 6 PM
  floors: "20:00"     # Floors due at 8 PM
```

## Validation

The config system automatically validates:
- ✅ `weeks_to_generate` >= 1
- ✅ `bonus_third_cleaning_min_roster` >= 1
- ✅ `bonus_third_cleaning_max_task_share` between 0.0 and 1.0
- ✅ Cadence values are "weekly" or "biweekly"
- ✅ Time formats are "HH:MM" with valid hours/minutes
- ✅ Days of week are 0-6 (Sunday-Saturday)

Invalid configs will show helpful error messages with the specific problem.

## Backward Compatibility

If `config.yaml` doesn't exist or PyYAML isn't installed, the scheduler falls back to hardcoded defaults. All existing workflows continue to work unchanged.

## Command-Line Override

CLI arguments always override config file values:

```bash
# Config says 1 week, but generate 2 weeks
python house_duties.py --weeks 2

# Use custom roster despite config
python house_duties.py --roster special_roster.txt
```

## Migration from Hardcoded Values

If you previously edited constants in `house_duties_legacy.py`:

1. Create `config.yaml` from the provided template
2. Copy your custom values to the appropriate sections
3. Delete your local changes to `house_duties_legacy.py`
4. Test with `--dry-run` to verify behavior matches

## Troubleshooting

**Config not loading?**
```bash
# Check if PyYAML is installed
python -c "import yaml; print(yaml.__version__)"

# If not:
pip install PyYAML>=6.0.0
```

**Invalid YAML syntax?**
- Check indentation (use spaces, not tabs)
- Verify colons have spaces after them: `key: value` not `key:value`
- Lists use square brackets or dashes:
  ```yaml
  list_style_1: [1, 2, 3]
  list_style_2:
    - item1
    - item2
  ```

**Want to see what's being loaded?**
```bash
# Run with verbose logging
python house_duties.py -v --dry-run
```

The log will show "Loaded configuration from 'config.yaml'" if successful.

## See Also

- [README.md](README.md) - Main documentation
- [ARCHITECTURE.md](ARCHITECTURE.md) - Code structure and design patterns
- [constraints.json](constraints.json) - Brother-specific opt-outs and preferences

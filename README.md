# House Duties Scheduler

A fraternity house chore scheduling system with persistent state tracking, fairness algorithms, and deck-based organization. Automatically assigns weekly chores to brothers while maintaining historical equity and respecting constraints.

## Features

- **Persistent State Management**: Tracks rotation history and assignment counts across weeks
- **Fairness Algorithm**: Distributes workload evenly with penalties for repeat assignments
- **Flexible Scheduling**: Supports weekly, biweekly, and n-times-per-week task cadences
- **Biweekly Parity System**: Maintains odd/even week rotation tracking from anchor Sunday
- **Bonus Task Selection**: Dynamically assigns 2-3 cleanings/week based on roster size
- **Constraint Support**: Handles opt-outs, category bans, and task-specific restrictions
- **Discord Bot Integration**: Optional bot for posting schedules and sending reminders

## Quick Start

### Prerequisites

- Python 3.7+
- Required packages: `pip install -r requirements.txt`

### Basic Usage

1. Update [brothers.txt](brothers.txt) with active roster (one name per line)
2. Run the scheduler:
```powershell
python house_duties.py
```

The script will:
- Auto-detect the most recent Sunday
- Generate assignments for the upcoming week
- Output schedule to CSV, JSON, and terminal
- Update persistent state in [chore_state.json](chore_state.json)

## Project Structure

### Core Files

- **[house_duties.py](house_duties.py)**: Main scheduler application (~750 lines)
- **[brothers.txt](brothers.txt)**: Active roster (one name per line, use `#` for comments)
- **[chore_state.json](chore_state.json)**: Persistent state tracking
  - `anchor_sunday`: Reference date for biweekly parity
  - `bonus_counts`: Tracks bonus task assignment history
  - `brother_task_counts`: Historical assignment counts per brother-task pair
  - `brother_last_week_tasks`: Recent week assignments for penalty calculation

### Output Files

- **[schedule.csv](schedule.csv)**: Sortable schedule by deck and due date
- **[schedule.json](schedule.json)**: Machine-readable assignment data for integrations

### Optional Files

- **constraints.json**: Define opt-outs, category bans, and preferences (see Configuration section)
- **[brother_categories.json](brother_categories.json)**: Brother category preferences

## How It Works

### Core Pipeline

1. **Load State** → Read persistent tracking from `chore_state.json`
2. **Build Templates** → Define hardcoded task definitions with deck assignments
3. **Expand Occurrences** → Generate concrete chore instances for the week
4. **Assign Brothers** → Use constraint-based greedy algorithm with fairness penalties
5. **Save Outputs** → Write `schedule.csv`, `schedule.json`, and updated state

### Task Template Structure

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

### Fairness Algorithm

Brother selection uses tuple sorting to minimize:
- **Repeat penalty** (1.50×): Discourages assigning same task repeatedly
- **Recent week penalty** (0.60×): Avoids back-to-back weeks on same task  
- **Same-day penalty** (0.75×): Spreads chores across days
- **Preference bonus** (-0.35): Rewards preferred category assignments

Lower scores are assigned first, ensuring equitable distribution over time.

### Bonus Third Cleaning System

Tasks marked `flexible_2_3x=True` can receive a 3rd weekly cleaning when roster ≥ 14 brothers:
- Uses deterministic seeding for reproducibility
- Priority: bathrooms > floors > common areas
- Tracks `bonus_counts` to rotate fairly across eligible tasks

## Configuration

### Task Cadences

- **`"weekly"`**: Fixed days every week (e.g., Sunday/Wednesday)
- **`"biweekly"`**: Alternates odd/even weeks from anchor Sunday
- **`"n_per_week"`**: Rotating days (2-3 times per week)

### Constraints File (Optional)

Create `constraints.json` to customize assignments:

```json
{
  "exempt_all": ["BrotherName"],
  "on_call_only": ["BackupBrother"],
  "max_per_brother_per_week": 5,
  "max_per_brother_per_day": 2,
  "brother_category_bans": {
    "John": ["bathrooms", "k&m"]
  },
  "brother_task_bans": {
    "Jane": ["SD_SINKS", "TD_TOILETS"]
  },
  "brother_preferred_categories": {
    "Alex": ["floors"]
  }
}
```

### Configuration Constants

Edit constants at the top of [house_duties.py](house_duties.py):

- `START_SUNDAY`: Leave `""` to auto-detect (recommended)
- `WEEKS_TO_GENERATE`: Typically `1` for weekly runs
- `BONUS_THIRD_CLEANING_MIN_ROSTER`: Minimum roster for 3rd cleanings (default: 14)
- `RANDOM_SEED`: Change to alter tie-breaking randomness

## Discord Bot (Optional)

Post schedules automatically to Discord with reminders.

### Setup

1. Follow [DISCORD_BOT_SETUP.md](DISCORD_BOT_SETUP.md) for bot creation
2. Copy `.env.example` to `.env` and add your bot token
3. Run: `python discord_bot.py`

See [DISCORD_BOT_SETUP.md](DISCORD_BOT_SETUP.md) for detailed configuration.

## Common Workflows

### Adding New Tasks

1. Add to `build_templates()` in [house_duties.py](house_duties.py), grouped by deck
2. Choose appropriate cadence type
3. Set `flexible_2_3x=True` for high-traffic areas needing variable frequency

### Resetting Rotation History

Delete or rename `chore_state.json`. Next run will create fresh state with new anchor Sunday.

### Testing Fairness Changes

1. Back up `chore_state.json`
2. Modify penalty constants at top of [house_duties.py](house_duties.py)
3. Run scheduler multiple times with same roster
4. Analyze `brother_task_counts` distribution in state file
5. Restore backup if results degrade

## Output Format

### Terminal
Deck-organized schedule grouped by date → deck (Zero/First/Second/Third order) → tasks with assigned brothers.

### CSV ([schedule.csv](schedule.csv))
Sorted by deck, then due date.  
Columns: `due, deck, task_key, task, category, people_needed, assigned, weight_total`

### JSON ([schedule.json](schedule.json))
Array of assignment objects for machine-readable integrations.

## Important Notes

- **Never modify `anchor_sunday`** in state file — breaks biweekly parity tracking
- **Keep `RANDOM_SEED` constant** during semester — changes alter fairness trajectory
- **Let algorithm manage `bonus_counts`** — manual edits defeat rotation equity
- **Always assign tasks to a deck** — required for proper output grouping

## License

MIT License - Feel free to adapt for your organization's needs.

## Contributing

Pull requests welcome! Please maintain the existing fairness algorithm behavior and add tests for new features.

# House Duties Scheduler

A modular chore scheduling system with persistent state tracking, fairness algorithms, and deck-based organization. Designed for fraternity houses but adaptable to any shared living situation.

## 🏗️ Project Structure

```
House Duties Script/
├── config/                      # Configuration files
│   ├── brothers.txt            # Active roster (one name per line)
│   └── brother_categories.json # Brother preferences (optional)
│
├── data/                        # Data files (generated)
│   ├── chore_state.json        # Persistent state tracking
│   ├── schedule.csv            # Current schedule (CSV format)
│   └── schedule.json           # Current schedule (JSON format)
│
├── docs/                        # Documentation
│   ├── ARCHITECTURE.md         # System architecture details
│   ├── DISCORD_BOT_SETUP.md    # Bot setup instructions
│   └── VALIDATION.md           # Validation procedures
│
├── house_duties/                # Main scheduler package
│   ├── __init__.py             # Package exports
│   ├── assignment.py           # Fairness-based assignment logic
│   ├── bonus.py                # Bonus 3rd cleaning selection
│   ├── cli.py                  # Command-line interface
│   ├── models.py               # Data models (TaskTemplate, Occurrence)
│   ├── output.py               # CSV/JSON output formatting
│   ├── scheduler.py            # Template expansion logic
│   ├── state.py                # State persistence
│   ├── templates.py            # Task definitions by deck
│   ├── utils.py                # Date/time utilities
│   └── validation.py           # Input validation
│
├── discord_bot/                 # Discord bot package
│   ├── __init__.py             # Package exports
│   ├── bot.py                  # Main bot instance
│   ├── commands.py             # Bot commands
│   ├── config.py               # Configuration management
│   ├── embeds.py               # Message formatting
│   └── scheduler.py            # Schedule execution
│
├── tests/                       # Test suite
│   ├── conftest.py             # Test fixtures
│   ├── test_assignment.py
│   ├── test_bonus.py
│   ├── test_cli.py
│   └── ...
│
├── house_duties.py              # Main entry point
├── discord_bot.py               # Discord bot entry point
├── house_duties_legacy.py       # Legacy monolithic version (backup)
├── .env.example                 # Environment variables template
├── .gitignore                   # Git ignore rules
├── pytest.ini                   # Test configuration
├── requirements.txt             # Python dependencies
└── README.md                    # This file
```

## 🚀 Quick Start

### Installation

1. **Clone the repository**
   ```bash
   git clone <repository-url>
   cd "House Duties Script"
   ```

2. **Install dependencies**
   ```bash
   pip install -r requirements.txt
   ```

3. **Configure roster**
   ```bash
   # Edit config/brothers.txt - one name per line
   John Smith
   Jane Doe
   # Comments start with #
   ```

4. **Run the scheduler**
   ```bash
   python house_duties.py
   ```

   Output will be saved to:
   - `data/schedule.csv` - Spreadsheet format
   - `data/schedule.json` - Machine-readable format
   - Terminal output - Organized by deck and date

## 📋 Usage

### Basic Commands

```bash
# Generate 1 week schedule (auto-detect Sunday)
python house_duties.py

# Generate 2 weeks
python house_duties.py --weeks 2

# Start from specific Sunday
python house_duties.py --start 2026-01-19

# Preview without saving state
python house_duties.py --dry-run

# Verbose debug logging
python house_duties.py --verbose
```

### Advanced Options

```bash
# Custom file paths
python house_duties.py \
  --brothers config/brothers.txt \
  --state data/chore_state.json \
  --categories config/brother_categories.json \
  --output-csv data/schedule.csv \
  --output-json data/schedule.json

# Custom seed for different tie-breaking
python house_duties.py --seed 123

# Adjust minimum roster for bonus cleanings
python house_duties.py --min-bonus-roster 12
```

## 🤖 Discord Bot

### Setup

1. **Create `.env` file from template**
   ```bash
   cp .env.example .env
   ```

2. **Configure environment variables**
   ```env
   DISCORD_TOKEN=your_bot_token_here
   CHANNEL_ID=123456789012345678
   RUN_TIME_HOUR=8
   RUN_TIME_MINUTE=0
   SCRIPT_PATH=house_duties.py
   PYTHON_CMD=python
   ```

3. **Run the bot**
   ```bash
   python discord_bot.py
   ```

### Bot Commands

| Command | Description | Permissions |
|---------|-------------|-------------|
| `!run-schedule` | Manually trigger scheduler | Admin only |
| `!my-chores [@member]` | View assigned chores | Everyone |
| `!chores-today` | View today's chores | Everyone |
| `!ping` | Check bot status | Everyone |

## 🧠 Key Concepts

### Fairness Algorithm

The scheduler uses a multi-factor scoring system to ensure equitable distribution:

- **Base Load**: Cumulative task weight (severity × effort_multiplier)
- **Repeat Penalty** (×1.50): Discourages same task assignment
- **Recent Penalty** (×0.60): Avoids back-to-back weeks on same task
- **Day Penalty** (×0.75): Spreads chores across days
- **Preference Bonus** (-0.35): Rewards preferred categories

Lower scores are assigned first.

### Biweekly Parity

Tasks like "Brasso" and "Blue" alternate between odd/even weeks based on `anchor_sunday` in state file. **Never modify the anchor** unless intentionally resetting the rotation cycle.

### Bonus Third Cleaning

Tasks marked `flexible_2_3x=True` can get a 3rd cleaning when roster ≥ `BONUS_THIRD_CLEANING_MIN_ROSTER` (default 14). Selection uses deterministic algorithm favoring:
1. High-priority categories (bathrooms > floors > common)
2. Tasks with fewer historical bonus counts
3. Stable hash for reproducibility

## ⚙️ Configuration

### Constraints File (Optional)

Create `constraints.json`:

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
  },
  "brother_unavailable_dates": {
    "Mike": ["2026-01-27"],
    "Sarah": [
      {"start": "2026-02-15", "end": "2026-02-22"}
    ],
    "Tom": [
      "2026-01-30",
      {"start": "2026-03-01", "end": "2026-03-07"}
    ]
  }
}
```

**Constraint Types:**
- `exempt_all`: Permanently exclude from all chores
- `on_call_only`: Use only as backup when no one else available
- `max_per_brother_per_week` / `max_per_brother_per_day`: Task limits
- `brother_category_bans`: Exclude from specific categories
- `brother_task_bans`: Exclude from specific tasks
- `brother_preferred_categories`: Give preference bonus (-0.35 score)
- **`brother_unavailable_dates`**: Temporarily exclude for specific dates/ranges
  - Single date: `"2026-01-27"` (YYYY-MM-DD format)
  - Date range: `{"start": "2026-02-15", "end": "2026-02-22"}` (inclusive)

### Adding New Tasks

Edit `house_duties/templates.py`:

```python
TaskTemplate(
    key="NEW_TASK",              # Unique identifier
    deck="Second Deck",          # Zero/First/Second/Third/Other
    label="My New Task",
    category="bathrooms",        # k&m, bathrooms, floors, laundry, common, other
    people_needed=2,
    cadence="n_per_week",        # weekly, biweekly, n_per_week
    times_per_week=2,
    preferred_days=[2, 4],       # 0=Sun, 6=Sat
    severity=4,                  # 1-5 scale
    effort_multiplier=1.1,
    flexible_2_3x=True           # Enable bonus 3rd cleaning
)
```

## 🧪 Testing

```bash
# Run all tests
pytest

# Run with coverage
pytest --cov=house_duties --cov-report=html

# Run specific test file
pytest tests/test_assignment.py -v

# Run specific test
pytest tests/test_bonus.py::test_bonus_selection -v
```

## 📦 Dependencies

- **Python 3.8+**
- `discord.py` - Discord bot integration
- `python-dotenv` - Environment variable management
- `pytest` - Testing framework (dev)

## 🔄 Migration from Legacy

The original monolithic `house_duties_legacy.py` has been refactored into modular packages. The legacy file is retained for reference but is no longer used.

**Benefits of new structure:**
- ✅ Easier testing and maintenance
- ✅ Better code organization
- ✅ Clearer separation of concerns
- ✅ Reusable components
- ✅ Improved documentation

## 🤝 Contributing

1. Make changes in feature branch
2. Add/update tests
3. Run test suite: `pytest`
4. Update documentation
5. Submit pull request

## 📝 License

Internal fraternity use. All rights reserved.

## 📞 Support

For questions or issues:
- Check `docs/` for detailed documentation
- Review test files for usage examples
- Contact system administrator

---

**Last Updated**: January 2026  
**Version**: 1.2.0  
**Maintainer**: House Duties Committee

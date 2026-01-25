# Brother Unavailability Examples

This file demonstrates how to mark brothers as unavailable for specific dates or date ranges when they're out of the house.

## Example Scenarios

### Spring Break Trip (Date Range)
John is going home for spring break from March 10-17, 2026:

```json
{
  "brother_unavailable_dates": {
    "John": [
      {"start": "2026-03-10", "end": "2026-03-17"}
    ]
  }
}
```

### Job Interview (Single Day)
Sarah has a job interview on January 30, 2026:

```json
{
  "brother_unavailable_dates": {
    "Sarah": ["2026-01-30"]
  }
}
```

### Multiple Absences
Mike has both a single day absence and a week-long trip:

```json
{
  "brother_unavailable_dates": {
    "Mike": [
      "2026-01-27",
      {"start": "2026-02-15", "end": "2026-02-22"}
    ]
  }
}
```

### Multiple Brothers
Several brothers out at different times:

```json
{
  "brother_unavailable_dates": {
    "John": [{"start": "2026-03-10", "end": "2026-03-17"}],
    "Sarah": ["2026-01-30"],
    "Mike": [
      "2026-01-27",
      {"start": "2026-02-15", "end": "2026-02-22"}
    ],
    "Alex": [{"start": "2026-04-01", "end": "2026-04-07"}]
  }
}
```

## Complete constraints.json Example

Here's a full constraints file with various settings including unavailable dates:

```json
{
  "exempt_all": [],
  "on_call_only": ["BackupBrother"],
  "max_per_brother_per_week": 5,
  "max_per_brother_per_day": 2,
  "brother_category_bans": {
    "Tom": ["bathrooms"]
  },
  "brother_task_bans": {
    "Jane": ["SD_SINKS"]
  },
  "brother_preferred_categories": {
    "Alex": ["floors"],
    "Chris": ["k&m"]
  },
  "brother_unavailable_dates": {
    "John": [{"start": "2026-03-10", "end": "2026-03-17"}],
    "Sarah": ["2026-01-30", "2026-02-14"],
    "Mike": [
      "2026-01-27",
      {"start": "2026-02-15", "end": "2026-02-22"}
    ]
  }
}
```

## Date Format Rules

- **Single dates**: Use ISO format `"YYYY-MM-DD"` (e.g., `"2026-01-30"`)
- **Date ranges**: Use object with `start` and `end` keys (both inclusive)
  ```json
  {"start": "2026-03-10", "end": "2026-03-17"}
  ```
- **Multiple entries**: Put them in an array
  ```json
  ["2026-01-30", {"start": "2026-03-10", "end": "2026-03-17"}]
  ```

## How It Works

1. When you run the scheduler, it checks each brother against the constraints
2. If a task is due on a date when a brother is unavailable, they won't be assigned
3. The scheduler will assign someone else who is available
4. Unavailable dates don't affect fairness tracking - brothers won't be penalized for being unavailable

## Usage Tips

- **Update before running**: Edit `config/constraints.json` before running the scheduler
- **Plan ahead**: Add unavailable dates as soon as brothers inform you
- **Remove old dates**: You can remove past dates to keep the file clean
- **No default file needed**: If no `constraints.json` exists, everyone is available
- **Test first**: Run with `--dry-run` (if implemented) to preview assignments

## Common Use Cases

- **Academic**: Exams, group projects, study abroad
- **Personal**: Family visits, medical appointments, interviews
- **Travel**: Vacations, conferences, athletic events
- **Emergencies**: Temporary situations requiring time off from chores

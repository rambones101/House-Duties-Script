# Quick Reference: Marking Brothers Unavailable

## Step-by-Step Guide

### 1. Locate the constraints file
File: `config/constraints.json`

If it doesn't exist, create it with this template:
```json
{
  "brother_unavailable_dates": {}
}
```

### 2. Add unavailable dates

**For a single day off:**
```json
{
  "brother_unavailable_dates": {
    "Brother Name": ["2026-01-30"]
  }
}
```

**For a week-long absence:**
```json
{
  "brother_unavailable_dates": {
    "Brother Name": [
      {"start": "2026-03-10", "end": "2026-03-17"}
    ]
  }
}
```

**For multiple brothers:**
```json
{
  "brother_unavailable_dates": {
    "John": ["2026-01-30"],
    "Sarah": [{"start": "2026-02-15", "end": "2026-02-22"}],
    "Mike": ["2026-01-27", "2026-02-03"]
  }
}
```

### 3. Run the scheduler
```bash
python house_duties.py
```

The scheduler will automatically skip assigning chores to unavailable brothers on those dates.

## Important Notes

✅ **DO:**
- Use exact names as they appear in `brothers.txt`
- Use YYYY-MM-DD format (e.g., "2026-01-30")
- Include both start and end dates for ranges
- Update as soon as you learn about absences

❌ **DON'T:**
- Use abbreviated names
- Use MM/DD/YYYY or other formats
- Forget to save the file after editing
- Leave old dates in the file indefinitely (clean up periodically)

## Real-World Example

Brothers tell you:
- "I'm going home Jan 27th" → Add single date
- "I'll be gone Feb 15-22 for spring break" → Add date range
- "I have interviews on Jan 30 and Feb 3" → Add multiple single dates

Your `config/constraints.json`:
```json
{
  "brother_unavailable_dates": {
    "John": ["2026-01-27"],
    "Sarah": [{"start": "2026-02-15", "end": "2026-02-22"}],
    "Mike": ["2026-01-30", "2026-02-03"]
  }
}
```

## Troubleshooting

**Problem:** Brother still got assigned on unavailable date
- Check spelling of name (must match `brothers.txt` exactly)
- Check date format (must be YYYY-MM-DD)
- Make sure you saved the file
- Check for JSON syntax errors (commas, brackets, quotes)

**Problem:** "Invalid JSON" error
- Use a JSON validator online
- Check for missing commas between entries
- Check for proper quote marks (" not ' or ")
- Ensure brackets and braces are balanced

**Problem:** Can I make someone unavailable for entire semester?
- Yes! Use a large date range covering the full semester:
  ```json
  {"start": "2026-01-15", "end": "2026-05-15"}
  ```
- Or better yet, add them to `exempt_all` for permanent exemption

# Data Validation Guide

The House Duties Scheduler includes comprehensive input validation to catch configuration errors early and ensure fair, correct scheduling. This document details all validation rules and how to resolve common issues.

## Overview

Validation occurs automatically after loading input files and before schedule generation. The process validates:

1. **Brother roster** - Names, duplicates, format
2. **Task templates** - Required fields, valid values, consistency
3. **Constraints** - Valid brother references, category names, numeric ranges
4. **Categories** - Brother membership validation

## Brother Validation

### Rules

| Check | Rule | Error Message |
|-------|------|---------------|
| Empty roster | At least one brother required | "Brother roster cannot be empty" |
| None values | No null entries allowed | "Brother at index {i} is None" |
| Type checking | All entries must be strings | "Brother at index {i} is not a string" |
| Empty strings | No blank names after trimming | "Empty brother names found at indices: {list}" |
| Duplicates | Case-insensitive uniqueness | "Duplicate brother names found: {names}" |

### Warnings

- **Short names** (< 2 characters): "Very short brother names found"
- **Special characters**: Names with non-alphabetic characters (except space, hyphen, period, apostrophe)

### Examples

**❌ Invalid:**
```txt
# brothers.txt
John
Jane
john    # Duplicate (case-insensitive)
        # Empty name
Bob
```

**✅ Valid:**
```txt
# brothers.txt
John
Jane
Bob
Alice
Charlie
```

### Resolution

1. Remove duplicate entries (keep one)
2. Remove empty lines between names
3. Ensure each name is on its own line
4. Use `#` for comments only

## Task Template Validation

### Required Attributes

Every task template must have:
- `key` - Unique identifier (non-empty string)
- `label` - Display name (non-empty string)
- `deck` - Deck assignment (non-empty string)
- `category` - Valid category name
- `people_needed` - Integer ≥ 1
- `cadence` - One of: weekly, biweekly, n_per_week

### Category Validation

Valid categories:
- `k&m` - Kitchen & Maintenance
- `bathrooms` - Bathroom cleaning
- `floors` - Floor sweeping/mopping
- `laundry` - Laundry room
- `common` - Common areas
- `other` - Miscellaneous tasks

**Error if category not in this list.**

### Cadence-Specific Rules

#### Weekly / Biweekly
- `days_of_week` (optional): List of integers 0-6 (Sun-Sat)
- Invalid day numbers cause error

#### N Per Week
- `times_per_week` (required): Integer 1-7
- `preferred_days` (optional): List of integers 0-6
- Error if `times_per_week` missing or out of range

### Numeric Validation

| Field | Type | Range | Default |
|-------|------|-------|---------|
| `people_needed` | int | ≥ 1 | Required |
| `severity` | int | 1-5 | 3 |
| `effort_multiplier` | float | > 0 | 1.0 |
| `times_per_week` | int | 1-7 | None |

### Examples

**❌ Invalid Template:**
```python
TaskTemplate(
    key="",  # Empty key
    label="Clean Bathroom",
    deck="First Deck",
    category="invalid_cat",  # Not a valid category
    people_needed=0,  # Must be ≥ 1
    cadence="daily",  # Invalid cadence
    times_per_week=8  # Exceeds 7
)
```

**✅ Valid Template:**
```python
TaskTemplate(
    key="FD_BATH_CLEAN",
    label="First Deck Bathroom",
    deck="First Deck",
    category="bathrooms",
    people_needed=2,
    cadence="n_per_week",
    times_per_week=2,
    preferred_days=[2, 4],  # Tuesday, Thursday
    severity=4,
    effort_multiplier=1.2
)
```

### Resolution

1. Ensure all required fields are present
2. Use valid category names from the allowed list
3. Choose valid cadence type
4. For `n_per_week`, always set `times_per_week`
5. Keep numeric values in specified ranges
6. Make task keys unique across all templates

## Constraint Validation

### Brother Reference Validation

All brother names referenced in constraints must exist in the roster:

- `exempt_all`
- `on_call_only`
- Keys in `brother_category_bans`
- Keys in `brother_task_bans`
- Keys in `brother_preferred_categories`

**Error if any referenced brother not found in roster.**

### Category Reference Validation

Category names in constraints must be valid:

- Values in `brother_category_bans`
- Values in `brother_preferred_categories`

**Error if any category not in valid set.**

### Numeric Constraint Validation

| Constraint | Type | Range |
|------------|------|-------|
| `max_per_brother_per_week` | int | ≥ 1 or null |
| `max_per_brother_per_day` | int | ≥ 1 or null |

### Logical Validation

- **Cannot exempt entire roster**: `exempt_all` cannot include all brothers
- **Task bans warning**: Warning if task ban references non-existent task key (non-fatal)

### Examples

**❌ Invalid Constraints:**
```json
{
  "exempt_all": ["John", "NonExistentBrother"],  // Invalid brother
  "brother_category_bans": {
    "Jane": ["bathrooms", "invalid_category"]  // Invalid category
  },
  "max_per_brother_per_week": -1  // Negative value
}
```

**✅ Valid Constraints:**
```json
{
  "exempt_all": ["John"],
  "on_call_only": ["BackupBrother"],
  "max_per_brother_per_week": 5,
  "max_per_brother_per_day": 2,
  "brother_category_bans": {
    "Jane": ["k&m", "laundry"]
  },
  "brother_task_bans": {
    "Bob": ["FD_KM_SUN", "SD_SINKS"]
  },
  "brother_preferred_categories": {
    "Alice": ["floors", "common"]
  }
}
```

### Resolution

1. Verify all brother names match roster exactly (case-sensitive in JSON)
2. Use only valid category names
3. Ensure numeric constraints are positive
4. Don't exempt all brothers
5. Check task key spelling against templates

## Category Validation

Categories file structure:
```json
{
  "actives": ["John", "Jane", "Bob"],
  "junior_actives": ["Alice", "Charlie"]
}
```

### Rules
- All values must be arrays
- All brother names must exist in roster
- Multiple categories can contain same brother

**Error if any brother name not found in roster.**

## Validation CLI Options

### Default Behavior
Validation errors **stop execution** with error message and exit code 1.

```powershell
python house_duties.py
# If validation fails:
# ERROR: Duplicate brother names found: john
# (exits with code 1)
```

### Override with --ignore-validation-errors

**⚠️ NOT RECOMMENDED** - Only use for debugging or emergency situations.

```powershell
python house_duties.py --ignore-validation-errors
# WARNING: Continuing with invalid data (--ignore-validation-errors enabled)
# (continues execution despite validation errors)
```

### Validation Logging

Validation uses these log levels:
- **ERROR**: Fatal validation failures (stops execution by default)
- **WARNING**: Non-fatal issues (short names, special characters, non-existent task keys)
- **INFO**: Validation success messages

Enable verbose logging to see all validation details:
```powershell
python house_duties.py -v
```

## Common Validation Errors

### 1. Duplicate Brothers

**Error:** `Duplicate brother names found: john`

**Cause:** Same name appears multiple times (case-insensitive)

**Fix:** Remove duplicate entries from brothers.txt

---

### 2. Invalid Brother in Constraints

**Error:** `Invalid brothers in 'exempt_all': John. Not found in roster.`

**Cause:** Constraint references brother not in roster

**Fix:** 
- Add brother to brothers.txt, OR
- Remove brother from constraints.json

---

### 3. Invalid Category

**Error:** `Invalid category 'invalid_cat'. Must be one of: k&m, bathrooms, floors, laundry, common, other`

**Cause:** Task template uses undefined category

**Fix:** Use one of the valid category names

---

### 4. Missing Required Field

**Error:** `Template 5: Missing required attribute 'cadence'`

**Cause:** Task template missing required field

**Fix:** Add the missing field to template definition

---

### 5. Invalid Cadence Configuration

**Error:** `Template KEY1: 'times_per_week' required for n_per_week cadence`

**Cause:** `n_per_week` cadence without `times_per_week` value

**Fix:** Add `times_per_week` parameter:
```python
add("KEY1", "First Deck", "Task", "bathrooms", 2,
    "n_per_week", times_per_week=2, preferred_days=[2, 4])
```

---

### 6. All Brothers Exempted

**Error:** `Cannot exempt all brothers - roster would be empty`

**Cause:** Every brother in roster is in `exempt_all`

**Fix:** Remove some brothers from `exempt_all` to have active pool

---

### 7. Invalid Day of Week

**Error:** `Invalid day in 'days_of_week': 7. Must be 0-6 (Sun-Sat)`

**Cause:** Day number outside valid range

**Fix:** Use 0-6 (Sunday=0, Monday=1, ..., Saturday=6)

---

## Best Practices

1. **Validate early**: Run scheduler with `--dry-run` after roster/constraint changes
2. **Fix errors immediately**: Don't use `--ignore-validation-errors` in production
3. **Use verbose logging**: `python house_duties.py -v --dry-run` to see all validation details
4. **Keep consistent naming**: Match brother names exactly between files
5. **Test constraints**: Verify constraint behavior with small roster first
6. **Document custom categories**: If adding new categories, update both code and documentation

## Testing Validation

Run validation test suite:
```powershell
pytest tests/test_validation.py -v
```

Test specific validation scenario:
```powershell
pytest tests/test_validation.py::test_validate_brothers_duplicates -v
```

## Integration with CI/CD

In automated workflows, validation ensures data quality:

```yaml
# Example GitHub Actions workflow
- name: Run scheduler with validation
  run: |
    python house_duties.py --dry-run
    # Exits with code 1 if validation fails
```

Validation exit codes:
- **0**: Success - all validation passed
- **1**: Failure - validation error encountered

## Module Usage

Direct module usage for custom validation:

```python
from house_duties.validation import (
    validate_brothers,
    validate_task_templates,
    validate_constraints,
    ValidationError
)

try:
    brothers = ["John", "Jane", "Bob"]
    validate_brothers(brothers)
    print("Brothers validated successfully")
except ValidationError as e:
    print(f"Validation failed: {e}")
```

See module docstrings for full API documentation.

"""
Tests for the validation module.
"""

import pytest
from house_duties.validation import (
    validate_brothers,
    validate_task_template,
    validate_task_templates,
    validate_constraints,
    validate_categories,
    validate_all,
    ValidationError
)
from dataclasses import dataclass
from typing import List, Optional


@dataclass
class MockTaskTemplate:
    """Mock TaskTemplate for testing."""
    key: str
    label: str
    deck: str
    category: str
    people_needed: int
    cadence: str
    days_of_week: Optional[List[int]] = None
    times_per_week: Optional[int] = None
    preferred_days: Optional[List[int]] = None
    severity: int = 3
    effort_multiplier: float = 1.0
    flexible_2_3x: bool = False


# =========================
# Brother Validation Tests
# =========================

def test_validate_brothers_valid():
    """Test valid brother roster."""
    brothers = ["John", "Jane", "Bob"]
    result = validate_brothers(brothers)
    assert result == ["John", "Jane", "Bob"]


def test_validate_brothers_strips_whitespace():
    """Test that whitespace is stripped."""
    brothers = ["  John  ", "Jane\t", " Bob "]
    result = validate_brothers(brothers)
    assert result == ["John", "Jane", "Bob"]


def test_validate_brothers_empty_not_allowed():
    """Test that empty roster raises error by default."""
    with pytest.raises(ValidationError, match="cannot be empty"):
        validate_brothers([])


def test_validate_brothers_empty_allowed():
    """Test that empty roster can be allowed."""
    result = validate_brothers([], allow_empty=True)
    assert result == []


def test_validate_brothers_none_value():
    """Test that None in list raises error."""
    with pytest.raises(ValidationError, match="is None"):
        validate_brothers(["John", None, "Jane"])


def test_validate_brothers_non_string():
    """Test that non-string value raises error."""
    with pytest.raises(ValidationError, match="not a string"):
        validate_brothers(["John", 123, "Jane"])


def test_validate_brothers_empty_string():
    """Test that empty string raises error."""
    with pytest.raises(ValidationError, match="Empty brother names"):
        validate_brothers(["John", "", "Jane"])


def test_validate_brothers_whitespace_only():
    """Test that whitespace-only string raises error."""
    with pytest.raises(ValidationError, match="Empty brother names"):
        validate_brothers(["John", "   ", "Jane"])


def test_validate_brothers_duplicates():
    """Test that duplicates raise error."""
    with pytest.raises(ValidationError, match="Duplicate brother names"):
        validate_brothers(["John", "Jane", "john"])


def test_validate_brothers_case_insensitive_duplicates():
    """Test that case-insensitive duplicates are caught."""
    with pytest.raises(ValidationError, match="Duplicate.*john"):
        validate_brothers(["John", "JOHN", "Jane"])


# =========================
# Task Template Validation Tests
# =========================

def test_validate_task_template_valid():
    """Test valid task template."""
    template = MockTaskTemplate(
        key="TEST_KEY",
        label="Test Task",
        deck="First Deck",
        category="bathrooms",
        people_needed=2,
        cadence="weekly",
        days_of_week=[0, 3]
    )
    validate_task_template(template)  # Should not raise


def test_validate_task_template_missing_required():
    """Test that missing required fields raise error."""
    @dataclass
    class IncompleteTemplate:
        key: str
        label: str
    
    template = IncompleteTemplate(key="TEST", label="Test")
    with pytest.raises(ValidationError, match="Missing required attribute"):
        validate_task_template(template)


def test_validate_task_template_empty_key():
    """Test that empty key raises error."""
    template = MockTaskTemplate(
        key="",
        label="Test Task",
        deck="First Deck",
        category="bathrooms",
        people_needed=2,
        cadence="weekly"
    )
    with pytest.raises(ValidationError, match="'key' must be non-empty"):
        validate_task_template(template)


def test_validate_task_template_invalid_category():
    """Test that invalid category raises error."""
    template = MockTaskTemplate(
        key="TEST_KEY",
        label="Test Task",
        deck="First Deck",
        category="invalid_category",
        people_needed=2,
        cadence="weekly"
    )
    with pytest.raises(ValidationError, match="Invalid category"):
        validate_task_template(template)


def test_validate_task_template_invalid_people_needed():
    """Test that invalid people_needed raises error."""
    template = MockTaskTemplate(
        key="TEST_KEY",
        label="Test Task",
        deck="First Deck",
        category="bathrooms",
        people_needed=0,
        cadence="weekly"
    )
    with pytest.raises(ValidationError, match="people_needed.*>= 1"):
        validate_task_template(template)


def test_validate_task_template_invalid_cadence():
    """Test that invalid cadence raises error."""
    template = MockTaskTemplate(
        key="TEST_KEY",
        label="Test Task",
        deck="First Deck",
        category="bathrooms",
        people_needed=2,
        cadence="invalid_cadence"
    )
    with pytest.raises(ValidationError, match="Invalid cadence"):
        validate_task_template(template)


def test_validate_task_template_invalid_day():
    """Test that invalid day of week raises error."""
    template = MockTaskTemplate(
        key="TEST_KEY",
        label="Test Task",
        deck="First Deck",
        category="bathrooms",
        people_needed=2,
        cadence="weekly",
        days_of_week=[0, 7]  # 7 is invalid
    )
    with pytest.raises(ValidationError, match="Invalid day.*Must be 0-6"):
        validate_task_template(template)


def test_validate_task_template_n_per_week_missing_times():
    """Test that n_per_week without times_per_week raises error."""
    template = MockTaskTemplate(
        key="TEST_KEY",
        label="Test Task",
        deck="First Deck",
        category="bathrooms",
        people_needed=2,
        cadence="n_per_week"
    )
    with pytest.raises(ValidationError, match="times_per_week.*required"):
        validate_task_template(template)


def test_validate_task_template_n_per_week_invalid_times():
    """Test that invalid times_per_week raises error."""
    template = MockTaskTemplate(
        key="TEST_KEY",
        label="Test Task",
        deck="First Deck",
        category="bathrooms",
        people_needed=2,
        cadence="n_per_week",
        times_per_week=0
    )
    with pytest.raises(ValidationError, match="times_per_week.*>= 1"):
        validate_task_template(template)


def test_validate_task_template_n_per_week_too_many_times():
    """Test that times_per_week > 7 raises error."""
    template = MockTaskTemplate(
        key="TEST_KEY",
        label="Test Task",
        deck="First Deck",
        category="bathrooms",
        people_needed=2,
        cadence="n_per_week",
        times_per_week=8
    )
    with pytest.raises(ValidationError, match="cannot exceed 7"):
        validate_task_template(template)


def test_validate_task_template_invalid_severity():
    """Test that invalid severity raises error."""
    template = MockTaskTemplate(
        key="TEST_KEY",
        label="Test Task",
        deck="First Deck",
        category="bathrooms",
        people_needed=2,
        cadence="weekly",
        severity=6
    )
    with pytest.raises(ValidationError, match="severity.*1-5"):
        validate_task_template(template)


def test_validate_task_template_negative_effort():
    """Test that negative effort_multiplier raises error."""
    template = MockTaskTemplate(
        key="TEST_KEY",
        label="Test Task",
        deck="First Deck",
        category="bathrooms",
        people_needed=2,
        cadence="weekly",
        effort_multiplier=-1.0
    )
    with pytest.raises(ValidationError, match="effort_multiplier.*positive"):
        validate_task_template(template)


# =========================
# Task Templates (Plural) Validation Tests
# =========================

def test_validate_task_templates_valid():
    """Test valid list of templates."""
    templates = [
        MockTaskTemplate("KEY1", "Task 1", "First Deck", "bathrooms", 2, "weekly"),
        MockTaskTemplate("KEY2", "Task 2", "Second Deck", "floors", 1, "weekly")
    ]
    validate_task_templates(templates)  # Should not raise


def test_validate_task_templates_empty():
    """Test that empty template list raises error."""
    with pytest.raises(ValidationError, match="No task templates"):
        validate_task_templates([])


def test_validate_task_templates_duplicate_keys():
    """Test that duplicate keys raise error."""
    templates = [
        MockTaskTemplate("KEY1", "Task 1", "First Deck", "bathrooms", 2, "weekly"),
        MockTaskTemplate("KEY1", "Task 2", "Second Deck", "floors", 1, "weekly")
    ]
    with pytest.raises(ValidationError, match="Duplicate template keys"):
        validate_task_templates(templates)


# =========================
# Constraints Validation Tests
# =========================

def test_validate_constraints_valid():
    """Test valid constraints."""
    brothers = ["John", "Jane", "Bob"]
    constraints = {
        "exempt_all": ["John"],
        "max_per_brother_per_week": 5
    }
    validate_constraints(constraints, brothers)  # Should not raise


def test_validate_constraints_invalid_brother_exempt():
    """Test that invalid brother in exempt_all raises error."""
    brothers = ["John", "Jane"]
    constraints = {"exempt_all": ["John", "InvalidBrother"]}
    with pytest.raises(ValidationError, match="Invalid brothers.*exempt_all"):
        validate_constraints(constraints, brothers)


def test_validate_constraints_all_exempt():
    """Test that exempting all brothers raises error."""
    brothers = ["John", "Jane"]
    constraints = {"exempt_all": ["John", "Jane"]}
    with pytest.raises(ValidationError, match="Cannot exempt all brothers"):
        validate_constraints(constraints, brothers)


def test_validate_constraints_invalid_brother_on_call():
    """Test that invalid brother in on_call_only raises error."""
    brothers = ["John", "Jane"]
    constraints = {"on_call_only": ["InvalidBrother"]}
    with pytest.raises(ValidationError, match="Invalid brothers.*on_call_only"):
        validate_constraints(constraints, brothers)


def test_validate_constraints_invalid_max_week():
    """Test that invalid max_per_brother_per_week raises error."""
    brothers = ["John", "Jane"]
    constraints = {"max_per_brother_per_week": 0}
    with pytest.raises(ValidationError, match="max_per_brother_per_week.*>= 1"):
        validate_constraints(constraints, brothers)


def test_validate_constraints_invalid_max_day():
    """Test that invalid max_per_brother_per_day raises error."""
    brothers = ["John", "Jane"]
    constraints = {"max_per_brother_per_day": -1}
    with pytest.raises(ValidationError, match="max_per_brother_per_day.*>= 1"):
        validate_constraints(constraints, brothers)


def test_validate_constraints_invalid_category_ban():
    """Test that invalid category in bans raises error."""
    brothers = ["John", "Jane"]
    constraints = {
        "brother_category_bans": {
            "John": ["bathrooms", "invalid_category"]
        }
    }
    with pytest.raises(ValidationError, match="Invalid categories.*invalid_category"):
        validate_constraints(constraints, brothers)


def test_validate_constraints_invalid_brother_in_bans():
    """Test that invalid brother in category bans raises error."""
    brothers = ["John", "Jane"]
    constraints = {
        "brother_category_bans": {
            "InvalidBrother": ["bathrooms"]
        }
    }
    with pytest.raises(ValidationError, match="Invalid brother.*InvalidBrother"):
        validate_constraints(constraints, brothers)


def test_validate_constraints_invalid_preferred_categories():
    """Test that invalid preferred categories raise error."""
    brothers = ["John", "Jane"]
    constraints = {
        "brother_preferred_categories": {
            "John": ["bathrooms", "invalid_category"]
        }
    }
    with pytest.raises(ValidationError, match="Invalid categories.*invalid_category"):
        validate_constraints(constraints, brothers)


# =========================
# Categories Validation Tests
# =========================

def test_validate_categories_valid():
    """Test valid categories."""
    brothers = ["John", "Jane", "Bob"]
    categories = {
        "actives": ["John", "Jane"],
        "pledges": ["Bob"]
    }
    validate_categories(categories, brothers)  # Should not raise


def test_validate_categories_invalid_brother():
    """Test that invalid brother in category raises error."""
    brothers = ["John", "Jane"]
    categories = {
        "actives": ["John", "InvalidBrother"]
    }
    with pytest.raises(ValidationError, match="Invalid brothers.*actives"):
        validate_categories(categories, brothers)


# =========================
# Validate All Tests
# =========================

def test_validate_all_success():
    """Test that validate_all succeeds with valid inputs."""
    brothers = ["John", "Jane", "Bob"]
    templates = [
        MockTaskTemplate("KEY1", "Task 1", "First Deck", "bathrooms", 2, "weekly"),
        MockTaskTemplate("KEY2", "Task 2", "Second Deck", "floors", 1, "weekly")
    ]
    constraints = {
        "exempt_all": [],
        "max_per_brother_per_week": 5
    }
    categories = {
        "actives": ["John", "Jane"],
        "pledges": ["Bob"]
    }
    
    validate_all(brothers, templates, constraints, categories)  # Should not raise


def test_validate_all_invalid_brothers():
    """Test that validate_all fails with invalid brothers."""
    brothers = ["John", "john"]  # Duplicate
    templates = [
        MockTaskTemplate("KEY1", "Task 1", "First Deck", "bathrooms", 2, "weekly")
    ]
    constraints = {}
    
    with pytest.raises(ValidationError, match="Duplicate"):
        validate_all(brothers, templates, constraints)


def test_validate_all_invalid_templates():
    """Test that validate_all fails with invalid templates."""
    brothers = ["John", "Jane"]
    templates = [
        MockTaskTemplate("KEY1", "Task 1", "First Deck", "bathrooms", 2, "weekly"),
        MockTaskTemplate("KEY1", "Task 2", "Second Deck", "floors", 1, "weekly")  # Duplicate key
    ]
    constraints = {}
    
    with pytest.raises(ValidationError, match="Duplicate"):
        validate_all(brothers, templates, constraints)


def test_validate_all_invalid_constraints():
    """Test that validate_all fails with invalid constraints."""
    brothers = ["John", "Jane"]
    templates = [
        MockTaskTemplate("KEY1", "Task 1", "First Deck", "bathrooms", 2, "weekly")
    ]
    constraints = {
        "exempt_all": ["InvalidBrother"]
    }
    
    with pytest.raises(ValidationError, match="Invalid brothers"):
        validate_all(brothers, templates, constraints)


def test_validate_all_task_ban_warning(caplog):
    """Test that task bans for non-existent tasks generate warning."""
    brothers = ["John", "Jane"]
    templates = [
        MockTaskTemplate("KEY1", "Task 1", "First Deck", "bathrooms", 2, "weekly")
    ]
    constraints = {
        "brother_task_bans": {
            "John": ["KEY1", "NONEXISTENT_KEY"]
        }
    }
    
    validate_all(brothers, templates, constraints)
    
    # Check that warning was logged
    assert any("non-existent tasks" in record.message.lower() for record in caplog.records)


def test_validate_all_no_categories():
    """Test that validate_all works without categories."""
    brothers = ["John", "Jane"]
    templates = [
        MockTaskTemplate("KEY1", "Task 1", "First Deck", "bathrooms", 2, "weekly")
    ]
    constraints = {}
    
    validate_all(brothers, templates, constraints, categories=None)  # Should not raise

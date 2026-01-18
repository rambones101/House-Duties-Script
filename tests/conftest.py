"""Test fixtures and utilities shared across test modules."""
import pytest
from datetime import date, datetime, time
from pathlib import Path
import tempfile
import json
import os


@pytest.fixture
def temp_dir():
    """Create a temporary directory for test files."""
    with tempfile.TemporaryDirectory() as tmpdir:
        yield Path(tmpdir)


@pytest.fixture
def sample_brothers():
    """Sample list of brothers for testing."""
    return ["Alex", "Bob", "Charlie", "Dave", "Eric", "Frank"]


@pytest.fixture
def sample_roster_file(temp_dir, sample_brothers):
    """Create a sample brothers.txt file."""
    roster_file = temp_dir / "brothers.txt"
    roster_file.write_text("\n".join(sample_brothers))
    return roster_file


@pytest.fixture
def sample_constraints():
    """Sample constraints dictionary."""
    return {
        "exempt_all": [],
        "on_call_only": [],
        "max_per_brother_per_week": 5,
        "max_per_brother_per_day": 2,
        "brother_category_bans": {
            "Alex": ["bathrooms"]
        },
        "brother_task_bans": {
            "Bob": ["SD_SINKS"]
        },
        "brother_preferred_categories": {
            "Charlie": ["floors"]
        }
    }


@pytest.fixture
def sample_constraints_file(temp_dir, sample_constraints):
    """Create a sample constraints.json file."""
    constraints_file = temp_dir / "constraints.json"
    constraints_file.write_text(json.dumps(sample_constraints, indent=2))
    return constraints_file


@pytest.fixture
def sample_state():
    """Sample state dictionary."""
    return {
        "anchor_sunday": "2026-01-18",
        "bonus_counts": {
            "ZD_RATSKELLER_FLOOR": 2,
            "SD_SINKS": 1
        },
        "brother_task_counts": {
            "Alex": {"SD_SINKS": 3, "FD_KM_SUN": 2},
            "Bob": {"SD_TOILETS": 2, "FD_KM_MON": 1}
        },
        "brother_last_week_tasks": {
            "Alex": {"SD_SINKS": 1},
            "Bob": {"FD_KM_MON": 1}
        }
    }


@pytest.fixture
def sample_state_file(temp_dir, sample_state):
    """Create a sample chore_state.json file."""
    state_file = temp_dir / "chore_state.json"
    state_file.write_text(json.dumps(sample_state, indent=2))
    return state_file


@pytest.fixture
def mock_sunday():
    """A fixed Sunday date for consistent testing."""
    return date(2026, 1, 18)


@pytest.fixture
def mock_datetime(monkeypatch, mock_sunday):
    """Mock date.today() to return a fixed date."""
    class MockDate(date):
        @classmethod
        def today(cls):
            return mock_sunday
    
    monkeypatch.setattr('house_duties.date', MockDate)
    return MockDate

"""Tests for brother unavailability date constraints."""
import pytest
from datetime import datetime, date
from house_duties.models import Occurrence
from house_duties.assignment import is_unavailable


def test_unavailable_single_date():
    """Test brother marked unavailable on a single date."""
    constraints = {
        "brother_unavailable_dates": {
            "John": ["2026-01-27"]
        }
    }
    
    occ_unavailable = Occurrence(
        task_key="TEST",
        task_label="Test Task",
        deck="Test Deck",
        category="test",
        people_needed=1,
        due_dt=datetime(2026, 1, 27, 23, 59),
        week_index=0,
        weight=1.0
    )
    
    occ_available = Occurrence(
        task_key="TEST",
        task_label="Test Task",
        deck="Test Deck",
        category="test",
        people_needed=1,
        due_dt=datetime(2026, 1, 28, 23, 59),
        week_index=0,
        weight=1.0
    )
    
    assert is_unavailable("John", occ_unavailable, constraints) is True
    assert is_unavailable("John", occ_available, constraints) is False
    assert is_unavailable("Jane", occ_unavailable, constraints) is False


def test_unavailable_date_range():
    """Test brother marked unavailable for a date range."""
    constraints = {
        "brother_unavailable_dates": {
            "Sarah": [
                {"start": "2026-02-15", "end": "2026-02-22"}
            ]
        }
    }
    
    # Before range
    occ_before = Occurrence(
        task_key="TEST",
        task_label="Test Task",
        deck="Test Deck",
        category="test",
        people_needed=1,
        due_dt=datetime(2026, 2, 14, 23, 59),
        week_index=0,
        weight=1.0
    )
    
    # Start of range
    occ_start = Occurrence(
        task_key="TEST",
        task_label="Test Task",
        deck="Test Deck",
        category="test",
        people_needed=1,
        due_dt=datetime(2026, 2, 15, 23, 59),
        week_index=0,
        weight=1.0
    )
    
    # Middle of range
    occ_middle = Occurrence(
        task_key="TEST",
        task_label="Test Task",
        deck="Test Deck",
        category="test",
        people_needed=1,
        due_dt=datetime(2026, 2, 18, 23, 59),
        week_index=0,
        weight=1.0
    )
    
    # End of range
    occ_end = Occurrence(
        task_key="TEST",
        task_label="Test Task",
        deck="Test Deck",
        category="test",
        people_needed=1,
        due_dt=datetime(2026, 2, 22, 23, 59),
        week_index=0,
        weight=1.0
    )
    
    # After range
    occ_after = Occurrence(
        task_key="TEST",
        task_label="Test Task",
        deck="Test Deck",
        category="test",
        people_needed=1,
        due_dt=datetime(2026, 2, 23, 23, 59),
        week_index=0,
        weight=1.0
    )
    
    assert is_unavailable("Sarah", occ_before, constraints) is False
    assert is_unavailable("Sarah", occ_start, constraints) is True
    assert is_unavailable("Sarah", occ_middle, constraints) is True
    assert is_unavailable("Sarah", occ_end, constraints) is True
    assert is_unavailable("Sarah", occ_after, constraints) is False


def test_unavailable_multiple_dates():
    """Test brother with multiple unavailable dates and ranges."""
    constraints = {
        "brother_unavailable_dates": {
            "Tom": [
                "2026-01-30",
                {"start": "2026-03-01", "end": "2026-03-07"}
            ]
        }
    }
    
    occ_single = Occurrence(
        task_key="TEST",
        task_label="Test Task",
        deck="Test Deck",
        category="test",
        people_needed=1,
        due_dt=datetime(2026, 1, 30, 23, 59),
        week_index=0,
        weight=1.0
    )
    
    occ_range = Occurrence(
        task_key="TEST",
        task_label="Test Task",
        deck="Test Deck",
        category="test",
        people_needed=1,
        due_dt=datetime(2026, 3, 5, 23, 59),
        week_index=0,
        weight=1.0
    )
    
    occ_available = Occurrence(
        task_key="TEST",
        task_label="Test Task",
        deck="Test Deck",
        category="test",
        people_needed=1,
        due_dt=datetime(2026, 2, 15, 23, 59),
        week_index=0,
        weight=1.0
    )
    
    assert is_unavailable("Tom", occ_single, constraints) is True
    assert is_unavailable("Tom", occ_range, constraints) is True
    assert is_unavailable("Tom", occ_available, constraints) is False


def test_unavailable_empty_constraints():
    """Test that brothers with no unavailable dates are always available."""
    constraints = {"brother_unavailable_dates": {}}
    
    occ = Occurrence(
        task_key="TEST",
        task_label="Test Task",
        deck="Test Deck",
        category="test",
        people_needed=1,
        due_dt=datetime(2026, 1, 27, 23, 59),
        week_index=0,
        weight=1.0
    )
    
    assert is_unavailable("Anyone", occ, constraints) is False


def test_unavailable_invalid_date_format():
    """Test that invalid date formats are handled gracefully."""
    constraints = {
        "brother_unavailable_dates": {
            "BadDate": ["not-a-date", "2026-99-99"]
        }
    }
    
    occ = Occurrence(
        task_key="TEST",
        task_label="Test Task",
        deck="Test Deck",
        category="test",
        people_needed=1,
        due_dt=datetime(2026, 1, 27, 23, 59),
        week_index=0,
        weight=1.0
    )
    
    # Should not raise exception, just return False
    assert is_unavailable("BadDate", occ, constraints) is False

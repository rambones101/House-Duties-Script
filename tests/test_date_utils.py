"""Tests for date and time utility functions."""
import pytest
from datetime import date, datetime, timedelta, time
import sys
import os

# Add parent directory to path to import house_duties
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from house_duties.utils import (
    most_recent_sunday,
    parse_start_sunday,
    week_start_for,
    dt_on,
    unique_sorted_days,
    week_index_from_anchor
)


class TestDateHelpers:
    """Test date utility functions."""
    
    @pytest.mark.unit
    def test_most_recent_sunday_on_sunday(self):
        """Test most_recent_sunday when given a Sunday."""
        sunday = date(2026, 1, 18)  # A Sunday
        assert most_recent_sunday(sunday) == sunday
    
    @pytest.mark.unit
    def test_most_recent_sunday_on_monday(self):
        """Test most_recent_sunday when given a Monday."""
        monday = date(2026, 1, 19)
        expected = date(2026, 1, 18)  # Previous Sunday
        assert most_recent_sunday(monday) == expected
    
    @pytest.mark.unit
    def test_most_recent_sunday_on_saturday(self):
        """Test most_recent_sunday when given a Saturday."""
        saturday = date(2026, 1, 24)
        expected = date(2026, 1, 18)  # Previous Sunday
        assert most_recent_sunday(saturday) == expected
    
    @pytest.mark.unit
    def test_parse_start_sunday_empty_string(self, mock_sunday):
        """Test parse_start_sunday with empty string uses today."""
        result = parse_start_sunday("")
        # Should return most recent Sunday from today
        assert result <= __import__('datetime').date.today()
        assert result.weekday() == 6  # Sunday
    
    @pytest.mark.unit
    def test_parse_start_sunday_with_date(self):
        """Test parse_start_sunday with explicit date."""
        date_str = "2026-01-25"
        result = parse_start_sunday(date_str)
        assert result == date(2026, 1, 25)
    
    @pytest.mark.unit
    def test_week_start_for_zero_weeks(self, mock_sunday):
        """Test week_start_for with week index 0."""
        start = week_start_for(mock_sunday, 0)
        assert start == mock_sunday
    
    @pytest.mark.unit
    def test_week_start_for_positive_weeks(self, mock_sunday):
        """Test week_start_for with positive week index."""
        start = week_start_for(mock_sunday, 2)
        expected = mock_sunday + timedelta(days=14)
        assert start == expected
    
    @pytest.mark.unit
    def test_dt_on_sunday(self, mock_sunday):
        """Test dt_on for Sunday."""
        due_time = time(23, 59)
        result = dt_on(mock_sunday, 0, due_time)
        expected = datetime(2026, 1, 18, 23, 59)
        assert result == expected
    
    @pytest.mark.unit
    def test_dt_on_saturday(self, mock_sunday):
        """Test dt_on for Saturday."""
        due_time = time(12, 0)
        result = dt_on(mock_sunday, 6, due_time)
        expected = datetime(2026, 1, 24, 12, 0)
        assert result == expected
    
    @pytest.mark.unit
    def test_unique_sorted_days_empty(self):
        """Test unique_sorted_days with empty list."""
        assert unique_sorted_days([]) == []
    
    @pytest.mark.unit
    def test_unique_sorted_days_duplicates(self):
        """Test unique_sorted_days removes duplicates."""
        days = [2, 4, 2, 6, 4]
        result = unique_sorted_days(days)
        assert result == [2, 4, 6]
    
    @pytest.mark.unit
    def test_unique_sorted_days_unsorted(self):
        """Test unique_sorted_days sorts the result."""
        days = [5, 1, 3]
        result = unique_sorted_days(days)
        assert result == [1, 3, 5]
    
    @pytest.mark.unit
    def test_week_index_from_anchor_same_week(self, mock_sunday):
        """Test week_index_from_anchor for same week."""
        anchor = mock_sunday
        current = mock_sunday
        assert week_index_from_anchor(anchor, current) == 0
    
    @pytest.mark.unit
    def test_week_index_from_anchor_one_week_later(self, mock_sunday):
        """Test week_index_from_anchor one week later."""
        anchor = mock_sunday
        current = mock_sunday + timedelta(days=7)
        assert week_index_from_anchor(anchor, current) == 1
    
    @pytest.mark.unit
    def test_week_index_from_anchor_four_weeks_later(self, mock_sunday):
        """Test week_index_from_anchor four weeks later."""
        anchor = mock_sunday
        current = mock_sunday + timedelta(days=28)
        assert week_index_from_anchor(anchor, current) == 4

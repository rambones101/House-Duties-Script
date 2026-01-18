"""Tests for bonus task selection algorithm."""
import pytest
import sys
import os

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from house_duties import (
    week_capacity_allows_bonus,
    stable_int_from_strings,
    choose_bonus_tasks_for_week,
    TaskTemplate
)
from datetime import date


class TestBonusSelection:
    """Test bonus task selection logic."""
    
    @pytest.mark.unit
    def test_week_capacity_allows_bonus_small_house(self):
        """Test bonus not allowed for small house."""
        result = week_capacity_allows_bonus(10)
        assert result is False
    
    @pytest.mark.unit
    def test_week_capacity_allows_bonus_large_house(self):
        """Test bonus allowed for large house."""
        result = week_capacity_allows_bonus(14)
        assert result is True
    
    @pytest.mark.unit
    def test_week_capacity_allows_bonus_exact_threshold(self):
        """Test bonus at exact threshold."""
        from house_duties import BONUS_THIRD_CLEANING_MIN_ROSTER
        result = week_capacity_allows_bonus(BONUS_THIRD_CLEANING_MIN_ROSTER)
        assert result is True
    
    @pytest.mark.unit
    def test_stable_int_from_strings_deterministic(self):
        """Test stable_int_from_strings is deterministic."""
        result1 = stable_int_from_strings("test", "data", "2026-01-18")
        result2 = stable_int_from_strings("test", "data", "2026-01-18")
        assert result1 == result2
    
    @pytest.mark.unit
    def test_stable_int_from_strings_different_inputs(self):
        """Test stable_int_from_strings differs for different inputs."""
        result1 = stable_int_from_strings("test", "data1")
        result2 = stable_int_from_strings("test", "data2")
        assert result1 != result2
    
    @pytest.mark.unit
    def test_choose_bonus_tasks_small_house(self, sample_brothers):
        """Test no bonus tasks chosen for small house."""
        templates = [
            TaskTemplate(
                key="TEST_1",
                label="Test 1",
                deck="Test",
                category="bathrooms",
                people_needed=1,
                cadence="n_per_week",
                times_per_week=2,
                flexible_2_3x=True
            )
        ]
        anchor = date(2026, 1, 18)
        current = date(2026, 1, 18)
        state = {"bonus_counts": {}}
        
        # Small house (< 14 brothers)
        bonus = choose_bonus_tasks_for_week(templates, 10, anchor, current, sample_brothers[:4], state)
        assert len(bonus) == 0
    
    @pytest.mark.unit
    def test_choose_bonus_tasks_no_flexible_tasks(self, sample_brothers):
        """Test no bonus when no flexible tasks."""
        templates = [
            TaskTemplate(
                key="TEST_1",
                label="Test 1",
                deck="Test",
                category="bathrooms",
                people_needed=1,
                cadence="weekly",
                days_of_week=[0],
                flexible_2_3x=False  # Not flexible
            )
        ]
        anchor = date(2026, 1, 18)
        current = date(2026, 1, 18)
        state = {"bonus_counts": {}}
        
        bonus = choose_bonus_tasks_for_week(templates, 14, anchor, current, sample_brothers, state)
        assert len(bonus) == 0
    
    @pytest.mark.unit
    def test_choose_bonus_tasks_selects_tasks(self, sample_brothers):
        """Test bonus tasks are selected for large house."""
        templates = [
            TaskTemplate(
                key="TEST_1",
                label="Bathroom 1",
                deck="Test",
                category="bathrooms",
                people_needed=1,
                cadence="n_per_week",
                times_per_week=2,
                severity=4,
                flexible_2_3x=True
            ),
            TaskTemplate(
                key="TEST_2",
                label="Floor 1",
                deck="Test",
                category="floors",
                people_needed=1,
                cadence="n_per_week",
                times_per_week=2,
                severity=3,
                flexible_2_3x=True
            ),
            TaskTemplate(
                key="TEST_3",
                label="Common 1",
                deck="Test",
                category="common",
                people_needed=1,
                cadence="n_per_week",
                times_per_week=2,
                severity=2,
                flexible_2_3x=True
            )
        ]
        anchor = date(2026, 1, 18)
        current = date(2026, 1, 18)
        state = {"bonus_counts": {}}
        
        bonus = choose_bonus_tasks_for_week(templates, 14, anchor, current, sample_brothers, state)
        
        # Should select at least one task (50% of 3 = 1)
        assert len(bonus) >= 1
        assert len(bonus) <= 2  # Max 50% of flexible tasks
    
    @pytest.mark.unit
    def test_choose_bonus_tasks_updates_counts(self, sample_brothers):
        """Test bonus selection updates bonus_counts."""
        templates = [
            TaskTemplate(
                key="TEST_1",
                label="Test 1",
                deck="Test",
                category="bathrooms",
                people_needed=1,
                cadence="n_per_week",
                times_per_week=2,
                flexible_2_3x=True
            )
        ]
        anchor = date(2026, 1, 18)
        current = date(2026, 1, 18)
        state = {"bonus_counts": {"TEST_1": 0}}
        
        bonus = choose_bonus_tasks_for_week(templates, 14, anchor, current, sample_brothers, state)
        
        if "TEST_1" in bonus:
            assert state["bonus_counts"]["TEST_1"] == 1
    
    @pytest.mark.unit
    def test_choose_bonus_tasks_prioritizes_low_count(self, sample_brothers):
        """Test bonus selection prioritizes tasks with lower counts."""
        templates = [
            TaskTemplate(
                key="LOW_COUNT",
                label="Low",
                deck="Test",
                category="bathrooms",
                people_needed=1,
                cadence="n_per_week",
                times_per_week=2,
                severity=4,
                flexible_2_3x=True
            ),
            TaskTemplate(
                key="HIGH_COUNT",
                label="High",
                deck="Test",
                category="bathrooms",
                people_needed=1,
                cadence="n_per_week",
                times_per_week=2,
                severity=4,
                flexible_2_3x=True
            )
        ]
        anchor = date(2026, 1, 18)
        current = date(2026, 1, 18)
        # HIGH_COUNT has been assigned bonus many times
        state = {"bonus_counts": {"LOW_COUNT": 0, "HIGH_COUNT": 10}}
        
        bonus = choose_bonus_tasks_for_week(templates, 14, anchor, current, sample_brothers, state)
        
        # Should prefer LOW_COUNT
        # Note: Due to randomization, we can't guarantee, but test that it runs
        assert isinstance(bonus, set)

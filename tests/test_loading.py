"""Tests for roster and constraints loading."""
import pytest
import sys
import os

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from house_duties_legacy import (
    load_brothers,
    load_constraints,
    load_categories,
    is_banned,
    preference_bonus
)


class TestRosterLoading:
    """Test roster file loading."""
    
    @pytest.mark.integration
    def test_load_brothers_valid_file(self, sample_roster_file):
        """Test loading brothers from valid file."""
        brothers = load_brothers(str(sample_roster_file))
        assert len(brothers) == 6
        assert "Alex" in brothers
        assert "Frank" in brothers
    
    @pytest.mark.integration
    def test_load_brothers_with_comments(self, temp_dir):
        """Test loading brothers file with comments."""
        roster_file = temp_dir / "brothers.txt"
        content = "Alex\n# This is a comment\nBob\n\n# Another comment\nCharlie"
        roster_file.write_text(content)
        
        brothers = load_brothers(str(roster_file))
        assert len(brothers) == 3
        assert brothers == ["Alex", "Bob", "Charlie"]
    
    @pytest.mark.integration
    def test_load_brothers_removes_duplicates(self, temp_dir):
        """Test loading brothers removes duplicates."""
        roster_file = temp_dir / "brothers.txt"
        content = "Alex\nBob\nAlex\nCharlie\nBob"
        roster_file.write_text(content)
        
        brothers = load_brothers(str(roster_file))
        assert len(brothers) == 3
        assert brothers.count("Alex") == 1
        assert brothers.count("Bob") == 1
    
    @pytest.mark.integration
    def test_load_brothers_empty_file(self, temp_dir):
        """Test loading empty brothers file raises error."""
        roster_file = temp_dir / "brothers.txt"
        roster_file.write_text("")
        
        with pytest.raises(ValueError, match="Roster file is empty"):
            load_brothers(str(roster_file))
    
    @pytest.mark.integration
    def test_load_brothers_nonexistent_file(self, temp_dir):
        """Test loading nonexistent file raises error."""
        with pytest.raises(FileNotFoundError):
            load_brothers(str(temp_dir / "nonexistent.txt"))


class TestConstraintsLoading:
    """Test constraints file loading."""
    
    @pytest.mark.integration
    def test_load_constraints_valid_file(self, sample_constraints_file):
        """Test loading constraints from valid file."""
        constraints = load_constraints(str(sample_constraints_file))
        assert constraints["max_per_brother_per_week"] == 5
        assert "Alex" in constraints["brother_category_bans"]
    
    @pytest.mark.integration
    def test_load_constraints_nonexistent_file(self, temp_dir):
        """Test loading nonexistent constraints returns defaults."""
        constraints = load_constraints(str(temp_dir / "nonexistent.json"))
        assert "exempt_all" in constraints
        assert constraints["exempt_all"] == []
    
    @pytest.mark.integration
    def test_load_constraints_validates_numeric(self, temp_dir):
        """Test loading constraints validates numeric values."""
        constraints_file = temp_dir / "constraints.json"
        content = {"max_per_brother_per_week": -5}
        constraints_file.write_text(str(content).replace("'", '"'))
        
        constraints = load_constraints(str(constraints_file))
        # Should ignore negative value
        assert constraints["max_per_brother_per_week"] is None
    
    @pytest.mark.unit
    def test_is_banned_category(self, sample_constraints):
        """Test is_banned with category ban."""
        from house_duties_legacy import Occurrence
        from datetime import datetime
        
        occ = Occurrence(
            task_key="TEST",
            task_label="Test Task",
            deck="Test Deck",
            category="bathrooms",
            people_needed=1,
            due_dt=datetime(2026, 1, 18),
            week_index=0,
            weight=1.0
        )
        
        assert is_banned("Alex", occ, sample_constraints) is True
        assert is_banned("Bob", occ, sample_constraints) is False
    
    @pytest.mark.unit
    def test_is_banned_task(self, sample_constraints):
        """Test is_banned with task ban."""
        from house_duties_legacy import Occurrence
        from datetime import datetime
        
        occ = Occurrence(
            task_key="SD_SINKS",
            task_label="Sinks",
            deck="Second Deck",
            category="bathrooms",
            people_needed=1,
            due_dt=datetime(2026, 1, 18),
            week_index=0,
            weight=1.0
        )
        
        # Bob is banned from this specific task
        assert is_banned("Bob", occ, sample_constraints) is True
        # Charlie is not banned (Alex is banned from bathrooms category, so skip him)
        assert is_banned("Charlie", occ, sample_constraints) is False
    
    @pytest.mark.unit
    def test_preference_bonus_preferred(self, sample_constraints):
        """Test preference_bonus for preferred category."""
        bonus = preference_bonus("Charlie", "floors", sample_constraints)
        assert bonus == -0.35
    
    @pytest.mark.unit
    def test_preference_bonus_not_preferred(self, sample_constraints):
        """Test preference_bonus for non-preferred category."""
        bonus = preference_bonus("Charlie", "bathrooms", sample_constraints)
        assert bonus == 0.0


class TestCategoriesLoading:
    """Test categories file loading."""
    
    @pytest.mark.integration
    def test_load_categories_valid_file(self, temp_dir):
        """Test loading categories from valid file."""
        categories_file = temp_dir / "categories.json"
        content = {"actives": ["Alex", "Bob"], "junior_actives": ["Charlie"]}
        categories_file.write_text(str(content).replace("'", '"'))
        
        categories = load_categories(str(categories_file))
        assert len(categories["actives"]) == 2
        assert "Alex" in categories["actives"]
    
    @pytest.mark.integration
    def test_load_categories_nonexistent_file(self, temp_dir):
        """Test loading nonexistent categories returns defaults."""
        categories = load_categories(str(temp_dir / "nonexistent.json"))
        assert "actives" in categories
        assert categories["actives"] == []

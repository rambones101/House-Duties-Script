"""Tests for state management functions."""
import pytest
import json
import sys
import os

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from house_duties.state import (
    load_state,
    save_state,
    get_anchor_sunday
)
from datetime import date


class TestStateManagement:
    """Test state persistence functions."""
    
    @pytest.mark.integration
    def test_load_state_nonexistent_file(self, temp_dir):
        """Test loading state when file doesn't exist."""
        state_file = temp_dir / "nonexistent.json"
        state = load_state(str(state_file))
        assert state == {}
    
    @pytest.mark.integration
    def test_load_state_valid_file(self, sample_state_file):
        """Test loading state from valid file."""
        state = load_state(str(sample_state_file))
        assert "anchor_sunday" in state
        assert state["anchor_sunday"] == "2026-01-18"
        assert "bonus_counts" in state
    
    @pytest.mark.integration
    def test_load_state_corrupted_json(self, temp_dir):
        """Test loading state from corrupted JSON file."""
        state_file = temp_dir / "corrupted.json"
        state_file.write_text("{invalid json content")
        
        state = load_state(str(state_file))
        assert state == {}
        
        # Check that backup was created
        backup_file = temp_dir / "corrupted.json.corrupt.bak"
        assert backup_file.exists()
    
    @pytest.mark.integration
    def test_save_state_creates_file(self, temp_dir):
        """Test saving state creates file."""
        state_file = temp_dir / "new_state.json"
        state = {"anchor_sunday": "2026-01-18", "bonus_counts": {}}
        
        save_state(str(state_file), state)
        
        assert state_file.exists()
        loaded = json.loads(state_file.read_text())
        assert loaded == state
    
    @pytest.mark.integration
    def test_save_state_creates_backup(self, sample_state_file):
        """Test saving state creates backup of existing file."""
        original_state = load_state(str(sample_state_file))
        new_state = {"anchor_sunday": "2026-01-25", "bonus_counts": {"new": 1}}
        
        save_state(str(sample_state_file), new_state)
        
        backup_file = sample_state_file.parent / (sample_state_file.name + ".bak")
        assert backup_file.exists()
        
        # Verify backup contains original state
        backup_state = json.loads(backup_file.read_text())
        assert backup_state["anchor_sunday"] == original_state["anchor_sunday"]
    
    @pytest.mark.integration
    def test_save_state_invalid_type(self, temp_dir):
        """Test saving state with invalid type raises error."""
        state_file = temp_dir / "test.json"
        
        with pytest.raises(ValueError, match="State must be a dictionary"):
            save_state(str(state_file), "not a dict")
    
    @pytest.mark.unit
    def test_get_anchor_sunday_existing(self):
        """Test get_anchor_sunday with existing anchor."""
        state = {"anchor_sunday": "2026-01-18"}
        current = date(2026, 1, 25)
        
        anchor = get_anchor_sunday(state, current)
        assert anchor == date(2026, 1, 18)
    
    @pytest.mark.unit
    def test_get_anchor_sunday_new(self):
        """Test get_anchor_sunday creates new anchor."""
        state = {}
        current = date(2026, 1, 25)
        
        anchor = get_anchor_sunday(state, current)
        assert anchor == current
        assert state["anchor_sunday"] == "2026-01-25"

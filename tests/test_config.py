"""
Tests for configuration loading and validation.
"""

import pytest
import os
import tempfile
import copy
from pathlib import Path

try:
    from house_duties.config import (
        load_config,
        get_due_times,
        get_deck_order,
        get_bonus_priority,
        get_severity_overrides,
        get_config_value,
        DEFAULT_CONFIG,
        _validate_config
    )
    CONFIG_MODULE_AVAILABLE = True
except ImportError:
    CONFIG_MODULE_AVAILABLE = False

try:
    import yaml
    YAML_AVAILABLE = True
except ImportError:
    YAML_AVAILABLE = False


@pytest.mark.skipif(not CONFIG_MODULE_AVAILABLE, reason="Config module not available")
class TestConfigLoading:
    """Test configuration loading functionality."""
    
    @pytest.mark.unit
    def test_load_default_config_when_file_missing(self):
        """Test that default config is returned when config file doesn't exist."""
        config = load_config("nonexistent_config.yaml")
        assert config is not None
        assert "files" in config
        assert "scheduling" in config
        assert config["files"]["roster"] == "brothers.txt"
    
    @pytest.mark.unit
    @pytest.mark.skipif(not YAML_AVAILABLE, reason="PyYAML not installed")
    def test_load_valid_config_file(self, tmp_path):
        """Test loading a valid YAML config file."""
        config_file = tmp_path / "test_config.yaml"
        config_content = """
files:
  roster: "custom_roster.txt"
  
scheduling:
  weeks_to_generate: 2
  bonus_third_cleaning_min_roster: 16
"""
        config_file.write_text(config_content)
        
        config = load_config(str(config_file))
        assert config["files"]["roster"] == "custom_roster.txt"
        assert config["scheduling"]["weeks_to_generate"] == 2
        assert config["scheduling"]["bonus_third_cleaning_min_roster"] == 16
        # Should still have defaults merged
        assert config["files"]["state"] == "chore_state.json"
    
    @pytest.mark.unit
    @pytest.mark.skipif(not YAML_AVAILABLE, reason="PyYAML not installed")
    def test_load_partial_config_merges_with_defaults(self, tmp_path):
        """Test that partial config is merged with defaults."""
        config_file = tmp_path / "partial_config.yaml"
        config_content = """
scheduling:
  weeks_to_generate: 3
"""
        config_file.write_text(config_content)
        
        config = load_config(str(config_file))
        assert config["scheduling"]["weeks_to_generate"] == 3
        # Should have defaults
        assert "files" in config
        assert config["files"]["roster"] == "brothers.txt"
        assert config["scheduling"]["random_seed"] == 42
    
    @pytest.mark.unit
    @pytest.mark.skipif(not YAML_AVAILABLE, reason="PyYAML not installed")
    def test_validate_config_valid(self):
        """Test config validation with valid config."""
        valid_config = copy.deepcopy(DEFAULT_CONFIG)
        # Should not raise
        _validate_config(valid_config)
    
    @pytest.mark.unit
    @pytest.mark.skipif(not YAML_AVAILABLE, reason="PyYAML not installed")
    def test_validate_config_invalid_weeks(self):
        """Test config validation fails with invalid weeks_to_generate."""
        invalid_config = copy.deepcopy(DEFAULT_CONFIG)
        invalid_config["scheduling"]["weeks_to_generate"] = 0
        with pytest.raises(ValueError, match="weeks_to_generate must be >= 1"):
            _validate_config(invalid_config)
    
    @pytest.mark.unit
    @pytest.mark.skipif(not YAML_AVAILABLE, reason="PyYAML not installed")
    def test_validate_config_invalid_roster_size(self):
        """Test config validation fails with invalid roster size."""
        invalid_config = copy.deepcopy(DEFAULT_CONFIG)
        invalid_config["scheduling"]["bonus_third_cleaning_min_roster"] = 0
        with pytest.raises(ValueError, match="bonus_third_cleaning_min_roster must be >= 1"):
            _validate_config(invalid_config)
    
    @pytest.mark.unit
    @pytest.mark.skipif(not YAML_AVAILABLE, reason="PyYAML not installed")
    def test_validate_config_invalid_max_share(self):
        """Test config validation fails with out-of-range max_task_share."""
        invalid_config = copy.deepcopy(DEFAULT_CONFIG)
        invalid_config["scheduling"]["bonus_third_cleaning_max_task_share"] = 1.5
        with pytest.raises(ValueError, match="must be between 0.0 and 1.0"):
            _validate_config(invalid_config)
    
    @pytest.mark.unit
    @pytest.mark.skipif(not YAML_AVAILABLE, reason="PyYAML not installed")
    def test_validate_config_invalid_cadence(self):
        """Test config validation fails with invalid cadence."""
        invalid_config = copy.deepcopy(DEFAULT_CONFIG)
        invalid_config["cadence"]["brasso_second_deck"] = "monthly"
        with pytest.raises(ValueError, match="Invalid cadence"):
            _validate_config(invalid_config)
    
    @pytest.mark.unit
    @pytest.mark.skipif(not YAML_AVAILABLE, reason="PyYAML not installed")
    def test_validate_config_invalid_time_format(self):
        """Test config validation fails with invalid time format."""
        invalid_config = copy.deepcopy(DEFAULT_CONFIG)
        invalid_config["due_times"]["k&m"] = "25:00"
        with pytest.raises(ValueError, match="Invalid time format.*Use HH:MM"):
            _validate_config(invalid_config)
    
    @pytest.mark.unit
    @pytest.mark.skipif(not YAML_AVAILABLE, reason="PyYAML not installed")
    def test_validate_config_invalid_day(self):
        """Test config validation fails with invalid day of week."""
        invalid_config = copy.deepcopy(DEFAULT_CONFIG)
        invalid_config["bonus"]["base_2x_days"] = [2, 7]
        with pytest.raises(ValueError, match="base_2x_days must contain values 0-6"):
            _validate_config(invalid_config)


@pytest.mark.skipif(not CONFIG_MODULE_AVAILABLE, reason="Config module not available")
class TestConfigAccessors:
    """Test configuration accessor functions."""
    
    @pytest.mark.unit
    def test_get_due_times(self):
        """Test get_due_times returns time objects."""
        config = DEFAULT_CONFIG
        due_times = get_due_times(config)
        assert "k&m" in due_times
        # Check it's a time object
        from datetime import time
        assert isinstance(due_times["k&m"], time)
        assert due_times["k&m"].hour == 23
        assert due_times["k&m"].minute == 59
    
    @pytest.mark.unit
    def test_get_deck_order(self):
        """Test get_deck_order returns list of decks."""
        config = DEFAULT_CONFIG
        deck_order = get_deck_order(config)
        assert isinstance(deck_order, list)
        assert "Zero Deck" in deck_order
        assert "First Deck" in deck_order
        assert len(deck_order) == 5
    
    @pytest.mark.unit
    def test_get_bonus_priority(self):
        """Test get_bonus_priority returns priority mapping."""
        config = DEFAULT_CONFIG
        priority = get_bonus_priority(config)
        assert isinstance(priority, dict)
        assert priority["bathrooms"] == 3
        assert priority["floors"] == 2
        assert priority["common"] == 1
    
    @pytest.mark.unit
    def test_get_severity_overrides(self):
        """Test get_severity_overrides returns overrides mapping."""
        config = DEFAULT_CONFIG
        overrides = get_severity_overrides(config)
        assert isinstance(overrides, dict)
    
    @pytest.mark.unit
    def test_get_config_value_nested(self):
        """Test get_config_value with nested keys."""
        config = DEFAULT_CONFIG
        value = get_config_value(config, "scheduling", "weeks_to_generate")
        assert value == 1
    
    @pytest.mark.unit
    def test_get_config_value_with_default(self):
        """Test get_config_value returns default for missing key."""
        config = DEFAULT_CONFIG
        value = get_config_value(config, "nonexistent", "key", default=99)
        assert value == 99
    
    @pytest.mark.unit
    def test_get_config_value_top_level(self):
        """Test get_config_value with top-level key."""
        config = DEFAULT_CONFIG
        value = get_config_value(config, "files")
        assert isinstance(value, dict)
        assert "roster" in value


@pytest.mark.skipif(not CONFIG_MODULE_AVAILABLE or not YAML_AVAILABLE, reason="Config module or PyYAML not available")
class TestConfigIntegration:
    """Integration tests for config system."""
    
    @pytest.mark.integration
    def test_full_config_workflow(self, tmp_path):
        """Test complete workflow of loading and using config."""
        config_file = tmp_path / "workflow_config.yaml"
        config_content = """
files:
  roster: "test_bros.txt"
  state: "test_state.json"

scheduling:
  weeks_to_generate: 4
  bonus_third_cleaning_min_roster: 20
  random_seed: 123

fairness:
  repeat_task_penalty: 2.0
  preference_bonus: -0.50

cadence:
  brasso_second_deck: "weekly"
"""
        config_file.write_text(config_content)
        
        config = load_config(str(config_file))
        
        # Verify all values loaded correctly
        assert config["files"]["roster"] == "test_bros.txt"
        assert config["files"]["state"] == "test_state.json"
        assert config["scheduling"]["weeks_to_generate"] == 4
        assert config["scheduling"]["bonus_third_cleaning_min_roster"] == 20
        assert config["scheduling"]["random_seed"] == 123
        assert config["fairness"]["repeat_task_penalty"] == 2.0
        assert config["fairness"]["preference_bonus"] == -0.50
        assert config["cadence"]["brasso_second_deck"] == "weekly"
        
        # Verify defaults still present
        assert config["files"]["constraints"] == "constraints.json"
        assert config["bonus"]["base_2x_days"] == [2, 4]

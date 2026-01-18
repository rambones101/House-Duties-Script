"""
Configuration loading and validation for House Duties Scheduler.
Supports YAML config files with fallback to defaults.
"""

import os
import logging
from datetime import time
from typing import Dict, List, Any, Optional
from pathlib import Path

logger = logging.getLogger(__name__)

# Default configuration (used if config file not found)
DEFAULT_CONFIG = {
    "files": {
        "roster": "brothers.txt",
        "constraints": "constraints.json",
        "categories": "brother_categories.json",
        "state": "chore_state.json",
    },
    "scheduling": {
        "start_sunday": "",
        "weeks_to_generate": 1,
        "bonus_third_cleaning_min_roster": 14,
        "bonus_third_cleaning_max_task_share": 0.50,
        "random_seed": 42,
    },
    "cadence": {
        "brasso_second_deck": "biweekly",
        "brasso_third_deck": "biweekly",
    },
    "due_times": {
        "k&m": "23:59",
        "bathrooms": "23:59",
        "floors": "23:59",
        "laundry": "23:59",
        "common": "23:59",
        "other": "23:59",
    },
    "bonus": {
        "base_2x_days": [2, 4],
        "bonus_3rd_day": 5,
        "priority": {
            "bathrooms": 3,
            "floors": 2,
            "common": 1,
            "laundry": 0,
            "k&m": 0,
            "other": 0,
        },
    },
    "fairness": {
        "repeat_task_penalty": 1.50,
        "recent_week_penalty": 0.60,
        "same_day_stack_penalty": 0.75,
        "preference_bonus": -0.35,
    },
    "display": {
        "deck_order": ["Zero Deck", "First Deck", "Second Deck", "Third Deck", "Other"],
    },
    "severity_overrides": {},
}


def load_config(config_path: Optional[str] = None) -> Dict[str, Any]:
    """
    Load configuration from YAML file.
    
    Args:
        config_path: Path to config.yaml. If None, looks in current directory.
        
    Returns:
        Configuration dictionary with all settings.
    """
    if config_path is None:
        config_path = "config.yaml"
    
    # If config file doesn't exist, use defaults
    if not os.path.exists(config_path):
        logger.info(f"Config file '{config_path}' not found. Using default configuration.")
        return DEFAULT_CONFIG.copy()
    
    # Try to load YAML
    try:
        import yaml
    except ImportError:
        logger.warning("PyYAML not installed. Using default configuration.")
        logger.info("Install with: pip install pyyaml")
        return DEFAULT_CONFIG.copy()
    
    # Load and parse YAML
    try:
        with open(config_path, "r", encoding="utf-8") as f:
            config = yaml.safe_load(f)
            if config is None:
                config = {}
            logger.info(f"Loaded configuration from '{config_path}'")
            
            # Merge with defaults (fill in missing values)
            merged_config = _merge_with_defaults(config, DEFAULT_CONFIG)
            
            # Validate configuration
            _validate_config(merged_config)
            
            return merged_config
    except yaml.YAMLError as e:
        logger.error(f"Invalid YAML in config file '{config_path}': {e}")
        logger.warning("Using default configuration")
        return DEFAULT_CONFIG.copy()
    except Exception as e:
        logger.error(f"Error reading config file '{config_path}': {e}")
        raise


def _merge_with_defaults(config: Dict[str, Any], defaults: Dict[str, Any]) -> Dict[str, Any]:
    """
    Recursively merge config with defaults.
    Config values override defaults, but missing keys are filled from defaults.
    """
    merged = defaults.copy()
    
    for key, value in config.items():
        if key in merged and isinstance(merged[key], dict) and isinstance(value, dict):
            merged[key] = _merge_with_defaults(value, merged[key])
        else:
            merged[key] = value
    
    return merged


def _validate_config(config: Dict[str, Any]) -> None:
    """
    Validate configuration values.
    Raises ValueError if configuration is invalid.
    """
    # Validate scheduling parameters
    sched = config.get("scheduling", {})
    
    if sched.get("weeks_to_generate", 1) < 1:
        raise ValueError("weeks_to_generate must be >= 1")
    
    if sched.get("bonus_third_cleaning_min_roster", 14) < 1:
        raise ValueError("bonus_third_cleaning_min_roster must be >= 1")
    
    max_share = sched.get("bonus_third_cleaning_max_task_share", 0.5)
    if not (0.0 <= max_share <= 1.0):
        raise ValueError("bonus_third_cleaning_max_task_share must be between 0.0 and 1.0")
    
    # Validate cadence values
    cadence = config.get("cadence", {})
    valid_cadences = ["weekly", "biweekly"]
    for key, value in cadence.items():
        if value not in valid_cadences:
            raise ValueError(f"Invalid cadence '{value}' for {key}. Must be 'weekly' or 'biweekly'")
    
    # Validate due times format
    due_times = config.get("due_times", {})
    for category, time_str in due_times.items():
        try:
            _parse_time(time_str)
        except ValueError:
            raise ValueError(f"Invalid time format '{time_str}' for category '{category}'. Use HH:MM")
    
    # Validate bonus days (0-6)
    bonus = config.get("bonus", {})
    base_days = bonus.get("base_2x_days", [])
    if not all(0 <= d <= 6 for d in base_days):
        raise ValueError("base_2x_days must contain values 0-6 (Sun-Sat)")
    
    bonus_day = bonus.get("bonus_3rd_day", 5)
    if not (0 <= bonus_day <= 6):
        raise ValueError("bonus_3rd_day must be 0-6 (Sun-Sat)")
    
    # Validate fairness penalties (should be positive)
    fairness = config.get("fairness", {})
    if fairness.get("repeat_task_penalty", 1.5) < 0:
        logger.warning("repeat_task_penalty is negative - this may cause unexpected behavior")
    if fairness.get("same_day_stack_penalty", 0.75) < 0:
        logger.warning("same_day_stack_penalty is negative - this may cause unexpected behavior")
    if fairness.get("recent_week_penalty", 0.60) < 0:
        logger.warning("recent_week_penalty is negative - this may cause unexpected behavior")
    
    logger.debug("Configuration validation passed")


def _parse_time(time_str: str) -> time:
    """Parse time string in HH:MM format."""
    parts = time_str.split(":")
    if len(parts) != 2:
        raise ValueError(f"Time must be in HH:MM format, got '{time_str}'")
    hour = int(parts[0])
    minute = int(parts[1])
    if not (0 <= hour <= 23):
        raise ValueError(f"Hour must be 0-23, got {hour}")
    if not (0 <= minute <= 59):
        raise ValueError(f"Minute must be 0-59, got {minute}")
    return time(hour, minute)


def get_due_times(config: Dict[str, Any]) -> Dict[str, time]:
    """Convert due_times from config (strings) to time objects."""
    due_times_str = config.get("due_times", {})
    return {
        category: _parse_time(time_str)
        for category, time_str in due_times_str.items()
    }


def get_deck_order(config: Dict[str, Any]) -> List[str]:
    """Get deck ordering from config."""
    return config.get("display", {}).get("deck_order", DEFAULT_CONFIG["display"]["deck_order"])


def get_bonus_priority(config: Dict[str, Any]) -> Dict[str, int]:
    """Get bonus priority mapping from config."""
    return config.get("bonus", {}).get("priority", DEFAULT_CONFIG["bonus"]["priority"])


def get_severity_overrides(config: Dict[str, Any]) -> Dict[str, int]:
    """Get severity overrides from config."""
    return config.get("severity_overrides", {})


# Convenience accessors for common config values
def get_config_value(config: Dict[str, Any], *keys: str, default: Any = None) -> Any:
    """
    Get nested config value using keys path.
    
    Example:
        get_config_value(config, "scheduling", "weeks_to_generate")
    """
    value = config
    for key in keys:
        if isinstance(value, dict) and key in value:
            value = value[key]
        else:
            return default
    return value

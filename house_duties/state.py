"""State persistence and management functions."""
import json
import logging
import os
from datetime import date
from typing import Dict, List, Any

logger = logging.getLogger(__name__)


def load_state(filepath: str) -> Dict[str, Any]:
    """Load persistent state from JSON file with error handling."""
    if not os.path.exists(filepath):
        logger.info(f"State file '{filepath}' not found. Starting with empty state.")
        return {}
    try:
        with open(filepath, "r", encoding="utf-8") as f:
            state = json.load(f)
            logger.info(f"Loaded state from '{filepath}'")
            return state
    except json.JSONDecodeError as e:
        logger.error(f"Invalid JSON in state file '{filepath}': {e}")
        logger.warning("Starting with empty state. Previous state will be backed up.")
        # Backup corrupted file
        backup_path = f"{filepath}.corrupt.bak"
        try:
            os.rename(filepath, backup_path)
            logger.info(f"Corrupted state backed up to '{backup_path}'")
        except OSError:
            pass
        return {}
    except Exception as e:
        logger.error(f"Error reading state file '{filepath}': {e}")
        raise


def save_state(filepath: str, state: Dict[str, Any]) -> None:
    """Save persistent state to JSON file with error handling and backup."""
    try:
        # Validate state before saving
        if not isinstance(state, dict):
            raise ValueError(f"State must be a dictionary, got {type(state)}")
        
        # Create backup of existing state
        if os.path.exists(filepath):
            backup_path = f"{filepath}.bak"
            try:
                with open(filepath, "r", encoding="utf-8") as f:
                    backup_state = json.load(f)
                with open(backup_path, "w", encoding="utf-8") as f:
                    json.dump(backup_state, f, indent=2)
                logger.debug(f"Created backup at '{backup_path}'")
            except Exception as e:
                logger.warning(f"Could not create backup: {e}")
        
        # Write new state
        with open(filepath, "w", encoding="utf-8") as f:
            json.dump(state, f, indent=2)
        logger.info(f"Saved state to '{filepath}'")
    except Exception as e:
        logger.error(f"Error saving state to '{filepath}': {e}")
        raise


def get_anchor_sunday(state: Dict[str, Any], current_sunday: date) -> date:
    """Get or initialize anchor Sunday for biweekly parity tracking."""
    anchor = state.get("anchor_sunday")
    if anchor:
        return date.fromisoformat(anchor)
    state["anchor_sunday"] = current_sunday.isoformat()
    return current_sunday


def load_brothers(filepath: str) -> List[str]:
    """Load brother roster from file with validation and error handling."""
    if not os.path.exists(filepath):
        logger.error(f"Roster file '{filepath}' not found")
        raise FileNotFoundError(
            f"Missing roster file: {filepath}\n"
            "Create brothers.txt with one brother name per line."
        )
    
    try:
        brothers: List[str] = []
        with open(filepath, "r", encoding="utf-8") as f:
            for line_num, line in enumerate(f, 1):
                name = line.strip()
                if name and not name.startswith("#"):
                    # Validate name
                    if len(name) > 100:
                        logger.warning(f"Line {line_num}: Name too long (truncating): {name[:50]}...")
                        name = name[:100]
                    if not name.replace(' ', '').replace('-', '').replace("'", '').isalnum():
                        logger.warning(f"Line {line_num}: Name contains unusual characters: {name}")
                    brothers.append(name)
        
        if not brothers:
            logger.error(f"Roster file '{filepath}' is empty or contains only comments")
            raise ValueError("Roster file is empty. Add at least one brother name.")
        
        # Remove duplicates while preserving order
        seen = set()
        out = []
        for b in brothers:
            if b not in seen:
                out.append(b)
                seen.add(b)
            else:
                logger.warning(f"Duplicate brother name removed: {b}")
        
        logger.info(f"Loaded {len(out)} brothers from '{filepath}'")
        return out
    
    except UnicodeDecodeError as e:
        logger.error(f"File encoding error in '{filepath}': {e}")
        raise ValueError(f"Could not read '{filepath}'. Ensure it's saved as UTF-8 text.") from e
    except Exception as e:
        logger.error(f"Error loading brothers from '{filepath}': {e}")
        raise


def load_categories(filepath: str) -> Dict[str, List[str]]:
    """Load brother categories for pairing rules with error handling."""
    if not os.path.exists(filepath):
        logger.debug(f"Categories file '{filepath}' not found. Using empty categories.")
        return {"actives": [], "junior_actives": []}
    
    try:
        with open(filepath, "r", encoding="utf-8") as f:
            data = json.load(f)
        
        # Validate structure
        if not isinstance(data, dict):
            logger.warning(f"Invalid categories file format. Expected dict, got {type(data)}")
            return {"actives": [], "junior_actives": []}
        
        # Ensure all values are lists
        for key, value in data.items():
            if not isinstance(value, list):
                logger.warning(f"Category '{key}' is not a list, converting")
                data[key] = list(value) if hasattr(value, '__iter__') else []
        
        logger.info(f"Loaded categories from '{filepath}'")
        return data
    
    except json.JSONDecodeError as e:
        logger.error(f"Invalid JSON in categories file '{filepath}': {e}")
        return {"actives": [], "junior_actives": []}
    except Exception as e:
        logger.error(f"Error loading categories from '{filepath}': {e}")
        return {"actives": [], "junior_actives": []}


DEFAULT_CONSTRAINTS = {
    "exempt_all": [],
    "on_call_only": [],
    "max_per_brother_per_week": None,
    "max_per_brother_per_day": None,
    "min_per_brother_per_week": None,
    "brother_category_bans": {},
    "brother_task_bans": {},
    "brother_preferred_categories": {},
    "brother_unavailable_dates": {},
}


def load_constraints(filepath: str) -> Dict[str, Any]:
    """Load constraints file with validation and error handling."""
    if not os.path.exists(filepath):
        logger.debug(f"Constraints file '{filepath}' not found. Using defaults.")
        return DEFAULT_CONSTRAINTS.copy()
    
    try:
        with open(filepath, "r", encoding="utf-8") as f:
            data = json.load(f)
        
        if not isinstance(data, dict):
            logger.warning(f"Invalid constraints format. Expected dict, got {type(data)}")
            return DEFAULT_CONSTRAINTS.copy()
        
        merged = DEFAULT_CONSTRAINTS.copy()
        merged.update(data or {})
        
        # Validate numeric constraints
        for key in ['max_per_brother_per_week', 'max_per_brother_per_day', 'min_per_brother_per_week']:
            if key in merged and merged[key] is not None:
                try:
                    merged[key] = int(merged[key])
                    if merged[key] < 0:
                        logger.warning(f"Constraint '{key}' is negative, ignoring")
                        merged[key] = None
                except (ValueError, TypeError):
                    logger.warning(f"Invalid value for '{key}', ignoring")
                    merged[key] = None
        
        logger.info(f"Loaded constraints from '{filepath}'")
        return merged
    
    except json.JSONDecodeError as e:
        logger.error(f"Invalid JSON in constraints file '{filepath}': {e}")
        logger.warning("Using default constraints")
        return DEFAULT_CONSTRAINTS.copy()
    except Exception as e:
        logger.error(f"Error loading constraints from '{filepath}': {e}")
        return DEFAULT_CONSTRAINTS.copy()

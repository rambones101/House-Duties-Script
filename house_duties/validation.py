"""
Data validation module for House Duties Scheduler.
Validates brothers, task templates, and constraints.
"""

import logging
from typing import List, Dict, Any, Set, Optional
from datetime import time

logger = logging.getLogger(__name__)


class ValidationError(ValueError):
    """Custom exception for validation errors."""
    pass


def validate_brothers(brothers: List[str], allow_empty: bool = False) -> List[str]:
    """
    Validate brother roster.
    
    Args:
        brothers: List of brother names
        allow_empty: Whether to allow empty roster (default False)
        
    Returns:
        Validated and cleaned list of brothers
        
    Raises:
        ValidationError: If validation fails
    """
    if not brothers and not allow_empty:
        raise ValidationError("Brother roster cannot be empty")
    
    # Check for None or non-string entries
    for i, brother in enumerate(brothers):
        if brother is None:
            raise ValidationError(f"Brother at index {i} is None")
        if not isinstance(brother, str):
            raise ValidationError(f"Brother at index {i} is not a string: {type(brother).__name__}")
    
    # Remove whitespace
    cleaned = [b.strip() for b in brothers]
    
    # Check for empty strings after stripping
    empty_indices = [i for i, b in enumerate(cleaned) if not b]
    if empty_indices:
        raise ValidationError(f"Empty brother names found at indices: {empty_indices}")
    
    # Check for duplicates (case-insensitive)
    lower_names = [b.lower() for b in cleaned]
    duplicates = set()
    seen = set()
    for name in lower_names:
        if name in seen:
            duplicates.add(name)
        seen.add(name)
    
    if duplicates:
        raise ValidationError(f"Duplicate brother names found: {', '.join(sorted(duplicates))}")
    
    # Warn about very short names
    short_names = [b for b in cleaned if len(b) < 2]
    if short_names:
        logger.warning(f"Very short brother names found: {', '.join(short_names)}")
    
    # Warn about names with special characters
    import re
    special_char_names = [b for b in cleaned if not re.match(r'^[a-zA-Z\s\-\.\']+$', b)]
    if special_char_names:
        logger.warning(f"Brother names with special characters: {', '.join(special_char_names)}")
    
    logger.info(f"Validated {len(cleaned)} brothers")
    return cleaned


def validate_task_template(template: Any, template_index: int = 0) -> None:
    """
    Validate a single task template.
    
    Args:
        template: TaskTemplate object to validate
        template_index: Index for error reporting
        
    Raises:
        ValidationError: If validation fails
    """
    # Check required attributes
    required_attrs = ['key', 'label', 'deck', 'category', 'people_needed', 'cadence']
    for attr in required_attrs:
        if not hasattr(template, attr):
            raise ValidationError(f"Template {template_index}: Missing required attribute '{attr}'")
        if getattr(template, attr) is None:
            raise ValidationError(f"Template {template_index}: Attribute '{attr}' cannot be None")
    
    # Validate key (unique identifier)
    if not isinstance(template.key, str) or not template.key.strip():
        raise ValidationError(f"Template {template_index}: 'key' must be non-empty string")
    
    # Validate label
    if not isinstance(template.label, str) or not template.label.strip():
        raise ValidationError(f"Template {template_index} ({template.key}): 'label' must be non-empty string")
    
    # Validate deck
    if not isinstance(template.deck, str) or not template.deck.strip():
        raise ValidationError(f"Template {template.key}: 'deck' must be non-empty string")
    
    # Validate category
    valid_categories = ['k&m', 'bathrooms', 'floors', 'laundry', 'common', 'other']
    if template.category not in valid_categories:
        raise ValidationError(
            f"Template {template.key}: Invalid category '{template.category}'. "
            f"Must be one of: {', '.join(valid_categories)}"
        )
    
    # Validate people_needed
    if not isinstance(template.people_needed, int):
        raise ValidationError(f"Template {template.key}: 'people_needed' must be an integer")
    if template.people_needed < 1:
        raise ValidationError(f"Template {template.key}: 'people_needed' must be >= 1")
    if template.people_needed > 10:
        logger.warning(f"Template {template.key}: Large people_needed value: {template.people_needed}")
    
    # Validate cadence
    valid_cadences = ['weekly', 'biweekly', 'n_per_week']
    if template.cadence not in valid_cadences:
        raise ValidationError(
            f"Template {template.key}: Invalid cadence '{template.cadence}'. "
            f"Must be one of: {', '.join(valid_cadences)}"
        )
    
    # Cadence-specific validation
    if template.cadence in ('weekly', 'biweekly'):
        if template.days_of_week is not None:
            if not isinstance(template.days_of_week, list):
                raise ValidationError(f"Template {template.key}: 'days_of_week' must be a list")
            for day in template.days_of_week:
                if not isinstance(day, int) or not (0 <= day <= 6):
                    raise ValidationError(
                        f"Template {template.key}: Invalid day in 'days_of_week': {day}. "
                        "Must be 0-6 (Sun-Sat)"
                    )
    
    if template.cadence == 'n_per_week':
        if template.times_per_week is None:
            raise ValidationError(f"Template {template.key}: 'times_per_week' required for n_per_week cadence")
        if not isinstance(template.times_per_week, int):
            raise ValidationError(f"Template {template.key}: 'times_per_week' must be an integer")
        if template.times_per_week < 1:
            raise ValidationError(f"Template {template.key}: 'times_per_week' must be >= 1")
        if template.times_per_week > 7:
            raise ValidationError(f"Template {template.key}: 'times_per_week' cannot exceed 7")
        
        if template.preferred_days is not None:
            if not isinstance(template.preferred_days, list):
                raise ValidationError(f"Template {template.key}: 'preferred_days' must be a list")
            for day in template.preferred_days:
                if not isinstance(day, int) or not (0 <= day <= 6):
                    raise ValidationError(
                        f"Template {template.key}: Invalid day in 'preferred_days': {day}. "
                        "Must be 0-6 (Sun-Sat)"
                    )
    
    # Validate severity
    if hasattr(template, 'severity') and template.severity is not None:
        if not isinstance(template.severity, int):
            raise ValidationError(f"Template {template.key}: 'severity' must be an integer")
        if not (1 <= template.severity <= 5):
            raise ValidationError(f"Template {template.key}: 'severity' must be 1-5")
    
    # Validate effort_multiplier
    if hasattr(template, 'effort_multiplier') and template.effort_multiplier is not None:
        if not isinstance(template.effort_multiplier, (int, float)):
            raise ValidationError(f"Template {template.key}: 'effort_multiplier' must be a number")
        if template.effort_multiplier <= 0:
            raise ValidationError(f"Template {template.key}: 'effort_multiplier' must be positive")
        if template.effort_multiplier > 5.0:
            logger.warning(f"Template {template.key}: Large effort_multiplier: {template.effort_multiplier}")
    
    # Validate flexible_2_3x
    if hasattr(template, 'flexible_2_3x') and template.flexible_2_3x is not None:
        if not isinstance(template.flexible_2_3x, bool):
            raise ValidationError(f"Template {template.key}: 'flexible_2_3x' must be boolean")


def validate_task_templates(templates: List[Any]) -> None:
    """
    Validate all task templates.
    
    Args:
        templates: List of TaskTemplate objects
        
    Raises:
        ValidationError: If validation fails
    """
    if not templates:
        raise ValidationError("No task templates provided")
    
    # Check for duplicate keys
    keys = [t.key for t in templates]
    duplicate_keys = set()
    seen_keys = set()
    for key in keys:
        if key in seen_keys:
            duplicate_keys.add(key)
        seen_keys.add(key)
    
    if duplicate_keys:
        raise ValidationError(f"Duplicate template keys found: {', '.join(sorted(duplicate_keys))}")
    
    # Validate each template
    for i, template in enumerate(templates):
        validate_task_template(template, i)
    
    logger.info(f"Validated {len(templates)} task templates")


def validate_constraints(
    constraints: Dict[str, Any],
    brothers: List[str],
    valid_categories: Optional[Set[str]] = None
) -> None:
    """
    Validate constraints configuration.
    
    Args:
        constraints: Constraints dictionary
        brothers: List of valid brother names
        valid_categories: Set of valid category names
        
    Raises:
        ValidationError: If validation fails
    """
    if valid_categories is None:
        valid_categories = {'k&m', 'bathrooms', 'floors', 'laundry', 'common', 'other'}
    
    brother_set = set(brothers)
    
    # Validate exempt_all
    if 'exempt_all' in constraints and constraints['exempt_all']:
        exempt = constraints['exempt_all']
        if not isinstance(exempt, (list, set)):
            raise ValidationError("'exempt_all' must be a list or set")
        
        invalid_brothers = [b for b in exempt if b not in brother_set]
        if invalid_brothers:
            raise ValidationError(
                f"Invalid brothers in 'exempt_all': {', '.join(invalid_brothers)}. "
                f"Not found in roster."
            )
        
        if len(exempt) == len(brothers):
            raise ValidationError("Cannot exempt all brothers - roster would be empty")
    
    # Validate on_call_only
    if 'on_call_only' in constraints and constraints['on_call_only']:
        on_call = constraints['on_call_only']
        if not isinstance(on_call, (list, set)):
            raise ValidationError("'on_call_only' must be a list or set")
        
        invalid_brothers = [b for b in on_call if b not in brother_set]
        if invalid_brothers:
            raise ValidationError(
                f"Invalid brothers in 'on_call_only': {', '.join(invalid_brothers)}. "
                f"Not found in roster."
            )
    
    # Validate max_per_brother_per_week
    if 'max_per_brother_per_week' in constraints:
        max_week = constraints['max_per_brother_per_week']
        if max_week is not None:
            if not isinstance(max_week, int):
                raise ValidationError("'max_per_brother_per_week' must be an integer")
            if max_week < 1:
                raise ValidationError("'max_per_brother_per_week' must be >= 1")
    
    # Validate max_per_brother_per_day
    if 'max_per_brother_per_day' in constraints:
        max_day = constraints['max_per_brother_per_day']
        if max_day is not None:
            if not isinstance(max_day, int):
                raise ValidationError("'max_per_brother_per_day' must be an integer")
            if max_day < 1:
                raise ValidationError("'max_per_brother_per_day' must be >= 1")
    
    # Validate brother_category_bans
    if 'brother_category_bans' in constraints:
        bans = constraints['brother_category_bans']
        if not isinstance(bans, dict):
            raise ValidationError("'brother_category_bans' must be a dictionary")
        
        for brother, categories in bans.items():
            if brother not in brother_set:
                raise ValidationError(
                    f"Invalid brother in 'brother_category_bans': {brother}. "
                    f"Not found in roster."
                )
            
            if not isinstance(categories, (list, set)):
                raise ValidationError(
                    f"Categories for brother '{brother}' in 'brother_category_bans' must be a list or set"
                )
            
            invalid_cats = [c for c in categories if c not in valid_categories]
            if invalid_cats:
                raise ValidationError(
                    f"Invalid categories for brother '{brother}' in 'brother_category_bans': "
                    f"{', '.join(invalid_cats)}. Valid categories: {', '.join(sorted(valid_categories))}"
                )
    
    # Validate brother_task_bans
    if 'brother_task_bans' in constraints:
        task_bans = constraints['brother_task_bans']
        if not isinstance(task_bans, dict):
            raise ValidationError("'brother_task_bans' must be a dictionary")
        
        for brother, tasks in task_bans.items():
            if brother not in brother_set:
                raise ValidationError(
                    f"Invalid brother in 'brother_task_bans': {brother}. "
                    f"Not found in roster."
                )
            
            if not isinstance(tasks, (list, set)):
                raise ValidationError(
                    f"Tasks for brother '{brother}' in 'brother_task_bans' must be a list or set"
                )
    
    # Validate brother_preferred_categories
    if 'brother_preferred_categories' in constraints:
        prefs = constraints['brother_preferred_categories']
        if not isinstance(prefs, dict):
            raise ValidationError("'brother_preferred_categories' must be a dictionary")
        
        for brother, categories in prefs.items():
            if brother not in brother_set:
                raise ValidationError(
                    f"Invalid brother in 'brother_preferred_categories': {brother}. "
                    f"Not found in roster."
                )
            
            if not isinstance(categories, (list, set)):
                raise ValidationError(
                    f"Categories for brother '{brother}' in 'brother_preferred_categories' must be a list or set"
                )
            
            invalid_cats = [c for c in categories if c not in valid_categories]
            if invalid_cats:
                raise ValidationError(
                    f"Invalid categories for brother '{brother}' in 'brother_preferred_categories': "
                    f"{', '.join(invalid_cats)}. Valid categories: {', '.join(sorted(valid_categories))}"
                )
    
    logger.info("Validated constraints")


def validate_categories(
    categories: Dict[str, List[str]],
    brothers: List[str]
) -> None:
    """
    Validate brother categories configuration.
    
    Args:
        categories: Categories dictionary (e.g., {'actives': [...], 'pledges': [...]})
        brothers: List of valid brother names
        
    Raises:
        ValidationError: If validation fails
    """
    brother_set = set(brothers)
    
    for category_name, category_brothers in categories.items():
        if not isinstance(category_brothers, list):
            raise ValidationError(f"Category '{category_name}' must be a list")
        
        invalid_brothers = [b for b in category_brothers if b not in brother_set]
        if invalid_brothers:
            raise ValidationError(
                f"Invalid brothers in category '{category_name}': {', '.join(invalid_brothers)}. "
                f"Not found in roster."
            )
    
    logger.info(f"Validated {len(categories)} categories")


def validate_all(
    brothers: List[str],
    templates: List[Any],
    constraints: Dict[str, Any],
    categories: Optional[Dict[str, List[str]]] = None
) -> None:
    """
    Validate all inputs together.
    
    Args:
        brothers: Brother roster
        templates: Task templates
        constraints: Constraints configuration
        categories: Optional categories configuration
        
    Raises:
        ValidationError: If any validation fails
    """
    # Validate brothers first (needed for constraint validation)
    validated_brothers = validate_brothers(brothers)
    
    # Validate templates
    validate_task_templates(templates)
    
    # Extract template keys for task ban validation
    template_keys = {t.key for t in templates}
    
    # Validate constraints
    validate_constraints(constraints, validated_brothers)
    
    # Check if task bans reference valid tasks
    if 'brother_task_bans' in constraints:
        for brother, tasks in constraints['brother_task_bans'].items():
            invalid_tasks = [t for t in tasks if t not in template_keys]
            if invalid_tasks:
                logger.warning(
                    f"Brother '{brother}' has bans for non-existent tasks: {', '.join(invalid_tasks)}"
                )
    
    # Validate categories if provided
    if categories:
        validate_categories(categories, validated_brothers)
    
    logger.info("All validations passed successfully")

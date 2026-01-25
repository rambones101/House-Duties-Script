"""Task template definitions for all house chores organized by deck."""
from typing import List
from .models import TaskTemplate


# Default day assignments for consistency
BASE_2X_DAYS_DEFAULT = [2, 4]  # Tuesday, Thursday
BONUS_3RD_DAY_DEFAULT = []     # Friday


def default_severity_for(label: str, category: str) -> int:
    """Determine default severity (1-5) based on task characteristics."""
    label_lower = label.lower()
    
    # High-severity tasks (4-5)
    if any(word in label_lower for word in ["deep clean", "brasso", "blue", "mop"]):
        return 5
    if any(word in label_lower for word in ["toilets", "showers"]):
        return 4
    
    # Low-severity tasks (1-2)
    if any(word in label_lower for word in ["trash", "sweep", "quick"]):
        return 2
    if "dust" in label_lower or "wipe" in label_lower:
        return 1
    
    # Category-based defaults
    if category == "k&m":
        return 3
    if category == "bathrooms":
        return 4
    if category == "floors":
        return 3
    
    return 3  # Default medium severity


def build_templates() -> List[TaskTemplate]:
    """
    Build all task templates organized by deck.
    
    Cadence types:
    - "weekly": Fixed days every week
    - "biweekly": Alternating weeks (odd/even from anchor)
    - "n_per_week": Rotates through preferred_days
    
    Flexible 2-3x flag:
    - When True and roster ≥ BONUS_THIRD_CLEANING_MIN_ROSTER,
      task gets 3rd cleaning selected via bonus algorithm
    """
    templates = []
    
    # ==================== ZERO DECK ====================
    templates.extend([
        TaskTemplate(
            key="ZD_RATSKELLER_FLOOR",
            deck="Zero Deck",
            label="Ratskeller Sweep+Mop",
            category="floors",
            people_needed=2,
            cadence="n_per_week",
            times_per_week=2,
            preferred_days=BASE_2X_DAYS_DEFAULT,
            severity=3,
            effort_multiplier=1.1,
            flexible_2_3x=True
        ),
        TaskTemplate(
            key="ZD_GAMEX_FLOOR",
            deck="Zero Deck",
            label="Game Room + X-Room Sweep+Mop",
            category="floors",
            people_needed=2,
            cadence="n_per_week",
            times_per_week=2,
            preferred_days=BASE_2X_DAYS_DEFAULT,
            severity=3,
            effort_multiplier=1.1,
            flexible_2_3x=True
        ),
    ])
    
    # ==================== FIRST DECK ====================
    templates.extend([
        TaskTemplate(
            key="FD_KM_SUN",
            deck="First Deck",
            label="k&m",
            category="k&m",
            people_needed=3,
            cadence="weekly",
            days_of_week=[0],  # Sunday
            severity=3,
            effort_multiplier=1.2
        ),
        TaskTemplate(
            key="FD_KM_MON",
            deck="First Deck",
            label="k&m",
            category="k&m",
            people_needed=2,
            cadence="weekly",
            days_of_week=[1],  # Monday
            severity=3,
            effort_multiplier=1.1
        ),
        TaskTemplate(
            key="FD_KM_TUE",
            deck="First Deck",
            label="k&m",
            category="k&m",
            people_needed=2,
            cadence="weekly",
            days_of_week=[2],  # Tuesday
            severity=3,
            effort_multiplier=1.1
        ),
        TaskTemplate(
            key="FD_KM_WED",
            deck="First Deck",
            label="k&m",
            category="k&m",
            people_needed=2,
            cadence="weekly",
            days_of_week=[3],  # Wednesday
            severity=3,
            effort_multiplier=1.1
        ),
        TaskTemplate(
            key="FD_KM_THU",
            deck="First Deck",
            label="k&m",
            category="k&m",
            people_needed=2,
            cadence="weekly",
            days_of_week=[4],  # Thursday
            severity=3,
            effort_multiplier=1.1
        ),
        TaskTemplate(
            key="FD_LIVING_FLOOR",
            deck="First Deck",
            label="Living Room Sweep+Mop",
            category="floors",
            people_needed=2,
            cadence="n_per_week",
            times_per_week=2,
            preferred_days=BASE_2X_DAYS_DEFAULT,
            severity=3,
            effort_multiplier=1.05,
            flexible_2_3x=True
        ),
        TaskTemplate(
            key="FD_DINING_FLOOR",
            deck="First Deck",
            label="Dining Room Sweep+Mop",
            category="floors",
            people_needed=2,
            cadence="n_per_week",
            times_per_week=2,
            preferred_days=BASE_2X_DAYS_DEFAULT,
            severity=3,
            effort_multiplier=1.05,
            flexible_2_3x=True
        ),
    ])
    
    # ==================== SECOND DECK ====================
    templates.extend([
        TaskTemplate(
            key="SD_HALL_FLOOR",
            deck="Second Deck",
            label="Hallway Sweep+Mop",
            category="floors",
            people_needed=2,
            cadence="n_per_week",
            times_per_week=2,
            preferred_days=BASE_2X_DAYS_DEFAULT,
            severity=3,
            effort_multiplier=1.0,
            flexible_2_3x=True
        ),
        TaskTemplate(
            key="SD_SINKS",
            deck="Second Deck",
            label="Sinks Clean/Sweep Bathroom",
            category="bathrooms",
            people_needed=1,
            cadence="n_per_week",
            times_per_week=2,
            preferred_days=BASE_2X_DAYS_DEFAULT,
            severity=4,
            effort_multiplier=1.0,
            flexible_2_3x=True
        ),
        TaskTemplate(
            key="SD_TOILETS",
            deck="Second Deck",
            label="Toilets Clean/Mop Bathroom",
            category="bathrooms",
            people_needed=1,
            cadence="n_per_week",
            times_per_week=2,
            preferred_days=BASE_2X_DAYS_DEFAULT,
            severity=4,
            effort_multiplier=1.0,
            flexible_2_3x=True
        ),
        TaskTemplate(
            key="SD_SHOWERS",
            deck="Second Deck",
            label="Showers Clean",
            category="bathrooms",
            people_needed=2,
            cadence="weekly",
            days_of_week=[6],  # Saturday
            severity=4,
            effort_multiplier=1.2
        ),
        TaskTemplate(
            key="SD_STAIRS_FLOOR",
            deck="Second Deck",
            label="Stairs Sweep+Mop",
            category="floors",
            people_needed=2,
            cadence="n_per_week",
            times_per_week=2,
            preferred_days=BASE_2X_DAYS_DEFAULT,
            severity=3,
            effort_multiplier=1.1,
            flexible_2_3x=True
        ),
        TaskTemplate(
            key="SD_LROOM",
            deck="Second Deck",
            label="L-Room Clean",
            category="common",
            people_needed=1,
            cadence="weekly",
            days_of_week=[6],  # Saturday
            severity=3,
            effort_multiplier=1.0
        ),
        TaskTemplate(
            key="SD_LIBRARY",
            deck="Second Deck",
            label="Library Clean",
            category="common",
            people_needed=1,
            cadence="weekly",
            days_of_week=[6],  # Saturday
            severity=3,
            effort_multiplier=1.0
        ),
        # TaskTemplate(
        #     key="SD_BRASSO",
        #     deck="Second Deck",
        #     label="Brasso",
        #     category="other",
        #     people_needed=1,
        #     cadence="biweekly",
        #     days_of_week=[6],  # Saturday
        #     severity=3,
        #     effort_multiplier=1.0
        # ),
        # TaskTemplate(
        #     key="SD_BLUE",
        #     deck="Second Deck",
        #     label="Blue",
        #     category="other",
        #     people_needed=1,
        #     cadence="biweekly",
        #     days_of_week=[6],  # Saturday
        #     severity=3,
        #     effort_multiplier=1.0
        # ),
    ])
    
    # ==================== THIRD DECK ====================
    templates.extend([
        TaskTemplate(
            key="TD_HALL_FLOOR",
            deck="Third Deck",
            label="Hallway Sweep+Mop",
            category="floors",
            people_needed=2,
            cadence="n_per_week",
            times_per_week=2,
            preferred_days=BASE_2X_DAYS_DEFAULT,
            severity=3,
            effort_multiplier=1.0,
            flexible_2_3x=True
        ),
        TaskTemplate(
            key="TD_SINKS",
            deck="Third Deck",
            label="Sinks Clean/Sweep Bathroom",
            category="bathrooms",
            people_needed=1,
            cadence="n_per_week",
            times_per_week=2,
            preferred_days=BASE_2X_DAYS_DEFAULT,
            severity=4,
            effort_multiplier=1.0,
            flexible_2_3x=True
        ),
        TaskTemplate(
            key="TD_TOILETS",
            deck="Third Deck",
            label="Toilets Clean/Mop Bathroom",
            category="bathrooms",
            people_needed=1,
            cadence="n_per_week",
            times_per_week=2,
            preferred_days=BASE_2X_DAYS_DEFAULT,
            severity=4,
            effort_multiplier=1.0,
            flexible_2_3x=True
        ),
        TaskTemplate(
            key="TD_SHOWERS",
            deck="Third Deck",
            label="Showers Clean",
            category="bathrooms",
            people_needed=2,
            cadence="weekly",
            days_of_week=[6],  # Saturday
            severity=4,
            effort_multiplier=1.2
        ),
        TaskTemplate(
            key="TD_STAIRS_FLOOR",
            deck="Third Deck",
            label="Stairs Sweep+Mop",
            category="floors",
            people_needed=2,
            cadence="n_per_week",
            times_per_week=2,
            preferred_days=BASE_2X_DAYS_DEFAULT,
            severity=3,
            effort_multiplier=1.1,
            flexible_2_3x=True
        ),
        # TaskTemplate(
        #     key="TD_BRASSO",
        #     deck="Third Deck",
        #     label="Brasso",
        #     category="other",
        #     people_needed=1,
        #     cadence="biweekly",
        #     days_of_week=[6],  # Saturday
        #     severity=3,
        #     effort_multiplier=1.0
        # ),
        # TaskTemplate(
        #     key="TD_BLUE",
        #     deck="Third Deck",
        #     label="Blue",
        #     category="other",
        #     people_needed=1,
        #     cadence="biweekly",
        #     days_of_week=[6],  # Saturday
        #     severity=3,
        #     effort_multiplier=1.0
        # ),
    ])
    
    return templates

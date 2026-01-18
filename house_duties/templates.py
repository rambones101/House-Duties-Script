"""Task template definitions for all house chores organized by deck."""
from typing import List
from .models import TaskTemplate


# Default day assignments for consistency
BASE_2X_DAYS_DEFAULT = [2, 4]  # Tuesday, Thursday
BONUS_3RD_DAY_DEFAULT = [5]     # Friday


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
            key="ZD_KM_DAILY",
            deck="Zero Deck",
            label="K&M Daily",
            category="k&m",
            people_needed=2,
            cadence="weekly",
            days_of_week=[0, 1, 2, 3, 4, 5, 6],  # Every day
            severity=3,
            effort_multiplier=1.0
        ),
        TaskTemplate(
            key="ZD_FLOORS",
            deck="Zero Deck",
            label="Floors",
            category="floors",
            people_needed=2,
            cadence="n_per_week",
            times_per_week=2,
            preferred_days=BASE_2X_DAYS_DEFAULT,
            severity=3,
            effort_multiplier=1.2,
            flexible_2_3x=True
        ),
        TaskTemplate(
            key="ZD_BATHROOMS",
            deck="Zero Deck",
            label="Bathrooms",
            category="bathrooms",
            people_needed=2,
            cadence="n_per_week",
            times_per_week=2,
            preferred_days=BASE_2X_DAYS_DEFAULT,
            severity=4,
            effort_multiplier=1.3,
            flexible_2_3x=True
        ),
    ])
    
    # ==================== FIRST DECK ====================
    templates.extend([
        TaskTemplate(
            key="FD_FLOORS",
            deck="First Deck",
            label="Floors Sweep/Vacuum",
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
            key="FD_BATHROOMS",
            deck="First Deck",
            label="Clean Bathrooms",
            category="bathrooms",
            people_needed=2,
            cadence="n_per_week",
            times_per_week=2,
            preferred_days=BASE_2X_DAYS_DEFAULT,
            severity=4,
            effort_multiplier=1.2,
            flexible_2_3x=True
        ),
    ])
    
    # ==================== SECOND DECK ====================
    templates.extend([
        TaskTemplate(
            key="SD_SINKS",
            deck="Second Deck",
            label="Sinks Clean/Sweep Bathroom",
            category="bathrooms",
            people_needed=2,
            cadence="n_per_week",
            times_per_week=2,
            preferred_days=BASE_2X_DAYS_DEFAULT,
            severity=4,
            effort_multiplier=1.1,
            flexible_2_3x=True
        ),
        TaskTemplate(
            key="SD_TOILETS",
            deck="Second Deck",
            label="Toilets/Showers",
            category="bathrooms",
            people_needed=2,
            cadence="n_per_week",
            times_per_week=2,
            preferred_days=BASE_2X_DAYS_DEFAULT,
            severity=5,
            effort_multiplier=1.3,
            flexible_2_3x=True
        ),
        TaskTemplate(
            key="SD_BRASSO",
            deck="Second Deck",
            label="Brasso",
            category="other",
            people_needed=2,
            cadence="biweekly",
            days_of_week=[6],  # Saturday
            severity=5,
            effort_multiplier=1.5
        ),
        TaskTemplate(
            key="SD_FLOORS",
            deck="Second Deck",
            label="Floors Sweep/Vacuum",
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
    
    # ==================== THIRD DECK ====================
    templates.extend([
        TaskTemplate(
            key="TD_SINKS",
            deck="Third Deck",
            label="Sinks Clean/Sweep",
            category="bathrooms",
            people_needed=2,
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
            label="Toilets/Showers",
            category="bathrooms",
            people_needed=2,
            cadence="n_per_week",
            times_per_week=2,
            preferred_days=BASE_2X_DAYS_DEFAULT,
            severity=5,
            effort_multiplier=1.2,
            flexible_2_3x=True
        ),
        TaskTemplate(
            key="TD_BLUE",
            deck="Third Deck",
            label="Blue (Deck Cleaning)",
            category="other",
            people_needed=2,
            cadence="biweekly",
            days_of_week=[6],  # Saturday
            severity=5,
            effort_multiplier=1.4
        ),
        TaskTemplate(
            key="TD_FLOORS",
            deck="Third Deck",
            label="Floors Sweep/Vacuum",
            category="floors",
            people_needed=2,
            cadence="n_per_week",
            times_per_week=2,
            preferred_days=BASE_2X_DAYS_DEFAULT,
            severity=3,
            effort_multiplier=1.0,
            flexible_2_3x=True
        ),
    ])
    
    # ==================== COMMON/OTHER ====================
    templates.extend([
        TaskTemplate(
            key="LAUNDRY",
            deck="Other",
            label="Laundry",
            category="laundry",
            people_needed=2,
            cadence="weekly",
            days_of_week=[1, 4],  # Monday, Thursday
            severity=3,
            effort_multiplier=1.0
        ),
        TaskTemplate(
            key="TRASH",
            deck="Other",
            label="Take Out Trash",
            category="common",
            people_needed=1,
            cadence="weekly",
            days_of_week=[0, 3, 6],  # Sun, Wed, Sat
            severity=2,
            effort_multiplier=0.8
        ),
    ])
    
    return templates

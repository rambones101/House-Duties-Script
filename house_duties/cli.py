"""Command-line interface for the House Duties Scheduler."""
import argparse
import sys
import logging
from pathlib import Path
from datetime import date
from typing import Optional

from .models import TaskTemplate, Occurrence
from .utils import most_recent_sunday, parse_start_sunday
from .state import load_state, save_state, get_anchor_sunday, load_brothers, load_categories, load_constraints
from .templates import build_templates
from .scheduler import occurrences_from_templates
from .assignment import assign_chores
from .output import write_csv, write_json, print_schedule_by_deck


# Configuration Constants
START_SUNDAY = ""  # Leave empty for auto-detect
WEEKS_TO_GENERATE = 1
BONUS_THIRD_CLEANING_MIN_ROSTER = 20  # Minimum roster size to enable bonus 3rd cleanings
RANDOM_SEED = 42


def configure_logging(verbose: bool = False, log_file: str = "house_duties.log") -> None:
    """Configure logging with file and console output."""
    level = logging.DEBUG if verbose else logging.INFO
    
    logging.basicConfig(
        level=level,
        format='%(asctime)s - %(levelname)s - %(message)s',
        handlers=[
            logging.StreamHandler(sys.stdout),
            logging.FileHandler(log_file, mode='a')
        ]
    )


def parse_arguments() -> argparse.Namespace:
    """Parse command-line arguments."""
    parser = argparse.ArgumentParser(
        description="House Duties Scheduler - Fairness-based chore assignment system",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  %(prog)s                          # Run with defaults (auto-detect Sunday, 1 week)
  %(prog)s --weeks 2                # Generate 2 weeks of schedule
  %(prog)s --start 2026-01-19       # Start from specific Sunday
  %(prog)s --dry-run                # Preview without saving
  %(prog)s --verbose                # Enable debug logging

File Paths:
  --brothers      Path to brothers.txt (default: config/brothers.txt)
  --state         Path to chore_state.json (default: data/chore_state.json)
  --categories    Path to brother_categories.json (default: config/brother_categories.json)
  --constraints   Path to constraints.json (optional)
  --output-csv    Output CSV file (default: data/schedule.csv)
  --output-json   Output JSON file (default: data/schedule.json)
        """
    )
    
    # Generation options
    parser.add_argument(
        '--start',
        type=str,
        default=START_SUNDAY,
        help='Start Sunday (YYYY-MM-DD). Leave empty for auto-detect.'
    )
    parser.add_argument(
        '--weeks',
        type=int,
        default=WEEKS_TO_GENERATE,
        help='Number of weeks to generate (default: 1)'
    )
    parser.add_argument(
        '--seed',
        type=int,
        default=RANDOM_SEED,
        help='Random seed for tie-breaking (default: 42)'
    )
    parser.add_argument(
        '--min-bonus-roster',
        type=int,
        default=BONUS_THIRD_CLEANING_MIN_ROSTER,
        help='Minimum roster size for bonus 3rd cleanings (default: 14)'
    )
    
    # File paths
    parser.add_argument(
        '--brothers',
        type=str,
        default='config/brothers.txt',
        help='Path to brothers roster file'
    )
    parser.add_argument(
        '--state',
        type=str,
        default='data/chore_state.json',
        help='Path to persistent state file'
    )
    parser.add_argument(
        '--categories',
        type=str,
        default='config/brother_categories.json',
        help='Path to brother categories file'
    )
    parser.add_argument(
        '--constraints',
        type=str,
        default='config/constraints.json',
        help='Path to constraints file (optional)'
    )
    parser.add_argument(
        '--output-csv',
        type=str,
        default='data/schedule.csv',
        help='Output CSV file path'
    )
    parser.add_argument(
        '--output-json',
        type=str,
        default='data/schedule.json',
        help='Output JSON file path'
    )
    
    # Behavior flags
    parser.add_argument(
        '--dry-run',
        action='store_true',
        help='Preview schedule without saving state'
    )
    parser.add_argument(
        '--verbose',
        action='store_true',
        help='Enable verbose debug logging'
    )
    parser.add_argument(
        '--quiet',
        action='store_true',
        help='Suppress schedule output (still writes files)'
    )
    
    return parser.parse_args()


def main(args: Optional[argparse.Namespace] = None) -> int:
    """
    Main entry point for the House Duties Scheduler.
    
    Returns:
        0 on success, non-zero on error
    """
    if args is None:
        args = parse_arguments()
    
    configure_logging(args.verbose)
    logger = logging.getLogger(__name__)
    
    try:
        # Load roster and constraints
        logger.info("Loading roster and configuration...")
        brothers = load_brothers(args.brothers)
        if not brothers:
            logger.error("No brothers found in roster file")
            return 1
        logger.info(f"Loaded {len(brothers)} brothers")
        
        categories = load_categories(args.categories)
        constraints = load_constraints(args.constraints)
        
        # Load persistent state
        state = load_state(args.state)
        
        # Determine start Sunday
        start_sunday = parse_start_sunday(args.start)
        anchor_sunday = get_anchor_sunday(state, start_sunday)
        logger.info(f"Anchor Sunday: {anchor_sunday}")
        logger.info(f"Generating schedule starting: {start_sunday}")
        logger.info(f"Generating {args.weeks} week(s)")
        
        # Build task templates
        templates = build_templates()
        logger.info(f"Built {len(templates)} task templates")
        
        # Expand to occurrences
        bonus_counts = state.get("bonus_counts", {})
        occurrences = occurrences_from_templates(
            templates=templates,
            start_sunday=start_sunday,
            num_weeks=args.weeks,
            anchor_sunday=anchor_sunday,
            bonus_counts=bonus_counts,
            roster_size=len(brothers),
            min_bonus_roster=args.min_bonus_roster
        )
        logger.info(f"Expanded to {len(occurrences)} chore occurrences")
        
        # Assign brothers
        logger.info("Assigning chores...")
        schedule, updated_state = assign_chores(
            occs=occurrences,
            brothers=brothers,
            constraints=constraints,
            state=state,
            random_seed=args.seed
        )
        logger.info(f"Assigned {len(schedule)} chores")
        
        # Update bonus counts for selected tasks
        for occ in occurrences:
            if "[BONUS]" in occ.task_label:
                task_key = occ.task_key
                updated_state.setdefault("bonus_counts", {})
                updated_state["bonus_counts"][task_key] = updated_state["bonus_counts"].get(task_key, 0) + 1
        
        # Save outputs
        if not args.dry_run:
            save_state(args.state, updated_state)
            logger.info(f"Saved state to {args.state}")
        else:
            logger.info("DRY RUN - State not saved")
        
        write_csv(schedule, args.output_csv)
        write_json(schedule, args.output_json)
        logger.info(f"Wrote schedule to {args.output_csv} and {args.output_json}")
        
        # Print schedule
        if not args.quiet:
            print("\n" + "="*80)
            print(f"HOUSE DUTIES SCHEDULE - Week of {start_sunday}")
            print("="*80 + "\n")
            print_schedule_by_deck(schedule, start_sunday, anchor_sunday, len(brothers))
        
        logger.info("Schedule generation completed successfully")
        return 0
        
    except FileNotFoundError as e:
        logger.error(f"File not found: {e}")
        return 1
    except ValueError as e:
        logger.error(f"Configuration error: {e}")
        return 1
    except Exception as e:
        logger.exception(f"Unexpected error: {e}")
        return 1


if __name__ == "__main__":
    sys.exit(main())

#!/usr/bin/env python3
"""
House Duties Scheduler - Main Entry Point

Modular chore scheduling system with persistent state tracking,
fairness algorithms, and deck-based organization.
"""

import sys
from house_duties.cli import main, parse_arguments

if __name__ == "__main__":
    try:
        args = parse_arguments()
        sys.exit(main(args))
    except KeyboardInterrupt:
        print("\n\nInterrupted by user", file=sys.stderr)
        sys.exit(130)

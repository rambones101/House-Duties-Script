#!/usr/bin/env python3
"""
House Duties Scheduler - Main Entry Point

This is a thin wrapper that maintains backward compatibility while using
the new modular structure under the house_duties/ package.

For the modular implementation, see house_duties/ directory.
"""

# Re-export everything for backward compatibility with existing code/tests
from house_duties_legacy import *

# This allows the script to be run directly
if __name__ == "__main__":
    import sys
    from house_duties_legacy import main, parse_arguments
    
    try:
        args = parse_arguments()
        sys.exit(main(args))
    except KeyboardInterrupt:
        print("\n\nInterrupted by user", file=sys.stderr)
        sys.exit(130)

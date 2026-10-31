"""CLI entry point for HOJJAT TUI.

Supports:
- Console script entry point: `hojjat-tui`
- Python module entry point: `python -m hojjat_tui`
- Management commands via: `python manage.py <command>`
"""

import sys
from typing import List, Optional

from hojjat_tui import __version__
from hojjat_tui.management import main as management_main


def main(argv: Optional[List[str]] = None):
    """Main entry point for the console script.
    
    If no arguments are provided, starts the TUI.
    If arguments are provided, delegates to management commands.
    
    Usage:
        hojjat-tui          # Start TUI
        hojjat-tui run      # Show help for management commands
        hojjat-tui --version # Show version
    """
    if argv is None:
        argv = sys.argv[1:]
    
    if not argv:
        # No arguments — start the TUI
        from hojjat_tui.tui import run
        run()
        return
    
    if "--version" in argv or "-V" in argv:
        print(f"hojjat-tui version {__version__}")
        return
    
    # Delegate to management commands
    # Filter out our own flags and pass remaining args
    management_main(argv)


def cli_main():
    """Console script entry point."""
    main()


def module_main():
    """Python module entry point: python -m hojjat_tui."""
    main()


if __name__ == "__main__":
    module_main()
#!/usr/bin/env python
"""Django-style management script for HOJJAT TUI.

Usage:
    python manage.py <command> [options]

Commands:
    init              Initialize the database (safe to rerun)
    createsuperuser Create a superuser account
    run [name]      Run a registered function
    check           Check project installation
    test [path]     Run tests
    --version       Show version
"""

import os
import sys

if __name__ == "__main__":
    # Ensure the src directory is on the path
    src_dir = os.path.join(os.path.dirname(os.path.abspath(__file__)), "src")
    if src_dir not in sys.path:
        sys.path.insert(0, src_dir)
    
    # Ensure built-in functions are registered FIRST
    from hojjat_tui import builtin_functions  # noqa: F401
    builtin_functions.register_builtins()
    
    from hojjat_tui.management import main
    
    main()
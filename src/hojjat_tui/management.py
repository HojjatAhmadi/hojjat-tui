"""Django-style management commands for HOJJAT TUI.

Usage:
    python manage.py <command> [options]

Commands:
    init              Initialize a HOJJAT TUI project structure
    createsuperuser Create a superuser account
    run               Run a registered function
    check             Check project installation
    test              Run test suite
    --version         Show version
"""

import argparse
import getpass
import logging
import os
import runpy
import sys
import time
from pathlib import Path
from typing import Any, Dict, List, Optional

from hojjat_tui import __version__, run
from hojjat_tui.function import get_registry, load_function_modules
from hojjat_tui.executor import execute_function
from hojjat_tui.persistence import Database, get_default_db_path

logger = logging.getLogger("hojjat_tui.management")

MANAGE_PY_TEMPLATE = '''"""HOJJAT TUI project entry point.

This file is the central entry point for your HOJJAT TUI project.
Import your function modules here so their @hojjat_function() decorators
register them before the TUI starts.

Usage:
    python manage.py          # Start the TUI
    python manage.py run <name> [--param KEY=VALUE]  # Run a function directly
    hojjat-tui                # Also starts the TUI (executes this file)
"""

from hojjat_tui import run

# Import your function modules below.
from functions import example


if __name__ == "__main__":
    run()
'''

FUNCTIONS_INIT_TEMPLATE = '''"""HOJJAT TUI function modules package.

Import your function modules here, or import them directly in manage.py.
"""


'''

EXAMPLE_PY_TEMPLATE = '''"""Example HOJJAT TUI functions.

This file demonstrates different function patterns that you can
register with the @hojjat_function() decorator. All functions will be
visible in the TUI once this module is imported (see manage.py).

To add your own functions, create new modules in this package and import
them from manage.py.
"""

from hojjat_tui.function import hojjat_function, FunctionResult, ChartOutput


# ---------------------------------------------------------------------------
# Example 1: Simple function with a string result
# ---------------------------------------------------------------------------
#
# Demonstrates the simplest possible registered function: no input
# parameters, returns a plain string. The TUI displays the string as text.
@hojjat_function(
    name="hello_world",
    label="Hello World",
    description="Return a simple greeting string.",
)
def hello_world() -> str:
    """Return a simple greeting.

    What it demonstrates:
        - A function with no input parameters.
        - A plain string return value.
    What to expect:
        - The TUI shows "Hello from HOJJAT TUI!" as text output.
    """
    return "Hello from HOJJAT TUI!"


# ---------------------------------------------------------------------------
# Example 2: Function returning a table
# ---------------------------------------------------------------------------
#
# Demonstrates returning tabular data. Return a list of dicts where each
# dict is a row and the keys are column names. The TUI detects this as
# table output and renders it as a Rich Table.
@hojjat_function(
    name="sample_data",
    label="Sample Data",
    description="Return a table of sample project data.",
)
def sample_data() -> list[dict]:
    """Return a table of sample project data.

    What it demonstrates:
        - Returning a list of dictionaries for table output.
        - Column names derived from dictionary keys.
    What to expect:
        - The TUI renders a table with columns: id, name, status, score.
    """
    return [
        {"id": 1, "name": "Project Alpha", "status": "active", "score": 95},
        {"id": 2, "name": "Project Beta", "status": "pending", "score": 78},
        {"id": 3, "name": "Project Gamma", "status": "active", "score": 88},
        {"id": 4, "name": "Project Delta", "status": "archived", "score": 62},
    ]


# ---------------------------------------------------------------------------
# Example 3: Function returning a bar chart
# ---------------------------------------------------------------------------
#
# Demonstrates explicit bar chart output using ChartOutput. The TUI
# automatically detects ChartOutput and renders it as a chart without
# requiring the user to press a manual "Chart" button.
@hojjat_function(
    name="sales_by_region",
    label="Sales by Region",
    description="Return regional sales as a bar chart.",
)
def sales_by_region() -> ChartOutput:
    """Return regional sales figures as a bar chart.

    What it demonstrates:
        - Explicit chart output via the ChartOutput class.
        - Bar chart rendering with categorical labels and numeric values.
        - Automatic chart detection by the TUI (no manual button needed).
    What to expect:
        - The TUI renders an ASCII bar chart of sales by region.
    """
    return ChartOutput(
        chart_type="bar",
        labels=["North", "South", "East", "West", "Central"],
        values=[12400, 9800, 15600, 11200, 13400],
        title="Regional Sales Q3",
    )


# ---------------------------------------------------------------------------
# Example 4: Function returning a line chart
# ---------------------------------------------------------------------------
#
# Demonstrates explicit line chart output using ChartOutput.
@hojjat_function(
    name="temperature_trend",
    label="Temperature Trend",
    description="Return daily temperatures as a line chart.",
)
def temperature_trend() -> ChartOutput:
    """Return daily temperature readings as a line chart.

    What it demonstrates:
        - Explicit chart output via the ChartOutput class.
        - Line chart rendering with time-series data.
        - Automatic chart detection by the TUI.
    What to expect:
        - The TUI renders an ASCII line chart of temperatures over time.
    """
    return ChartOutput(
        chart_type="line",
        labels=["Mon", "Tue", "Wed", "Thu", "Fri", "Sat", "Sun"],
        values=[68, 72, 75, 73, 78, 81, 76],
        title="Weekly Temperature",
    )


# ---------------------------------------------------------------------------
# Example 5: Function with input parameters
# ---------------------------------------------------------------------------
#
# Demonstrates accepting typed input parameters. The TUI generates a
# parameter form before execution.
@hojjat_function(
    name="greet_user",
    label="Greet User",
    description="Generate a personalized greeting for a user.",
    annotations={"name": {"type": "str", "description": "The user's name"}},
    defaults={"name": "Guest"},
    required=["name"],
)
def greet_user(name: str) -> str:
    """Generate a personalized greeting.

    What it demonstrates:
        - Accepting a typed input parameter (name: str).
        - Using the parameter in the return value.
        - The TUI builds an input form before execution.
    What to expect:
        - The TUI prompts for a name, then returns "Hello <name>!".
    """
    return f"Hello {name}!"


# ---------------------------------------------------------------------------
# Example 6: Function returning JSON / dict output
# ---------------------------------------------------------------------------
#
# Demonstrates returning a dictionary, which the TUI renders as formatted
# JSON.
@hojjat_function(
    name="system_info",
    label="System Info",
    description="Return system information as JSON output.",
)
def system_info() -> dict:
    """Return system information as JSON output.

    What it demonstrates:
        - Returning a dictionary for JSON-formatted output.
    What to expect:
        - The TUI renders the dictionary as indented JSON.
    """
    import platform
    import sys

    return {
        "python_version": sys.version,
        "platform": platform.platform(),
        "processor": platform.processor(),
    }


# ---------------------------------------------------------------------------
# Example 7: Function that can fail (error handling)
# ---------------------------------------------------------------------------
#
# Demonstrates what happens when a function raises an exception.
@hojjat_function(
    name="error_demo",
    label="Error Demo",
    description="Demonstrate error handling in the TUI.",
)
def error_demo(message: str = "Something went wrong") -> str:
    """Demonstrate error handling.

    What it demonstrates:
        - A function that deliberately raises an exception.
        - The TUI catches the error and shows a traceback.
    What to expect:
        - The TUI shows an execution failure with the error message.
    """
    raise RuntimeError(message)

'''

def init_project() -> bool:
    """Initialize a HOJJAT TUI project structure in the current directory.

    Creates:
        manage.py          - Project entry point
        functions/         - Package directory for function modules
        functions/__init__.py - Package marker
        functions/example.py  - Example function module

    Does NOT create or initialize a database.

    Returns:
        True if the project was created (or already existed), False on error.
    """
    root = Path.cwd()

    # Check if project structure already exists
    manage_py = root / "manage.py"
    functions_dir = root / "functions"
    functions_init = functions_dir / "__init__.py"
    example_py = functions_dir / "example.py"

    if manage_py.exists() or functions_dir.exists():
        print("[info] HOJJAT TUI project structure already exists in "
              f"'{root}'. No files were overwritten.")
        return True

    try:
        # Create functions/ directory
        functions_dir.mkdir(parents=True, exist_ok=False)

        # Write files
        manage_py.write_text(MANAGE_PY_TEMPLATE, encoding="utf-8")
        functions_init.write_text(FUNCTIONS_INIT_TEMPLATE, encoding="utf-8")
        example_py.write_text(EXAMPLE_PY_TEMPLATE, encoding="utf-8")

        print(f"[success] HOJJAT TUI project initialized in '{root}'")
        print("")
        print("  Created: manage.py")
        print("  Created: functions/__init__.py")
        print("  Created: functions/example.py")
        print("")
        print("  Next steps:")
        print("    1. Review functions/example.py for examples.")
        print("    2. Add your own function modules to functions/.")
        print("    3. Import them in manage.py.")
        print("    4. Run: hojjat-tui   (or: python manage.py)")
        return True

    except FileExistsError:
        print("[info] HOJJAT TUI project structure already exists. "
              "No files were overwritten.")
        return True
    except Exception as e:
        print(f"[error] Failed to initialize project: {e}")
        logger.exception("Project initialization failed")
        return False


def cmd_init(args: argparse.Namespace):
    """Initialize a HOJJAT TUI project structure."""
    init_project()

def cmd_createsuperuser(args: argparse.Namespace):
    """Create a superuser account."""
    db_path = args.db_path if hasattr(args, "db_path") and args.db_path else None
    db = Database(db_path) if db_path else Database()
    
    username = args.username
    if not username:
        username = input("Username: ").strip()
        if not username:
            print("[error] Username is required")
            sys.exit(1)
    
    email = args.email
    if not email:
        try:
            email = input("Email (optional): ").strip() or None
        except EOFError:
            pass
    
    # Password input
    if args.password:
        password = args.password
    else:
        password = getpass.getpass("Password: ")
        if not password:
            print("[error] Password is required")
            sys.exit(1)
        confirm = getpass.getpass("Password (confirm): ")
        if password != confirm:
            print("[error] Passwords do not match")
            sys.exit(1)
    
    if db.create_user(username, password, email=email, is_superuser=True):
        print(f"[success] Superuser '{username}' created successfully")
    else:
        print(f"[error] User '{username}' already exists")
        sys.exit(1)

def cmd_run(args: argparse.Namespace):
    """Run a registered function by name, or launch the TUI if no name given."""
    # Execute the project's manage.py (if present) so that module imports
    # and @hojjat_function() decorators populate the registry in the current process.
    # Use run_name != "__main__" to avoid triggering manage.py's `if __name__ == "__main__": run()`
    # block — we only want the module imports, not to start the TUI here.
    manage_file = Path.cwd() / "manage.py"
    if manage_file.is_file():
        root_str = str(manage_file.parent)
        if root_str not in sys.path:
            sys.path.insert(0, root_str)
        try:
            runpy.run_path(str(manage_file), run_name="hojjat_tui.management.cmd_run")
        except Exception:
            pass

    # Load user-configured function modules so decorators populate the registry.
    loaded, errors = load_function_modules()
    for err in errors:
        print(f"[warning] {err}")
    if loaded:
        print(f"[info] Loaded function modules: {', '.join(loaded)}")

    # Ensure builtins are loaded
    from hojjat_tui import builtin_functions
    builtin_functions.register_builtins()

    registry = get_registry()
    
    if not args.name:
        # Launch the interactive TUI
        from hojjat_tui.tui import run as tui_run
        try:
            tui_run()
            return
        except Exception as e:
            # Fall back to function list in non-interactive mode
            if "TTY" in str(e).upper() or "terminal" in str(e).lower():
                print("Available functions (interactive TUI not available in this context):")
                for name, metadata in registry.items():
                    print(f"  {name}: {metadata.get('description', '')}")
            else:
                raise
    
    if args.name not in registry:
        print(f"[error] Function '{args.name}' is not registered")
        sys.exit(1)
    
    # Build kwargs from command line arguments
    kwargs = {}
    for key, value in (args.params or {}).items():
        kwargs[key] = value
    
    start_time = time.time()
    result = execute_function(args.name, kwargs=kwargs)
    duration = time.time() - start_time
    
    # Log to database
    try:
        db = Database()
        db.log_function_execution(
            args.name, result.success, result.duration, result.type,
            result.error, None
        )
    except Exception as e:
        logger.error(f"Failed to log execution: {e}")
    
    if result.success:
        # Use rich console for output
        from rich.console import Console
        console = Console()
        console.print(result.to_text())
    else:
        print(f"[error] {result.error}")
        sys.exit(1)

def cmd_check(args: argparse.Namespace):
    """Check project installation and configuration."""
    print("HOJJAT TUI Installation Check")
    print(f"Version: {__version__}")
    print(f"Python: {sys.version}")
    print()
    
    # Check imports
    checks = []
    try:
        import textual
        checks.append(("textual", textual.__version__, True))
    except ImportError:
        checks.append(("textual", None, False))
    
    try:
        import pydantic
        checks.append(("pydantic", pydantic.__version__, True))
    except ImportError:
        checks.append(("pydantic", None, False))
    
    try:
        import bcrypt
        checks.append(("bcrypt", bcrypt.__version__, True))
    except ImportError:
        checks.append(("bcrypt", None, False))
    
    try:
        import sqlite3
        checks.append(("sqlite3", sqlite3.sqlite_version, True))
    except ImportError:
        checks.append(("sqlite3", None, False))
    
    print("Dependencies:")
    for name, version, ok in checks:
        status = "[ok]" if ok else "[error]"
        ver_str = version if version else "missing"
        print(f"  {status} {name}: {ver_str}")
    
    print()
    
    # Check database
    try:
        db_path = get_default_db_path()
        db = Database()
        db.init_db()
        print(f"[ok] Database: {db_path}")
    except Exception as e:
        print(f"[error] Database: {e}")
    
    print()
    
    # Check registered functions
    registry = get_registry()
    print(f"Registered functions: {len(registry)}")
    for name, metadata in registry.items():
        print(f"  - {name}: {metadata.get('description', 'No description')}")

def cmd_test(args: argparse.Namespace):
    """Run test suite."""
    import pytest
    sys.exit(pytest.main([args.test_path or "tests/"]))

def cmd_version(args: argparse.Namespace):
    """Show version information."""
    print(f"hojjat-tui version {__version__}")

def create_parser() -> argparse.ArgumentParser:
    """Create the argument parser for management commands."""
    parser = argparse.ArgumentParser(
        prog="python manage.py",
        description="HOJJAT TUI management commands",
    )
    parser.add_argument("--version", action="store_true", help="Show version and exit")
    
    subparsers = parser.add_subparsers(dest="command", help="Available commands")
    
    # init command
    init_parser = subparsers.add_parser("init", help="Initialize project structure")
    init_parser.set_defaults(func=cmd_init)
    
    # createsuperuser command
    su_parser = subparsers.add_parser("createsuperuser", help="Create a superuser")
    su_parser.add_argument("--username", type=str, default=None, help="Username")
    su_parser.add_argument("--email", type=str, default=None, help="Email")
    su_parser.add_argument("--password", type=str, default=None, help="Password (use with caution)")
    su_parser.add_argument("--db-path", type=str, default=None, help="Database path")
    su_parser.set_defaults(func=cmd_createsuperuser)
    
    # run command
    run_parser = subparsers.add_parser("run", help="Run a registered function")
    run_parser.add_argument("name", nargs="?", help="Function name to run")
    run_parser.add_argument("--param", action="append", metavar="KEY=VALUE",
                           dest="params", help="Parameter key=value pairs")
    run_parser.set_defaults(func=cmd_run)
    
    # check command
    check_parser = subparsers.add_parser("check", help="Check installation")
    check_parser.set_defaults(func=cmd_check)
    
    # test command
    test_parser = subparsers.add_parser("test", help="Run tests")
    test_parser.add_argument("test_path", nargs="?", default="tests/", help="Test path")
    test_parser.set_defaults(func=cmd_test)
    
    return parser

def main(argv: Optional[List[str]] = None):
    """Entry point for management commands."""
    parser = create_parser()
    args = parser.parse_args(argv)
    
    if args.version:
        cmd_version(args)
        return
    
    if not args.command:
        parser.print_help()
        return
    
    # Convert params list to dict
    if hasattr(args, "params") and args.params:
        parsed = {}
        for param in args.params:
            if "=" in param:
                key, value = param.split("=", 1)
                # Try to convert to int or float
                try:
                    parsed[key.strip()] = int(value.strip())
                except ValueError:
                    try:
                        parsed[key.strip()] = float(value.strip())
                    except ValueError:
                        parsed[key.strip()] = value.strip()
        args.params = parsed
    
    func = args.func
    func(args)
"""Django-style management commands for HOJJAT TUI.

Usage:
    python manage.py <command> [options]

Commands:
    init              Initialize the database (safe to rerun)
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
import sys
import time
from pathlib import Path
from typing import Any, Dict, List, Optional

from hojjat_tui import __version__
from hojjat_tui.function import get_registry
from hojjat_tui.executor import execute_function
from hojjat_tui.persistence import Database, get_default_db_path

logger = logging.getLogger("hojjat_tui.management")

def cmd_init(args: argparse.Namespace):
    """Initialize the database. Safe to rerun without data loss."""
    db_path = args.db_path if hasattr(args, "db_path") and args.db_path else None
    db = Database(db_path) if db_path else Database()
    db.init_db()
    print(f"[success] Database initialized at: {db.db_path}")

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
    # Ensure builtins are loaded
    from hojjat_tui import builtin_functions
    builtin_functions.register_builtins()
    
    registry = get_registry()
    
    if not args.name:
        # Launch the interactive TUI
        from hojjat_tui.tui import run as tui_run
        try:
            tui_run()
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
    init_parser = subparsers.add_parser("init", help="Initialize database")
    init_parser.add_argument("--db-path", type=str, default=None, help="Database path")
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
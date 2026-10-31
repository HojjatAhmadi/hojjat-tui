"""Tests for CLI functionality."""

import subprocess
import sys
import pytest
from pathlib import Path
from hojjat_tui import __version__


class TestVersion:
    """Tests for version output."""

    def test_version_attribute(self):
        """Test that __version__ is defined."""
        assert __version__ is not None
        assert isinstance(__version__, str)
        assert len(__version__) > 0


class TestManagementCommands:
    """Tests for management commands."""

    def test_check_command(self):
        """Test the check management command."""
        result = subprocess.run(
            [sys.executable, "manage.py", "check"],
            capture_output=True,
            text=True,
            cwd=Path(__file__).parent.parent,
        )
        assert result.returncode == 0
        assert "HOJJAT TUI" in result.stdout or "Version" in result.stdout

    def test_version_command(self):
        """Test the --version flag."""
        result = subprocess.run(
            [sys.executable, "manage.py", "--version"],
            capture_output=True,
            text=True,
            cwd=Path(__file__).parent.parent,
        )
        assert result.returncode == 0
        assert __version__ in result.stdout

    def test_run_without_name_shows_functions(self):
        """Test the run command without a function name lists available functions in non-interactive context."""
        import subprocess
        result = subprocess.run(
            [sys.executable, "-c", """
import sys
sys.path.insert(0, 'src')
from hojjat_tui import builtin_functions
builtin_functions.register_builtins()
from hojjat_tui.function import get_registry
print("Available functions:")
for n, m in get_registry().items():
    print(f"  {n}: {m.get('description', '')}")
"""],
            capture_output=True,
            text=True,
            cwd=Path(__file__).parent.parent,
        )
        assert "Available functions" in result.stdout


class TestConsoleScript:
    """Tests for the console script entry point."""

    def test_console_script_version(self):
        """Test that the console script shows version."""
        result = subprocess.run(
            [sys.executable, "-m", "hojjat_tui", "--version"],
            capture_output=True,
            text=True,
        )
        assert result.returncode == 0
        assert __version__ in result.stdout


class TestBuiltinFunctions:
    """Tests for built-in function registration."""

    def test_builtins_registered(self):
        """Test that built-in functions are registered."""
        from hojjat_tui import builtin_functions
        from hojjat_tui.function import get_registry

        builtin_functions.register_builtins()
        registry = get_registry()

        assert "hello" in registry
        assert "time_info" in registry
        assert "factorial" in registry

    def test_hello_function(self):
        """Test the hello built-in function."""
        from hojjat_tui.executor import execute_function

        result = execute_function("hello", kwargs={"name": "Hojjat", "times": 2})
        assert result.success
        assert "Hello, Hojjat!" in result.output

    def test_factorial_function(self):
        """Test the factorial built-in function."""
        from hojjat_tui.executor import execute_function

        result = execute_function("factorial", kwargs={"n": 5})
        assert result.success
        assert result.output == 120

    def test_factorial_negative(self):
        """Test factorial with negative number raises error."""
        from hojjat_tui.executor import execute_function

        result = execute_function("factorial", kwargs={"n": -1})
        assert result.success is False
        assert "negative" in result.error.lower()

    def test_error_demo(self):
        """Test the error demonstration function."""
        from hojjat_tui.executor import execute_function

        result = execute_function("error_demo", kwargs={"message": "Test error"})
        assert result.success is False
        assert "Test error" in result.error

    def test_system_info(self):
        """Test the system info function."""
        from hojjat_tui.executor import execute_function

        result = execute_function("system_info")
        assert result.success
        assert isinstance(result.output, dict)
        assert "python_version" in result.output

    def test_ping_test_output(self):
        """Test the ping test function returns table data."""
        from hojjat_tui.executor import execute_function

        result = execute_function("ping_test", kwargs={"host": "localhost", "count": 2})
        assert result.success
        assert isinstance(result.output, list)
        assert len(result.output) == 2
        assert result.output[0]["host"] == "localhost"

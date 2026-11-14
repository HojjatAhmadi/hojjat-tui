"""Tests for project initialization and manage.py entry point architecture."""

import sys
from pathlib import Path

import pytest


def _setup_test_path(tmp_path, monkeypatch):
    """Add src and tmp_path to sys.path, change to tmp_path."""
    monkeypatch.chdir(tmp_path)
    src_path = str(Path(__file__).parent.parent / "src")
    if src_path not in sys.path:
        sys.path.insert(0, src_path)
    tmp_str = str(tmp_path)
    if tmp_str not in sys.path:
        sys.path.insert(0, tmp_str)


def _clear_registry():
    """Clear the function registry for test isolation."""
    from hojjat_tui.function import _REGISTRY

    for name in list(_REGISTRY.keys()):
        del _REGISTRY[name]


def _clear_example_module():
    """Remove functions package modules from sys.modules to force re-import."""
    for mod_name in list(sys.modules.keys()):
        if mod_name == "functions" or mod_name.startswith("functions."):
            del sys.modules[mod_name]


class TestProjectInitialization:
    """Tests for hojjat-tui init project creation."""

    def test_init_creates_expected_structure(self, tmp_path, monkeypatch):
        """init creates manage.py, functions/, functions/__init__.py, functions/example.py."""
        _setup_test_path(tmp_path, monkeypatch)

        from hojjat_tui.management import init_project

        result = init_project()
        assert result is True

        # Check structure
        assert (tmp_path / "manage.py").is_file()
        assert (tmp_path / "functions").is_dir()
        assert (tmp_path / "functions" / "__init__.py").is_file()
        assert (tmp_path / "functions" / "example.py").is_file()

    def test_init_creates_manage_py_with_run_import(self, tmp_path, monkeypatch):
        """Generated manage.py imports run from hojjat_tui."""
        _setup_test_path(tmp_path, monkeypatch)

        from hojjat_tui.management import init_project

        init_project()
        manage_py = tmp_path / "manage.py"
        content = manage_py.read_text(encoding="utf-8")

        assert "from hojjat_tui import run" in content
        assert "from functions import example" in content
        assert 'if __name__ == "__main__":' in content
        assert "run()" in content

    def test_init_creates_example_py_with_four_examples(self, tmp_path, monkeypatch):
        """Generated example.py contains the required example functions."""
        _setup_test_path(tmp_path, monkeypatch)

        from hojjat_tui.management import init_project

        init_project()
        example_py = tmp_path / "functions" / "example.py"
        content = example_py.read_text(encoding="utf-8")

        # Check all required example functions exist
        assert "def hello_world" in content
        assert "def sample_data" in content
        assert "def sales_by_region" in content
        assert "def temperature_trend" in content
        assert "def greet_user" in content

        # Check they are decorated with @hojjat_function
        assert "@hojjat_function" in content

        # Check ChartOutput is imported
        assert "ChartOutput" in content

    def test_init_does_not_overwrite_existing_files(self, tmp_path, monkeypatch):
        """init does not overwrite existing files."""
        _setup_test_path(tmp_path, monkeypatch)

        from hojjat_tui.management import init_project

        # Run init once
        result1 = init_project()
        assert result1 is True

        # Modify manage.py
        manage_py = tmp_path / "manage.py"
        original_content = manage_py.read_text(encoding="utf-8")
        modified_content = original_content + "\n# CUSTOM MODIFICATION\n"
        manage_py.write_text(modified_content, encoding="utf-8")

        # Run init again - should not overwrite
        result2 = init_project()
        assert result2 is True

        # File should still have custom modification
        assert manage_py.read_text(encoding="utf-8") == modified_content

    def test_init_is_idempotent(self, tmp_path, monkeypatch):
        """Running init more than once is safe."""
        _setup_test_path(tmp_path, monkeypatch)

        from hojjat_tui.management import init_project

        result1 = init_project()
        result2 = init_project()
        result3 = init_project()

        assert result1 is True
        assert result2 is True
        assert result3 is True

    def test_init_does_not_create_database(self, tmp_path, monkeypatch):
        """init does not initialize or create a database."""
        _setup_test_path(tmp_path, monkeypatch)

        from hojjat_tui.management import init_project

        init_project()

        # No database file should be created in the project directory
        db_files = list(tmp_path.glob("*.db"))
        assert len(db_files) == 0


class TestManagePyEntryPoint:
    """Tests for manage.py entry point execution."""

    def test_manage_py_is_executable_python(self, tmp_path, monkeypatch):
        """Generated manage.py can be imported as a Python module."""
        _setup_test_path(tmp_path, monkeypatch)

        from hojjat_tui.management import init_project

        init_project()

        # Verify manage.py is valid Python syntax
        import py_compile

        py_compile.compile(str(tmp_path / "manage.py"), doraise=True)

    def test_manage_py_imports_run_from_hojjat_tui(self, tmp_path, monkeypatch):
        """manage.py uses `from hojjat_tui import run`."""
        _setup_test_path(tmp_path, monkeypatch)

        from hojjat_tui.management import init_project

        init_project()
        content = (tmp_path / "manage.py").read_text(encoding="utf-8")
        assert "from hojjat_tui import run" in content

    def test_manage_py_imports_example_module(self, tmp_path, monkeypatch):
        """manage.py imports functions.example."""
        _setup_test_path(tmp_path, monkeypatch)

        from hojjat_tui.management import init_project

        init_project()
        content = (tmp_path / "manage.py").read_text(encoding="utf-8")
        assert "from functions import example" in content


class TestExampleFunctions:
    """Tests for the example functions in functions/example.py."""

    def _import_example(self, tmp_path, monkeypatch):
        """Helper: init project, clear registry, import functions.example."""
        _setup_test_path(tmp_path, monkeypatch)

        from hojjat_tui.management import init_project

        init_project()
        _clear_registry()
        _clear_example_module()

        import functions.example

    def test_example_functions_register(self, tmp_path, monkeypatch):
        """All example functions register when example module is imported."""
        self._import_example(tmp_path, monkeypatch)

        from hojjat_tui.function import get_registry

        registry = get_registry()

        # All required functions should be registered
        assert "hello_world" in registry
        assert "sample_data" in registry
        assert "sales_by_region" in registry
        assert "temperature_trend" in registry
        assert "greet_user" in registry

    def test_hello_world_returns_string(self, tmp_path, monkeypatch):
        """hello_world returns a plain string."""
        self._import_example(tmp_path, monkeypatch)

        from hojjat_tui.executor import execute_function

        result = execute_function("hello_world")
        assert result.success
        assert isinstance(result.output, str)
        assert result.output == "Hello from HOJJAT TUI!"
        assert result.type == "text"

    def test_sample_data_returns_table(self, tmp_path, monkeypatch):
        """sample_data returns a list of dicts (table output)."""
        self._import_example(tmp_path, monkeypatch)

        from hojjat_tui.executor import execute_function

        result = execute_function("sample_data")
        assert result.success
        assert isinstance(result.output, list)
        assert len(result.output) == 4
        assert result.output[0]["name"] == "Project Alpha"
        assert result.type == "table"

    def test_bar_chart_returns_chart_output(self, tmp_path, monkeypatch):
        """sales_by_region returns a ChartOutput with chart_type='bar'."""
        self._import_example(tmp_path, monkeypatch)

        from hojjat_tui.executor import execute_function
        from hojjat_tui.function import ChartOutput

        result = execute_function("sales_by_region")
        assert result.success
        assert isinstance(result.output, ChartOutput)
        assert result.output.chart_type == "bar"
        assert len(result.output.labels) == 5
        assert len(result.output.values) == 5
        assert result.output.title == "Regional Sales Q3"

    def test_line_chart_returns_chart_output(self, tmp_path, monkeypatch):
        """temperature_trend returns a ChartOutput with chart_type='line'."""
        self._import_example(tmp_path, monkeypatch)

        from hojjat_tui.executor import execute_function
        from hojjat_tui.function import ChartOutput

        result = execute_function("temperature_trend")
        assert result.success
        assert isinstance(result.output, ChartOutput)
        assert result.output.chart_type == "line"
        assert len(result.output.labels) == 7
        assert len(result.output.values) == 7
        assert result.output.title == "Weekly Temperature"

    def test_greet_user_accepts_parameter(self, tmp_path, monkeypatch):
        """greet_user accepts a name parameter and uses it."""
        self._import_example(tmp_path, monkeypatch)

        from hojjat_tui.executor import execute_function

        result = execute_function("greet_user", kwargs={"name": "Alice"})
        assert result.success
        assert isinstance(result.output, str)
        assert result.output == "Hello Alice!"

        # Test with default
        result2 = execute_function("greet_user", kwargs={"name": "Bob"})
        assert result2.success
        assert result2.output == "Hello Bob!"

    def test_all_examples_in_registry(self, tmp_path, monkeypatch):
        """All example functions appear in the registry after import."""
        self._import_example(tmp_path, monkeypatch)

        from hojjat_tui.function import get_registry

        registry = get_registry()
        expected = {"hello_world", "sample_data", "sales_by_region", "temperature_trend", "greet_user"}
        assert expected.issubset(set(registry.keys()))


class TestCliNoArgsBehavior:
    """Tests for hojjat-tui with no arguments (TUI startup via manage.py)."""

    def test_no_manage_py_shows_helpful_error(self, tmp_path, monkeypatch, capsys):
        """Running hojjat-tui without manage.py shows actionable error."""
        _setup_test_path(tmp_path, monkeypatch)

        from hojjat_tui.cli import main

        with pytest.raises(SystemExit) as exc_info:
            main([])

        assert exc_info.value.code == 1
        captured = capsys.readouterr()
        assert "No manage.py found" in captured.out
        assert "hojjat-tui init" in captured.out


class TestRefreshBehavior:
    """Tests for Refresh behavior with new architecture."""

    def test_refresh_reads_registry_without_rerunning_manage_py(self, tmp_path, monkeypatch):
        """refresh_functions reads registry without re-executing manage.py."""
        _setup_test_path(tmp_path, monkeypatch)

        from hojjat_tui.management import init_project
        from hojjat_tui.function import _REGISTRY, get_registry, load_function_modules

        init_project()
        _clear_registry()
        _clear_example_module()

        import functions.example

        # Verify functions are registered
        registry = get_registry()
        assert "hello_world" in registry

        # Refresh should not duplicate registrations
        loaded, errors = load_function_modules()
        assert loaded == []  # Already loaded, skipped

        registry2 = get_registry()
        assert "hello_world" in registry2
        assert len(registry2) == len(registry)  # No duplicates


class TestChartOutput:
    """Tests for native Chart output detection and validation."""

    def test_chart_output_detected_as_chart_type(self, tmp_path, monkeypatch):
        """ChartOutput is detected as 'chart' output type."""
        _setup_test_path(tmp_path, monkeypatch)

        from hojjat_tui.function import ChartOutput
        from hojjat_tui.executor import _detect_output_type

        chart = ChartOutput(
            chart_type="bar",
            labels=["Jan", "Feb", "Mar"],
            values=[100, 150, 200],
        )
        assert _detect_output_type(chart) == "chart"

    def test_ordinary_list_detected_as_table(self, tmp_path, monkeypatch):
        """Ordinary list of dicts is still detected as 'table', not 'chart'."""
        _setup_test_path(tmp_path, monkeypatch)

        from hojjat_tui.executor import _detect_output_type

        data = [{"a": 1, "b": 2}, {"a": 3, "b": 4}]
        assert _detect_output_type(data) == "table"

    def test_list_of_numbers_detected_as_table(self, tmp_path, monkeypatch):
        """List of numbers is detected as 'table', not 'chart'."""
        _setup_test_path(tmp_path, monkeypatch)

        from hojjat_tui.executor import _detect_output_type

        data = [1, 2, 3, 4]
        assert _detect_output_type(data) == "table"

    def test_chart_output_invalid_type_raises(self, tmp_path, monkeypatch):
        """Invalid chart_type raises ValueError."""
        _setup_test_path(tmp_path, monkeypatch)

        from hojjat_tui.function import ChartOutput

        with pytest.raises(ValueError, match="Invalid chart type"):
            ChartOutput(
                chart_type="pie",
                labels=["a", "b"],
                values=[1, 2],
            )

    def test_chart_output_mismatched_lengths_raises(self, tmp_path, monkeypatch):
        """Mismatched labels and values lengths raises ValueError."""
        _setup_test_path(tmp_path, monkeypatch)

        from hojjat_tui.function import ChartOutput

        with pytest.raises(ValueError, match="same length"):
            ChartOutput(
                chart_type="bar",
                labels=["a", "b", "c"],
                values=[1, 2],
            )

    def test_chart_output_empty_labels_raises(self, tmp_path, monkeypatch):
        """Empty labels raises ValueError."""
        _setup_test_path(tmp_path, monkeypatch)

        from hojjat_tui.function import ChartOutput

        with pytest.raises(ValueError, match="at least one"):
            ChartOutput(
                chart_type="bar",
                labels=[],
                values=[],
            )


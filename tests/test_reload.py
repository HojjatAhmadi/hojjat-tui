"""Tests for the project hot reload / refresh system.

Tests cover:
- Detecting newly added functions in existing modules
- Detecting modified function implementations
- Detecting changed function signatures (parameters, defaults, annotations)
- Detecting deleted functions
- Detecting new Python modules
- Detecting deleted Python modules
- No duplicate registrations on repeated refresh
- Error recovery when a module has a syntax error
"""

import sys
import time
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


def _clear_registry_and_loaded():
    """Clear the function registry and loaded module tracker for test isolation."""
    from hojjat_tui.function import (
        _REGISTRY, _LOADED_MODULES, _MODULE_TIMESTAMPS, _MODULE_FILE_PATHS,
    )

    for name in list(_REGISTRY.keys()):
        del _REGISTRY[name]
    _LOADED_MODULES.clear()
    _MODULE_TIMESTAMPS.clear()
    _MODULE_FILE_PATHS.clear()
    # Remove from sys.modules to force re-import
    for mod_name in list(sys.modules.keys()):
        if mod_name.startswith("mod_"):
            del sys.modules[mod_name]


def _write_module(tmp_path, name, code):
    """Write a Python module file directly in tmp_path."""
    (tmp_path / f"{name}.py").write_text(code, encoding="utf-8")


def _write_pyproject(tmp_path, modules=None):
    """Write a pyproject.toml with optional function_modules."""
    if modules is None:
        modules = []
    mod_list = ", ".join(f'"{m}"' for m in modules)
    content = f'[tool.hojjat-tui]\nfunction_modules = [{mod_list}]\n'
    (tmp_path / "pyproject.toml").write_text(content, encoding="utf-8")


class TestReloadBasics:
    """Tests for basic reload functionality."""

    def test_no_changes_detected(self, tmp_path, monkeypatch):
        """Refresh with no changes reports 'No changes detected.'"""
        _setup_test_path(tmp_path, monkeypatch)
        _write_pyproject(tmp_path, ["mod_a"])
        _write_module(
            tmp_path, "mod_a",
            '''
from hojjat_tui.function import hojjat_function

@hojjat_function(name="func_a")
def func_a():
    return "hello from a"
''',
        )
        monkeypatch.chdir(tmp_path)
        sys.path.insert(0, str(tmp_path))

        from hojjat_tui.function import (
            _REGISTRY, load_function_modules, reload_function_modules,
            get_registry,
        )
        _clear_registry_and_loaded()
        load_function_modules()
        assert "func_a" in get_registry()

        # Small sleep to ensure mtime is stable
        time.sleep(0.05)

        # Second refresh — no changes
        result = reload_function_modules()
        assert result["added"] == []
        assert result["updated"] == []
        assert result["removed"] == []
        assert result["errors"] == []
        assert "No changes detected" in result["summary"]

    def test_reload_no_duplicates(self, tmp_path, monkeypatch):
        """Multiple refreshes do not create duplicate registrations."""
        _setup_test_path(tmp_path, monkeypatch)
        _write_pyproject(tmp_path, ["mod_b"])
        _write_module(
            tmp_path, "mod_b",
            '''
from hojjat_tui.function import hojjat_function

@hojjat_function(name="func_b")
def func_b():
    return "b"
''',
        )
        monkeypatch.chdir(tmp_path)
        sys.path.insert(0, str(tmp_path))

        from hojjat_tui.function import (
            _REGISTRY, load_function_modules, reload_function_modules,
            get_registry,
        )
        _clear_registry_and_loaded()
        load_function_modules()
        assert len(get_registry()) == 1

        # Refresh three times — should still be 1 function
        for _ in range(3):
            reload_function_modules()

        assert len(get_registry()) == 1
        assert "func_b" in get_registry()


class TestReloadNewFunction:
    """Tests for detecting newly added functions."""

    def test_new_function_in_existing_module(self, tmp_path, monkeypatch):
        """Adding a function to an existing module is detected on refresh."""
        _setup_test_path(tmp_path, monkeypatch)
        _write_pyproject(tmp_path, ["mod_c"])
        _write_module(
            tmp_path, "mod_c",
            '''
from hojjat_tui.function import hojjat_function

@hojjat_function(name="func_c1")
def func_c1():
    return "c1"
''',
        )
        monkeypatch.chdir(tmp_path)
        sys.path.insert(0, str(tmp_path))

        from hojjat_tui.function import (
            _REGISTRY, load_function_modules, reload_function_modules,
            get_registry,
        )
        from hojjat_tui.executor import execute_function

        _clear_registry_and_loaded()
        load_function_modules()
        assert "func_c1" in get_registry()
        assert "func_c2" not in get_registry()

        # Add a new function to the module
        new_code = '''
from hojjat_tui.function import hojjat_function

@hojjat_function(name="func_c1")
def func_c1():
    return "c1"

@hojjat_function(name="func_c2")
def func_c2():
    return "c2"
'''
        _write_module(tmp_path, "mod_c", new_code)
        time.sleep(0.05)

        result = reload_function_modules()
        # The module was reloaded (updated), not added
        assert "mod_c" in result["updated"], f"Expected mod_c in updated, got {result}"
        assert "func_c2" in get_registry()

        # Verify the new function executes
        exec_result = execute_function("func_c2")
        assert exec_result.success
        assert exec_result.output == "c2"


class TestReloadModifiedFunction:
    """Tests for detecting modified function implementations."""

    def test_modified_function_implementation(self, tmp_path, monkeypatch):
        """Modifying a function's implementation is detected on refresh."""
        _setup_test_path(tmp_path, monkeypatch)
        _write_pyproject(tmp_path, ["mod_d"])
        _write_module(
            tmp_path, "mod_d",
            '''
from hojjat_tui.function import hojjat_function

@hojjat_function(name="func_d")
def func_d():
    return "original"
''',
        )
        monkeypatch.chdir(tmp_path)
        sys.path.insert(0, str(tmp_path))

        from hojjat_tui.function import (
            _REGISTRY, load_function_modules, reload_function_modules,
            get_registry,
        )
        from hojjat_tui.executor import execute_function

        _clear_registry_and_loaded()
        load_function_modules()
        assert execute_function("func_d").output == "original"

        # Modify the implementation
        new_code = '''
from hojjat_tui.function import hojjat_function

@hojjat_function(name="func_d")
def func_d():
    return "modified!"
'''
        _write_module(tmp_path, "mod_d", new_code)
        time.sleep(0.05)

        result = reload_function_modules()
        assert "mod_d" in result["updated"], f"Expected mod_d in updated, got {result}"
        exec_result = execute_function("func_d")
        assert exec_result.success
        assert exec_result.output == "modified!", f"Expected 'modified!', got {exec_result.output}"


class TestReloadChangedSignature:
    """Tests for detecting changed function signatures."""

    def test_added_parameter(self, tmp_path, monkeypatch):
        """Adding a parameter to a function is detected on refresh."""
        _setup_test_path(tmp_path, monkeypatch)
        _write_pyproject(tmp_path, ["mod_e"])
        _write_module(
            tmp_path, "mod_e",
            '''
from hojjat_tui.function import hojjat_function

@hojjat_function(name="func_e")
def func_e(x: int = 0) -> int:
    return x
''',
        )
        monkeypatch.chdir(tmp_path)
        sys.path.insert(0, str(tmp_path))

        from hojjat_tui.function import (
            _REGISTRY, load_function_modules, reload_function_modules,
            get_registry,
        )
        _clear_registry_and_loaded()
        load_function_modules()

        registry = get_registry()
        sig = registry["func_e"]["signature"]
        assert "y" not in sig.parameters

        # Add a parameter
        new_code = '''
from hojjat_tui.function import hojjat_function

@hojjat_function(name="func_e")
def func_e(x: int = 0, y: str = "default") -> str:
    return f"{x}:{y}"
'''
        _write_module(tmp_path, "mod_e", new_code)
        time.sleep(0.05)

        reload_function_modules()
        registry = get_registry()
        sig = registry["func_e"]["signature"]
        assert "y" in sig.parameters
        assert sig.parameters["y"].annotation == str


class TestReloadDeletedFunction:
    """Tests for detecting deleted functions."""

    def test_deleted_function_removed(self, tmp_path, monkeypatch):
        """Deleting a function from a module removes it from the registry."""
        _setup_test_path(tmp_path, monkeypatch)
        _write_pyproject(tmp_path, ["mod_f"])
        _write_module(
            tmp_path, "mod_f",
            '''
from hojjat_tui.function import hojjat_function

@hojjat_function(name="func_f_keep")
def func_f_keep():
    return "keep"

@hojjat_function(name="func_f_delete")
def func_f_delete():
    return "delete me"
''',
        )
        monkeypatch.chdir(tmp_path)
        sys.path.insert(0, str(tmp_path))

        from hojjat_tui.function import (
            _REGISTRY, load_function_modules, reload_function_modules,
            get_registry,
        )
        _clear_registry_and_loaded()
        load_function_modules()
        assert "func_f_delete" in get_registry()

        # Delete the function
        new_code = '''
from hojjat_tui.function import hojjat_function

@hojjat_function(name="func_f_keep")
def func_f_keep():
    return "keep"
'''
        _write_module(tmp_path, "mod_f", new_code)
        time.sleep(0.05)

        result = reload_function_modules()
        # The module was reloaded (updated), not removed (file still exists)
        assert "mod_f" in result["updated"], f"Expected mod_f in updated, got {result}"
        assert "func_f_delete" not in get_registry()
        assert "func_f_keep" in get_registry()


class TestReloadNewModule:
    """Tests for detecting new Python modules."""

    def test_new_module_discovered(self, tmp_path, monkeypatch):
        """Creating a new module file is detected on refresh."""
        _setup_test_path(tmp_path, monkeypatch)
        # Configure the module in pyproject.toml so it's discoverable
        _write_pyproject(tmp_path, ["mod_g"])
        monkeypatch.chdir(tmp_path)
        sys.path.insert(0, str(tmp_path))

        from hojjat_tui.function import (
            reload_function_modules, get_registry,
        )
        _clear_registry_and_loaded()

        # Module doesn't exist yet — first refresh finds nothing new
        result = reload_function_modules()
        assert result["added"] == []

        # Create the module
        _write_module(tmp_path, "mod_g",
            '''
from hojjat_tui.function import hojjat_function

@hojjat_function(name="func_g")
def func_g():
    return "g"
''',
        )
        time.sleep(0.05)

        result = reload_function_modules()
        assert "mod_g" in result["added"], f"Expected mod_g in added, got {result}"
        assert "func_g" in get_registry()


class TestReloadDeletedModule:
    """Tests for detecting deleted Python modules."""

    def test_deleted_module_removed(self, tmp_path, monkeypatch):
        """Deleting a module file removes its functions from the registry."""
        _setup_test_path(tmp_path, monkeypatch)
        monkeypatch.chdir(tmp_path)
        sys.path.insert(0, str(tmp_path))

        from hojjat_tui.function import (
            load_function_modules, reload_function_modules,
            get_registry,
        )
        _clear_registry_and_loaded()

        # Create and configure a module
        _write_pyproject(tmp_path, ["mod_h"])
        _write_module(tmp_path, "mod_h",
            '''
from hojjat_tui.function import hojjat_function

@hojjat_function(name="func_h")
def func_h():
    return "h"
''',
        )
        load_function_modules()
        assert "func_h" in get_registry()

        # Remove from pyproject.toml AND delete the file
        _write_pyproject(tmp_path, [])  # No configured modules
        mod_file = tmp_path / "mod_h.py"
        mod_file.unlink()
        time.sleep(0.05)

        result = reload_function_modules()
        assert "mod_h" in result["removed"], f"Expected mod_h in removed, got {result}"
        assert "func_h" not in get_registry()


class TestReloadErrorRecovery:
    """Tests for error recovery during reload."""

    def test_syntax_error_does_not_crash(self, tmp_path, monkeypatch):
        """A syntax error in a module does not crash the reload or corrupt the registry."""
        _setup_test_path(tmp_path, monkeypatch)
        _write_pyproject(tmp_path, ["mod_i"])
        _write_module(
            tmp_path, "mod_i",
            '''
from hojjat_tui.function import hojjat_function

@hojjat_function(name="func_i")
def func_i():
    return "i"
''',
        )
        monkeypatch.chdir(tmp_path)
        sys.path.insert(0, str(tmp_path))

        from hojjat_tui.function import (
            _REGISTRY, load_function_modules, reload_function_modules,
            get_registry,
        )
        from hojjat_tui.executor import execute_function

        _clear_registry_and_loaded()
        load_function_modules()
        assert "func_i" in get_registry()
        assert execute_function("func_i").output == "i"

        # Introduce a syntax error
        new_code = '''
from hojjat_tui.function import hojjat_function

@hojjat_function(name="func_i")
def func_i(
    return "broken syntax"
'''
        _write_module(tmp_path, "mod_i", new_code)
        time.sleep(0.05)

        result = reload_function_modules()
        assert len(result["errors"]) > 0, f"Expected errors, got {result}"
        # The old registry should be preserved
        assert "func_i" in get_registry()
        assert execute_function("func_i").output == "i"


class TestStartupIntegration:
    """Integration tests for project startup and refresh recovery."""

    def test_startup_populates_registry_from_manage_py(self, tmp_path, monkeypatch):
        """Functions imported by manage.py appear in the registry at startup."""
        _setup_test_path(tmp_path, monkeypatch)

        # Create a minimal project structure
        _write_pyproject(tmp_path, [])
        _write_module(tmp_path, "my_functions",
            '''
from hojjat_tui.function import hojjat_function

@hojjat_function(name="startup_func")
def startup_func():
    return "startup"
''',
        )
        monkeypatch.chdir(tmp_path)
        sys.path.insert(0, str(tmp_path))

        from hojjat_tui.function import get_registry, load_function_modules

        _clear_registry_and_loaded()

        # Simulate what manage.py does: import the module, triggering decorators
        import my_functions

        # Functions from the module should be in the registry
        registry = get_registry()
        assert "startup_func" in registry, f"Expected startup_func in registry, got {list(registry.keys())}"

        # load_function_modules should populate tracking state for configured modules
        loaded, errors = load_function_modules()
        assert "startup_func" in get_registry()

    def test_explicit_module_registration(self, tmp_path, monkeypatch):
        """Modules listed in pyproject.toml function_modules load at startup."""
        _setup_test_path(tmp_path, monkeypatch)
        _write_pyproject(tmp_path, ["explicit_mod"])
        _write_module(
            tmp_path, "explicit_mod",
            '''
from hojjat_tui.function import hojjat_function

@hojjat_function(name="explicit_func")
def explicit_func():
    return "explicit"
''',
        )
        monkeypatch.chdir(tmp_path)
        sys.path.insert(0, str(tmp_path))

        from hojjat_tui.function import (
            load_function_modules, reload_function_modules,
            get_registry,
        )
        _clear_registry_and_loaded()

        loaded, errors = load_function_modules()
        assert "explicit_mod" in loaded, f"Expected explicit_mod in loaded, got {loaded}"
        assert errors == [], f"Expected no errors, got {errors}"
        assert "explicit_func" in get_registry()

    def test_automatic_discovery_of_functions_directory(self, tmp_path, monkeypatch):
        """Modules in functions/ directory are discovered automatically."""
        _setup_test_path(tmp_path, monkeypatch)
        _write_pyproject(tmp_path, [])  # No configured modules
        monkeypatch.chdir(tmp_path)
        sys.path.insert(0, str(tmp_path))

        from hojjat_tui.function import (
            scan_functions_directory, reload_function_modules, get_registry,
            _REGISTRY, _LOADED_MODULES, _MODULE_TIMESTAMPS, _MODULE_FILE_PATHS,
        )
        _clear_registry_and_loaded()

        # Clean up any leftover 'functions' package from other tests
        for mod_name in list(sys.modules.keys()):
            if mod_name == "functions" or mod_name.startswith("functions."):
                del sys.modules[mod_name]

        # Create a module in functions/
        functions_dir = tmp_path / "functions"
        functions_dir.mkdir()
        (functions_dir / "__init__.py").write_text("", encoding="utf-8")
        (functions_dir / "discovered_mod.py").write_text(
            '''
from hojjat_tui.function import hojjat_function

@hojjat_function(name="discovered_func")
def discovered_func():
    return "discovered"
''',
            encoding="utf-8",
        )

        # scan_functions_directory should find it
        discovered = scan_functions_directory()
        assert "functions.discovered_mod" in discovered, f"Expected functions.discovered_mod in {discovered}"

        # reload_function_modules should load it
        result = reload_function_modules()
        assert "functions.discovered_mod" in result["added"], f"Expected added, got {result}"
        assert "discovered_func" in get_registry()

    def test_refresh_recovery_empty_registry(self, tmp_path, monkeypatch):
        """Refresh restores functions when registry is empty but modules exist."""
        _setup_test_path(tmp_path, monkeypatch)
        _write_pyproject(tmp_path, ["recovery_mod"])
        _write_module(
            tmp_path, "recovery_mod",
            '''
from hojjat_tui.function import hojjat_function

@hojjat_function(name="recovery_func")
def recovery_func():
    return "recovered"
''',
        )
        monkeypatch.chdir(tmp_path)
        sys.path.insert(0, str(tmp_path))

        from hojjat_tui.function import (
            load_function_modules, reload_function_modules,
            get_registry, _REGISTRY,
        )
        _clear_registry_and_loaded()

        # Load normally first
        load_function_modules()
        assert "recovery_func" in get_registry()

        # Simulate an empty registry (e.g., corrupted state)
        _REGISTRY.clear()
        assert len(get_registry()) == 0

        # Refresh should recover the functions
        result = reload_function_modules()
        # The module was re-imported (functions restored) but since timestamps
        # didn't change, it's not reported as "added" or "updated".
        assert "recovery_func" in get_registry(), f"Expected recovery_func restored, got {list(get_registry().keys())}"

    def test_reload_multiple_times_no_duplicates(self, tmp_path, monkeypatch):
        """Multiple refreshes don't create duplicate registrations."""
        _setup_test_path(tmp_path, monkeypatch)
        _write_pyproject(tmp_path, ["multi_mod"])
        _write_module(
            tmp_path, "multi_mod",
            '''
from hojjat_tui.function import hojjat_function

@hojjat_function(name="multi_func")
def multi_func():
    return "multi"
''',
        )
        monkeypatch.chdir(tmp_path)
        sys.path.insert(0, str(tmp_path))

        from hojjat_tui.function import (
            load_function_modules, reload_function_modules, get_registry,
        )
        _clear_registry_and_loaded()

        load_function_modules()
        assert len(get_registry()) == 1

        # Reload 5 times
        for _ in range(5):
            reload_function_modules()

        assert len(get_registry()) == 1
        assert "multi_func" in get_registry()


class TestRefreshEmptyModules:
    """Tests for Refresh behavior when no modules are configured or discovered."""

    def test_refresh_empty_modules_preserves_registry(self, tmp_path, monkeypatch):
        """Refresh with no configured/discovered modules must not clear the registry.

        Functions registered via direct imports (not tracked by module discovery)
        must survive a Refresh even when all_modules is empty.
        """
        _setup_test_path(tmp_path, monkeypatch)
        # No pyproject.toml → no configured modules, no discovered modules
        monkeypatch.chdir(tmp_path)
        sys.path.insert(0, str(tmp_path))

        from hojjat_tui.function import (
            hojjat_function, load_function_modules, reload_function_modules,
            get_registry, _REGISTRY,
        )
        _clear_registry_and_loaded()

        # Register a function directly (simulating what manage.py does via imports)
        @hojjat_function(name="direct_func")
        def direct_func():
            return "direct"

        assert "direct_func" in get_registry()

        # Refresh with no modules configured/discovered
        result = reload_function_modules()
        assert result["added"] == []
        assert result["updated"] == []
        assert result["removed"] == []
        assert result["errors"] == []
        assert "No changes detected" in result["summary"]

        # Registry must be preserved
        assert "direct_func" in get_registry()
        assert get_registry()["direct_func"]["label"] == "direct_func"

    def test_refresh_empty_modules_no_crash(self, tmp_path, monkeypatch):
        """Refresh with empty registry and empty modules doesn't crash."""
        _setup_test_path(tmp_path, monkeypatch)
        monkeypatch.chdir(tmp_path)
        sys.path.insert(0, str(tmp_path))

        from hojjat_tui.function import (
            reload_function_modules, get_registry,
        )
        _clear_registry_and_loaded()

        # Registry is empty, no modules configured
        result = reload_function_modules()
        assert result["summary"] == "No changes detected."
        assert len(get_registry()) == 0

    def test_registry_identity_consistent(self, tmp_path, monkeypatch):
        """get_registry() always returns the same underlying _REGISTRY object."""
        _setup_test_path(tmp_path, monkeypatch)
        monkeypatch.chdir(tmp_path)
        sys.path.insert(0, str(tmp_path))

        from hojjat_tui.function import (
            _REGISTRY, get_registry, load_function_modules,
        )
        _clear_registry_and_loaded()

        load_function_modules()
        first = get_registry()
        second = get_registry()
        assert first == second
        assert set(first.keys()) == set(_REGISTRY.keys())


class TestStartupPopulation:
    """Tests for startup population of the function list UI."""

    def test_on_mount_populates_function_list(self, tmp_path, monkeypatch):
        """on_mount() must call update_function_list() so the OptionList
        shows all registered functions immediately at startup."""
        _setup_test_path(tmp_path, monkeypatch)

        # Register some functions
        from hojjat_tui.function import (
            hojjat_function, get_registry, _REGISTRY,
        )
        _clear_registry_and_loaded()

        @hojjat_function(name="startup_func_1")
        def startup_func_1():
            return "one"

        @hojjat_function(name="startup_func_2")
        def startup_func_2():
            return "two"

        # Verify registry has functions
        assert len(get_registry()) == 2

        # Create app and verify update_function_list populates OptionList
        from hojjat_tui.tui import HojjatTUIApplication
        app = HojjatTUIApplication()
        app.registry = get_registry()

        async def run_test():
            async with app.run_test() as pilot:
                # on_mount should have called update_function_list
                menu = app.query_one("#function-list")
                assert menu.option_count == 2, f"Expected 2 options, got {menu.option_count}"
                option_ids = [o.id for o in menu._options]
                assert "startup_func_1" in option_ids
                assert "startup_func_2" in option_ids

        import asyncio
        asyncio.run(run_test())

    def test_empty_registry_shows_no_functions(self, tmp_path, monkeypatch):
        """When no functions are registered, update_function_list() shows
        'No functions available' placeholder."""
        _setup_test_path(tmp_path, monkeypatch)

        from hojjat_tui.function import (
            _REGISTRY, get_registry,
        )
        _clear_registry_and_loaded()

        assert len(get_registry()) == 0

        from hojjat_tui.tui import HojjatTUIApplication
        app = HojjatTUIApplication()
        app.registry = {}

        async def run_test():
            async with app.run_test() as pilot:
                menu = app.query_one("#function-list")
                assert menu.option_count == 1
                assert menu._options[0].disabled

        import asyncio
        asyncio.run(run_test())
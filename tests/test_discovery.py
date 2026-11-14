"""Tests for automatic function module discovery and loading."""

import importlib
import sys
import tempfile
from pathlib import Path

import pytest
from hojjat_tui.function import (
    _LOADED_MODULES,
    get_loaded_modules,
    get_registry,
    hojjat_function,
    load_function_modules,
    read_function_modules,
)


def _write_pyproject(tmp_path: Path, modules):
    """Write a pyproject.toml with the given function_modules."""
    mod_list = ", ".join(f'"{m}"' for m in modules)
    content = f'[tool.hojjat-tui]\nfunction_modules = [{mod_list}]\n'
    (tmp_path / "pyproject.toml").write_text(content, encoding="utf-8")


def _write_module(tmp_path: Path, name: str, code: str):
    """Write a Python module file in tmp_path."""
    (tmp_path / f"{name}.py").write_text(code, encoding="utf-8")


def _clear_registry_and_loaded():
    """Clear the registry and loaded module tracker for test isolation."""
    from hojjat_tui.function import _REGISTRY

    for name in list(_REGISTRY.keys()):
        del _REGISTRY[name]
    _LOADED_MODULES.clear()
    # Also remove from sys.modules to force re-import
    for mod_name in list(sys.modules.keys()):
        if mod_name.startswith("test_mod_") or mod_name == "user_main":
            del sys.modules[mod_name]


class TestReadFunctionModules:
    """Tests for reading function_modules from pyproject.toml."""

    def test_reads_configured_modules(self, tmp_path, monkeypatch):
        _write_pyproject(tmp_path, ["main", "utils"])
        monkeypatch.chdir(tmp_path)
        modules = read_function_modules()
        assert "main" in modules
        assert "utils" in modules

    def test_returns_empty_when_no_config(self, tmp_path, monkeypatch):
        # No pyproject.toml
        monkeypatch.chdir(tmp_path)
        modules = read_function_modules()
        assert modules == []

    def test_returns_empty_when_no_hojjat_section(self, tmp_path, monkeypatch):
        (tmp_path / "pyproject.toml").write_text(
            '[project]\nname = "test"\nversion = "0.1.0"\n', encoding="utf-8"
        )
        monkeypatch.chdir(tmp_path)
        modules = read_function_modules()
        assert modules == []

    def test_single_module_string(self, tmp_path, monkeypatch):
        (tmp_path / "pyproject.toml").write_text(
            '[tool.hojjat-tui]\nfunction_modules = "main"\n', encoding="utf-8"
        )
        monkeypatch.chdir(tmp_path)
        modules = read_function_modules()
        assert modules == ["main"]


class TestLoadFunctionModules:
    """Tests for loading configured function modules."""

    def test_loads_module_with_decorated_function(self, tmp_path, monkeypatch):
        _write_pyproject(tmp_path, ["user_main"])
        _write_module(
            tmp_path,
            "user_main",
            '''
from hojjat_tui.function import hojjat_function

@hojjat_function(name="say_hello", description="Say hello")
def say_hello(name: str) -> str:
    return f"Hello {name}!"
''',
        )
        monkeypatch.chdir(tmp_path)
        sys.path.insert(0, str(tmp_path))

        _clear_registry_and_loaded()
        loaded, errors = load_function_modules()

        assert "user_main" in loaded
        assert errors == []
        assert "say_hello" in get_registry()

    def test_loads_package_with_decorated_functions(self, tmp_path, monkeypatch):
        _write_pyproject(tmp_path, ["myfuncs"])
        pkg_dir = tmp_path / "myfuncs"
        pkg_dir.mkdir()
        (pkg_dir / "__init__.py").write_text("", encoding="utf-8")
        (pkg_dir / "ops.py").write_text(
            '''
from hojjat_tui.function import hojjat_function

@hojjat_function(name="add_one", description="Add one")
def add_one(x: int) -> int:
    return x + 1
''',
            encoding="utf-8",
        )
        # Import the function in __init__ so it's registered when package is imported
        (pkg_dir / "__init__.py").write_text(
            "from .ops import add_one\n", encoding="utf-8"
        )
        monkeypatch.chdir(tmp_path)
        sys.path.insert(0, str(tmp_path))

        _clear_registry_and_loaded()
        loaded, errors = load_function_modules()

        assert "myfuncs" in loaded
        assert errors == []
        assert "add_one" in get_registry()

    def test_no_config_does_not_crash(self, tmp_path, monkeypatch):
        monkeypatch.chdir(tmp_path)
        _clear_registry_and_loaded()
        loaded, errors = load_function_modules()
        assert loaded == []
        assert errors == []

    def test_missing_module_produces_error(self, tmp_path, monkeypatch):
        _write_pyproject(tmp_path, ["nonexistent_module_xyz"])
        monkeypatch.chdir(tmp_path)
        _clear_registry_and_loaded()
        loaded, errors = load_function_modules()
        assert loaded == []
        assert len(errors) == 1
        assert "nonexistent_module_xyz" in errors[0]
        assert "No module named" in errors[0]

    def test_not_loaded_twice(self, tmp_path, monkeypatch):
        _write_pyproject(tmp_path, ["user_main"])
        _write_module(
            tmp_path,
            "user_main",
            '''
from hojjat_tui.function import hojjat_function

@hojjat_function(name="twice_test")
def twice_test():
    return "ok"
''',
        )
        monkeypatch.chdir(tmp_path)
        sys.path.insert(0, str(tmp_path))

        _clear_registry_and_loaded()
        loaded1, _ = load_function_modules()
        loaded2, _ = load_function_modules()

        assert "user_main" in loaded1
        assert "user_main" not in loaded2  # Already loaded, skipped

    def test_loaded_modules_tracker(self, tmp_path, monkeypatch):
        _write_pyproject(tmp_path, ["user_main"])
        _write_module(
            tmp_path,
            "user_main",
            '''
from hojjat_tui.function import hojjat_function

@hojjat_function(name="tracker_test")
def tracker_test():
    return "ok"
''',
        )
        monkeypatch.chdir(tmp_path)
        sys.path.insert(0, str(tmp_path))

        _clear_registry_and_loaded()
        load_function_modules()
        assert "user_main" in get_loaded_modules()


class TestDiscoveryIntegration:
    """Integration tests for discovery with the registry."""

    def test_function_visible_in_registry_after_load(self, tmp_path, monkeypatch):
        _write_pyproject(tmp_path, ["discovery_main"])
        _write_module(
            tmp_path,
            "discovery_main",
            '''
from hojjat_tui.function import hojjat_function

@hojjat_function(name="discovered_func", description="A discovered function")
def discovered_func(x: int = 0) -> int:
    return x * 2
''',
        )
        monkeypatch.chdir(tmp_path)
        sys.path.insert(0, str(tmp_path))

        _clear_registry_and_loaded()
        loaded, errors = load_function_modules()

        assert "discovery_main" in loaded
        assert errors == []
        registry = get_registry()
        assert "discovered_func" in registry
        assert registry["discovered_func"]["description"] == "A discovered function"
"""Shared test fixtures for HOJJAT TUI tests."""

import sys
import os
import pytest
from pathlib import Path

# Ensure src is on the path
src_dir = Path(__file__).parent.parent / "src"
if str(src_dir) not in sys.path:
    sys.path.insert(0, str(src_dir))


@pytest.fixture
def temp_db_path(tmp_path):
    """Provide a temporary database path."""
    return tmp_path / "test_hojjat_tui.db"


@pytest.fixture
def registry():
    """Import and return the function registry."""
    from hojjat_tui.function import get_registry
    return get_registry()


@pytest.fixture
def execute_func():
    """Return the execute_function function."""
    from hojjat_tui.executor import execute_function
    return execute_function
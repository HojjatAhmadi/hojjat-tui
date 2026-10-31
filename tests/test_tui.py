"""Tests for the TUI application."""

import pytest
from unittest.mock import Mock, patch, MagicMock


class TestHojjatTUIApplication:
    """Tests for the main TUI application."""

    def test_app_import(self):
        """Test that the TUI app can be imported."""
        from hojjat_tui.tui import HojjatTUIApplication
        assert HojjatTUIApplication is not None

    def test_app_creation(self):
        """Test that the app can be created."""
        from hojjat_tui.tui import HojjatTUIApplication
        app = HojjatTUIApplication()
        assert app is not None
        assert app.registry is not None

    def test_logo_defined(self):
        """Test that the logo branding is defined."""
        from hojjat_tui.tui import LOGO
        assert "TUI" in LOGO
        assert "TUI" in LOGO
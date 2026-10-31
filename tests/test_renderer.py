"""Tests for the output renderer."""

import pytest
from hojjat_tui.renderer import render_output, render_menu, render_error, render_info, render_success


class TestRenderOutput:
    """Tests for the render_output function."""

    def test_render_text(self):
        """Test rendering text output."""
        from rich.console import Console
        import io as _io
        buf = _io.StringIO()
        console = Console(file=buf, width=100, force_terminal=False)
        
        result = render_output("Hello World", "text", console=console)
        assert isinstance(result, str)
        assert "Hello World" in result or "Hello World" in buf.getvalue()

    def test_render_markdown(self):
        """Test rendering markdown output."""
        from rich.console import Console
        import io as _io
        buf = _io.StringIO()
        console = Console(file=buf, width=100, force_terminal=False)
        
        render_output("# Hello\n\nThis is markdown.", "markdown", console=console)
        output = buf.getvalue()
        assert "Hello" in output or "markdown" in output.lower() or len(output) > 0

    def test_render_json(self):
        """Test rendering JSON output."""
        from rich.console import Console
        import io as _io
        buf = _io.StringIO()
        console = Console(file=buf, width=100, force_terminal=False)
        
        render_output({"key": "value"}, "json", console=console)
        output = buf.getvalue()
        assert "key" in output

    def test_render_json_from_string(self):
        """Test rendering JSON from a JSON string."""
        import json
        from rich.console import Console
        import io as _io
        buf = _io.StringIO()
        console = Console(file=buf, width=100, force_terminal=False)
        
        render_output(json.dumps({"key": "value"}), "json", console=console)
        output = buf.getvalue()
        assert "key" in output

    def test_render_table_list(self):
        """Test rendering a list as a table."""
        from rich.console import Console
        import io as _io
        buf = _io.StringIO()
        console = Console(file=buf, width=100, force_terminal=False)
        
        data = [{"a": 1, "b": 2}, {"a": 3, "b": 4}]
        render_output(data, "table", console=console)
        output = buf.getvalue()
        assert "a" in output or "1" in output

    def test_render_table_dict(self):
        """Test rendering a dict as a table."""
        from rich.console import Console
        import io as _io
        buf = _io.StringIO()
        console = Console(file=buf, width=100, force_terminal=False)
        
        data = {"key1": "value1", "key2": "value2"}
        render_output(data, "table", console=console)
        output = buf.getvalue()
        assert "key1" in output or "value1" in output

    def test_render_error(self):
        """Test rendering an error message."""
        from rich.console import Console
        import io as _io
        buf = _io.StringIO()
        console = Console(file=buf, width=100, force_terminal=False)
        
        render_output("Error message", "error", console=console)
        output = buf.getvalue()
        assert "Error message" in output

    def test_render_chart_placeholder(self):
        """Test that chart rendering returns a placeholder."""
        from rich.console import Console
        import io as _io
        buf = _io.StringIO()
        console = Console(file=buf, width=100, force_terminal=False)
        
        result = render_output({"data": [1, 2, 3]}, "chart", console=console)
        output = buf.getvalue()
        assert "placeholder" in output.lower() or "Phase 2" in output


class TestRenderInfoError:
    """Tests for info/error rendering."""

    def test_render_info(self):
        """Test rendering an info message."""
        from rich.console import Console
        import io as _io
        buf = _io.StringIO()
        console = Console(file=buf, width=100, force_terminal=False)
        
        render_info("Informational message", console=console)
        output = buf.getvalue()
        assert "Informational message" in output

    def test_render_error(self):
        """Test rendering an error message."""
        from rich.console import Console
        import io as _io
        buf = _io.StringIO()
        console = Console(file=buf, width=100, force_terminal=False)
        
        render_error("Error message", console=console)
        output = buf.getvalue()
        assert "Error message" in output

    def test_render_success(self):
        """Test rendering a success message."""
        from rich.console import Console
        import io as _io
        buf = _io.StringIO()
        console = Console(file=buf, width=100, force_terminal=False)
        
        render_success("Success message", console=console)
        output = buf.getvalue()
        assert "Success message" in output


class TestRenderMenu:
    """Tests for menu rendering."""

    def test_render_menu_with_functions(self):
        """Test rendering a menu with functions."""
        from hojjat_tui.function import get_registry
        functions = get_registry()
        
        if functions:
            table = render_menu(functions)
            assert "Registered Functions" in table.title or "Functions" in str(table.title)

    def test_render_menu_empty(self):
        """Test rendering an empty menu."""
        table = render_menu({})
        assert table is not None
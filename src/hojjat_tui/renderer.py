"""Centralized output renderer for HOJJAT TUI.

This module provides rendering functions for various output types:
- Text
- Markdown
- Tables
- JSON
- Charts (documented as pending for Phase 2)
- Informational and error messages
"""

import json
from typing import Any, Dict, List, Optional, Union
from rich.console import Console, RenderableType
from rich.console import Console
from rich.markdown import Markdown
from rich.table import Table
from rich.panel import Panel
from rich.columns import Columns
from rich.text import Text as RichText

_chart_renderer_documented = False

def render_output(
    output: Any,
    output_type: str = "text",
    title: Optional[str] = None,
    console: Optional[Console] = None,
) -> Union[str, Panel, Table, Markdown]:
    """Render output based on its type.
    
    Args:
        output: The data to render.
        output_type: Type of output ('text', 'markdown', 'json', 'table', 'error', 'info').
        title: Optional title for the output.
        console: Optional rich Console for rendering.
    
    Returns:
        Renderable object or string.
    """
    if output_type == "text" or output_type is None:
        return str(output)
    elif output_type == "markdown":
        if console:
            console.print(Markdown(str(output)))
            return str(output)
        return Markdown(str(output))
    elif output_type == "json":
        if isinstance(output, str):
            try:
                output = json.loads(output)
            except json.JSONDecodeError:
                return Panel(str(output), title=title or "JSON Output (Error)", border_style="red")
        formatted = json.dumps(output, indent=2, default=str)
        if console:
            console.print(formatted)
        return formatted
    elif output_type == "table":
        table = _render_table(output, title)
        if console:
            console.print(table)
        return table
    elif output_type == "error":
        panel = Panel(str(output), title="Error", border_style="red", title_align="left")
        if console:
            console.print(panel)
        return panel
    elif output_type == "info":
        panel = Panel(str(output), title="Info", border_style="blue", title_align="left")
        if console:
            console.print(panel)
        return panel
    elif output_type == "chart":
        return _render_chart_placeholder(output, title, console)
    else:
        return str(output)

def _render_table(data: Union[List, Dict, Any], title: Optional[str] = None) -> Table:
    """Render data as a table."""
    table = Table(title=title, show_lines=True)
    
    if isinstance(data, list):
        if data and isinstance(data[0], dict):
            columns = list(data[0].keys())
            for col in columns:
                table.add_column(col, style="cyan", overflow="fold")
            for row in data:
                table.add_row(*[str(row.get(col, "")) for col in columns])
        elif data and isinstance(data[0], (list, tuple)):
            if data:
                num_cols = len(data[0])
                for i in range(num_cols):
                    table.add_column(f"Column {i+1}", style="cyan", overflow="fold")
                for row in data:
                    table.add_row(*[str(cell) for cell in row])
        else:
            table.add_column("Value", style="cyan", overflow="fold")
            for item in data:
                table.add_row(str(item))
    elif isinstance(data, dict):
        table.add_column("Key", style="cyan", overflow="fold")
        table.add_column("Value", overflow="fold")
        for key, value in data.items():
            table.add_row(str(key), str(value))
    else:
        table.add_column("Output", style="cyan", overflow="fold")
        table.add_row(str(data))
    
    return table

def _render_chart_placeholder(data: Any, title: Optional[str], console: Optional[Console]) -> Panel:
    """Placeholder for chart renderer — Phase 2 feature."""
    global _chart_renderer_documented
    _chart_renderer_documented = True
    
    message = (
        "[bold yellow]Chart Renderer[/bold yellow]\n\n"
        "Charts are documented as a Phase 2 feature.\n"
        "This renderer is a placeholder and does not render charts yet."
    )
    panel = Panel(
        message,
        title=title or "Chart Output",
        border_style="yellow",
        title_align="left",
    )
    
    if console:
        console.print(panel)
    return panel

def render_menu(functions: Dict[str, Dict[str, Any]]) -> Table:
    """Render a menu table of registered functions."""
    table = Table(title="HOJJAT TUI — Registered Functions", show_lines=True)
    table.add_column("#", style="dim", width=4)
    table.add_column("Name", style="bold cyan", overflow="fold")
    table.add_column("Label", style="green", overflow="fold")
    table.add_column("Description", overflow="fold")
    table.add_column("Params", style="yellow", overflow="fold")
    
    for i, (name, metadata) in enumerate(functions.items(), 1):
        params = metadata.get("signature")
        if params:
            params_str = str(params)
        else:
            sig = metadata.get("signature")
            params_str = str(sig) if sig else "-"
        
        table.add_row(
            str(i),
            name,
            metadata.get("label", name),
            metadata.get("description", "-"),
            params_str,
        )
    
    return table

def render_info(message: str, title: str = "Info", console: Optional[Console] = None) -> Panel:
    """Render an informational message."""
    panel = Panel(message, title=title, border_style="blue", title_align="left")
    if console:
        console.print(panel)
    return panel

def render_error(message: str, title: str = "Error", console: Optional[Console] = None) -> Panel:
    """Render an error message."""
    panel = Panel(message, title=title, border_style="red", title_align="left")
    if console:
        console.print(panel)
    return panel

def render_success(message: str, title: str = "Success", console: Optional[Console] = None) -> Panel:
    """Render a success message."""
    panel = Panel(message, title=title, border_style="green", title_align="left")
    if console:
        console.print(panel)
    return panel

def is_chart_renderer_documented() -> bool:
    """Check if the chart renderer placeholder has been used."""
    return _chart_renderer_documented
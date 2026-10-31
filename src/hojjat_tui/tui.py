"""HOJJAT TUI — Interactive terminal UI for running functions and chains."""

import inspect
import json
import logging
import time
from shutil import get_terminal_size
from datetime import datetime
from typing import Any, Dict, List, Optional

from textual.app import App, ComposeResult
from textual.binding import Binding
from textual.containers import Container, Horizontal, Vertical, VerticalScroll
from textual.screen import Screen
from textual.widgets import (
    Button, Header, Footer, Static, Input, Label, OptionList,
    TabbedContent, TabPane, Select, TextArea,
)
from textual.widgets._option_list import Option, OptionDoesNotExist
from rich.console import Console
from rich.table import Table
from rich.markdown import Markdown
from rich.panel import Panel

try:
    from pyfiglet import Figlet
except ImportError:  # Keep the TUI usable before optional dependencies are installed.
    Figlet = None

from hojjat_tui import __version__
from hojjat_tui.function import get_registry
from hojjat_tui.executor import execute_function
from hojjat_tui.chain import (
    Chain, ChainStep, ParameterBinding, BindingType, ChainStatus,
    ChainExecution, StepExecutionResult, validate_chain, execute_chain,
    save_chain, load_chain, list_chains, delete_chain,
    create_chain, add_step, literal, output_of,
)
from hojjat_tui.persistence import Database

logger = logging.getLogger("hojjat_tui.tui")

def _build_logo() -> str:
    """Render a compact HOJJAT TUI wordmark with pyfiglet when available."""
    try:
        columns = get_terminal_size((100, 30)).columns
        width = max(38, min(columns - 8, 100))

        if Figlet is None:
            return "HOJJAT TUI\nTerminal User Interface"

        if columns >= 100:
            fonts = ("ANSI Shadow", "Slant", "small")
        elif columns >= 70:
            fonts = ("Slant", "small", "mini")
        else:
            fonts = ("small", "mini", "standard")

        for font in fonts:
            try:
                rendered = Figlet(font=font, width=width).renderText("HOJJAT TUI").rstrip()
                if rendered:
                    return rendered
            except (OSError, RuntimeError, ValueError):
                continue
    except Exception:
        logger.debug("Could not render pyfiglet logo; using text fallback.", exc_info=True)

    return "HOJJAT TUI\nTerminal User Interface"


LOGO = _build_logo()


class FunctionForm(Static):
    """A form for entering function parameters."""

    def __init__(self, function_name: str):
        super().__init__()
        self.function_name = function_name
        self.registry = get_registry()
        self.metadata = self.registry.get(function_name, {})
        self.inputs: Dict[str, Input] = {}

    def compose(self) -> ComposeResult:
        sig = self.metadata.get("signature")
        defaults = self.metadata.get("defaults", {})
        required = self.metadata.get("required", [])

        yield Label(f"[bold cyan]{self.metadata.get('label', self.function_name)}[/bold cyan]")
        yield Static(self.metadata.get("description", "No description"))

        if sig:
            for param_name, param in sig.parameters.items():
                yield self._make_input_field(param_name, param, defaults.get(param_name), param_name in required)

        with Horizontal():
            yield Button("▶ Execute Function", id="exec-btn", variant="primary")
            yield Button("Cancel", id="cancel-btn", variant="default")

    def _make_input_field(self, name: str, param: inspect.Parameter,
                          default: Any, is_required: bool):
        """Create an input widget for a parameter."""
        type_hint = param.annotation if param.annotation != inspect.Parameter.empty else str
        type_str = getattr(type_hint, '__name__', str(type_hint))

        annotation_info = f"[{type_str}]"
        if is_required:
            annotation_info += " [red]*[/red]"
        if default is not None:
            annotation_info += f" (default: {default})"

        container = Static()
        container.mount(Label(f"{name}{annotation_info}"))

        input_widget = Input(id=f"param-{name}", placeholder=type_str or "string")
        if default is not None:
            input_widget.value = str(default)

        container.inputs = {name: input_widget}  # Store for later
        return container


class ChainBuilder(Static):
    """A wizard for building chains."""

    def __init__(self):
        super().__init__()
        self.chain_name: Optional[str] = None
        self.steps: List[ChainStep] = []

    def compose(self) -> ComposeResult:
        yield Label("[bold]Chain Builder[/bold]")
        yield Input(id="chain-name", placeholder="Chain name")
        yield Input(id="chain-label", placeholder="Chain display label")
        yield TextArea(id="chain-desc", placeholder="Description (optional)")
        yield OptionList(id="function-selector")
        yield Button("Add Step", id="add-step", variant="primary")
        yield Button("Save Chain", id="save-chain", variant="success")
        yield Button("Cancel", id="cancel-chain", variant="default")


class ResultScreen(Screen):
    """A full-screen view that displays the complete function output with scrolling.

    Supports additional visualization modes (Table, Chart) when the underlying
    raw output (a Python object) is supplied via *raw_output*.  The full string
    representation is always preserved in *full_output* and never reconstructed.
    """

    BINDINGS = [Binding("escape", "back", "Back")]

    # --- construction -------------------------------------------------------

    def __init__(self, full_output: str, raw_output: Any = None):
        super().__init__()
        self._full_output = full_output
        self._raw_output = raw_output
        self._current_view = "raw"  # "raw" | "table" | "chart"

    # --- composition --------------------------------------------------------

    def compose(self) -> ComposeResult:
        with Vertical(id="result-root"):
            with VerticalScroll(id="result-scroll"):
                yield Static(self._full_output, id="full-result", expand=True)
            with Horizontal(id="result-screen-button-bar"):
                yield Button("Back", id="back-btn", variant="primary")
                self._table_btn = Button(
                    "Table", id="table-btn", variant="success",
                    disabled=not self._can_render_table(),
                )
                yield self._table_btn
                self._chart_btn = Button(
                    "Chart", id="chart-btn", variant="success",
                    disabled=not self._can_render_chart(),
                )
                yield self._chart_btn
            with Horizontal(id="result-explanation-bar"):
                explanation = self._build_explanation()
                yield Static(explanation, id="result-explanation")

    # --- data validation ----------------------------------------------------

    def _can_render_table(self) -> bool:
        """Return True when *raw_output* looks like a table-ready structure."""
        data = self._raw_output
        if not isinstance(data, list) or len(data) == 0:
            return False
        supported = (list, tuple, dict)
        return all(isinstance(row, supported) for row in data)

    def _can_render_chart(self) -> bool:
        """Return True when *raw_output* contains enough numeric data for a chart."""
        data = self._raw_output
        numeric_values = self._extract_numeric_values(data)
        return len(numeric_values) >= 2

    def _build_explanation(self) -> str:
        """Return a human-readable explanation for disabled modes."""
        parts: List[str] = []
        if not self._can_render_table():
            parts.append("Table view is not supported for this output")
        if not self._can_render_chart():
            parts.append("Chart view is not supported for this output")
        return "; ".join(parts) if parts else ""

    @staticmethod
    def _extract_numeric_values(data: Any) -> List[float]:
        """Flatten *data* collecting every int/float value found.

        Supports: scalar numbers, flat lists of numbers, and lists of tuples/lists
        whose elements are numeric.  Mixed or invalid entries are skipped.
        """
        values: List[float] = []

        def _flatten(item: Any):
            if isinstance(item, (int, float)) and not isinstance(item, bool):
                try:
                    values.append(float(item))
                except (TypeError, ValueError):
                    pass
            elif isinstance(item, (list, tuple)):
                for sub in item:
                    _flatten(sub)
            # dicts, strings, None and other types are intentionally skipped

        _flatten(data)
        return values

    # --- rendering ----------------------------------------------------------

    def _render_table(self) -> str:
        """Render *raw_output* as a Rich table and return its string form."""
        data = self._raw_output
        if not data:
            return "(empty table data)"

        # Determine headers / column count
        if isinstance(data[0], dict):
            headers = list(data[0].keys())
            rows = [[str(row.get(h, "")) for h in headers] for row in data]
        else:
            first = data[0]
            if isinstance(first, (list, tuple)):
                headers = [f"Col {i}" for i in range(len(first))]
                rows = [[str(v) for v in row] for row in data]
            else:
                headers = ["Index", "Value"]
                rows = [[str(i), str(v)] for i, v in enumerate(data)]

        table = Table(show_lines=True, header_style="bold cyan")
        for h in headers:
            table.add_column(h)
        for row in rows:
            if len(row) < len(headers):
                row += [""] * (len(headers) - len(row))
            table.add_row(*row[: len(headers)])

        # Render the Rich Table to a plain string via Console.export_text
        console = Console(force_terminal=False, no_color=True, width=80, record=True)
        console.print(table)
        return console.export_text()

    def _render_chart(self) -> str:
        """Render *raw_output* as a simple text-based horizontal bar chart."""
        values = self._extract_numeric_values(self._raw_output)
        if len(values) < 2:
            return "(not enough numeric data for a chart)"

        max_val = max(values) if max(values) > 0 else 1.0
        bar_width = 40
        lines: List[str] = []
        for i, val in enumerate(values):
            filled = int(round((val / max_val) * bar_width)) if max_val > 0 else 0
            filled = min(filled, bar_width)
            bar_str = "#" * filled + "." * (bar_width - filled)
            lines.append(f"{i:>4}  [{bar_str}] {val}")
        return "\n".join(lines)

    def _show_table(self):
        self._current_view = "table"
        renderable = self._render_table()
        self.query_one("#full-result", Static).update(renderable)
        self.query_one("#result-explanation", Static).update("")
        self.refresh_scrollbars()

    def _show_chart(self):
        self._current_view = "chart"
        renderable = self._render_chart()
        self.query_one("#full-result", Static).update(renderable)
        self.query_one("#result-explanation", Static).update("")
        self.refresh_scrollbars()

    def _show_raw(self):
        self._current_view = "raw"
        self.query_one("#full-result", Static).update(self._full_output)
        self.query_one("#result-explanation", Static).update("")
        self.refresh_scrollbars()

    def refresh_scrollbars(self):
        """Re-trigger layout so the scroll area updates its bars."""
        sv = self.query_one("#result-scroll", VerticalScroll)
        sv.refresh()

    # --- event handlers -----------------------------------------------------

    def on_button_pressed(self, event: Button.Pressed):
        btn_id = event.button.id
        if btn_id == "back-btn":
            self.action_back()
        elif btn_id == "table-btn":
            self._show_table()
        elif btn_id == "chart-btn":
            self._show_chart()

    def action_back(self):
        self.app.pop_screen()


class ConfirmScreen(Screen):
    """A modal confirmation dialog that returns the user's choice via dismiss()."""

    BINDINGS = [Binding("escape", "cancel", "Cancel")]

    def __init__(self, message: str):
        super().__init__()
        self._message = message

    def compose(self) -> ComposeResult:
        with Vertical(id="confirm-root"):
            yield Static(self._message, id="confirm-message")
            with Horizontal(id="confirm-button-bar"):
                yield Button("Cancel", id="confirm-cancel", variant="default")
                yield Button("Confirm", id="confirm-confirm", variant="error")

    def on_button_pressed(self, event: Button.Pressed):
        if event.button.id == "confirm-confirm":
            self.dismiss(True)
        else:
            self.dismiss(False)

    def action_cancel(self):
        self.dismiss(False)


class HojjatTUIApplication(App):
    """Main interactive TUI application."""

    TITLE = "HOJJAT TUI"
    SUB_TITLE = "Terminal Workflow Studio"

    CSS = """
    Screen {
        layout: vertical;
        padding: 1;
        background: #1a1b26;
        color: #c0caf5;
    }

    Header {
        dock: top;
        background: #1a1b26;
        color: #7aa2f7;
        text-style: bold;
    }

    /* لوگو در صفحه‌های کوچک کوچیک‌تر میشه */
    #logo {
        width: 100%;
        height: auto;
        max-height: 5;
        min-height: 3;
        margin-bottom: 1;
        padding: 0 1;
        content-align: center middle;
        text-align: center;
        color: #bb9af7;
        background: #24283b;
        border: double #7aa2f7;
        overflow: hidden;
    }

    #main {
        height: 1fr;
        width: 100%;
        layout: horizontal;
    }

    /* در صفحه‌های کوچک منو اسکرول میشه */
    #menu-panel {
        width: 38;
        height: 100%;
        border: round #7aa2f7;
        margin: 0 1 0 0;
        padding: 1;
        background: #24283b;
        overflow-y: auto; 
    }

    #content-panel {
        width: 1fr;
        height: 100%;
        layout: vertical;
        margin: 0;
    }

    #nav-bar {
        height: auto;
        min-height: 3;
        layout: grid;
        grid-size: 2;
        grid-gutter: 0 1;
        margin-bottom: 1;
    }

    #nav-bar Button {
        width: 100%;
        margin: 0;
        min-height: 3;
    }

    /* حداقل ارتفاع برای جلوگیری از ناپدید شدن لیست */
    #function-list {
        height: 1fr;
        min-height: 8;
        border: round #bb9af7;
        background: #1a1b26;
    }

    #content-area {
        height: 1fr;
        border: round #f7768e;
        padding: 1 2;
        background: #1a1b26;
        overflow-y: auto;
    }

    /* استایل باکس نتیجه */
    #result-preview {
        margin-top: 1;
        padding: 1;
        border: dashed #9ece6a;
        background: #24283b;
        height: auto;
        min-height: 3;
    }

    .param-label {
        margin-top: 1;
        color: #7aa2f7;
        text-style: bold;
    }

    #form-buttons {
        height: auto;
        min-height: 3;
        margin-top: 1;
    }

    #form-buttons Button {
        min-width: 16;
        min-height: 3;
        margin-right: 1;
    }

    #status-bar {
        height: 3;
        background: #24283b;
        border: round #7aa2f7;
        padding: 0 1;
        color: #9ece6a;
        text-style: bold;
    }

    #action-bar {
        height: auto;
        min-height: 3;
        margin-top: 1;
    }

    #action-bar Button {
        min-width: 14;
        margin: 0 1 0 0;
        min-height: 3;
    }

    Button {
        background: #24283b;
        color: #c0caf5;
        border: tall #7aa2f7;
        text-style: bold;
    }

    Button:hover {
        background: #7aa2f7;
        color: #1a1b26;
        border: tall #bb9af7;
    }

    Button.-primary {
        background: #7aa2f7;
        color: #1a1b26;
        border: tall #7aa2f7;
    }

    Button.-primary:hover {
        background: #bb9af7;
        color: #1a1b26;
        border: tall #bb9af7;
    }

    Button.-success {
        background: #9ece6a;
        color: #1a1b26;
        border: tall #9ece6a;
    }

    Button.-success:hover {
        background: #73daca;
        color: #1a1b26;
        border: tall #73daca;
    }

    Input {
        background: #24283b;
        color: #c0caf5;
        border: tall #7aa2f7;
    }

    Input:focus {
        border: tall #bb9af7;
    }

    ResultScreen {
        layout: vertical;
        padding: 1;
        background: #1a1b26;
    }

    #result-scroll {
        height: 1fr;
        overflow: auto;
        background: #24283b;
        border: round #7aa2f7;
    }

    #full-result {
        height: auto;
        width: 100%;
        background: transparent;
        padding: 1;
    }

    #result-screen-button-bar {
        height: auto;
        width: 100%;
        align: left middle;
        margin-top: 1;
    }

    ResultScreen #back-btn {
        min-width: 14;
        min-height: 3;
    }

    #result-explanation-bar {
        height: auto;
        width: 100%;
        align: left middle;
        margin-top: 1;
    }

    #result-explanation {
        color: #f7768e;
        height: auto;
        width: 1fr;
        padding: 0 1;
    }
    #chain-builder-actions, 
    #exec-chain-actions, 
    #chain-exec-actions {
        height: auto;
        min-height: 3;
        margin-top: 1;
        align: left middle;
    }

    /* تنظیم دکمه‌های داخل این کانتینرها تا له نشن */
    #chain-builder-actions Button,
    #exec-chain-actions Button,
    #chain-exec-actions Button {
        min-width: 16;
        min-height: 3;
        margin-right: 1;
    }

    /* تنظیم ارتفاع لیست‌های داینامیک تا دکمه‌های زیرشون رو به بیرون هول ندن */
    #content-area OptionList {
        height: auto;
        max-height: 10;
        min-height: 5;
        border: round #7aa2f7;
        margin-bottom: 1;
    }

    #content-area Horizontal {
        height: auto;
        min-height: 3;
        margin-bottom: 1;
    }
    
    #content-area Horizontal Button {
        min-height: 3;
        min-width: 10;
    }
    """

    BINDINGS = [
        ("q", "quit", "Quit"),
        ("ctrl+c", "quit", "Quit"),
        ("r", "refresh", "Refresh Functions"),
        ("ctrl+r", "refresh", "Refresh"),
        ("f", "focus_functions", "Focus Function List"),
        ("c", "focus_chains", "Focus Chains"),
        ("s", "show_settings", "Settings"),
    ]

    def __init__(self):
        super().__init__()
        self.registry: Dict[str, Dict] = {}
        self.db: Optional[Database] = None
        self.selected: Optional[str] = None
        self.current_view: str = "functions"
        self._dynamic_inputs: Dict[str, Input] = {}
        self._current_form_function: Optional[str] = None
        self._form_widgets: List = []
        self._last_result_output: str = ""
        self._last_result_raw: Any = None

        # Chain execution state
        self._selected_execute_chain: Optional[str] = None

        # Chain building state
        self._chain_builder_mode: bool = False
        self._chain_being_built: Optional[Chain] = None
        self._chain_step_params: Dict[str, List[ParameterBinding]] = {}
        self._chain_name_input: Optional[Input] = None
        self._chain_label_input: Optional[Input] = None
        self._chain_desc_input: Optional[Input] = None

    def compose(self) -> ComposeResult:
        yield Header()
        yield Static(LOGO, id="logo")

        with Container(id="main"):
            with Vertical(id="menu-panel"):
                yield Label("[bold]Navigation[/bold]")

                with Horizontal(id="nav-bar"):
                    yield Button("Functions", id="nav-functions", variant="primary")
                    yield Button("Chains", id="nav-chains", variant="default")
                    yield Button("Results", id="nav-results", variant="default")
                    yield Button("Settings", id="nav-settings", variant="default")

                yield Static("", id="nav-divider")
                yield Label("[bold]Functions[/bold]", id="list-label")
                yield OptionList(id="function-list")

            with Vertical(id="content-panel"):
                with VerticalScroll(id="content-area"):
                    yield Static("Select a function to begin", id="content-text")
                with Horizontal(id="action-bar"):
                    yield Button("New Chain", id="new-chain-btn", variant="success")
                    yield Button("Execute Chain", id="exec-chain-btn")
                    yield Button("Refresh", id="refresh-btn")

        yield Static("", id="status-bar")
        yield Footer()

    async def on_mount(self) -> None:
        await self.init_db()
        await self.refresh_functions()
        await self.status_update("Ready — select a function to run")

    async def status_update(self, msg: str):
        self.query_one("#status-bar", Static).update(msg)
        # await self._set_content_text(
        #     msg
        # )

    async def _set_content_text(self, text: str):
        content_area = self.query_one("#content-area", VerticalScroll)
        await content_area.remove_children()
        await content_area.mount(Static(text, id="content-text"))

    async def init_db(self):
        try:
            self.db = Database()
            self.db.init_db()
            await self.status_update("Database ready")
        except Exception as e:
            await self.status_update(f"Database error: {e}")
            logger.error(f"Database init failed: {e}")

    async def refresh_functions(self):
        try:
            from hojjat_tui.builtin_functions import register_builtins
            register_builtins()
        except Exception as e:
            logger.warning(f"Could not load builtins: {e}")

        self.registry = get_registry()
        menu = self.query_one("#function-list", OptionList)
        menu.clear_options()

        if not self.registry:
            menu.add_option(Option("No functions available", disabled=True))
        else:
            for name in sorted(self.registry.keys()):
                meta = self.registry[name]
                label = meta.get("label", name)
                desc = meta.get("description", "")
                show = f"{label}"
                if desc:
                    show += f" — {desc}"
                menu.add_option(Option(show, name))

        await self.status_update(f"Loaded {len(self.registry)} functions")

    def _clear_form_state(self):
        """Reset form state after execution."""
        self._dynamic_inputs.clear()
        self._form_widgets.clear()
        self._current_form_function = None

    async def on_button_pressed(self, event: Button.Pressed):
        btn = event.button.id

        if btn == "nav-functions":
            self.current_view = "functions"
            await self.update_function_list()
        elif btn == "nav-chains":
            self.current_view = "chains"
            await self.update_chains_view()
        elif btn == "nav-results":
            self.current_view = "results"
            await self.update_results_view()
        elif btn == "nav-settings":
            self.current_view = "settings"
            await self.update_settings_view()
        elif btn == "new-chain-btn":
            await self.show_chain_creation()
        elif btn == "exec-chain-btn":
            await self.show_chain_execution()
        elif btn == "refresh-btn":
            await self.refresh_functions()
        elif btn == "execute-fn":
            await self._on_execute_function()
        elif btn == "cancel-fn":
            await self._on_cancel_form()
        elif btn == "show-result-btn":
            full_output = getattr(self, "_last_result_output", "") or ""
            raw_output = getattr(self, "_last_result_raw", None)
            await self.push_screen(ResultScreen(full_output, raw_output))
        elif btn == "chain-save-btn":
            await self._on_save_chain()
        elif btn == "chain-cancel-btn":
            await self._on_cancel_chain_builder()
        elif btn == "exec-chain-btn":
            await self.show_chain_execution()
        elif btn == "run-chain-btn":
            await self._on_exec_chain_pressed()
        elif btn == "run-chain-execute":
            await self._on_run_chain_execute_pressed()
        elif btn == "run-chain-cancel":
            await self._on_run_chain_cancel_pressed()
        elif btn and btn.startswith("step-remove-"):
            step_uuid = btn.replace("step-remove-", "")
            await self._on_remove_step(step_uuid)
        elif btn and btn.startswith("step-moveup-"):
            step_uuid = btn.replace("step-moveup-", "")
            await self._on_move_step(step_uuid, -1)
        elif btn and btn.startswith("step-movedown-"):
            step_uuid = btn.replace("step-movedown-", "")
            await self._on_move_step(step_uuid, +1)
        elif btn and btn.startswith("step-configure-"):
            step_uuid = btn.replace("step-configure-", "")
            await self._on_configure_step_params(step_uuid)
        elif btn and btn.startswith("step-done-"):
            await self._render_chain_builder()
        elif btn and btn.startswith("step-cancel-"):
            await self._render_chain_builder()

    async def on_option_list_option_selected(self, event: OptionList.OptionSelected):
        option_id = event.option_id
        # Chain Builder: selecting a function adds it as a step.  Never open the
        # standalone Execute Function screen from the chain step selector.
        if self._chain_builder_mode and event.option_list is not None and event.option_list.id == "chain-step-selector":
            if option_id and option_id in self.registry:
                await self._on_add_step_to_chain(option_id)
            return
        if self.current_view == "functions":
            if not option_id or option_id not in self.registry:
                self.selected = None
                return
            self.selected = option_id
            await self.show_function_form(option_id)
        elif self.current_view == "chains":
            self.selected = option_id
            await self.show_chain_details(option_id)
        elif self.current_view == "results":
            self.selected = option_id
            await self.show_execution_details(option_id)
        elif self.current_view == "settings":
            await self.handle_setting(option_id)

    async def update_function_list(self):
        self.current_view = "functions"
        self.query_one("#list-label", Label).update("Functions")
        menu = self.query_one("#function-list", OptionList)
        menu.clear_options()

        if not self.registry:
            menu.add_option(Option("No functions available", disabled=True))
        else:
            for name in sorted(self.registry.keys()):
                meta = self.registry[name]
                label = meta.get("label", name)
                desc = meta.get("description", "")
                show = f"{label}" + (f" — {desc}" if desc else "")
                menu.add_option(Option(show, name))

        await self._set_content_text("Select a function to execute")

    async def update_chains_view(self):
        self.current_view = "chains"
        self.query_one("#list-label", Label).update("Chains")
        menu = self.query_one("#function-list", OptionList)
        menu.clear_options()

        try:
            chains = list_chains()
            if not chains:
                menu.add_option(Option("No chains — create one with 'New Chain'", disabled=True))
            else:
                for chain in chains:
                    menu.add_option(Option(f"{chain['label']} ({chain['name']})", chain["name"]))
        except Exception as e:
            menu.add_option(Option(f"Error loading chains: {e}", disabled=True))

        await self._set_content_text("Select a chain to inspect")

    async def update_results_view(self):
        self.current_view = "results"
        self.query_one("#list-label", Label).update("Results")
        menu = self.query_one("#function-list", OptionList)
        menu.clear_options()

        try:
            db = self.db or Database()
            executions = db.get_chain_executions(20)
            if not executions:
                menu.add_option(Option("No execution history", disabled=True))
            else:
                for ex in executions:
                    time_str = datetime.fromtimestamp(ex["started_at"]).strftime("%m-%d %H:%M")
                    status_icon = "✓" if ex["status"] == ChainStatus.SUCCESS.value else "✗"
                    menu.add_option(Option(f"{ex['chain_name']} @ {time_str} [{status_icon}]", str(ex["id"])))
        except Exception as e:
            menu.add_option(Option(f"Error loading results: {e}", disabled=True))

        await self._set_content_text("Select an execution to view details")

    async def update_settings_view(self):
        self.current_view = "settings"
        self.query_one("#list-label", Label).update("Settings")
        menu = self.query_one("#function-list", OptionList)
        menu.clear_options()
        menu.add_option(Option("Clear Execution History", "clear-history"))
        menu.add_option(Option("Reset Database (Clear All Data)", "reset-db"))
        await self._set_content_text(
            "Settings: Use arrow keys to navigate, Enter to select."
        )

    async def _clear_form_widgets(self):
        """Remove previously mounted dynamic widgets before creating a new form."""
        content_area = self.query_one("#content-area", VerticalScroll)
        for widget in list(self._form_widgets):
            try:
                await widget.remove()
            except Exception:
                pass
        self._form_widgets.clear()
        self._dynamic_inputs.clear()
        self._current_form_function = None  # اضافه شد
        self.selected = None
        # Clear residual children as a defensive measure, preventing duplicate IDs.
        try:
            await content_area.remove_children()
        except Exception:
            pass

    async def show_function_form(self, function_name: str):
        """Render a parameter form for the selected function."""
        if not function_name or function_name not in self.registry:
            self._current_form_function = None
            await self.status_update("No function selected")
            return

        await self._clear_form_widgets()
        self.selected = function_name
        self._current_form_function = function_name

        meta = self.registry.get(function_name, {})
        sig = meta.get("signature")
        if not sig:
            await self.run_function(function_name, {})
            return

        content_area = self.query_one("#content-area", VerticalScroll)

        heading = Static(self._build_form_content(function_name, meta, sig), id="form-heading")
        await content_area.mount(heading)
        self._form_widgets.append(heading)

        defaults = meta.get("defaults", {})
        required = meta.get("required", [])
        for param_name, param in sig.parameters.items():
            type_hint = param.annotation if param.annotation != inspect.Parameter.empty else str
            type_str = getattr(type_hint, "__name__", str(type_hint))
            input_widget = Input(
                id=f"form-{param_name}",
                placeholder=f"{type_str} (required)" if param_name in required else f"{type_str} (optional)",
            )
            default_val = defaults.get(param_name)
            if default_val is not None:
                input_widget.value = str(default_val)

            label = Label(f"{param_name}:", classes="param-label")
            await content_area.mount(label)
            await content_area.mount(input_widget)
            self._dynamic_inputs[param_name] = input_widget
            self._form_widgets.extend([label, input_widget])

        result_preview = Static("", id="result-preview")
        await content_area.mount(result_preview)
        self._form_widgets.append(result_preview)

        button_container = Horizontal(id="form-buttons")
        await content_area.mount(button_container)
        self._form_widgets.append(button_container)

        exec_btn = Button("▶ Execute Function", id="execute-fn", variant="primary")
        cancel_btn = Button("Cancel", id="cancel-fn", variant="default")
        show_res_btn = Button("Show Result", id="show-result-btn", variant="success", disabled=True)

        await button_container.mount(exec_btn, cancel_btn, show_res_btn)
        self._form_widgets.extend([exec_btn, cancel_btn, show_res_btn])

    def _build_form_content(self, function_name: str, meta: Dict, sig) -> str:
        label = meta.get("label", function_name)
        desc = meta.get("description", "")
        required = meta.get("required", [])
        required_hint = f"\n[red]Required:[/red] {', '.join(required)}" if required else ""
        return f"[bold cyan]{label}[/bold cyan]\n{desc}{required_hint}\n\nEnter parameters below:"

    async def _on_execute_function(self):
        """Execute the currently selected function with form values."""
        func_name = self._current_form_function
        if not func_name or func_name not in self.registry:
            await self.status_update("No function selected to execute")
            await self._set_content_text("[red]Error[/red]: No function selected. Choose a function from the list first.")
            return

        params: Dict[str, Any] = {}
        meta = self.registry.get(func_name, {})
        sig = meta.get("signature")
        for param_name, input_widget in self._dynamic_inputs.items():
            raw = input_widget.value
            if raw == "":
                continue
            param = sig.parameters.get(param_name) if sig else None
            annotation = param.annotation if param else inspect.Parameter.empty
            params[param_name] = self._coerce_parameter(raw, annotation)

        await self.run_function(func_name, params)

    @staticmethod
    def _coerce_parameter(raw: str, annotation: Any) -> Any:
        """Convert text input into the function's annotated type when possible."""
        if annotation is inspect.Parameter.empty or annotation is str:
            return raw
        try:
            if annotation is bool:
                lowered = raw.strip().lower()
                if lowered in {"true", "1", "yes", "y"}:
                    return True
                if lowered in {"false", "0", "no", "n"}:
                    return False
                return raw
            if annotation in (int, float):
                return annotation(raw)
            if annotation in (dict, list):
                return json.loads(raw)
        except (TypeError, ValueError, json.JSONDecodeError):
            return raw
        return raw

    async def _on_cancel_form(self):
        await self._clear_form_widgets()
        self._current_form_function = None
        self.selected = None
        await self._set_content_text("Select a function to execute")
        await self.status_update("Form cancelled — select a function to run")

    @staticmethod
    def _truncate_preview(text: str, max_len: int = 100) -> str:
        """Return the first line of *text*, truncated to *max_len* characters."""
        if not text:
            return ""
        first_line = text.splitlines()[0]
        if len(first_line) > max_len:
            first_line = first_line[:max_len - 3] + "..."
        return first_line

    async def _clear_content_area_buttons(self) -> None:
        """Remove any previously mounted 'Show Result' button from the content area."""
        content_area = self.query_one("#content-area", Static)
        try:
            btn = content_area.query_one("#show-result-btn", Button)
            await btn.remove()
        except Exception:
            pass

    async def run_function(self, function_name: str, params: Dict[str, Any]):
        """Execute and display a function result, without destroying the form."""
        if not function_name or function_name not in self.registry:
            message = f"Function '{function_name}' is not registered"
            await self._set_content_text(f"[red]Error[/red]: {message}")
            await self.status_update("Execution failed — invalid function selection")
            return

        await self.status_update(f"Running {function_name}...")
        try:
            result = execute_function(function_name, kwargs=params)

            if self.db:
                try:
                    self.db.log_function_execution(
                        function_name, result.success, result.duration,
                        result.type, result.error, None
                    )
                except Exception:
                    logger.exception("Failed to log function execution")

            if result.success:
                if isinstance(result.output, dict):
                    display_str = json.dumps(result.output, indent=2, ensure_ascii=False)
                elif isinstance(result.output, list) and result.type == "table":
                    table = Table(show_lines=True)
                    if result.output and isinstance(result.output[0], dict):
                        for key in result.output[0].keys():
                            table.add_column(str(key))
                        for row in result.output:
                            table.add_row(*[str(row.get(k, "")) for k in result.output[0].keys()])
                    else:
                        for index, value in enumerate(result.output):
                            table.add_row(str(index), str(value))
                    display_str = str(table)
                else:
                    display_str = str(result.output)

                self._last_result_output = display_str
                self._last_result_raw = result.output
                preview = self._truncate_preview(display_str)

                try:
                    preview_widget = self.query_one("#result-preview", Static)
                    preview_widget.update(f"[green]Success[/green] ({result.duration:.3f}s)\n\n{preview}")
                    self.query_one("#show-result-btn", Button).disabled = False
                except Exception:
                    pass

                await self.status_update(f"Completed: {result.type} output")
            else:
                details = result.error or "Unknown execution error"
                traceback_text = (result.metadata or {}).get("traceback")
                if traceback_text:
                    details += f"\n\n[dim]Traceback:[/dim]\n{traceback_text}"

                try:
                    preview_widget = self.query_one("#result-preview", Static)
                    preview_widget.update(f"[red]Execution failed[/red]\n\n{details}")
                    self.query_one("#show-result-btn", Button).disabled = False
                except Exception:
                    pass
                await self.status_update("Execution failed")
        except Exception as e:
            logger.exception("Function execution failed")
            try:
                preview_widget = self.query_one("#result-preview", Static)
                preview_widget.update(f"[red]Exception[/red]: {type(e).__name__}: {e}")
            except Exception:
                pass
            await self.status_update(f"Error: {e}")

    async def show_chain_creation(self):
        """Show the chain builder interface."""
        self._chain_builder_mode = True
        # Use a placeholder name to avoid validation errors during initialization;
        # the real name will be entered by the user and validated on save.
        self._chain_being_built = create_chain("new-chain", "New Chain", "")
        self._chain_step_params = {}
        await self._render_chain_builder()

    async def show_chain_execution(self):
        """Show the chain execution interface."""
        self._chain_builder_mode = False
        await self._render_chain_execution_list()

    # ------------------------------------------------------------------
    # Chain Builder UI
    # ------------------------------------------------------------------

    async def _render_chain_builder(self):
        """Render the chain builder form in the content area."""
        content_area = self.query_one("#content-area", VerticalScroll)
        await content_area.remove_children()

        chain = self._chain_being_built

        # Preserve metadata the user typed into the inputs before rebuilding.
        # The chain object is the source of truth, so sync in-flight edits
        # back into it first; this keeps name/label/desc intact across add /
        # move / remove / configure operations.
        first_render = self._chain_name_input is None
        if not first_render:
            chain.name = self._chain_name_input.value.strip()
            chain.label = self._chain_label_input.value.strip() or chain.label
            chain.description = self._chain_desc_input.value.strip()

        await content_area.mount(
            Static("[bold cyan]Chain Builder[/bold cyan]", id="chain-builder-heading")
        )

        # Chain metadata inputs
        self._chain_name_input = Input(placeholder="Chain name (required)", id="chain-name-input")
        self._chain_label_input = Input(placeholder="Display label", id="chain-label-input")
        self._chain_desc_input = Input(placeholder="Description (optional)", id="chain-desc-input")
        # First render starts with an empty name (user must enter a valid
        # name); subsequent renders restore the value the user entered.
        self._chain_name_input.value = "" if first_render else chain.name
        self._chain_label_input.value = chain.label or ""
        self._chain_desc_input.value = chain.description or ""

        await content_area.mount(Label("Chain Name:"))
        await content_area.mount(self._chain_name_input)
        await content_area.mount(Label("Display Label:"))
        await content_area.mount(self._chain_label_input)
        await content_area.mount(Label("Description:"))
        await content_area.mount(self._chain_desc_input)

        # Step selector — shows all registered functions
        await content_area.mount(Label("[bold]Add Step — Select a function:[/bold]"))
        step_selector = OptionList(id="chain-step-selector")
        for fname in sorted(self.registry.keys()):
            meta = self.registry[fname]
            label = meta.get("label", fname)
            desc = meta.get("description", "")
            show = f"{label}" + (f" — {desc}" if desc else "")
            step_selector.add_option(Option(show, fname))
        await content_area.mount(step_selector)

        # Show current steps (in execution order)
        await content_area.mount(Label("[bold]CHAIN STEPS — Execution Order[/bold]"))
        for i, step in enumerate(chain.steps):
            await content_area.mount(self._step_row(step, i, len(chain.steps)))

        # Action buttons
        action_container = Horizontal(id="chain-builder-actions")
        await content_area.mount(action_container)
        save_btn = Button("Save Chain", id="chain-save-btn", variant="success")
        cancel_btn = Button("Cancel", id="chain-cancel-btn", variant="default")
        await action_container.mount(save_btn)
        await action_container.mount(cancel_btn)

        await self.status_update("Chain builder ready — select a function to add it as a step")

    def _format_chain_steps(self) -> str:
        """Format the current chain steps for display as a static text summary."""
        chain = self._chain_being_built
        if not chain.steps:
            return "No steps added yet."

        lines = []
        for i, step in enumerate(chain.steps):
            label = f" ({step.label})" if step.label else ""
            lines.append(f"{i + 1}. {step.function_name}{label} [uuid={step.uuid[:8]}]")
            for p in step.params:
                bt = p.binding_type.value
                if bt == BindingType.LITERAL.value:
                    lines.append(f"   - {p.name}: literal = {p.value}")
                elif bt == BindingType.USER_INPUT.value:
                    lines.append(f"   - {p.name}: user input (\"{p.prompt}\")")
                elif bt == BindingType.PREVIOUS_STEP.value:
                    lines.append(f"   - {p.name}: output of step {p.source_step_uuid[:8]}")
        return "\n".join(lines)

    def _step_binding_summary(self, step: ChainStep) -> str:
        """Return a short summary of a step's parameter bindings."""
        parts: List[str] = []
        for p in step.params:
            bt = p.binding_type.value
            if bt == BindingType.LITERAL.value:
                parts.append(f"{p.name}=literal({p.value!r})")
            elif bt == BindingType.USER_INPUT.value:
                parts.append(f'{p.name}=user_input("{p.prompt}")')
            elif bt == BindingType.PREVIOUS_STEP.value:
                parts.append(f"{p.name}=previous({p.source_step_uuid[:8]})")
        return " | ".join(parts) if parts else "no params"

    def _step_row(self, step: ChainStep, index: int, total: int) -> Horizontal:
        """Build a row summarizing a single chain step with move/remove/configure controls."""
        return Horizontal(
            Label(f"{index + 1}. {step.function_name}" + (f" ({step.label})" if step.label else "")),
            Static(self._step_binding_summary(step), id=f"step-summary-{step.uuid}"),
            Button("Configure", id=f"step-configure-{step.uuid}", variant="default"),
            Button("Up", id=f"step-moveup-{step.uuid}", variant="default", disabled=index == 0),
            Button("Down", id=f"step-movedown-{step.uuid}", variant="default", disabled=index == total - 1),
            Button("Remove", id=f"step-remove-{step.uuid}", variant="default"),
            id=f"step-row-{step.uuid}",
        )

    async def _on_exec_chain_pressed(self):
        """Handle executing a selected chain from the execution list."""
        try:
            selector = self.query_one("#exec-chain-selector", OptionList)
            index = selector.highlighted
            if index is None or index < 0:
                await self.status_update("[red]Select a chain first[/red]")
                return
            option = selector.get_option_at_index(index)
            chain_name = option.id
            if chain_name:
                self._selected_execute_chain = chain_name
                await self._on_execute_selected_chain(chain_name)
            else:
                await self.status_update("[red]Invalid chain selected[/red]")
        except OptionDoesNotExist:
            # No chain selector available — likely no chains saved yet
            await self.status_update("[red]No chains available to execute[/red]")

    async def _on_add_step_to_chain(self, function_name: str):
        """Add a new step with the given function to the chain being built."""
        chain = self._chain_being_built
        step = add_step(chain, function_name)

        # Auto-configure parameters: use defaults where available, literal otherwise
        func_meta = self.registry.get(function_name, {})
        sig = func_meta.get("signature")
        defaults = func_meta.get("defaults", {})
        required = func_meta.get("required", [])

        if sig:
            for param_name, param in sig.parameters.items():
                if param_name in defaults and defaults[param_name] is not None:
                    step.params.append(literal(param_name, defaults[param_name]))
                elif param_name in defaults:
                    step.params.append(literal(param_name, defaults[param_name]))
                elif param_name not in required and param.default != inspect.Parameter.empty:
                    step.params.append(literal(param_name, param.default))
                else:
                    step.params.append(literal(param_name, ""))

        self._chain_step_params[step.uuid] = step.params

        await self._render_chain_builder()
        await self.status_update(f"Added step: {function_name}")

    async def _refresh_chain_steps_display(self):
        """Refresh the steps display in the chain builder."""
        try:
            display = self.query_one("#chain-steps-display", Static)
            display.update(self._format_chain_steps())
        except Exception:
            pass

    async def _on_configure_step_params(self, step_uuid: str):
        """Configure parameter bindings for a step within the Chain Builder."""
        chain = self._chain_being_built
        step = chain.get_step_by_uuid(step_uuid)
        if not step:
            return

        content_area = self.query_one("#content-area", VerticalScroll)
        await content_area.remove_children()
        await content_area.mount(
            Static(f"[bold]Configure Step: {step.function_name}[/bold]", id="step-config-heading")
        )
        await content_area.mount(
            Static(self._step_binding_summary(step), id="step-config-summary")
        )

        func_meta = self.registry.get(step.function_name, {})
        sig = func_meta.get("signature")
        if sig:
            for param_name, param in sig.parameters.items():
                await content_area.mount(Label(f"{param_name}:"))

                binding_select = Select(
                    options=[
                        ("Literal", "literal"),
                        ("Default", "default"),
                        ("Previous Step Output", "previous_step"),
                    ],
                    id=f"bind-{step_uuid}-{param_name}",
                    type_to_search=True,
                )
                await content_area.mount(binding_select)

                value_input = Input(
                    placeholder="Enter literal value",
                    id=f"val-{step_uuid}-{param_name}",
                )
                await content_area.mount(value_input)

        action_container = Horizontal(id="step-config-actions")
        await content_area.mount(action_container)
        done_btn = Button("Done", id=f"step-done-{step_uuid}", variant="success")
        cancel_btn = Button("Cancel", id=f"step-cancel-{step_uuid}", variant="default")
        await action_container.mount(done_btn)
        await action_container.mount(cancel_btn)

        await self.status_update(f"Configuring step: {step.function_name}")

    async def _on_remove_step(self, step_uuid: str):
        """Remove a step from the chain being built."""
        chain = self._chain_being_built
        chain.steps = [s for s in chain.steps if s.uuid != step_uuid]
        chain.steps.sort(key=lambda s: s.order)
        # Renumber orders
        for i, step in enumerate(chain.steps):
            step.order = i

        if step_uuid in self._chain_step_params:
            del self._chain_step_params[step_uuid]

        await self._render_chain_builder()

    async def _on_move_step(self, step_uuid: str, delta: int):
        """Move a step up (delta=-1) or down (delta=+1) in execution order."""
        chain = self._chain_being_built
        position = None
        for i, step in enumerate(chain.steps):
            if step.uuid == step_uuid:
                position = i
                break
        if position is None:
            return
        target = position + delta
        if target < 0 or target >= len(chain.steps):
            return
        steps = list(chain.steps)
        step = steps.pop(position)
        steps.insert(target, step)
        for i, s in enumerate(steps):
            s.order = i
        chain.steps = steps
        await self._render_chain_builder()
        await self.status_update(f"Moved {step.function_name} to position {target + 1}")

    async def _on_save_chain(self):
        """Save the current chain being built."""
        chain = self._chain_being_built
        name = chain.name
        label = chain.label

        # Get values from inputs
        if self._chain_name_input:
            name = self._chain_name_input.value.strip()
        if self._chain_label_input:
            label = self._chain_label_input.value.strip()
        if self._chain_desc_input:
            chain.description = self._chain_desc_input.value.strip()

        if not name:
            await self.status_update("[red]Chain name is required[/red]")
            return

        chain.name = name
        chain.label = label or name

        # Validate
        errors = validate_chain(chain)
        if errors:
            await self.status_update(f"[red]Validation errors: {'; '.join(errors)}[/red]")
            return

        try:
            save_chain(chain)
            await self.status_update(f"Chain '{name}' saved successfully")
            await self._render_chain_saved(chain.name)
        except Exception as e:
            logger.exception("Failed to save chain")
            await self.status_update(f"[red]Failed to save chain: {e}[/red]")

    async def _render_chain_saved(self, chain_name: str):
        """Display confirmation after saving a chain."""
        content_area = self.query_one("#content-area", VerticalScroll)
        await content_area.remove_children()
        await content_area.mount(
            Static(f"[green]Chain '{chain_name}' saved successfully.[/green]")
        )

    async def _on_cancel_chain_builder(self):
        """Cancel chain building and return to the chains view."""
        self._chain_builder_mode = False
        self._chain_being_built = None
        self._chain_step_params = {}
        self.current_view = "chains"
        await self.update_chains_view()

    # ------------------------------------------------------------------
    # Chain Execution UI
    # ------------------------------------------------------------------

    async def _render_chain_execution_list(self):
        """Render the list of saved chains for execution."""
        content_area = self.query_one("#content-area", VerticalScroll)
        await content_area.remove_children()

        await content_area.mount(Static("[bold cyan]Execute Chain[/bold cyan]"))

        chains = list_chains()
        if not chains:
            await content_area.mount(
                Static("No chains found. Create one first.")
            )
            await self.status_update("No chains to execute")
            return

        await content_area.mount(Label("[bold]Select a chain to execute:[/bold]"))
        chain_menu = OptionList(id="exec-chain-selector")
        for chain in chains:
            show = f"{chain['label']} ({chain['name']})"
            chain_menu.add_option(Option(show, chain["name"]))
        await content_area.mount(chain_menu)

        exec_btn = Button("Execute Selected Chain", id="run-chain-btn", variant="success")
        cancel_btn = Button("Cancel", id="exec-chain-cancel-btn", variant="default")
        await content_area.mount(Horizontal(exec_btn, cancel_btn, id="exec-chain-actions"))

        await self.status_update(f"Loaded {len(chains)} chain(s) — select one to execute")

    async def _on_execute_selected_chain(self, chain_name: str):
        """Load a saved chain, gather any required user input, then execute it.

        Steps that derive all their parameter values from literals or from a
        previous step's output are executed immediately.  Parameters bound to
        ``user_input`` (or any binding that has no resolvable value) are surfaced
        as input controls and the user is asked to press the **Run Chain**
        button once they have been filled in.
        """
        chain = load_chain(chain_name)
        if not chain:
            await self.status_update(f"[red]Chain '{chain_name}' not found[/red]")
            return

        content_area = self.query_one("#content-area", VerticalScroll)
        await content_area.remove_children()
        await content_area.mount(
            Static(f"[bold cyan]Execute Chain: {chain.label}[/bold cyan]")
        )
        await content_area.mount(
            Static(f"Description: {chain.description or 'None'}")
        )

        # --- collect parameters that require user input -------------------
        registry = get_registry()
        user_input_bindings: List[tuple] = []  # (step_index, binding, input_widget)
        needs_input = False

        for i, step in enumerate(chain.steps):
            await content_area.mount(
                Static(
                    f"[bold]Step {i + 1}:[/bold] {step.function_name}"
                    + (f" ({step.label})" if step.label else "")
                )
            )

            func_meta = registry.get(step.function_name, {})
            sig = func_meta.get("signature")
            param_objs = sig.parameters if sig else {}
            for p in step.params:
                bt = p.binding_type.value
                if bt == BindingType.LITERAL.value:
                    await content_area.mount(
                        Static(f"  {p.name}: literal = {p.value!r}")
                    )
                elif bt == BindingType.PREVIOUS_STEP.value:
                    src = chain.get_step_by_uuid(p.source_step_uuid) if p.source_step_uuid else None
                    src_name = src.function_name if src else (p.source_step_uuid or "?")
                    await content_area.mount(
                        Static(
                            f"  {p.name}: from previous step [{p.source_step_uuid[:8]}] ({src_name})"
                        )
                    )
                elif bt == BindingType.USER_INPUT.value:
                    needs_input = True
                    await content_area.mount(
                        Label(f"  {p.name} (required input):")
                    )
                    inp = Input(
                        placeholder=p.prompt or f"Value for {p.name}",
                        id=f"ui-{i}-{p.name}",
                    )
                    await content_area.mount(inp)
                    user_input_bindings.append((i, p, inp))

        if not needs_input:
            await content_area.mount(
                Static(
                    "[green]All parameters are supplied by literals or previous-step outputs.[/green]"
                )
            )

        run_btn = Button("▶ Run Chain", id="run-chain-execute", variant="primary")
        cancel_btn = Button("Cancel", id="run-chain-cancel", variant="default")
        await content_area.mount(
            Horizontal(run_btn, cancel_btn, id="chain-exec-actions")
        )

        # If nothing requires user input, execute straight away so the user
        # isn't forced to press another button to see results.
        self._selected_execute_chain = chain_name
        if not needs_input:
            await self._do_execute_selected_chain(chain_name, {})

    async def _do_execute_selected_chain(
        self, chain_name: str, extra_user_inputs: Optional[Dict[str, str]] = None
    ):
        """Execute a chain via the existing Chain Engine and render step results."""
        chain = load_chain(chain_name)
        if not chain:
            await self.status_update(f"[red]Chain '{chain_name}' not found[/red]")
            return

        content_area = self.query_one("#content-area", VerticalScroll)
        await content_area.remove_children()
        await content_area.mount(
            Static(f"[bold cyan]Executing Chain: {chain.label}[/bold cyan]")
        )
        await self.status_update(f"Executing chain '{chain_name}'...")

        user_inputs: Dict[str, str] = dict(extra_user_inputs or {})
        if extra_user_inputs is None:
            # Gather values from any input widgets still present on screen.
            try:
                for w in content_area.query(Input):
                    if w.id and w.id.startswith("ui-"):
                        user_inputs[w.id.replace("ui-", "")] = w.value
            except Exception:
                pass

        try:
            execution = execute_chain(chain, user_inputs=user_inputs)
        except Exception as e:
            logger.exception("Chain execution raised")
            await content_area.mount(
                Static(f"[red]Execution error: {type(e).__name__}: {e}[/red]")
            )
            await self.status_update(f"[red]Chain execution failed: {e}[/red]")
            return

        await content_area.mount(
            Static(f"Status: [bold]{execution.status.value}[/bold]")
        )
        if execution.completed_at and execution.started_at:
            await content_area.mount(
                Static(
                    f"Completed in {execution.completed_at - execution.started_at:.3f}s"
                )
            )

        final_output = None
        for i, step in enumerate(chain.steps):
            result = execution.step_results.get(step.uuid)
            if not result:
                continue
            ok = result.status.value == "success"
            status_icon = "[green]✓[/green]" if ok else "[red]✗[/red]"
            step_title = f"{status_icon} Step {i + 1}: {step.function_name}"
            if step.label:
                step_title += f" ({step.label})"
            await content_area.mount(Static(step_title))

            if result.error:
                await content_area.mount(
                    Static(f"  [red]Error: {result.error}[/red]")
                )
            if result.output is not None:
                output_str = str(result.output)
                if len(output_str) > 300:
                    output_str = output_str[:297] + "..."
                await content_area.mount(Static(f"  Output: {output_str}"))
            if result.output_summary:
                await content_area.mount(
                    Static(f"  Summary: {result.output_summary}")
                )
            if result.duration:
                await content_area.mount(
                    Static(f"  Duration: {result.duration:.3f}s")
                )

            if ok:
                final_output = result.output

        # Final summary
        if execution.status == ChainStatus.SUCCESS:
            await content_area.mount(
                Static(f"[green]Final result: {final_output!s}[/green]")
            )
        else:
            await content_area.mount(
                Static(
                    f"[red]Chain did not complete successfully ({execution.status.value})[/red]"
                )
            )

        # Save execution to database
        try:
            db = self.db or Database()
            db.save_chain_execution(chain_name, execution.status.value)
        except Exception:
            logger.exception("Failed to persist chain execution")

        await self.status_update(f"Chain execution complete: {execution.status.value}")

    async def _on_run_chain_execute_pressed(self):
        """Read input controls for the selected chain and execute it."""
        chain_name = self._selected_execute_chain
        if not chain_name:
            await self.status_update("[red]No chain selected[/red]")
            return
        await self._do_execute_selected_chain(chain_name)

    async def _on_run_chain_cancel_pressed(self):
        """Abort execution and return to the chain list."""
        content_area = self.query_one("#content-area", VerticalScroll)
        await content_area.remove_children()
        await content_area.mount(Static("[yellow]Chain execution cancelled.[/yellow]"))
        await self.status_update("Chain execution cancelled")
        await self._render_chain_execution_list()

    async def show_chain_details(self, chain_name: str):
        try:
            chain = load_chain(chain_name)
            if chain:
                detail = f"[bold]{chain.label}[/bold]\n\nName: {chain.name}\n"
                detail += f"Description: {chain.description or 'None'}\n\n"

                # Validate and show validation status
                errors = validate_chain(chain)
                if errors:
                    detail += f"[red]Validation errors:[/red]\n"
                    for err in errors:
                        detail += f"  - {err}\n"
                    detail += "\n"

                detail += f"Steps ({len(chain.steps)}):\n"
                for i, step in enumerate(chain.steps):
                    detail += f"  {i + 1}. {step.function_name}"
                    if step.label:
                        detail += f" ({step.label})"
                    detail += "\n"
                    for p in step.params:
                        bt = p.binding_type.value
                        if bt == BindingType.LITERAL.value:
                            detail += f"     • {p.name}: literal = {p.value}"
                        elif bt == BindingType.USER_INPUT.value:
                            detail += f"     • {p.name}: user input (\"{p.prompt}\")"
                        elif bt == BindingType.PREVIOUS_STEP.value:
                            detail += f"     • {p.name}: output of step {p.source_step_uuid[:8]}"
                        detail += "\n"

                # Add execute button for this specific chain
                detail += f"\n[green]Use 'Execute Chain' button to run this chain.[/green]"
                await self._set_content_text(detail)
            else:
                await self._set_content_text(f"Chain '{chain_name}' not found")
        except Exception as e:
            logger.exception("Failed to load chain details")
            await self._set_content_text(f"[red]Error:[/red] {e}")

    async def show_execution_details(self, execution_id: str):
        await self._set_content_text(
            f"Execution details for ID {execution_id}\n\nDetailed result view is not implemented yet."
        )

    async def handle_setting(self, setting_id: str):
        if setting_id == "clear-history":
            try:
                db = self.db or Database()
                # Only clear function history if the database supports this method.
                if hasattr(db, "clear_execution_history"):
                    db.clear_execution_history()
                await self._set_content_text("Execution history cleared.")
                await self.status_update("Execution history cleared")
            except Exception as e:
                await self._set_content_text(f"[red]Error:[/red] {e}")
        elif setting_id == "reset-db":
            confirmed = await self.app.push_screen(
                ConfirmScreen(
                    "Reset Database (Clear All Data)\n\n"
                    "This will permanently delete all saved chains, chain "
                    "executions, function execution logs, users, and settings.\n"
                    "This action cannot be undone. Back up your data first.\n\n"
                    "Confirm to proceed."
                )
            )
            if not confirmed:
                await self.status_update("Database reset cancelled")
                return
            try:
                db = self.db or Database()
                db.init_db()
                db.clear_all_data()
            except Exception as e:
                logger.exception("Database reset failed")
                await self._set_content_text(f"[red]Database reset failed:[/red] {e}")
                await self.status_update("Database reset failed")
                return
            # Clear in-memory chain-builder / execution state and refresh views.
            self._chain_being_built = None
            self._chain_step_params = {}
            self._selected_execute_chain = None
            if self.current_view == "chains":
                await self.update_chains_view()
            await self._set_content_text(
                "Database has been reset. All persisted data was cleared."
            )
            await self.status_update("Database reset complete")

    def action_refresh(self):
        self.run_worker(self.refresh_functions, exclusive=True)

    def action_quit(self):
        self.exit()

    def action_focus_functions(self):
        self.current_view = "functions"
        self.run_worker(self.update_function_list, exclusive=True)

    def action_focus_chains(self):
        self.current_view = "chains"
        self.run_worker(self.update_chains_view, exclusive=True)

    def action_show_settings(self):
        self.current_view = "settings"
        self.run_worker(self.update_settings_view, exclusive=True)


def run():
    """Entry point for TUI."""
    HojjatTUIApplication().run()


if __name__ == "__main__":
    run()

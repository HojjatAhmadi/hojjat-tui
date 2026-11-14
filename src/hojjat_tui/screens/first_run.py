"""First-run account creation screen for HOJJAT TUI.

Shown when no user accounts exist yet.  Collects a username, password, and
password confirmation, validates the input, hashes the password, and
persists the account through the application's persistence layer.
"""

from typing import Optional

from textual.app import ComposeResult
from textual.binding import Binding
from textual.containers import Vertical, VerticalScroll
from textual.screen import Screen
from textual.widgets import Button, Input, Label, Static

from hojjat_tui.auth import AuthenticationService


class FirstRunScreen(Screen):
    """First-run account creation screen."""

    BINDINGS = [
        Binding("enter", "submit", "Submit", show=False),
        Binding("escape", "quit", "Quit", show=False),
    ]

    CSS = """
    FirstRunScreen {
        background: #1a1b26;
        layout: vertical;
        align: center middle;
    }

    #first-run-scroll {
        width: 100%;
        height: 100%;
        layout: vertical;
        align: center middle;
        overflow-y: auto;
    }

    #logo-container {
        width: auto;
        height: auto;
        margin-bottom: 1;
        align: center middle;
        content-align: center middle;
    }

    #logo {
        color: #bb9af7;
        text-align: center;
        content-align: center middle;
        width: auto;
        height: auto;
    }

    #title {
        width: auto;
        text-align: center;
        content-align: center middle;
        color: #c0caf5;
        text-style: bold;
        margin-bottom: 1;
    }

    #subtitle {
        width: auto;
        text-align: center;
        content-align: center middle;
        color: #9ece6a;
        text-style: italic;
        margin-bottom: 2;
    }

    #setup-form {
        layout: vertical;
        width: 60;
        max-width: 100%;
        height: auto;
        padding: 1 2;
        background: #24283b;
        border: round #7aa2f7;
        align: center middle;
    }

    #setup-form Label {
        width: 100%;
        color: #7aa2f7;
        text-style: bold;
        margin-top: 1;
        margin-bottom: 0;
    }

    #setup-form Input {
        width: 100%;
        margin-bottom: 1;
        background: #1a1b26;
        border: tall #7aa2f7;
    }

    #setup-form Input:focus {
        border: tall #bb9af7;
    }

    #setup-form Button {
        width: 100%;
        margin-top: 1;
        min-height: 3;
        background: #9ece6a;
        color: #1a1b26;
        border: tall #9ece6a;
    }

    #setup-form Button:hover {
        background: #73daca;
        border: tall #73daca;
    }

    #error {
        width: 100%;
        text-align: center;
        content-align: center middle;
        color: #f7768e;
        height: auto;
        margin-top: 1;
        display: none;
        text-style: bold;
    }

    #error.visible {
        display: block;
    }

    #footer-hint {
        width: 100%;
        text-align: center;
        content-align: center middle;
        color: #565f89;
        margin-top: 2;
        text-style: dim;
    }
    """

    def __init__(self, auth_service: AuthenticationService):
        super().__init__()
        self.auth = auth_service
        self._username_input: Optional[Input] = None
        self._password_input: Optional[Input] = None
        self._confirm_input: Optional[Input] = None
        self._error: Optional[Static] = None

    # -- composition ---------------------------------------------------

    def compose(self) -> ComposeResult:
        with VerticalScroll(id="first-run-scroll"):
            with Vertical(id="logo-container"):
                yield Static(self._render_logo(), id="logo")

            yield Label("Welcome to HOJJAT TUI", id="title")
            yield Label("Create your first account", id="subtitle")

            with Vertical(id="setup-form"):
                yield Label("Username")
                self._username_input = Input(
                    id="username-input",
                    placeholder="Choose a username",
                )
                yield self._username_input

                yield Label("Password")
                self._password_input = Input(
                    id="password-input",
                    placeholder="Choose a password",
                    password=True,
                )
                yield self._password_input

                yield Label("Confirm Password")
                self._confirm_input = Input(
                    id="confirm-input",
                    placeholder="Confirm your password",
                    password=True,
                )
                yield self._confirm_input

                yield Button("Create Account", id="create-btn", variant="success")

            self._error = Static("Account creation failed", id="error")
            yield self._error

            yield Label("Press Enter to create account  •  Esc to quit", id="footer-hint")

    # -- rendering helpers ---------------------------------------------

    @staticmethod
    def _render_logo() -> str:
        """Render the HOJJAT TUI logo with PyFiglet."""
        from pyfiglet import Figlet

        fonts = ("slant", "big", "standard", "small", "mini")
        for font in fonts:
            try:
                figlet = Figlet(font=font, width=100)
                rendered = figlet.renderText("HOJJAT TUI").rstrip()
                if rendered:
                    return rendered
            except Exception:
                continue
        return "HOJJAT TUI\nTerminal User Interface"

    # -- event handlers ------------------------------------------------

    def on_mount(self) -> None:
        self._username_input = self.query_one("#username-input", Input)
        self._password_input = self.query_one("#password-input", Input)
        self._confirm_input = self.query_one("#confirm-input", Input)
        self._error = self.query_one("#error", Static)
        self._username_input.focus()

    def action_submit(self) -> None:
        """Handle Enter-key submission."""
        self._attempt_create()

    def action_quit(self) -> None:
        """Escape quits the application."""
        self.app.exit()

    def on_button_pressed(self, event: Button.Pressed) -> None:
        if event.button.id == "create-btn":
            self._attempt_create()

    def _attempt_create(self) -> None:
        if not self._username_input or not self._password_input or not self._confirm_input:
            return

        username = (self._username_input.value or "").strip()
        password = self._password_input.value or ""
        confirm = self._confirm_input.value or ""

        if not username or not password or not confirm:
            self._show_error("Please fill in all fields.")
            return

        if password != confirm:
            self._show_error("Passwords do not match.")
            self._confirm_input.value = ""
            self._confirm_input.focus()
            return

        if len(password) < 6:
            self._show_error("Password must be at least 6 characters.")
            self._password_input.focus()
            return

        if self.auth.user_exists(username):
            self._show_error("Username already exists.")
            self._username_input.focus()
            return

        if self.auth.create_user(username, password, is_superuser=True):
            self.dismiss(True)
        else:
            self._show_error("Failed to create account. Please try again.")

    def _show_error(self, message: str) -> None:
        """Display error message and ensure it is visible to the user."""
        if self._error is None:
            self._error = self.query_one("#error", Static)

        self._error.update(f"❌ {message}")
        self._error.add_class("visible")
        self._error.refresh(layout=True)
        self._error.scroll_visible()

    def _hide_error(self) -> None:
        """Hide the error when the user starts typing again."""
        if self._error is None:
            self._error = self.query_one("#error", Static)

        self._error.remove_class("visible")

    def on_input_changed(self, event: Input.Changed) -> None:
        """Hide the error when the user starts typing again."""
        self._hide_error()

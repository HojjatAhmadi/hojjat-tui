"""Welcome / Login screen for HOJJAT TUI.

Displays a PyFiglet-rendered HOJJAT TUI logo, a product subtitle, and a
polished login form with masked password input.  Supports Enter-key
submission and shows validation errors inline without crashing.
"""

from typing import Optional

from pyfiglet import Figlet

from textual.app import ComposeResult
from textual.binding import Binding
from textual.containers import Vertical, VerticalScroll
from textual.screen import Screen
from textual.widgets import Button, Input, Label, Static

from hojjat_tui.auth import AuthenticationService


class WelcomeScreen(Screen):
    """Professional welcome / login screen."""

    BINDINGS = [
        Binding("enter", "submit", "Submit", show=False),
        Binding("escape", "quit", "Quit", show=False),
    ]

    CSS = """
    WelcomeScreen {
        background: #1a1b26;
        layout: vertical;
        align: center middle;
    }

    #welcome-scroll {
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

    #subtitle {
        width: auto;
        text-align: center;
        content-align: center middle;
        color: #9ece6a;
        text-style: italic;
        margin-bottom: 2;
    }

    #login-form {
        layout: vertical;
        width: 60;
        max-width: 100%;
        height: auto;
        padding: 1 2;
        background: #24283b;
        border: round #7aa2f7;
        align: center middle;
    }

    #login-form Label {
        width: 100%;
        color: #7aa2f7;
        text-style: bold;
        margin-top: 1;
        margin-bottom: 0;
    }

    #login-form Input {
        width: 100%;
        margin-bottom: 1;
        background: #1a1b26;
        border: tall #7aa2f7;
    }

    #login-form Input:focus {
        border: tall #bb9af7;
    }

    #login-form Button {
        width: 100%;
        margin-top: 1;
        min-height: 3;
        background: #7aa2f7;
        color: #1a1b26;
        border: tall #7aa2f7;
        text-style: bold;
    }

    #login-form Button:hover {
        background: #bb9af7;
        border: tall #bb9af7;
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
        self._error: Optional[Static] = None

    # -- composition ---------------------------------------------------

    def compose(self) -> ComposeResult:
        with VerticalScroll(id="welcome-scroll"):
            with Vertical(id="logo-container"):
                yield Static(self._render_logo(), id="logo")

            yield Label("Terminal Workflow Studio", id="subtitle")

            with Vertical(id="login-form"):
                yield Label("Username")
                self._username_input = Input(
                    id="username-input",
                    placeholder="Enter your username",
                )
                yield self._username_input

                yield Label("Password")
                self._password_input = Input(
                    id="password-input",
                    placeholder="Enter your password",
                    password=True,
                )
                yield self._password_input

                yield Button("Login", id="login-btn", variant="primary")

            self._error = Static("Invalid username or password", id="error")
            yield self._error

            yield Label("Press Enter to login  •  Esc to quit", id="footer-hint")

    # -- rendering helpers ---------------------------------------------

    @staticmethod
    def _render_logo() -> str:
        """Render the HOJJAT TUI logo with PyFiglet.

        Tries a list of professional fonts in order, falling back to a
        plain text wordmark if PyFiglet or every font fails.
        """
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
        self._error = self.query_one("#error", Static)
        self._username_input.focus()

    def action_submit(self) -> None:
        """Handle Enter-key submission."""
        self._attempt_login()

    def action_quit(self) -> None:
        """Escape quits the application."""
        self.app.exit()

    def on_button_pressed(self, event: Button.Pressed) -> None:
        if event.button.id == "login-btn":
            self._attempt_login()

    def _attempt_login(self) -> None:
        username = (self._username_input.value or "").strip() if self._username_input else ""
        password = self._password_input.value or "" if self._password_input else ""

        if not username or not password:
            self._show_error("Please enter both username and password.")
            return

        if self.auth.authenticate(username, password):
            self.dismiss(True)
        else:
            self._show_error("Invalid username or password.")
            # Clear the password field so the user retypes it.
            if self._password_input:
                self._password_input.value = ""
                self._password_input.focus()

    def _show_error(self, message: str) -> None:
        """Display error message and ensure it is visible to the user."""
        if self._error is None:
            self._error = self.query_one("#error", Static)

        self._error.update(f"❌ {message}")
        self._error.add_class("visible")
        # Force a layout refresh so the newly-visible widget participates
        # in scrolling, then scroll it into view.
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

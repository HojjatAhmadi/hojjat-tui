"""Welcome / Login screen for HOJJAT TUI.

Displays a PyFiglet-rendered HOJJAT TUI logo, a product subtitle, and a
polished login form with masked password input.  Supports Enter-key
submission and shows validation errors inline without crashing.
"""

from typing import Optional

from pyfiglet import Figlet

from textual.app import ComposeResult
from textual.binding import Binding
from textual.containers import Center, Vertical, VerticalScroll
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
    #welcome-root {
        layout: vertical;
        align: center middle;
        height: 100%;
        width: 100%;
    }

    #welcome-scroll {
        height: 100%;
        width: 100%;
        layout: vertical;
        align: center middle;
    }

    #logo {
        width: auto;
        height: auto;
        text-align: center;
        content-align: center middle;
        color: #bb9af7;
        margin-bottom: 1;
        overflow: hidden;
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
        max-width: 90%;
        height: auto;
        padding: 1;
        background: #24283b;
        border: round #7aa2f7;
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
    }

    #login-form Button {
        width: 100%;
        margin-top: 1;
        min-height: 3;
    }

    #error {
        width: 100%;
        text-align: center;
        content-align: center middle;
        color: #f7768e;
        height: auto;
        margin-top: 1;
        display: none;
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
        with Center(id="welcome-root"):
            with VerticalScroll(id="welcome-scroll"):
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

    def _show_error(self, message: str) -> None:
        if self._error is None:
            return
        self._error.update(message)
        self._error.add_class("visible")

    def _hide_error(self) -> None:
        if self._error is None:
            return
        self._error.remove_class("visible")

    def on_input_changed(self, event: Input.Changed) -> None:
        """Hide the error when the user starts typing again."""
        self._hide_error()

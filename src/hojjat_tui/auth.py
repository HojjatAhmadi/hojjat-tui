"""Authentication service for HOJJAT TUI.

Provides authentication logic separate from the UI layer. All password
hashing and verification is delegated to the persistence layer which uses
bcrypt.  Generic error messages avoid revealing whether a username exists.
"""

import logging
from typing import Optional

from hojjat_tui.persistence import Database

logger = logging.getLogger("hojjat_tui.auth")


class AuthenticationError(Exception):
    """Raised when authentication fails.

    The message is intentionally generic to avoid leaking whether a
    username exists.
    """

    def __init__(self, message: str = "Invalid username or password"):
        super().__init__(message)


class AuthenticationService:
    """Handles user authentication and account creation.

    All credential storage and verification is delegated to the
    :class:`~hojjat_tui.persistence.Database` persistence layer.
    Passwords are never stored or compared in plain text.
    """

    def __init__(self, db: Optional[Database] = None):
        self.db = db or Database()

    # ------------------------------------------------------------------
    # Account queries
    # ------------------------------------------------------------------

    def has_users(self) -> bool:
        """Return True if at least one user account exists."""
        try:
            return self.db.get_user_count() > 0
        except Exception:
            logger.exception("Failed to check user count")
            return False

    def user_exists(self, username: str) -> bool:
        """Return True if *username* exists in the database."""
        try:
            return self.db.user_exists(username)
        except Exception:
            logger.exception("Failed to check user existence")
            return False

    # ------------------------------------------------------------------
    # Authentication
    # ------------------------------------------------------------------

    def authenticate(self, username: str, password: str) -> bool:
        """Verify credentials for *username* and *password*.

        Returns True on success.  Returns False (never raises) on failure
        so callers cannot distinguish "wrong password" from "unknown user".
        """
        if not username or not password:
            return False
        try:
            return self.db.verify_user(username, password)
        except Exception:
            logger.exception("Authentication error for user %r", username)
            return False

    # ------------------------------------------------------------------
    # Account creation
    # ------------------------------------------------------------------

    def create_user(
        self,
        username: str,
        password: str,
        email: Optional[str] = None,
        is_superuser: bool = False,
    ) -> bool:
        """Create a new user account with a bcrypt-hashed password.

        Returns True on success, False if the username already exists.
        Passwords are hashed by the persistence layer before storage.
        """
        if not username or not password:
            return False
        try:
            return self.db.create_user(
                username,
                password,
                email=email,
                is_superuser=is_superuser,
            )
        except Exception:
            logger.exception("Failed to create user %r", username)
            return False

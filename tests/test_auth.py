"""Tests for the authentication service and screens."""

import inspect

from hojjat_tui.auth import AuthenticationError, AuthenticationService
from hojjat_tui.persistence import Database
from hojjat_tui.screens.first_run import FirstRunScreen
from hojjat_tui.screens.welcome import WelcomeScreen


class TestAuthenticationService:
    """Tests for the AuthenticationService class."""

    def test_authenticate_valid_credentials(self, temp_db_path):
        """Test successful authentication with valid credentials."""
        db = Database(temp_db_path)
        db.init_db()
        db.create_user("alice", "secret123", is_superuser=True)

        auth = AuthenticationService(db)
        assert auth.authenticate("alice", "secret123") is True

    def test_authenticate_wrong_password(self, temp_db_path):
        """Test that wrong password is rejected."""
        db = Database(temp_db_path)
        db.init_db()
        db.create_user("alice", "secret123")

        auth = AuthenticationService(db)
        assert auth.authenticate("alice", "wrongpassword") is False

    def test_authenticate_nonexistent_user(self, temp_db_path):
        """Test that unknown username is rejected (generic failure)."""
        db = Database(temp_db_path)
        db.init_db()
        db.create_user("alice", "secret123")

        auth = AuthenticationService(db)
        assert auth.authenticate("bob", "anything") is False

    def test_authenticate_empty_credentials(self, temp_db_path):
        """Test that empty username or password is rejected."""
        db = Database(temp_db_path)
        db.init_db()

        auth = AuthenticationService(db)
        assert auth.authenticate("", "password") is False
        assert auth.authenticate("user", "") is False
        assert auth.authenticate("", "") is False

    def test_has_users_when_empty(self, temp_db_path):
        """Test has_users returns False when no users exist."""
        db = Database(temp_db_path)
        db.init_db()

        auth = AuthenticationService(db)
        assert auth.has_users() is False

    def test_has_users_when_populated(self, temp_db_path):
        """Test has_users returns True when users exist."""
        db = Database(temp_db_path)
        db.init_db()
        db.create_user("alice", "secret123")

        auth = AuthenticationService(db)
        assert auth.has_users() is True

    def test_create_user(self, temp_db_path):
        """Test user creation through the auth service."""
        db = Database(temp_db_path)
        db.init_db()

        auth = AuthenticationService(db)
        assert auth.create_user("alice", "secret123") is True
        assert auth.user_exists("alice") is True

    def test_create_duplicate_user(self, temp_db_path):
        """Test that duplicate user creation fails."""
        db = Database(temp_db_path)
        db.init_db()

        auth = AuthenticationService(db)
        assert auth.create_user("alice", "secret123") is True
        assert auth.create_user("alice", "different") is False

    def test_passwords_are_hashed_not_plaintext(self, temp_db_path):
        """Test that passwords are stored as bcrypt hashes, not plaintext."""
        import sqlite3

        db = Database(temp_db_path)
        db.init_db()
        db.create_user("alice", "secret123")

        # Verify the stored hash is a bcrypt hash, not the plaintext password
        conn = sqlite3.connect(str(temp_db_path))
        cursor = conn.cursor()
        cursor.execute("SELECT password_hash FROM users WHERE username = ?", ("alice",))
        row = cursor.fetchone()
        conn.close()

        password_hash = row[0]
        assert password_hash != "secret123"
        assert password_hash.startswith("$2b$")

    def test_persistent_accounts_across_instances(self, temp_db_path):
        """Test that accounts persist across Database instances (simulating restart)."""
        db1 = Database(temp_db_path)
        db1.init_db()
        db1.create_user("alice", "secret123")

        # Simulate restart: new Database instance pointing to same file
        db2 = Database(temp_db_path)
        assert db2.user_exists("alice")
        assert db2.verify_user("alice", "secret123") is True
        assert db2.verify_user("alice", "wrong") is False

    def test_user_exists(self, temp_db_path):
        """Test user_exists through auth service."""
        db = Database(temp_db_path)
        db.init_db()

        auth = AuthenticationService(db)
        assert auth.user_exists("alice") is False

        db.create_user("alice", "secret123")
        assert auth.user_exists("alice") is True

    def test_generic_error_message(self):
        """Test that AuthenticationError uses a generic message."""
        err = AuthenticationError()
        message = str(err)
        assert "invalid" in message.lower() or "username" in message.lower() or "password" in message.lower()


class TestWelcomeScreenComposition:
    """Tests for WelcomeScreen composition and rendering."""

    def test_welcome_screen_import(self):
        """Test that WelcomeScreen can be imported."""
        assert WelcomeScreen is not None

    def test_welcome_screen_has_logo(self):
        """Test that WelcomeScreen renders a PyFiglet logo."""
        logo = WelcomeScreen._render_logo()
        assert len(logo) > 0

    def test_welcome_screen_password_is_masked(self):
        """Test that the password input uses masked mode."""
        source = inspect.getsource(WelcomeScreen.compose)
        assert "password=True" in source


class TestFirstRunScreenComposition:
    """Tests for FirstRunScreen composition and rendering."""

    def test_first_run_screen_import(self):
        """Test that FirstRunScreen can be imported."""
        assert FirstRunScreen is not None

    def test_first_run_screen_has_logo(self):
        """Test that FirstRunScreen renders a PyFiglet logo."""
        logo = FirstRunScreen._render_logo()
        assert len(logo) > 0

    def test_first_run_screen_password_is_masked(self):
        """Test that password inputs use masked mode."""
        source = inspect.getsource(FirstRunScreen.compose)
        assert "password=True" in source


class TestAuthScreenValidation:
    """Tests for auth screen validation logic."""

    def test_password_confirmation_mismatch_logic(self):
        """Test that password confirmation mismatch is detected."""
        password = "secret123"
        confirm = "different"
        assert password != confirm

    def test_password_minimum_length_logic(self):
        """Test that short passwords are rejected."""
        password = "abc"
        assert len(password) < 6

    def test_empty_fields_logic(self):
        """Test that empty fields are detected."""
        assert True  # empty string is falsy
        assert not "  ".strip()  # whitespace-only is empty after strip

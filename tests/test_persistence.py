"""Tests for the persistence layer (SQLite database and password hashing)."""

import pytest
from hojjat_tui.persistence import Database, hash_password, verify_password


class TestDatabase:
    """Tests for the Database class."""

    def test_init_database(self, temp_db_path):
        """Test database initialization."""
        db = Database(temp_db_path)
        db.init_db()
        assert temp_db_path.exists()

    def test_init_database_safe_rerun(self, temp_db_path):
        """Test that database initialization is safe to rerun."""
        db = Database(temp_db_path)
        db.init_db()
        
        # Create a user
        db.create_user("testuser", "password123", "test@test.com", is_superuser=True)
        
        # Reinitialize
        db.init_db()
        
        # User should still exist
        assert db.user_exists("testuser")

    def test_create_user(self, temp_db_path):
        """Test user creation."""
        db = Database(temp_db_path)
        db.init_db()
        
        result = db.create_user("testuser", "password123", "test@test.com")
        assert result is True
        assert db.user_exists("testuser")

    def test_create_duplicate_user(self, temp_db_path):
        """Test that duplicate user creation fails."""
        db = Database(temp_db_path)
        db.init_db()
        
        db.create_user("testuser", "password123")
        result = db.create_user("testuser", "different_password")
        assert result is False

    def test_verify_user(self, temp_db_path):
        """Test user verification."""
        db = Database(temp_db_path)
        db.init_db()
        
        db.create_user("testuser", "password123")
        assert db.verify_user("testuser", "password123") is True
        assert db.verify_user("testuser", "wrongpassword") is False
        assert db.verify_user("nonexistent", "password123") is False

    def test_log_function_execution(self, temp_db_path):
        """Test logging function execution."""
        db = Database(temp_db_path)
        db.init_db()
        
        db.log_function_execution("test_func", True, 0.5, "text", None, None)
        logs = db.get_function_logs()
        
        assert len(logs) == 1
        assert logs[0]["function_name"] == "test_func"
        assert logs[0]["success"] == 1
        assert logs[0]["duration"] == 0.5
        assert logs[0]["output_type"] == "text"

    def test_config_storage(self, temp_db_path):
        """Test configuration storage."""
        db = Database(temp_db_path)
        db.init_db()
        
        db.set_config("test_key", "test_value")
        value = db.get_config("test_key")
        assert value == "test_value"


class TestPasswordHashing:
    """Tests for password hashing."""

    def test_hash_password(self):
        """Test password hashing."""
        password_hash, salt = hash_password("mypassword")
        assert password_hash is not None
        assert salt is not None
        assert len(password_hash) > 0
        assert len(salt) > 0

    def test_verify_password(self):
        """Test password verification."""
        password = "mypassword"
        password_hash, salt = hash_password(password)
        
        assert verify_password(password, password_hash) is True
        assert verify_password("wrongpassword", password_hash) is False

    def test_bcrypt_rounds(self):
        """Test that bcrypt uses sufficient rounds."""
        password_hash, salt = hash_password("test")
        # bcrypt hash should start with $2b$
        assert password_hash.startswith("$2b$")
        # Salt should have 12 rounds by default
        assert "$12$" in salt or "$12$" in password_hash


class TestSafeReinit:
    """Tests for safe database reinitialization without data loss."""

    def test_data_preserved_on_rerun(self, temp_db_path):
        """Test that data is preserved when reinitializing."""
        db = Database(temp_db_path)
        db.init_db()
        
        # Add data
        db.create_user("user1", "pass1", "user1@test.com")
        db.create_user("user2", "pass2", "user2@test.com")
        db.log_function_execution("func1", True, 0.1, "text", None, None)
        
        # Reinitialize
        db.init_db()
        
        # Data should still exist
        assert db.user_exists("user1")
        assert db.user_exists("user2")
        logs = db.get_function_logs()
        assert len(logs) == 1
        assert logs[0]["function_name"] == "func1"

    def test_clear_all_data(self, temp_db_path):
        """Test clearing all data."""
        db = Database(temp_db_path)
        db.init_db()
        
        db.create_user("testuser", "password")
        assert db.user_exists("testuser")
        
        db.clear_all_data()
        assert not db.user_exists("testuser")
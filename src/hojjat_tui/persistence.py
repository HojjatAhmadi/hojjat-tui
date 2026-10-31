"""Persistence layer for HOJJAT TUI.

Provides SQLite-based storage for metadata and password hashing for
administrative users.
"""

import hashlib
import json
import logging
import os
import secrets
import sqlite3
import time
from pathlib import Path
from typing import Any, Dict, List, Optional, Tuple

import bcrypt

logger = logging.getLogger("hojjat_tui.persistence")

_DB_VERSION = 2  # Incremented for Chain Engine

def get_default_db_path() -> Path:
    """Get the default database path based on OS conventions."""
    app_data = os.environ.get("HOJJAT_TUI_DATA_DIR")
    if app_data:
        return Path(app_data) / "hojjat_tui.db"
    
    if os.name == "nt":
        base = Path(os.environ.get("APPDATA", Path.home() / "AppData" / "Roaming"))
    else:
        base = Path(os.environ.get("XDG_DATA_HOME", Path.home() / ".local" / "share"))
    
    return base / "hojjat_tui" / "hojjat_tui.db"

class Database:
    """SQLite database wrapper with automatic initialization."""
    
    def __init__(self, db_path: Optional[Path] = None):
        self.db_path = db_path or get_default_db_path()
        self._ensure_parent_dir()
        self._init_db()
    
    def _ensure_parent_dir(self):
        """Ensure the parent directory exists."""
        self.db_path.parent.mkdir(parents=True, exist_ok=True)
    
    def _get_connection(self) -> sqlite3.Connection:
        """Get a database connection."""
        conn = sqlite3.connect(str(self.db_path))
        conn.row_factory = sqlite3.Row
        conn.execute("PRAGMA foreign_keys = ON")
        return conn
    
    def _init_db(self):
        """Initialize database tables if they don't exist."""
        conn = self._get_connection()
        try:
            cursor = conn.cursor()
            
            # Schema version table
            cursor.execute("""
                CREATE TABLE IF NOT EXISTS schema_meta (
                    key TEXT PRIMARY KEY,
                    value TEXT
                )
            """)
            
            # Check if this is a fresh database
            cursor.execute("SELECT value FROM schema_meta WHERE key = 'version'")
            row = cursor.fetchone()
            current_version = int(row[0]) if row else 0
            
            if current_version < _DB_VERSION:
                self._create_tables(cursor)
                cursor.execute(
                    "INSERT OR REPLACE INTO schema_meta (key, value) VALUES ('version', ?)",
                    (str(_DB_VERSION),)
                )
                conn.commit()
                logger.info(f"Database initialized to version {_DB_VERSION}")
            else:
                # Ensure all tables exist even if version matches
                self._create_tables(cursor)
                conn.commit()
        
        finally:
            conn.close()
    
    def _create_tables(self, cursor: sqlite3.Cursor):
        """Create all database tables."""
        # Users table
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS users (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                username TEXT UNIQUE NOT NULL,
                password_hash TEXT NOT NULL,
                salt TEXT NOT NULL,
                email TEXT,
                is_superuser BOOLEAN DEFAULT 0,
                is_active BOOLEAN DEFAULT 1,
                created_at REAL NOT NULL,
                updated_at REAL NOT NULL
            )
        """)
        
        # Function executions log
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS function_logs (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                function_name TEXT NOT NULL,
                success BOOLEAN NOT NULL,
                duration REAL NOT NULL,
                timestamp REAL NOT NULL,
                output_type TEXT,
                error_message TEXT,
                metadata TEXT
            )
        """)
        
        # Configuration settings
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS config (
                key TEXT PRIMARY KEY,
                value TEXT,
                encrypted BOOLEAN DEFAULT 0
            )
        """)

        # Chain definitions
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS chains (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                name TEXT UNIQUE NOT NULL,
                label TEXT NOT NULL,
                description TEXT,
                created_at REAL NOT NULL,
                updated_at REAL NOT NULL
            )
        """)

        # Chain steps (ordered list of function references)
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS chain_steps (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                chain_id INTEGER NOT NULL,
                step_order INTEGER NOT NULL,
                step_uuid TEXT NOT NULL,
                function_name TEXT NOT NULL,
                label TEXT,
                FOREIGN KEY (chain_id) REFERENCES chains(id) ON DELETE CASCADE
            )
        """)

        # Parameter bindings for each step
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS chain_param_bindings (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                step_uuid TEXT NOT NULL,
                param_name TEXT NOT NULL,
                binding_type TEXT NOT NULL,
                binding_value TEXT,
                source_step_uuid TEXT,
                source_path TEXT,
                prompt TEXT,
                UNIQUE(step_uuid, param_name)
            )
        """)

        # Chain execution history
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS chain_executions (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                chain_name TEXT NOT NULL,
                started_at REAL NOT NULL,
                completed_at REAL,
                status TEXT NOT NULL
            )
        """)

        # Per-step execution results
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS step_executions (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                execution_id INTEGER NOT NULL,
                step_uuid TEXT NOT NULL,
                function_name TEXT NOT NULL,
                status TEXT NOT NULL,
                duration REAL,
                output_summary TEXT,
                error_message TEXT,
                FOREIGN KEY (execution_id) REFERENCES chain_executions(id) ON DELETE CASCADE
            )
        """)
    
    def init_db(self):
        """Public method to initialize/reinitialize the database.
        
        This is safe to rerun — it uses CREATE TABLE IF NOT EXISTS
        and will not drop or lose existing data.
        """
        self._init_db()
        logger.info("Database initialization completed (safe to rerun)")
    
    def user_exists(self, username: str) -> bool:
        """Check if a user exists."""
        conn = self._get_connection()
        try:
            cursor = conn.cursor()
            cursor.execute("SELECT 1 FROM users WHERE username = ?", (username,))
            return cursor.fetchone() is not None
        finally:
            conn.close()
    
    def create_user(self, username: str, password: str, email: Optional[str] = None,
                    is_superuser: bool = False) -> bool:
        """Create a new user with hashed password.
        
        Returns True if user was created, False if username already exists.
        """
        if self.user_exists(username):
            return False
        
        password_hash, salt = hash_password(password)
        
        conn = self._get_connection()
        try:
            cursor = conn.cursor()
            now = time.time()
            cursor.execute("""
                INSERT INTO users (username, password_hash, salt, email, is_superuser, 
                                   is_active, created_at, updated_at)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?)
            """, (
                username, password_hash, salt, email, 1 if is_superuser else 0,
                1, now, now
            ))
            conn.commit()
            logger.info(f"User '{username}' created successfully")
            return True
        finally:
            conn.close()
    
    def verify_user(self, username: str, password: str) -> bool:
        """Verify user credentials.
        
        Returns True if credentials are valid.
        """
        conn = self._get_connection()
        try:
            cursor = conn.cursor()
            cursor.execute(
                "SELECT password_hash, salt FROM users WHERE username = ? AND is_active = 1",
                (username,)
            )
            row = cursor.fetchone()
            
            if row is None:
                return False
            
            password_hash = row["password_hash"]
            return verify_password(password, password_hash)
        finally:
            conn.close()
    
    def log_function_execution(self, name: str, success: bool, duration: float,
                                output_type: str, error: Optional[str] = None,
                                metadata: Optional[str] = None):
        """Log a function execution to the database."""
        conn = self._get_connection()
        try:
            cursor = conn.cursor()
            cursor.execute("""
                INSERT INTO function_logs (function_name, success, duration, 
                                           timestamp, output_type, error_message, metadata)
                VALUES (?, ?, ?, ?, ?, ?, ?)
            """, (name, success, duration, time.time(), output_type, error, metadata))
            conn.commit()
        finally:
            conn.close()
    
    def get_function_logs(self, limit: int = 100) -> List[Dict[str, Any]]:
        """Get recent function execution logs."""
        conn = self._get_connection()
        try:
            cursor = conn.cursor()
            cursor.execute("""
                SELECT * FROM function_logs 
                ORDER BY timestamp DESC 
                LIMIT ?
            """, (limit,))
            rows = cursor.fetchall()
            return [dict(row) for row in rows]
        finally:
            conn.close()
    
    def set_config(self, key: str, value: str, encrypted: bool = False):
        """Set a configuration value."""
        conn = self._get_connection()
        try:
            cursor = conn.cursor()
            cursor.execute("""
                INSERT OR REPLACE INTO config (key, value, encrypted)
                VALUES (?, ?, ?)
            """, (key, value, 1 if encrypted else 0))
            conn.commit()
        finally:
            conn.close()
    
    def get_config(self, key: str) -> Optional[str]:
        """Get a configuration value."""
        conn = self._get_connection()
        try:
            cursor = conn.cursor()
            cursor.execute("SELECT value FROM config WHERE key = ?", (key,))
            row = cursor.fetchone()
            return row["value"] if row else None
        finally:
            conn.close()
    
    def clear_all_data(self):
        """Clear all user data (for reinitialization)."""
        conn = self._get_connection()
        try:
            cursor = conn.cursor()
            cursor.execute("DELETE FROM users")
            cursor.execute("DELETE FROM function_logs")
            cursor.execute("DELETE FROM config")
            cursor.execute("DELETE FROM chains")
            cursor.execute("DELETE FROM chain_steps")
            cursor.execute("DELETE FROM chain_param_bindings")
            cursor.execute("DELETE FROM chain_executions")
            cursor.execute("DELETE FROM step_executions")
            conn.commit()
            logger.info("All data cleared from database")
        finally:
            conn.close()

    # Chain persistence methods

    def save_chain(self, chain_data: Dict[str, Any]) -> int:
        """Save a chain definition. Returns chain id."""
        conn = self._get_connection()
        try:
            cursor = conn.cursor()
            now = time.time()

            # Check if chain exists
            cursor.execute("SELECT id FROM chains WHERE name = ?", (chain_data["name"],))
            row = cursor.fetchone()

            if row:
                chain_id = row["id"]
                cursor.execute(
                    "UPDATE chains SET label = ?, description = ?, updated_at = ? WHERE id = ?",
                    (chain_data["label"], chain_data.get("description", ""), now, chain_id)
                )
            else:
                cursor.execute(
                    "INSERT INTO chains (name, label, description, created_at, updated_at) VALUES (?, ?, ?, ?, ?)",
                    (chain_data["name"], chain_data["label"], chain_data.get("description", ""), now, now)
                )
                chain_id = cursor.lastrowid

            # Remove existing steps for this chain
            cursor.execute("DELETE FROM chain_steps WHERE chain_id = ?", (chain_id,))

            for step_data in chain_data.get("steps", []):
                cursor.execute(
                    "INSERT INTO chain_steps (chain_id, step_order, step_uuid, function_name, label) VALUES (?, ?, ?, ?, ?)",
                    (chain_id, step_data["order"], step_data["uuid"], step_data["function_name"], step_data.get("label"))
                )
                step_db_id = cursor.lastrowid

                # Save parameter bindings
                for param in step_data.get("params", []):
                    # Handle binding_type enum
                    binding_type = param["binding_type"]
                    if hasattr(binding_type, "value"):
                        binding_type = binding_type.value

                    # JSON-encode the value so types (int, float, dict, list) survive
                    # the round-trip through SQLite TEXT columns.
                    raw_value = param.get("value")
                    if raw_value is not None:
                        raw_value = json.dumps(raw_value)

                    cursor.execute(
                        """INSERT OR REPLACE INTO chain_param_bindings
                           (step_uuid, param_name, binding_type, binding_value, source_step_uuid, source_path, prompt)
                           VALUES (?, ?, ?, ?, ?, ?, ?)""",
                        (
                            step_data["uuid"],
                            param["name"],
                            binding_type,
                            raw_value,
                            param.get("source_step_uuid"),
                            param.get("source_path"),
                            param.get("prompt")
                        )
                    )

            conn.commit()
            return chain_id
        finally:
            conn.close()

    def load_chain(self, name: str) -> Optional[Dict[str, Any]]:
        """Load a chain definition by name."""
        conn = self._get_connection()
        try:
            cursor = conn.cursor()
            cursor.execute("SELECT * FROM chains WHERE name = ?", (name,))
            chain_row = cursor.fetchone()

            if not chain_row:
                return None

            cursor.execute("SELECT * FROM chain_steps WHERE chain_id = ? ORDER BY step_order", (chain_row["id"],))
            step_rows = cursor.fetchall()

            steps = []
            for step_row in step_rows:
                step_uuid = step_row["step_uuid"]
                cursor.execute("SELECT * FROM chain_param_bindings WHERE step_uuid = ?", (step_uuid,))
                binding_rows = cursor.fetchall()

                params = []
                for br in binding_rows:
                    params.append({
                        "name": br["param_name"],
                        "binding_type": br["binding_type"],
                        "value": br["binding_value"],
                        "source_step_uuid": br["source_step_uuid"],
                        "source_path": br["source_path"],
                        "prompt": br["prompt"],
                    })

                steps.append({
                    "id": step_row["id"],
                    "uuid": step_uuid,
                    "order": step_row["step_order"],
                    "function_name": step_row["function_name"],
                    "label": step_row["label"],
                    "params": params,
                })

            return {
                "id": chain_row["id"],
                "name": chain_row["name"],
                "label": chain_row["label"],
                "description": chain_row["description"],
                "steps": steps,
            }
        finally:
            conn.close()

    def list_chains(self) -> List[Dict[str, Any]]:
        """List all chains."""
        conn = self._get_connection()
        try:
            cursor = conn.cursor()
            cursor.execute("SELECT * FROM chains ORDER BY name")
            rows = cursor.fetchall()
            return [dict(row) for row in rows]
        finally:
            conn.close()

    def delete_chain(self, name: str) -> bool:
        """Delete a chain by name. Returns True if deleted."""
        conn = self._get_connection()
        try:
            cursor = conn.cursor()
            cursor.execute("DELETE FROM chains WHERE name = ?", (name,))
            deleted = cursor.rowcount > 0
            conn.commit()
            return deleted
        finally:
            conn.close()

    def save_chain_execution(self, chain_name: str, status: str) -> int:
        """Save a chain execution start. Returns execution id."""
        conn = self._get_connection()
        try:
            cursor = conn.cursor()
            now = time.time()
            cursor.execute(
                "INSERT INTO chain_executions (chain_name, started_at, status) VALUES (?, ?, ?)",
                (chain_name, now, status)
            )
            execution_id = cursor.lastrowid
            conn.commit()
            return execution_id
        finally:
            conn.close()

    def save_step_execution(self, execution_id: int, step_data: Dict[str, Any]):
        """Save a step execution result."""
        conn = self._get_connection()
        try:
            cursor = conn.cursor()
            cursor.execute(
                """INSERT INTO step_executions
                   (execution_id, step_uuid, function_name, status, duration, output_summary, error_message)
                   VALUES (?, ?, ?, ?, ?, ?, ?)""",
                (
                    execution_id,
                    step_data["uuid"],
                    step_data["function_name"],
                    step_data["status"],
                    step_data.get("duration", 0.0),
                    step_data.get("output_summary", ""),
                    step_data.get("error", None)
                )
            )
            conn.commit()
        finally:
            conn.close()

    def update_chain_execution(self, execution_id: int, status: str, completed_at: Optional[float] = None):
        """Update chain execution status."""
        conn = self._get_connection()
        try:
            cursor = conn.cursor()
            if completed_at is None:
                completed_at = time.time()
            cursor.execute(
                "UPDATE chain_executions SET status = ?, completed_at = ? WHERE id = ?",
                (status, completed_at, execution_id)
            )
            conn.commit()
        finally:
            conn.close()

    def get_chain_executions(self, limit: int = 50) -> List[Dict[str, Any]]:
        """Get recent chain executions."""
        conn = self._get_connection()
        try:
            cursor = conn.cursor()
            cursor.execute(
                "SELECT * FROM chain_executions ORDER BY started_at DESC LIMIT ?",
                (limit,)
            )
            return [dict(row) for row in cursor.fetchall()]
        finally:
            conn.close()

def hash_password(password: str) -> Tuple[str, str]:
    """Hash a password using bcrypt and return (hash, salt).
    
    Args:
        password: Plain text password.
    
    Returns:
        Tuple of (password_hash, salt). Both are strings.
    """
    salt = bcrypt.gensalt(rounds=12)
    password_hash = bcrypt.hashpw(password.encode("utf-8"), salt)
    return password_hash.decode("utf-8"), salt.decode("utf-8")

def verify_password(password: str, password_hash: str) -> bool:
    """Verify a password against a stored bcrypt hash.
    
    Args:
        password: Plain text password to check.
        password_hash: Stored bcrypt hash.
    
    Returns:
        True if password matches the hash.
    """
    try:
        return bcrypt.checkpw(password.encode("utf-8"), password_hash.encode("utf-8"))
    except (ValueError, TypeError):
        return False

# Module-level convenience function
def default_db() -> Database:
    """Get the default database instance."""
    return Database()
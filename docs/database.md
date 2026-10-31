# Database

## Overview

HOJJAT TUI uses [SQLite](https://www.sqlite.org/) as the persistence layer for user metadata, chain definitions, and execution history. The database is created and managed automatically via the `Database` class in `src/hojjat_tui/persistence.py`.

### Database File Location

The database file is platform-appropriate:

| OS | Default Path |
|---|---|
| **Windows** | `%APPDATA%\hojjat_tui\hojjat_tui.db` |
| **macOS** | `$HOME/Library/Application Support/hojjat_tui/hojjat_tui.db` |
| **Linux** | `$HOME/.local/share/hojjat_tui/hojjat_tui.db` (if `$XDG_DATA_HOME` is not set) |

### Custom Database Path

The database path can be customized via:

1. **Environment variable**: Set `HOJJAT_TUI_DATA_DIR` before launching:

   ```bash
   export HOJJAT_TUI_DATA_DIR=/custom/path/hojjat_tui.db
   hojjat-tui
   ```

2. **Management command**: Use `--db-path` with `python manage.py`:

   ```bash
   python manage.py init --db-path /custom/path/hojjat_tui.db
   ```

3. **Code**: Pass a `db_path` to the `Database` constructor:

   ```python
   from hojjat_tui.persistence import Database
   db = Database(db_path=Path("/custom/path/hojjat_tui.db"))
   ```

### Database Initialization

On first run (or when `python manage.py init` is called), the database is initialized with the following tables:

- `users`: User accounts with bcrypt-hashed passwords
- `function_logs`: Function execution history
- `config`: Configuration settings key-value store
- `chains`: User-created chain definitions
- `chain_steps`: Individual steps within chains
- `chain_param_bindings`: Parameter bindings for each chain step
- `chain_executions`: Chain execution history
- `step_executions`: Per-step execution results

### Schema Versioning

The database tracks its schema version in the `schema_meta` table:

```sql
CREATE TABLE IF NOT EXISTS schema_meta (
    key TEXT PRIMARY KEY,
    value TEXT
);
```

The version is checked on initialization. If the current version is less than the expected version (`_DB_VERSION = 2`), tables are created or updated. This allows for future schema migrations without data loss.

**Note**: The schema version is currently 2, incremented for the Chain Engine. Future phases will increment this version as new features are added.

### Tables

#### `users`

Stores user account information with bcrypt-hashed passwords.

| Column | Type | Description |
|--------|------|-------------|
| `id` | INTEGER | Primary key, auto-increment |
| `username` | TEXT | Unique username, not null |
| `password_hash` | TEXT | bcrypt hash, not null |
| `salt` | TEXT | bcrypt salt, not null |
| `email` | TEXT | Optional email address |
| `is_superuser` | BOOLEAN | Admin privileges, default 0 |
| `is_active` | BOOLEAN | Account active status, default 1 |
| `created_at` | REAL | Timestamp of account creation |
| `updated_at` | REAL | Timestamp of last update |

#### `function_logs`

Logs function execution events.

| Column | Type | Description |
|--------|------|-------------|
| `id` | INTEGER | Primary key, auto-increment |
| `function_name` | TEXT | Name of the executed function, not null |
| `success` | BOOLEAN | Whether execution succeeded, not null |
| `duration` | REAL | Execution time in seconds, not null |
| `timestamp` | REAL | Execution timestamp, not null |
| `output_type` | TEXT | Detected output type (text, markdown, json, table) |
| `error_message` | TEXT | Error message if execution failed |

#### `config`

Key-value configuration store.

| Column | Type | Description |
|--------|------|-------------|
| `key` | TEXT | Configuration key, primary key |
| `value` | TEXT | Configuration value |
| `encrypted` | BOOLEAN | Whether the value is encrypted, default 0 |

#### `chains`

User-created chain definitions.

| Column | Type | Description |
|--------|------|-------------|
| `id` | INTEGER | Primary key, auto-increment |
| `name` | TEXT | Unique chain name, not null |
| `label` | TEXT | Display label, not null |
| `description` | TEXT | Human-readable description |
| `created_at` | REAL | Timestamp of chain creation |
| `updated_at` | REAL | Timestamp of last update |

#### `chain_steps`

Individual steps within chains, defining the ordered function execution sequence.

| Column | Type | Description |
|--------|------|-------------|
| `id` | INTEGER | Primary key, auto-increment |
| `chain_id` | INTEGER | Foreign key to `chains.id`, ON DELETE CASCADE |
| `step_order` | INTEGER | Execution order (0 = first) |
| `step_uuid` | TEXT | Unique step UUID, not null |
| `function_name` | TEXT | Name of the executed function, not null |
| `label` | TEXT | Display label for this step |

#### `chain_param_bindings`

Parameter bindings for each step, defining how parameters receive their values.

| Column | Type | Description |
|--------|------|-------------|
| `id` | INTEGER | Primary key, auto-increment |
| `step_uuid` | TEXT | Associated step UUID, not null |
| `param_name` | TEXT | Parameter name on the function, not null |
| `binding_type` | TEXT | How the value is sourced (literal, user_input, previous_step) |
| `binding_value` | TEXT | The actual value (JSON-encoded for type survival) |
| `source_step_uuid` | UUID of the source step (for PREVIOUS_STEP bindings) |
| `source_path` | Dot-separated path into step output (for PREVIOUS_STEP) |
| `prompt` | Prompt text (for USER_INPUT bindings) |
| UNIQUE(`step_uuid`, `param_name`) | Prevents duplicate parameter bindings per step |

#### `chain_executions`

Chain execution history.

| Column | Type | Description |
|--------|------|-------------|
| `id` | INTEGER | Primary key, auto-increment |
| `chain_name` | TEXT | Name of the executed chain, not null |
| `started_at` | REAL | Execution start timestamp, not null |
| `completed_at` | REAL | Execution completion timestamp |
| `status` | TEXT | Overall execution status (pending, success, failed, partial) |

#### `step_executions`

Per-step execution results.

| Column | Type | Description |
|--------|------|-------------|
| `id` | INTEGER | Primary key, auto-increment |
| `execution_id` | INTEGER | Foreign key to `chain_executions.id`, ON DELETE CASCADE |
| `step_uuid` | UUID of the executed step, not null |
| `function_name` | Name of the executed function, not null |
| `status` | Step status (pending, success, failed, skipped) |
| `duration` | Execution duration in seconds |
| `output_summary` | Brief summary of output (first 500 chars, JSON-encoded for dict/list) |
| `error_message` | Error message if step failed |

### bcrypt Password Hashing

Passwords are hashed using [bcrypt](https://bcrypt.github.io/) with 12 rounds:

```python
from hojjat_tui.persistence import hash_password, verify_password

# Hash a password
password_hash, salt = hash_password("mysecretpassword")

# Verify a password
is_valid = verify_password("mysecretpassword", password_hash)
# Returns True if password matches the hash
```

**Security notes**:
- bcrypt automatically generates a unique salt for each password
- 12 rounds provide good security/performance balance
- The hash format is `$2b$12$...` or `$2a$12$...`
- Passwords are never stored in plain text

### Chain Persistence

#### Saving a Chain

When a chain is saved via `save_chain()`, the following happens:

1. The chain definition (name, label, description) is inserted into the `chains` table
2. Existing steps for this chain are deleted from `chain_steps` and `chain_param_bindings` (cascade)
3. Each step is inserted into `chain_steps` with its UUID, order, function name, and label
4. Each parameter binding is inserted into `chain_param_bindings` with:
   - The binding type (literal, user_input, previous_step)
   - The binding value (JSON-encoded for type survival through SQLite TEXT columns)
   - Source step UUID (for previous_step bindings)
   - Source path (for previous_step bindings, e.g., "data.items.0.name")
   - Prompt text (for user_input bindings)

#### Loading a Chain

When a chain is loaded via `load_chain()`:

1. The chain definition is retrieved from the `chains` table by name
2. All steps for this chain are retrieved from `chain_steps` ordered by `step_order`
3. For each step, its parameter bindings are retrieved from `chain_param_bindings`
4. Binding values are JSON-decoded to restore their original Python types
5. A `Chain` model object is constructed with all steps and bindings

### Database Reset

#### `python manage.py init`

Safe to rerun — initializes the database if it doesn't exist, or validates the schema if it does. Does **not** drop or lose existing data.

```bash
python manage.py init
```

#### `python manage.py reset-db`

Clears all user data from the database (chains, users, function logs, config). The schema is preserved.

```bash
python manage.py reset-db
```

This is useful for starting fresh without uninstalling the package.

#### Direct SQLite Access

For advanced users, the database can be queried directly using `sqlite3`:

```bash
sqlite3 "$(python -c "import os; print(os.environ.get('APPDATA', '$HOME/.local/share'))/hojjat_tui/hojjat_tui.db"))
```

Or via Python:

```python
import sqlite3
conn = sqlite3.connect(str(db_path))
cursor = conn.cursor()
cursor.execute("SELECT * FROM chains")
for row in cursor.fetchall():
    print(row)
conn.close()
```

### Database Backup and Restore

#### Backup

```bash
# Windows
copy %APPDATA%\hojjat_tui\hojjat_tui.db C:\backup\hojjat_tui_2024.db

# macOS/Linux
cp $HOME/.local/share/hojjat_tui/hojjat_tui.db /backup/hojjat_tui_2024.db
```

#### Restore

Replace the database file with the backup:

```bash
# Windows
copy C:\backup\hojjat_tui_2024.db %APPDATA%\hojjat_tui\hojjat_tui.db

# macOS/Linux
cp /backup/hojjat_tui_2024.db $HOME/.local/share/hojjat_tui/hojjat_tui.db
```

After restoring, reinitialize the management commands:

```bash
python manage.py init
```

### Database Cleanup

The database file will grow over time as execution history accumulates. To manage size:

1. **Periodic reset**: Use `python manage.py reset-db` to clear old data
2. **Selective deletion**: Use SQL DELETE statements to remove specific records
3. **Auto-cleanup**: Future versions may include automatic history cleanup

### SQLite Tools

Recommended tools for inspecting the database:

- **sqlite3** command-line tool (included with Python/SQLite)
- **DB Browser for SQLite** (GUI, cross-platform)
- **Python sqlite3** module (already used by HOJJAT TUI)
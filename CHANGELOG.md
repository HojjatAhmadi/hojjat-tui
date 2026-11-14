# Changelog

All notable changes to HOJJAT TUI will be documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.1.0/),
and this project adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

## [2.0.1] - 2026-11-14

### Fixed

- **Refresh / hot reload**: `refresh_functions()` now uses `reload_function_modules()` which detects added, modified, and deleted functions and modules. Previously it only imported new modules and never reloaded changed ones or removed stale registrations.
- **Duplicate TUI startup**: `cli.py` no longer calls `run()` after executing `manage.py` via `runpy.run_path()`, preventing a second TUI instance from starting.
- **Form error display**: `on_mount()` now focuses the function list so Enter-key selection works, ensuring `#form-message` is available when function errors are displayed.

### Added

- `reload_function_modules()` in `src/hojjat_tui/function.py` — atomic hot reload with backup/restore on failure
- `scan_functions_directory()` — discovers modules in the `functions/` directory
- File-change detection via mtime + size tracking (`_MODULE_TIMESTAMPS`)
- `get_last_reload_result()` — returns the summary of the most recent reload
- Refresh summary messages: "N added, N updated, N removed" or "No changes detected."

## [2.0.0] - 2026-11-14

### Added

- `init_project()` in `src/hojjat_tui/management.py` — creates project structure (`manage.py`, `functions/`, `functions/__init__.py`, `functions/example.py`)
- `run()` exported from `hojjat_tui.__init__` — public application launcher API
- `runpy.run_path()`-based project entry point execution — `manage.py` runs in the current process
- Complete `functions/example.py` with six example functions (string, table, chart, input, JSON, error)
- Project initialization workflow: `hojjat-tui init` then `hojjat-tui`

### Changed

- **BREAKING CHANGE**: `hojjat-tui init` now creates a project structure instead of initializing an empty database
- **BREAKING CHANGE**: `hojjat-tui` (no args) now executes the project's `manage.py` via `runpy.run_path()` before starting the TUI
- `management.py.cmd_init()` now calls `init_project()` instead of `Database.init_db()`
- Removed `--db-path` option from `init` subcommand
- Version: `1.6.8` → `2.0.0`

### Preserved

- Function Registry, `@hojjat_function()` decorator, Chain Engine, and all existing public APIs
- `src/hojjat_tui/auth.py`, `src/hojjat_tui/screens/welcome.py`, and `src/hojjat_tui/screens/first_run.py` remain available for optional future authentication support
- Database initialization remains available via `Database.init_db()` and `python manage.py check`
- `refresh_functions()` continues to read the in-memory registry without re-executing `manage.py`

## [1.6.8] - 2026-11-14

### Added

- Automatic user function module discovery via `[tool.hojjat-tui].function_modules` in `pyproject.toml`
- `load_function_modules()` in `src/hojjat_tui/function.py` — imports configured modules so `@hojjat_function()` decorators populate the registry
- Module loading integrated into `hojjat-tui`, `hojjat-tui run`, and `python manage.py run` startup paths
- `refresh_functions()` (TUI Refresh button) re-runs module discovery before reading the registry
- Graceful error handling: missing modules produce actionable warnings without crashing

### Changed

- `hojjat-tui` (no args) now loads user function modules before starting the TUI
- `hojjat-tui run` and `python manage.py run` now load user function modules before reading the registry
- Version: `1.5.8` → `1.6.8`

## [1.5.8] - 2026-11-14

### Changed

- Removed mandatory Welcome / Login screen from default application startup
- Removed mandatory first-run account registration from default application startup
- Removed authentication checks that blocked normal application usage
- Removed Logout binding and Settings menu option (no longer applicable without auth)
- `python manage.py run` now launches directly into the main TUI interface

### Preserved

- `src/hojjat_tui/auth.py`, `src/hojjat_tui/screens/welcome.py`, and
  `src/hojjat_tui/screens/first_run.py` remain available for optional
  future authentication support
- Function Registry, `@hojjat_function()` decorator, Chain Engine, and
  all existing public APIs remain unchanged

## [1.4.8] - 2026-11-14

### Fixed

- `python manage.py run` no longer errors with `[error] Function 'None' is not registered` after the TUI exits
- `cmd_run` now returns after launching the TUI, preventing fall-through to the unregistered-function check when no function name is provided

## [1.4.7] - 2026-11-04

### Added

#### Authentication & Startup

- PyFiglet dependency for branded ASCII logo rendering
- `AuthenticationService` in `src/hojjat_tui/auth.py` — secure authentication logic separate from UI
- `WelcomeScreen` — professional login screen with PyFiglet logo, masked password input, Enter-key submission, and inline validation errors
- `FirstRunScreen` — first-run account creation with username, password, and confirmation validation
- `Database.get_user_count()` — query for total user account count
- Logout support via `L` key and Settings menu

#### Startup Flow

- `python manage.py run` now shows the Welcome / Login screen first
- First-run installations show the Account Setup screen before login
- Successful authentication opens the existing main TUI
- Logout returns to the login screen without terminating the application

### Changed

- Version synchronized: `pyproject.toml` and `__init__.py` both report `1.4.7`
- `HojjatTUIApplication.on_mount()` now performs authentication check before revealing main TUI

### Security

- Passwords are hashed with bcrypt (12 rounds) via the existing persistence layer
- No plaintext passwords are stored or logged
- Login errors are generic — do not reveal whether a username exists
- No default administrator account is created

## [0.1.0] - 2024-01-01

### Added

#### Packaging & Installation
- Project structure with `src/` package layout
- `pyproject.toml` with setuptools build backend
- Console script entry point `hojjat-tui`
- Module entry point `python -m hojjat_tui`
- `manage.py` Django-style management script
- Dev dependencies: pytest, pytest-asyncio, ruff, black, build, twine
- `.gitignore` with Python and project ignore patterns
- MIT LICENSE file

#### Function Registry & Execution
- `@hojjat_function` decorator with metadata (name, label, description, annotations, defaults, required)
- Duplicate function name detection
- `FunctionResult` dataclass for standardized results
- Centralized execution engine with duration tracking and status reporting
- Execution logging (in-memory and SQLite)
- Dynamic input form support based on parameter annotations
- Input validation and helpful error messages

#### TUI Interface
- Full Textual-based TUI application
- HOJJAT TUI branding with ASCII logo
- Interactive function menu with navigation
- Parameter input field with key=value format
- Structured output rendering (text, markdown, table, JSON)
- Informational and error message panels
- Color-coded borders and status bar
- Keyboard shortcuts: Ctrl+Q (quit), Ctrl+R (refresh), R (run), Enter

#### Built-in Functions
- `hello` — greeting function with name and count parameters
- `time_info` — current time and date information as JSON
- `factorial` — factorial calculator
- `random_quote` — random inspirational quote generator
- `ping_test` — simulated network ping test (table output)
- `system_info` — basic system information as JSON
- `error_demo` — intentional error to demonstrate error handling

#### Persistence
- SQLite database for user metadata and execution logs
- Schema versioning with safe reinitialization
- bcrypt password hashing with 12 rounds
- User creation and verification
- Configuration key-value storage
- Execution log storage

#### Management Commands
- `init` — Initialize database (safe to rerun)
- `createsuperuser` — Create superuser with bcrypt-hashed password
- `run` — Execute a registered function from CLI
- `check` — Verify installation and show project status
- `test` — Run the test suite via pytest
- `--version` — Show version information

#### Tests
- `tests/test_function.py` — decorator and registry tests
- `tests/test_executor.py` — function execution tests
- `tests/test_persistence.py` — database and password hashing tests
- `tests/test_renderer.py` — output rendering tests
- `tests/test_cli.py` — CLI and built-in function tests
- `tests/test_tui.py` — TUI application tests
- `tests/conftest.py` — shared test fixtures

#### Documentation
- `README.md` with full usage, API, and architecture documentation
- `CHANGELOG.md` with version history
- `AGENTS.md` with project rules and contracts
- GitHub and ZIP installation instructions (with placeholder URLs)
- Developer documentation

### Notes

- The **Chain Engine** feature (linking functions together in sequences) is deferred to Phase 2.
- Chart rendering is documented as a Phase 2 feature with a placeholder implementation.
- Installation URLs are placeholders until the repository URL is finalized.

## [0.3.0] - 2026-10-31

### Changed

- Cleaned development and test data from release baseline (removed 6 test chains from database)
- Updated `.gitignore` with comprehensive exclusions for runtime data
- Initialized Git repository with proper baseline commit
- Updated README.md with comprehensive project documentation
- Created professional developer documentation suite (docs/)
- Applied structured commit history with meaningful commit messages
- Verified fresh installation starts with empty Chain list
- Confirmed built-in functions remain available after cleanup

### Fixed

- Database persistence configuration investigation and cleanup
- Git baseline verification (no developer-specific data tracked)

### Pending

- **Chain Engine** (linking functions together in sequences) — deferred to Phase 2
- Chart rendering — placeholder implementation, full implementation in Phase 2
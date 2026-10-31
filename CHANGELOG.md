# Changelog

All notable changes to HOJJAT TUI will be documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.1.0/),
and this project adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

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
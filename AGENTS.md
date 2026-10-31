## Project Overview
HOJJAT TUI is a terminal-based TUI tool built with Python + Textual. It provides a registry of
user-contributed functions that run inside the terminal, render structured results, and chain
together in future phases.

## Current Phase: Phase 1 (Packaging, Installation, Function Registry, TUI, Management Commands)

### Implementation Status
- ✅ Packaging and installation (pyproject.toml, src layout, console script)
- ✅ Function registry and execution (decorator API, validation, scheduling, logging)
- ⏳ TUI interface with Textual (menu, results rendering, branding) - **Partially implemented**
- ✅ Management commands (init, createsuperuser, run, check, test, --version)
- ✅ Persistence (SQLite for metadata, password hashing)
- ✅ Tests and developer documentation

### Pending for Phase 2
- ⏳ Chain Engine (the full chain execution engine that links functions together)

## Coding Style
- Python 3.9+ required.
- PEP 8 compliant. Use `black` for formatting.
- Package code lives under `src/hojjat_tui/`.
- Tests live under `tests/`.
- No business logic in UI components.
- Use `ruff` for linting in dev.

## Development Workflow
- Install dev dependencies: `python -m pip install -e ".[dev]"`
- Run tests: `python -m pytest`
- Run management commands: `python manage.py <command>`
- Run TUI: `hojjat-tui` or `python -m hojjat_tui`

## Project Layout
```
.
├── src/hojjat_tui/      # Main package
├── tests/               # Test suite
├── manage.py            # Django-style management script
└── pyproject.toml       # Project configuration
```

## Key Contracts
- Functions registered via `@hojjat_function` decorator.
- Results returned as a `FunctionResult` dataclass with a contract for text/markdown/table/json.
- Charts are documented as a later feature (Phase 2).

## Coding Style
- Python 3.9+ required.
- PEP 8 compliant. Use `black` for formatting.
- Package code lives under `src/hojjat_tui/`.
- Tests live under `tests/`.
- No business logic in UI components.
- Use `ruff` for linting in dev.

## Development Workflow
- Install dev dependencies: `python -m pip install -e ".[dev]"`
- Run tests: `python -m pytest`
- Run management commands: `python manage.py <command>`
- Run TUI: `hojjat-tui` or `python -m hojjat_tui`

## Project Layout
```
.
├── src/hojjat_tui/      # Main package
├── tests/               # Test suite
├── manage.py            # Django-style management script
└── pyproject.toml       # Project configuration
```

## Key Contracts
- Functions registered via `@hojjat_function` decorator.
- Results returned as a `FunctionResult` dataclass with a contract for text/markdown/table/json.
- Charts are documented as a later feature (Phase 2).

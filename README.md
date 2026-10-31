# HOJJAT TUI

[![Version](https://img.shields.io/badge/version-0.1.0-blue)](https://github.com/placeholder/hojjat-tui)
[![Python](https://img.shields.io/badge/python-3.9%2B-blue.svg)](https://www.python.org/downloads/)
[![License](https://img.shields.io/badge/license-MIT-green.svg)](LICENSE)

HOJJAT TUI is a terminal-based user interface (TUI) tool built with Python and [Textual](https://textual.textualize.io/). It provides a registry of user-contributed functions that can run inside the terminal, render structured results, and chain together in future phases.

> **Note**: This is Phase 1 — a stable package foundation with a working end-to-end user journey through the TUI.

---

## Features

- **Function Registry**: Register Python functions with metadata via the `@hojjat_function` decorator
- **TUI Interface**: Navigate registered functions and enter parameters in an interactive Textual UI
- **Structured Output**: Render results as text, Markdown, tables, JSON, and error/info panels
- **Persistence**: SQLite database for user metadata and execution logs
- **Password Security**: bcrypt-hashed administrative passwords
- **Management Commands**: Django-style `manage.py` interface for init, user management, running, checking, and testing

---

## Installation

### Prerequisites
- Python 3.9+

### Install from GitHub (placeholder URL)

> Replace the URL below with the actual repository URL once available.

```bash
pip install git+https://github.com/placeholder/hojjat-tui.git
```

### Install from ZIP (placeholder URL)

> Replace the URL below with the actual release archive URL once available.

```bash
# Download the ZIP from:
# https://github.com/placeholder/hojjat-tui/archive/refs/heads/main.zip
# Then:
pip install .
```

### Development Installation

```bash
python -m pip install -e ".[dev]"
```

---

## Quick Start

### Launch the TUI

```bash
hojjat-tui
```

### Use management commands

```bash
python manage.py init              # Initialize the SQLite database
python manage.py createsuperuser  # Create an admin user
python manage.py check            # Verify installation
python manage.py test             # Run the test suite
python manage.py --version        # Show version
```

---

## Function Registry

Register functions using the `@hojjat_function` decorator:

```python
from hojjat_tui.function import hojjat_function

@hojjat_function(
    name="my_function",
    label="My Function",
    description="Does something useful",
    annotations={
        "input_text": {"type": "str", "description": "Text to process"},
    },
    defaults={"input_text": ""},
    required=["input_text"],
)
def my_function(input_text: str = "") -> dict:
    return {"processed": input_text.upper()}
```

### Running a Function

In the TUI:
1. Select a function from the menu (navigate with arrow keys)
2. Enter parameters in the input box (e.g., `name=World`)
3. Press **Run** or **Ctrl+R**

From CLI:
```bash
python manage.py run my_function --param name World
```

---

## Architecture

```
src/hojjat_tui/
├── __init__.py          # Public API exports
├── __main__.py          # python -m hojjat_tui entry point
├── cli.py               # Console script + module CLI
├── function.py          # @hojjat_function decorator + FunctionResult
├── executor.py          # Centralized function execution
├── renderer.py          # Output rendering (text, markdown, table, json)
├── persistence.py       # SQLite database + bcrypt password hashing
├── management.py        # Django-style management commands
├── tui.py               # Textual TUI application
├── builtin_functions.py # Built-in sample functions
└── py.typed             # PEP 561 type markers
```

---

## Output Contract

All registered functions return values through a `FunctionResult` dataclass:

| Field        | Type    | Description                        |
|-------------|---------|------------------------------------|
| name        | `str`   | Function name                      |
| success     | `bool`  | Whether execution succeeded        |
| duration    | `float` | Execution time in seconds          |
| output      | `Any`   | Return value (str, dict, list)     |
| error       | `str?`  | Error message if failed            |
| type        | `str`   | Detected output type               |
| metadata    | `dict`  | Additional execution metadata      |

### Supported Output Types
- **text**: Plain text output
- **markdown**: Markdown content (rendered with Rich)
- **table**: List of dicts or list of lists rendered as a table
- **json**: Dict or JSON-compatible objects
- **error**: Error messages in a red panel
- **info**: Informational messages in a blue panel

### Chart Output (Phase 2)
Charts are documented as a **later feature**. The current chart renderer returns a placeholder panel. Full chart rendering will be implemented in Phase 2.

---

## Development

### Setup

```bash
python -m pip install -e ".[dev]"
```

### Running Tests

```bash
python -m pytest
```

### Running Linting

```bash
ruff check src/ tests/
black --check src/ tests/
```

### Adding New Functions

Place function modules in `src/hojjat_tui/` or import them at application startup. The `@hojjat_function` decorator adds them to the global registry automatically.

---

## Project Structure

```
hojjat-tui/
├── src/hojjat_tui/       # Package source
│   └── py.typed
├── tests/                # Test suite
├── manage.py             # Management script
├── pyproject.toml        # Project configuration
├── AGENTS.md             # Project rules
├── README.md
├── CHANGELOG.md
├── LICENSE
└── .gitignore
```

---

## Roadmap

| Phase | Feature                          | Status     |
|-------|----------------------------------|------------|
| 1     | Packaging, installation          | ✅ Complete |
| 1     | Function registry and execution  | ✅ Complete |
| 1     | TUI and output rendering         | ✅ Complete |
| 1     | Management commands and persistence | ✅ Complete |
| 1     | Tests and documentation          | ✅ Complete |
| 2     | **Chain Engine** (linking functions together) | ⏳ Pending |

---

## License

MIT License — see [LICENSE](LICENSE) for details.
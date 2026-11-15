# HOJJAT TUI

[![Version](https://img.shields.io/badge/version-2.0.1-blue)](https://github.com/HojjatAhmadi/hojjat-tui)
[![Python](https://img.shields.io/badge/python-3.9%2B-blue.svg)](https://www.python.org/downloads/)
[![License](https://img.shields.io/badge/license-MIT-green.svg)](LICENSE)

HOJJAT TUI is a terminal-based user interface (TUI) tool built with Python and [Textual](https://textual.textualize.io/). It provides a registry of user-contributed functions that can run inside the terminal, render structured results (text, Markdown, tables, charts, JSON), and chain together for sequential workflows.

Register your Python functions with the `@hojjat_function()` decorator, then launch `hojjat-tui` to browse, configure, and execute them from a clean terminal interface.

---

## Features

- **Function Registry**: Register Python functions with metadata via the `@hojjat_function()` decorator
- **TUI Interface**: Navigate registered functions and enter parameters in an interactive Textual UI
- **Structured Output**: Render results as text, Markdown, tables, charts, JSON, and error/info panels
- **Chain Engine**: Link multiple functions together into sequential workflows with parameter bindings (literal, user input, previous step output)
- **Persistence**: SQLite database for user metadata, chain definitions, and execution logs
- **Password Security**: bcrypt-hashed administrative passwords for user accounts
- **Management Commands**: Django-style `manage.py` interface for init, user management, running, checking, and testing
- **Hot Reload**: Refresh function modules without restarting the TUI

---

## Installation

### Prerequisites

- Python 3.9 or later
- pip (Python package manager)

### Install from GitHub

```bash
pip install git+https://github.com/HojjatAhmadi/hojjat-tui.git
```

### Install from Source

```bash
git clone https://github.com/HojjatAhmadi/hojjat-tui.git
cd hojjat-tui
pip install .
```

### Development Installation

For development, install the package in "editable" mode so that changes to the source code are immediately reflected:

```bash
python -m pip install -e ".[dev]"
```

This installs the development dependencies (pytest, ruff, black, etc.) and sets up the package for development.

### Verifying the Installation

After installation, verify that the package is correctly installed:

```bash
hojjat-tui --version
```

This should display `hojjat-tui version 2.0.1`.

---

## Quick Start

### Step 1: Initialize a HOJJAT TUI project

```bash
hojjat-tui init
```

This creates the project structure in the current directory:

```text
MyProject/
├── manage.py
├── functions/
│   ├── __init__.py
│   └── example.py
```

- `manage.py` — the project entry point. Import your function modules here so their `@hojjat_function()` decorators register them before the TUI starts.
- `functions/__init__.py` — marks `functions/` as a Python package.
- `functions/example.py` — seven example functions demonstrating string, table, bar chart, line chart, input, JSON, and error output patterns.
- No database is created during initialization.

### Step 2: Launch the TUI

```bash
hojjat-tui
```

This executes your project's `manage.py` (which imports your function modules, triggering their `@hojjat_function()` decorators), then starts the TUI. All registered functions appear in the function list.

Alternatively:

```bash
python manage.py
```

Both commands produce the same application behavior.

### Step 3: Run a function from CLI

```bash
hojjat-tui run <function_name> --param KEY=VALUE
```

Or via manage.py:

```bash
python manage.py run <function_name> --param KEY=VALUE
```

---

## Project Initialization (`hojjat-tui init`)

The `init` command creates a new HOJJAT TUI project in the current working directory. It is safe to run multiple times — existing files are never overwritten.

### Generated files

| File | Purpose |
|------|---------|
| `manage.py` | Project entry point. Imports function modules and calls `run()`. |
| `functions/__init__.py` | Marks `functions/` as a Python package. |
| `functions/example.py` | Seven example functions demonstrating string, table, bar chart, line chart, input, JSON, and error output patterns. |

### Adding your own functions

1. Create a new module in `functions/` (e.g., `functions/my_functions.py`).
2. Register functions with `@hojjat_function()`.
3. Import the module in `manage.py`:

```python
from hojjat_tui import run
from functions import example
from functions import my_functions   # your new module

if __name__ == "__main__":
    run()
```

### Example: `functions/example.py`

The generated `example.py` contains seven functions:

1. **`hello_world`** — Simple string output (no parameters)
2. **`sample_data`** — Table output (list of dicts)
3. **`sales_by_region`** — Bar chart output (`ChartOutput` with `chart_type="bar"`)
4. **`temperature_trend`** — Line chart output (`ChartOutput` with `chart_type="line"`)
5. **`greet_user`** — Input parameter (typed `name: str` parameter)
6. **`system_info`** — JSON output (dict returned as formatted JSON)
7. **`error_demo`** — Error handling (raises `RuntimeError`)

Each function has docstrings explaining what it demonstrates and what to expect in the TUI.

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

### Decorator Parameters

| Parameter | Type | Required | Description |
|-----------|------|----------|-------------|
| `name` | `str` | No | Unique name for the function. If None, uses the function name. |
| `label` | `str` | No | Display label. If None, uses the `name`. |
| `description` | `str` | No | Human-readable description. Shown in TUI and documentation. |
| `annotations` | `dict` | No | Parameter type hints and descriptions for form generation. |
| `defaults` | `dict` | No | Default values for optional parameters. |
| `required` | `list[str]` | No | List of required parameter names. Parameters without defaults must be in this list. |

### Return Type

Functions can return any Python value. The executor automatically detects the output type:

- `ChartOutput` → `chart` (bar or line chart rendered as ASCII art)
- `str` → `text` (or `markdown` if it looks like markdown)
- `dict` → `json`
- `list` → `table`
- Other → `text`

### Running a Function

**In the TUI:**

1. Select a function from the menu (navigate with arrow keys)
2. Enter parameters in the input form
3. Press **Run** or `Ctrl+R`

**From CLI:**

```bash
python manage.py run my_function --param name World
```

or:

```bash
hojjat-tui run my_function --param name World
```

---

## Chain Engine

Chains allow you to link multiple functions together in a specified execution order. Each step in a chain can execute a registered function, with parameters sourced from literal values, user input, or output from previous steps. Chains are persisted in the SQLite database.

### Creating a Chain

```python
from hojjat_tui.chain import create_chain, add_step, literal
from hojjat_tui.chain import output_of, save_chain

# Create a new chain
chain = create_chain("greet", "Greeting Chain", "A chain that greets a user")

# Add steps
add_step(chain, "hello", params=[literal("name", "Alice")])
add_step(chain, "time_info")  # No extra params needed

# Save the chain
save_chain(chain)
```

### Parameter Binding Types

| Type | Description |
|------|-------------|
| **LITERAL** | Use a fixed value directly. Example: `literal("name", "Alice")` |
| **USER_INPUT** | Prompt the user for a value at runtime. Example: `user_input("name", "Enter your name")` |
| **PREVIOUS_STEP** | Use the output from a previous step in the chain. Example: `output_of("result", "step-uuid")` |

### Executing a Chain

**In the TUI:**

1. Navigate to the **Chains** menu
2. Select **New Chain** to open the chain builder
3. Enter a chain name, display label, and optional description
4. Select functions from the registry to add as steps
5. For each step, configure parameter bindings:
   - **Literal**: Use a fixed value
   - **User Input**: Prompt the user for a value
   - **Previous Step**: Use output from an earlier step
6. Save the chain with a unique name
7. Execute the chain from the chains menu

**From Python:**

```python
from hojjat_tui.chain import create_chain, add_step, literal, execute_chain

chain = create_chain("greet", "Greeting Chain", "A chain that greets a user")
add_step(chain, "hello", params=[literal("name", "Alice")])

execution = execute_chain(chain)
print(f"Chain status: {execution.status}")
```

---

## Chart Output

Functions can return chart data that the TUI displays as a text-based bar or line chart. To explicitly declare chart output, return a `ChartOutput` instance from your function:

```python
from hojjat_tui.function import hojjat_function, ChartOutput

@hojjat_function(
    name="sales_by_region",
    label="Sales by Region",
    description="Return regional sales as a bar chart.",
)
def sales_by_region() -> ChartOutput:
    return ChartOutput(
        chart_type="bar",
        labels=["North", "South", "East", "West", "Central"],
        values=[12400, 9800, 15600, 11200, 13400],
        title="Regional Sales Q3",
    )
```

When `sales_by_region()` is executed, the TUI automatically detects the `ChartOutput` and renders a bar chart:

```
    Title: Regional Sales Q3
    Data points: 5

          North   South   East    West   Central
          ------- ------- ------- ------- -------
  100%  |  ██████  ██████  ██████  ██████  ██████
   90%  |                                   ██████
   80%  |                                   ██████
   70%  |              ██████  ██████  ██████
   60%  |              ██████  ██████  ██████
   50%  |                                    ██████
   40%  |              ██████         ██████
   30%  |              ██████         ██████
   20%  |              ██████         ██████
   10%  |                                    ██████
    0%  |              12400.0  9800.0  15600.0  11200.0  13400.0
```

For a line chart, use `chart_type="line"`:

```python
@hojjat_function(
    name="temperature_trend",
    label="Temperature Trend",
    description="Return daily temperatures as a line chart.",
)
def temperature_trend() -> ChartOutput:
    return ChartOutput(
        chart_type="line",
        labels=["Mon", "Tue", "Wed", "Thu", "Fri", "Sat", "Sun"],
        values=[68, 72, 75, 73, 78, 81, 76],
        title="Weekly Temperature",
    )
```

**Chart API**: `ChartOutput(chart_type="bar"|"line", labels=[...], values=[...], title="...")`

- `chart_type`: Either `"bar"` or `"line"`
- `labels`: Category labels for the x-axis (strings)
- `values`: Numeric values for each label (floats or ints)
- `title`: Optional chart title

Charts require at least one label/value pair, and labels and values must have the same length.

---

## Hot Reload

HOJJAT TUI supports hot reloading function modules without restarting the TUI. Press **R** or **Ctrl+R**, or click **Refresh** in the TUI, to:

- Detect newly added functions in existing modules
- Detect modified function implementations (including changed signatures and parameter metadata)
- Detect newly created modules in the `functions/` directory
- Detect deleted functions and modules
- Remove stale registrations for functions that no longer exist

The refresh summary shows how many modules were added, updated, or removed. If a module fails to load (e.g., syntax error), the error is reported and the previous working registry is preserved.

Consumer projects do not require a `pyproject.toml`. Modules imported by `manage.py` are automatically tracked, and modules in the `functions/` directory are automatically discovered.

---

## Persistence Behavior

- **Chains**: User-created chains are persisted in the SQLite database (`hojjat_tui.db` in the platform-appropriate data directory, or configurable via `HOJJAT_TUI_DATA_DIR` environment variable)
- **Database location**:
  - Windows: `%APPDATA%\hojjat_tui\hojjat_tui.db`
  - macOS/Linux: `$XDG_DATA_HOME/hojjat_tui/hojjat_tui.db` (default: `$HOME/.local/share/hojjat_tui/hojjat_tui.db`)
- **On fresh startup**: The database is initialized empty with no saved chains
- **Database reset**: Use "Reset Database (Clear All Data)" in the TUI settings menu
- **User data**: Usernames and bcrypt-hashed passwords are also persisted in the same database

---

## Testing

### Run the Test Suite

```bash
python manage.py test
```

Or directly with pytest:

```bash
python -m pytest
```

---

## Project Structure

```
.
├── docs/                  # Professional developer documentation
├── src/hojjat_tui/        # Main package
│   ├── __init__.py        # Public API exports
│   ├── __main__.py        # python -m hojjat_tui entry point
│   ├── cli.py             # Console script + module CLI
│   ├── function.py        # @hojjat_function decorator + FunctionResult + ChartOutput
│   ├── executor.py        # Centralized function execution
│   ├── persistence.py     # SQLite database + bcrypt password hashing
│   ├── management.py      # Django-style management commands
│   ├── tui.py             # Textual TUI application
│   └── chain.py           # Chain Engine — persistent function chaining
├── manage.py              # Django-style management script
├── pyproject.toml         # Project configuration
├── AGENTS.md              # Project rules for AI agents
├── CHANGELOG.md           # Change log
├── LICENSE                # MIT License
├── README.md              # This file
└── .gitignore             # Git exclusions
```

---

## Contribution Guidelines

1. Follow Python 3.9+ PEP 8 style
2. Use `black` for formatting and `ruff` for linting
3. Add new functions using the `@hojjat_function` decorator
4. Add chain step binding types as needed
5. Write tests for new functionality
6. Run `python -m pytest` to verify existing tests pass
7. Respect the existing project structure and conventions
8. Update CHANGELOG.md for significant changes

---

## License

MIT License — see [LICENSE](LICENSE) for details.

**Current version: 2.0.1**

---

## Links

- [GitHub Repository](https://github.com/HojjatAhmadi/hojjat-tui)
- [Bug Tracker](https://github.com/HojjatAhmadi/hojjat-tui/issues)
- [Source Code](https://github.com/HojjatAhmadi/hojjat-tui)

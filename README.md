# HOJJAT TUI

[![Version](https://img.shields.io/badge/version-2.0.0-blue)](https://github.com/placeholder/hojjat-tui)
[![Python](https://img.shields.io/badge/python-3.9%2B-blue.svg)](https://www.python.org/downloads/)
[![License](https://img.shields.io/badge/license-MIT-green.svg)](LICENSE)

HOJJAT TUI is a terminal-based user interface (TUI) tool built with Python and [Textual](https://textual.textualize.io/). It provides a registry of user-contributed functions that can run inside the terminal, render structured results (text, Markdown, tables, charts, JSON), and chain together in future phases.

> **Note**: This is Phase 1 — a stable package foundation with a working end-to-end user journey through the TUI.

---

## Features

- **Function Registry**: Register Python functions with metadata via the `@hojjat_function` decorator
- **TUI Interface**: Navigate registered functions and enter parameters in an interactive Textual UI
- **Structured Output**: Render results as text, Markdown, tables, charts, JSON, and error/info panels
- **Persistence**: SQLite database for user metadata and execution logs
- **Password Security**: bcrypt-hashed administrative passwords
- **Management Commands**: Django-style `manage.py` interface for init, user management, running, checking, and testing

---

## Installation

### Prerequisites

- Python 3.9+

### Install from PyPI

```bash
pip install hojjat-tui
```

### Install from Source

```bash
git clone https://github.com/placeholder/hojjat-tui.git
cd hojjat-tui
pip install .
```

### Development Installation

```bash
python -m pip install -e ".[dev]"
```

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

- `manage.py` — the project entry point. Import your function modules here.
- `functions/example.py` — six example functions demonstrating string, table, chart, input, JSON, and error output patterns.
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
| `functions/example.py` | Six example functions demonstrating all output types. |

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

The generated `example.py` contains six functions:

1. **`hello_world`** — Simple string output (no parameters)
2. **`sample_data`** — Table output (list of dicts)
3. **`sales_by_region`** — Bar chart output (ChartOutput with `chart_type="bar"`)
4. **`temperature_trend`** — Line chart output (ChartOutput with `chart_type="line"`)
5. **`greet_user`** — Input parameter (typed `name: str` parameter)
6. **`system_info`** — JSON output (dict returned as formatted JSON)
7. **`error_demo`** — Error handling (raises `RuntimeError`)

Each function has docstrings explaining what it demonstrates and what to expect in the TUI.

---

## Management Commands

```bash
hojjat-tui init              # Create project structure
hojjat-tui                   # Start the TUI (executes manage.py)
hojjat-tui run <name>        # Run a registered function from CLI
hojjat-tui --version         # Show version
python manage.py             # Start the TUI (same as hojjat-tui)
python manage.py run <name>  # Run a function from CLI
python manage.py check       # Verify installation
python manage.py test        # Run the test suite
python manage.py createsuperuser  # Create a superuser account
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

**In the TUI:**

1. Select a function from the menu (navigate with arrow keys)
2. Enter parameters in the input box (e.g., `name=World`)
3. Press **Run** or **Ctrl+R**

**From CLI:**

```bash
python manage.py run my_function --param name World
```

---



### `hello`

- **Purpose**: Generate a greeting message.
- **Parameters**: 
  - `name` (required, str): Name to greet, default "World"
  - `times` (optional, int): Number of greetings to display, default 1
- **Output**: Text string with greeting messages
- **Example**: `hello(name="Alice", times=3)` returns `"Hello, Alice!\nHello, Alice!\nHello, Alice!"`

### `time_info`

- **Purpose**: Display current time and date information.
- **Parameters**: None (no parameters)
- **Output**: Dict with current time information
- **Example**: Returns `{"current_time": "2024-01-15 14:30:00", "timestamp": 1705312200.0, "weekday": "Monday", "iso_format": "2024-01-15T14:30:00", "day_of_year": 15, "week_of_year": 3}`.

### `factorial`

- **Purpose**: Calculate the factorial of a given number.
- **Parameters**: 
  - `n` (required, int): Number to calculate factorial of
- **Output**: Integer result
- **Example**: `factorial(n=5)` returns `120`

### `random_quote`

- **Purpose**: Generate a random inspirational quote.
- **Parameters**: None (no parameters)
- **Output**: String quote
- **Example**: Returns one of several quoted statements from notable figures.

### `ping_test`

- **Purpose**: Simulate a ping test and return timing results as a table.
- **Parameters**: 
  - `host` (required, str): Host to ping, default "localhost"
  - `count` (optional, int): Number of pings to send, default 3
- **Output**: List of dicts with timing data (seq, host, bytes, time_ms, ttl)
- **Example**: Returns `[{"seq": 1, "host": "localhost", "bytes": 64, "time_ms": 1.23, "ttl": 64}, ...]`

### `system_info`

- **Purpose**: Return basic system information as structured data.
- **Parameters**: None (no parameters)
- **Output**: Dict with system information
- **Example**: Returns `{"platform": "Windows-10-10.0-19041", "python_version": "3.9.0", ...}`

### `error_demo`

- **Purpose**: Demonstrate error handling in the TUI.
- **Parameters**: 
  - `message` (required, str): Error message to use, default "This is an intentional error"
- **Output**: Error result (raises RuntimeError)
- **Example**: Always raises `RuntimeError` with the provided message.

---

## Chain Creation and Execution

### Creating a Chain

Chains allow you to link multiple functions together in a specified order. Each step in a chain can:

- Execute a registered function
- Pass output from previous steps as input to subsequent steps
- Use literal values for parameters
- Request user input for parameters

### Building a Chain in the TUI

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

### Building a Chain via CLI or Python

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

### Executing a Chain

**In the TUI:**

1. Navigate to the **Chains** menu
2. Select a saved chain
3. Press **Execute Chain**
4. View results step by step, with table/chart rendering where applicable

**From CLI:**

```bash
python manage.py run-chain greet
```

### Parameter Binding Types

- **LITERAL**: Use a fixed value directly. Example: `literal("name", "Alice")`
- **USER_INPUT**: Prompt the user for a value at runtime. Example: `user_input("name", "Enter your name")`
- **PREVIOUS_STEP**: Use the output from a previous step in the chain. Example: `output_of("result", "step-uuid")`

### Result Presentation

Function results are rendered based on their detected output type:

| Type | Description |
|------|-------------|
| **text** | Plain text output |
| **markdown** | Markdown content (rendered with Rich) |
| **table** | List of dicts or list of lists rendered as a table |
| **chart** | ChartOutput (bar or line chart rendered as ASCII art) |
| **json** | Dict or JSON-compatible objects |
| **error** | Error messages in a red panel |
| **info** | Informational messages in a blue panel |

---

## Table Example

Functions can return tabular data that the TUI displays as a table. Supported formats:

- **List of dicts**: Each dict represents a row, keys become column headers
- **List of lists/tuples**: Each inner list/tuple represents a row

### Practical Example

```python
@hojjat_function(
    name="get_users",
    label="Get Users",
    description="Return a list of user records",
    annotations={},
    defaults={},
    required=[],
)
def get_users() -> list:
    return [
        ["Name", "Age"],
        ["Alice", 28],
        ["Bob", 34],
        ["Charlie", 22],
    ]
```

When `get_users()` is executed, the TUI automatically renders the output as a table with columns "Name" and "Age", displaying all four user records.

**Table access in TUI**: After executing a function with table output, press the **Table** button in the result screen to view the structured table view.

---

## Chart Example

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

**Chart access in TUI**: When a function returns `ChartOutput`, the TUI automatically renders the chart — no need to press a manual **Chart** button. The chart is shown directly in the result screen.

**Chart API**: `ChartOutput(chart_type="bar"|"line", labels=[...], values=[...], title="...")`

- `chart_type`: Either `"bar"` or `"line"`
- `labels`: Category labels for the x-axis (strings)
- `values`: Numeric values for each label (floats or ints)
- `title`: Optional chart title

Charts require at least one label/value pair, and labels and values must have the same length.

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

### Test Coverage

The test suite covers:

- **Persistence layer**: Database initialization, user management, password hashing, chain save/load/list/delete
- **Chain models**: Chain creation, step definitions, parameter bindings, validation
- **Chain execution**: Single-step and multi-step execution, output references, failed step handling
- **Function registration**: Decorator API, registry management
- **Password hashing**: bcrypt hash generation and verification

---

## Project Structure

```
.
├── docs/                  # Professional developer documentation
│   ├── index.md           # Landing page
│   ├── installation.md    # Installation guide
│   ├── architecture.md    # System architecture
│   ├── functions.md       # Function registration API
│   ├── chains.md          # Chain creation and execution
│   ├── results.md         # Result presentation and rendering
│   ├── database.md        # Database schema and persistence
│   └── development.md     # Development setup and contribution
├── src/hojjat_tui/        # Main package
│   ├── __init__.py        # Public API exports
│   ├── __main__.py        # python -m hojjat_tui entry point
│   ├── cli.py             # Console script + module CLI
│   ├── function.py        # @hojjat_function decorator + FunctionResult
│   ├── executor.py        # Centralized function execution
│   ├── renderer.py        # Output rendering (text, markdown, table, json)
│   ├── persistence.py     # SQLite database + bcrypt password hashing
│   ├── management.py      # Django-style management commands
│   ├── tui.py             # Textual TUI application
│   ├── builtin_functions.py # Built-in sample functions
│   └── py.typed           # PEP 561 type markers
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

**Current version: 2.0.0**
# Architecture

## Overview

HOJJAT TUI is a Python-based terminal user interface application built with the [Textual](https://textual.textualize.io/) framework. The system follows a modular architecture with clear separation of concerns between the UI layer, business logic, and data persistence.

## Component Diagram

```mermaid
graph TD
    subgraph "Application Layer"
        TUI[Textual TUI Application] -->|drives| CLI[CLI / Management Commands]
        TUI -->|drives| Executor[Function Executor]
    end

    subgraph "Business Logic Layer"
        Registry[Function Registry] -->|contains| Functions[Registered Functions]
        ChainEngine[Chain Engine] -->|manages| Chains[Chain Definitions]
        ChainExecutor[Chain Executor] -->|executes| Chains
    end

    subgraph "Data Persistence Layer"
        Database[SQLite Database] -->|stores| Chains[Chain Definitions]
        Database -->|stores| Executions[Execution History]
        Database -->|stores| Logs[Function Execution Logs]
    end

    style Database fill:#f9f6ec,stroke:#7aa2f7,stroke-width:2px
    style TUI fill:#24283b,stroke:#7aa2f7,stroke-width:2px,color:#c0caf5
```

## Core Modules

### `src/hojjat_tui/function.py`

- **Purpose**: Function registration decorator and global registry management.
- **Key APIs**: `@hojjat_function` decorator, `get_registry()`, `FunctionResult`, `ChartOutput`
- **Mechanism**: When a function is decorated with `@hojkat_function`, its metadata (name, label, description, annotations, defaults, required parameters) is stored in a global `_REGISTRY` dictionary. The decorator also stores a `_hojjat_metadata` attribute on the decorated function.

### `src/hojjat_tui/executor.py`

- **Purpose**: Centralized function execution with output type detection and execution logging.
- **Key APIs**: `execute_function(name, kwargs)`, `_detect_output_type(output)`, `_log_execution(name, result)`
- **Mechanism**: Looks up the function in `_REGISTRY`, calls it with the given keyword arguments, detects the output type (text, markdown, json, table, chart), logs the execution, and returns a `FunctionResult` dataclass.

### `src/hojjat_tui/chain.py`

- **Purpose**: Chain Engine — persistent function chaining framework.
- **Key APIs**: `create_chain()`, `add_step()`, `literal()`, `user_input()`, `output_of()`, `validate_chain()`, `execute_chain()`, `save_chain()`, `load_chain()`, `list_chains()`, `delete_chain()`
- **Mechanism**: Implements Pydantic data models for `Chain`, `ChainStep`, `ParameterBinding`, and `ChainExecution`. Supports three binding types: `LITERAL`, `USER_INPUT`, and `PREVIOUS_STEP`. Chains are persisted in the SQLite database via the persistence layer.

### `src/hojjat_tui/tui.py`

- **Purpose**: Textual-based interactive TUI application.
- **Key Features**: Function menu navigation, chain builder wizard, function execution forms, result display with table/chart rendering, persistent chain management, hot reload.
- **Mechanism**: A `textual.app.App` subclass that composes screens for function selection, chain building, chain execution, and result viewing. On mount, reads the function registry populated by `manage.py`. Supports hot reload via the `R` key or **Refresh** button.

### `src/hojjat_tui/persistence.py`

- **Purpose**: SQLite-based storage for metadata, chain definitions, and execution logs.
- **Key APIs**: `Database` class, `hash_password()`, `verify_password()`, `save_chain()`, `load_chain()`, `list_chains()`, `clear_all_data()`, `get_default_db_path()`
- **Mechanism**: Provides a SQLite database wrapper with automatic table initialization. Stores chain definitions, chain steps, parameter bindings, execution history, and function execution logs. Database schema versioning is tracked in the `schema_meta` table.

### `src/hojjat_tui/cli.py`

- **Purpose**: Console script entry point for the `hojjat-tui` command.
- **Key Features**: Starts the TUI when no arguments are provided, delegates to management commands when arguments are given, version display.
- **Mechanism**: The `main()` function checks `sys.argv` and either starts the TUI or delegates to the management command dispatcher.

### `src/hojjat_tui/management.py`

- **Purpose**: Django-style management commands for project administration.
- **Key Commands**: `init`, `createsuperuser`, `run`, `check`, `test`, `--version`
- **Mechanism**: An argparse-based command-line interface that provides administrative functions for project initialization, user management, function execution, project checking, and testing.

### `src/hojjat_tui/builtin_functions.py`

- **Purpose**: Built-in function registration module (placeholder).
- **Key APIs**: `register_builtins()` (no-op)
- **Mechanism**: Intentionally a no-op. No built-in functions are automatically registered. Users register their own functions via the `@hojjat_function` decorator.

## Data Flow

### Function Execution Flow

1. User selects a function from the TUI menu or runs via CLI
2. The TUI gathers parameter values from the user (via form inputs or parameter bindings)
3. `execute_function(name, kwargs)` is called
4. The function is looked up in the global registry and executed
5. Output type is detected and a `FunctionResult` is returned
6. The result is rendered by the TUI (text, table, markdown, etc.)
7. Execution is logged to the SQLite database

### Chain Execution Flow

1. User selects a saved chain from the TUI chains menu
2. `load_chain(name)` retrieves the chain definition from the database
3. `execute_chain(chain)` runs each step sequentially
4. Parameter bindings are resolved:
   - LITERAL values are used directly
   - USER_INPUT prompts the user at runtime
   - PREVIOUS_STEP retrieves output from a previous step
5. Each step's function is executed via `execute_function()`
6. Step results are collected and the overall chain status is determined
7. Execution history is saved to the SQLite database
8. Results are displayed in the TUI with appropriate rendering

### Chain Building Flow

1. User initiates chain creation from the TUI
2. The chain builder screen is displayed with function selector
3. User adds steps by selecting functions from the registry
4. For each step, user configures parameter bindings (literal, user input, previous step)
5. User saves the chain with a unique name
6. The chain definition is persisted via `save_chain()` to the SQLite database
7. The chain is immediately available for execution from the chains menu

### Hot Reload Flow

1. User presses **R** or **Ctrl+R** (or clicks **Refresh**)
2. `reload_function_modules()` is called
3. All tracked modules (from `pyproject.toml`, `functions/` directory, and `_LOADED_MODULES`) are re-imported
4. `_REGISTRY` is rebuilt with the current state of all decorated functions
5. The TUI function list is updated to reflect added, modified, or deleted functions
6. A summary message shows how many modules were added, updated, or removed

## Extensibility

### Adding New Functions

To add a new function:

```python
from hojjat_tui.function import hojjat_function

@hojkat_function(
    name="my_new_function",
    label="My New Function",
    description="Does something useful",
    annotations={"input_param": {"type": "str", "description": "Input parameter"}},
    defaults={"input_param": ""},
    required=["input_param"],
)
def my_new_function(input_param: str = "") -> dict:
    return {"processed": input_param.upper()}
```

The function will be automatically registered in the global registry and available in the TUI once its module is imported by `manage.py`.

### Adding New Chart Rendering

Chart output is supported via the `ChartOutput` class:

```python
from hojjat_tui.function import hojjat_function, ChartOutput

@hojkat_function(
    name="my_chart",
    label="My Chart",
    description="Returns chart data.",
)
def my_chart() -> ChartOutput:
    return ChartOutput(
        chart_type="bar",
        labels=["A", "B", "C"],
        values=[10, 20, 15],
        title="Sample Chart",
    )
```

The TUI automatically detects `ChartOutput` and renders it as ASCII art without requiring a manual button press.

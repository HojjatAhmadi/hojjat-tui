# Development Guide — HOJJAT TUI

## Setting Up a Development Environment

```bash
python -m pip install -e ".[dev]"
```

## Running the Application

### TUI
```bash
hojjat-tui          # console script
python -m hojjat_tui  # Python module
```

### Management Commands
```bash
python manage.py init              # Initialize project structure
python manage.py check             # Verify installation
python manage.py test              # Run tests
python manage.py run <function> --param KEY=VALUE  # Run a function
python manage.py createsuperuser   # Create an administrative user
```

## Running Tests

```bash
python -m pytest                    # Run all tests
python -m pytest -v                # Verbose output
python -m pytest tests/ -k test_name  # Run specific tests
```

## Code Quality

```bash
ruff check src/ tests/    # Lint
ruff format src/ tests/   # Format
black --check src/ tests/ # Verify formatting
```

## Project Layout

```
hojjat-tui/
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
│   ├── chain.py           # Chain Engine — persistent function chaining
│   ├── builtin_functions.py # Built-in function registration (no-op placeholder)
│   └── py.typed           # PEP 561 type markers
├── manage.py              # Django-style management script
├── pyproject.toml         # Project configuration
├── AGENTS.md              # Project rules for AI agents
├── CHANGELOG.md           # Change log
├── LICENSE                # MIT License
├── README.md              # This file
└── .gitignore             # Git exclusions
```

## Adding New Functions

1. Create a new Python module in your project's `functions/` directory
2. Use the `@hojjat_function` decorator:

```python
from hojjat_tui.function import hojjat_function

@hojjat_function(
    name="my_tool",
    label="My Tool",
    description="Does something useful",
    annotations={
        "input": {"type": "str", "description": "Input text"},
    },
    defaults={"input": ""},
    required=["input"],
)
def my_tool(input: str = "") -> dict:
    return {"result": input.upper()}
```

3. Import the module in your project's `manage.py` so the decorator executes:

```python
from hojjat_tui import run
from functions import example
from functions import my_functions   # your new module

if __name__ == "__main__":
    run()
```

## Output Contract

Functions should return one of these types for proper rendering:

| Return Type        | Rendered As         |
|-------------------|---------------------|
| `str`             | Text or Markdown    |
| `dict`            | JSON                |
| `list[dict]`      | Table               |
| `ChartOutput`     | Bar or Line chart   |
| Any other type    | String representation |

## Error Handling

Functions should:
- Raise descriptive exceptions (caught by the executor)
- Return `FunctionResult` only if you need explicit control

The executor wraps all calls in try/except and converts exceptions to `FunctionResult` objects with `success=False`.

## Database

- SQLite database stored in platform-specific app data directory
- Tables: `function_logs`, `config`, `chains`, `chain_steps`, `chain_param_bindings`, `chain_executions`, `step_executions`
- `init_db()` is idempotent — safe to rerun
- Password hashing uses bcrypt with 12 rounds (for user accounts)

## Hot Reload

Press **R** or **Ctrl+R** (or click **Refresh**) in the TUI to reload function modules without restarting the application. This:

- Detects newly added functions in existing modules
- Detects modified function implementations (including changed signatures)
- Detects newly created modules in `functions/`
- Detects deleted functions and modules
- Removes stale registrations

Consumer projects do not require a `pyproject.toml`. Modules imported by `manage.py` are automatically tracked.

## Chains

The Chain Engine allows linking multiple functions together. See [chains.md](chains.md) for details on `create_chain()`, `add_step()`, `literal()`, `user_input()`, `output_of()`, `validate_chain()`, `execute_chain()`, `save_chain()`, `load_chain()`, `list_chains()`, and `delete_chain()`.

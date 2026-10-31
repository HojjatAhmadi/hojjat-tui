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
python manage.py init              # Initialize database
python manage.py createsuperuser  # Create admin user
python manage.py check            # Verify installation
python manage.py test             # Run tests
python manage.py run hello --param name=World  # Run a function
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
ruff format src/ tests/   # Format (if configured)
black --check src/ tests/ # Verify formatting
```

## Project Layout

```
hojjat-tui/
├── src/hojjat_tui/
│   ├── __init__.py          # Public API
│   ├── __main__.py          # Module entry point
│   ├── cli.py               # Console script entry point
│   ├── function.py          # Decorator + FunctionResult
│   ├── executor.py          # Execution engine
│   ├── renderer.py          # Output rendering
│   ├── persistence.py       # SQLite + bcrypt
│   ├── management.py        # Management commands
│   ├── tui.py               # Textual TUI app
│   ├── builtin_functions.py # Built-in sample functions
│   └── py.typed             # PEP 561 marker
├── tests/
│   ├── __init__.py
│   ├── conftest.py
│   ├── test_function.py
│   ├── test_executor.py
│   ├── test_persistence.py
│   ├── test_renderer.py
│   ├── test_cli.py
│   └── test_tui.py
├── manage.py
├── pyproject.toml
├── AGENTS.md
├── README.md
├── CHANGELOG.md
├── LICENSE
└── .gitignore
```

## Adding New Functions

1. Create a new Python module in `src/hojjat_tui/`
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

3. Import the module at startup (e.g., in `manage.py` or `__init__.py`)

## Output Contract

Functions should return one of these types for proper rendering:

| Return Type        | Rendered As         |
|-------------------|---------------------|
| `str`             | Text or Markdown    |
| `dict`            | JSON                |
| `list[dict]`      | Table               |
| Any other type    | String representation |

## Error Handling

Functions should:
- Raise descriptive exceptions (caught by the executor)
- Return `FunctionResult` only if you need explicit control

The executor wraps all calls in try/except and converts exceptions to `FunctionResult` objects with `success=False`.

## Database

- SQLite database stored in platform-specific app data directory
- Tables: `users`, `function_logs`, `config`, `schema_meta`
- `init_db()` is idempotent — safe to rerun
- Password hashing uses bcrypt with 12 rounds
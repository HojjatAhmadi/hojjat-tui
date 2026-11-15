# Functions

## Function Registration

### The `@hojjat_function` Decorator

Register Python functions with HOJJAT TUI using the `@hojjat_function` decorator. This adds the function to the global registry and makes it available through the TUI and CLI.

### Syntax

```python
from hojjat_tui.function import hojjat_function

@hojjat_function(
    name="function_name",
    label="Display Label",
    description="Human-readable description",
    annotations={
        "param1": {"type": "str", "description": "Parameter 1 description"},
        "param2": {"type": "int", "description": "Parameter 2 description"},
    },
    defaults={"param1": "", "param2": 0},
    required=["param1"],
)
def my_function(param1: str = "", param2: int = 0) -> dict:
    """Function description."""
    return {"result": f"{param1} - {param2}"}
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

### Example: Simple Greeting

```python
from hojjat_tui.function import hojjat_function

@hojjat_function(
    name="hello",
    label="Hello World",
    description="A simple greeting function that takes a name parameter",
    annotations={
        "name": {"type": "str", "description": "Name to greet"},
        "times": {"type": "int", "description": "Number of greetings to display"},
    },
    defaults={"name": "World", "times": 1},
    required=["name"],
)
def hello(name: str = "World", times: int = 1) -> str:
    """Generate a greeting message."""
    messages = [f"Hello, {name}!" for _ in range(times)]
    return "\n".join(messages)
```

### Example: No-Parameter Function

```python
from hojjat_tui.function import hojjat_function

@hojjat_function(
    name="time_info",
    label="Time Info",
    description="Display current time and date information",
)
def time_info() -> dict:
    """Return current time information."""
    from datetime import datetime
    now = datetime.now()
    return {
        "current_time": now.strftime("%Y-%m-%d %H:%M:%S"),
        "timestamp": now.timestamp(),
        "weekday": now.strftime("%A"),
        "iso_format": now.isoformat(),
    }
```

### Getting the Registry

### `get_registry()`

Returns a dictionary of all registered functions with their metadata:

```python
from hojjat_tui.function import get_registry

registry = get_registry()
for name, metadata in registry.items():
    print(f"{name}: {metadata['description']}")
```

### Registry Entry Structure

Each entry in the registry dictionary contains:

```python
{
    "label": str,           # Display label
    "description": str,     # Function description
    "annotations": dict,    # Parameter type hints
    "defaults": dict,       # Default values for optional parameters
    "required": list,       # Required parameter names
    "signature": inspect.Signature,  # Function signature
    "module": str,          # Module where the function is defined
}
```

## Built-in Functions

HOJJAT TUI does not include any pre-registered built-in functions. The `register_builtins()` function in `builtin_functions.py` is intentionally a no-op. All functions must be explicitly registered by the user via the `@hojjat_function()` decorator and imported through `manage.py`.

## Adding Functions at Runtime

Functions can be registered at runtime using the `register()` alias:

```python
from hojjat_tui.function import register

@register
def my_function(x: int) -> int:
    return x * 2
```

This is equivalent to `@hojjat_function()(func)`.

## Function Result Structure

All registered functions return values through a `FunctionResult` dataclass:

| Field | Type | Description |
|-------|------|-------------|
| `name` | `str` | Function name |
| `success` | `bool` | Whether execution succeeded |
| `duration` | `float` | Execution time in seconds |
| `timestamp` | `float` | Execution timestamp |
| `output` | `Any` | Return value (str, dict, list) |
| `error` | `str?` | Error message if failed |
| `type` | `str` | Detected output type (text, markdown, json, table, chart, error, info) |
| `metadata` | `dict` | Additional execution metadata |

### `FunctionResult.to_text()`

Converts the result to a text representation:

- If successful and output is a dict: JSON-serialized string
- If successful and output is a string: the string itself
- If successful and output is other: `str(output)`
- If failed: `f"Error: {self.error}"`

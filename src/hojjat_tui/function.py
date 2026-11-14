import inspect
import importlib
import logging
import sys
import time
import typing as t
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any, Callable, Dict, List, Optional, Tuple, Union

if t.TYPE_CHECKING:
    from textual.message import Message

logger = logging.getLogger("hojjat_tui.function")

@dataclass
class FunctionResult:
    """Standardized result structure for registered functions."""
    name: str
    success: bool
    duration: float
    timestamp: float = field(default_factory=time.time)
    output: Union[str, Dict[str, Any], None] = None
    error: Optional[str] = None
    type: str = "text"
    metadata: Dict[str, Any] = field(default_factory=dict)

    def to_text(self) -> str:
        """Convert result to text representation."""
        if self.success:
            if isinstance(self.output, dict):
                import json
                return json.dumps(self.output, indent=2)
            elif isinstance(self.output, str):
                return self.output
            else:
                return str(self.output)
        else:
            return f"Error: {self.error}"

# Global registry
_REGISTRY: Dict[str, Callable] = {}
# Execution logger
_LOGGER: Dict[str, list] = {}

def hojjat_function(
    name: Optional[str] = None,
    label: Optional[str] = None,
    description: str = "",
    annotations: Optional[Dict[str, Any]] = None,
    defaults: Optional[Dict[str, Any]] = None,
    required: Optional[list[str]] = None,
):
    """Decorator to register a Python function with HOJJAT TUI.
    
    Args:
        name: Unique name for the function. If None, uses the function name.
        label: Display label. If None, uses the name.
        description: Human-readable description.
        annotations: Parameter type hints and descriptions for form generation.
        defaults: Default values for optional parameters.
        required: List of required parameter names.
    """
    def decorator(func: Callable) -> Callable:
        local_name = name if name is not None else func.__name__
        
        # Duplicate name detection
        if local_name in _REGISTRY:
            raise ValueError(f"Function name '{local_name}' is already registered")
        
        # Set defaults for missing parameters
        local_defaults = defaults if defaults is not None else {}
        local_required = required if required is not None else []
        local_annotations = annotations if annotations is not None else {}
        
        # Store function metadata
        func._hojjat_metadata = {
            "name": local_name,
            "label": label or local_name,
            "description": description,
            "annotations": local_annotations,
            "defaults": local_defaults,
            "required": local_required,
            "func": func,
            "signature": inspect.signature(func),
            "module": func.__module__,
        }
        
        # Register the function
        _REGISTRY[local_name] = func
        
        # Store in logger
        if local_name not in _LOGGER:
            _LOGGER[local_name] = []
        
        return func
    
    return decorator

def register(func: Callable) -> Callable:
    """Alias for hojjat_function decorator."""
    # Use the same defaults as hojjat_function but with no arguments
    return hojjat_function()(func)

def get_registry() -> Dict[str, Dict[str, Any]]:
    """Get all registered functions with their metadata."""
    registry = {}
    for name, func in _REGISTRY.items():
        metadata = getattr(func, "_hojjat_metadata", {})
        registry[name] = {
            "label": metadata.get("label", name),
            "description": metadata.get("description", ""),
            "annotations": metadata.get("annotations", {}),
            "defaults": metadata.get("defaults", {}),
            "required": metadata.get("required", []),
            "signature": metadata.get("signature"),
            "module": metadata.get("module"),
        }
    return registry

def get_logger() -> Dict[str, list]:
    """Get execution logs."""
    return _LOGGER.copy()

def clear_logger():
    """Clear execution logs."""
    global _LOGGER
    _LOGGER = {name: [] for name in _LOGGER}


# ---------------------------------------------------------------------------
# Automatic function module discovery
# ---------------------------------------------------------------------------

_LOADED_MODULES: set[str] = set()


def find_project_root() -> Optional[Path]:
    """Find the project root by walking up from CWD looking for pyproject.toml."""
    current = Path.cwd()
    for parent in [current] + list(current.parents):
        if (parent / "pyproject.toml").is_file():
            return parent
    return None


def read_function_modules() -> List[str]:
    """Read function_modules from [tool.hojjat-tui] in pyproject.toml.

    Returns an empty list if no configuration exists or the file cannot be read.
    """
    root = find_project_root()
    if root is None:
        return []

    pyproject_path = root / "pyproject.toml"
    if not pyproject_path.is_file():
        return []

    try:
        try:
            import tomllib  # Python 3.11+

            with open(pyproject_path, "rb") as f:
                data = tomllib.load(f)
        except ImportError:
            # Python < 3.11: minimal fallback parser for [tool.hojjat-tui]
            data = _parse_pyproject_toml_simple(pyproject_path)

        tool = data.get("tool", {}) if isinstance(data, dict) else {}
        hojjat = tool.get("hojjat-tui", {}) if isinstance(tool, dict) else {}
        modules = hojjat.get("function_modules", []) if isinstance(hojjat, dict) else []
        if isinstance(modules, str):
            modules = [modules]
        return [str(m) for m in modules]
    except Exception:
        logger.debug("Failed to read function_modules from pyproject.toml", exc_info=True)
        return []


def _parse_pyproject_toml_simple(path: Path) -> Dict[str, Any]:
    """Minimal TOML fallback parser for [tool.hojjat-tui].function_modules.

    Only handles the specific key we need; returns {} on any parsing difficulty.
    """
    try:
        text = path.read_text(encoding="utf-8")
    except Exception:
        return {}

    in_hojjat = False
    result: Dict[str, Any] = {}
    current_key: Optional[str] = None
    current_values: List[str] = []

    for raw_line in text.splitlines():
        line = raw_line.strip()
        if not line or line.startswith("#"):
            continue

        if line == "[tool.hojjat-tui]":
            in_hojjat = True
            continue
        if line.startswith("[") and line.endswith("]"):
            in_hojjat = False
            continue

        if not in_hojjat:
            continue

        if "=" in line:
            # Flush any previous multi-line array
            if current_key is not None:
                result[current_key] = current_values
                current_key = None
                current_values = []

            key, _, value = line.partition("=")
            key = key.strip()
            value = value.strip()

            if key == "function_modules":
                if value.startswith("["):
                    # Inline array: ["main", "functions"]
                    current_key = key
                    current_values = _parse_inline_array(value)
                else:
                    # Single quoted string
                    result[key] = [_strip_quotes(value)]

    if current_key is not None:
        result[current_key] = current_values

    return result


def _parse_inline_array(value: str) -> List[str]:
    """Parse a simple inline TOML array of strings."""
    if not (value.startswith("[") and value.endswith("]")):
        return []
    inner = value[1:-1].strip()
    if not inner:
        return []
    parts = [p.strip() for p in inner.split(",")]
    return [_strip_quotes(p) for p in parts if p]


def _strip_quotes(value: str) -> str:
    """Remove surrounding matching quotes from a string."""
    value = value.strip()
    if len(value) >= 2 and value[0] == value[-1] and value[0] in ("'", '"'):
        return value[1:-1]
    return value


def load_function_modules() -> Tuple[List[str], List[str]]:
    """Import configured function modules so their decorators register functions.

    Returns:
        (loaded_modules, errors) where loaded_modules is a list of successfully
        imported module names and errors is a list of human-readable error
        messages for modules that failed to import.

    Modules already in sys.modules are not re-imported (Python module caching
    ensures decorators only run once per module).
    """
    modules = read_function_modules()
    loaded: List[str] = []
    errors: List[str] = []

    root = find_project_root()
    if root is not None:
        root_str = str(root)
        if root_str not in sys.path:
            sys.path.insert(0, root_str)

    for module_name in modules:
        if not module_name:
            continue
        if module_name in _LOADED_MODULES:
            continue
        try:
            importlib.import_module(module_name)
            _LOADED_MODULES.add(module_name)
            loaded.append(module_name)
        except ImportError as e:
            errors.append(
                f"Failed to import function module '{module_name}': {e}"
            )
            logger.warning("Failed to import function module '%s': %s", module_name, e)
        except Exception as e:
            errors.append(
                f"Failed to import function module '{module_name}': {e}"
            )
            logger.exception("Failed to import function module '%s'", module_name)

    return loaded, errors


def get_loaded_modules() -> List[str]:
    """Return the sorted list of loaded function module names."""
    return sorted(_LOADED_MODULES)
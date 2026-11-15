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


@dataclass
class ChartOutput:
    """Explicit chart output for bar and line charts.

    Functions return a :class:`ChartOutput` instance to declare that their
    result should be rendered as a chart rather than as a table or text.

    Attributes:
        chart_type: Either ``"bar"`` or ``"line"``.
        labels: Category labels for the x-axis.
        values: Numeric values for each label.
        title: Optional chart title.
    """

    chart_type: str
    labels: List[str]
    values: List[float]
    title: str = ""

    def __post_init__(self):
        if self.chart_type not in ("bar", "line"):
            raise ValueError(
                f"Invalid chart type: {self.chart_type!r}. "
                "Must be 'bar' or 'line'."
            )
        if len(self.labels) != len(self.values):
            raise ValueError(
                f"Labels and values must have the same length "
                f"({len(self.labels)} labels vs {len(self.values)} values)."
            )
        if not self.labels:
            raise ValueError("Chart must have at least one label/value pair.")

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
    """Find the project root by walking up from CWD looking for project markers.

    A project root is identified by the presence of any of:
    - pyproject.toml (configuration file)
    - manage.py (HOJJAT TUI project entry point)
    - functions/ directory (contains registered function modules)

    Returns None if no project marker is found.
    """
    current = Path.cwd()
    for parent in [current] + list(current.parents):
        if (parent / "pyproject.toml").is_file():
            return parent
        if (parent / "manage.py").is_file():
            return parent
        if (parent / "functions").is_dir():
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

    # Also discover modules from _REGISTRY metadata. Functions registered
    # by direct imports in manage.py (e.g. "from functions import example")
    # have _hojjat_metadata["module"] set, but may not appear in
    # pyproject.toml's function_modules. Including them ensures hot reload
    # works for consumer projects without pyproject.toml.
    for func in _REGISTRY.values():
        metadata = getattr(func, "_hojjat_metadata", {})
        mod = metadata.get("module")
        if mod and mod not in modules:
            modules.append(mod)

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
            # Track file stats for future change detection
            root = find_project_root()
            file_path = _find_module_file(module_name, root)
            if file_path is not None:
                _MODULE_FILE_PATHS[module_name] = file_path
                try:
                    stat = file_path.stat()
                    _MODULE_TIMESTAMPS[module_name] = (stat.st_mtime, stat.st_size)
                except OSError:
                    pass
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


# ---------------------------------------------------------------------------
# Hot reload / module change detection
# ---------------------------------------------------------------------------

_MODULE_TIMESTAMPS: Dict[str, Tuple[float, int]] = {}
_MODULE_FILE_PATHS: Dict[str, Path] = {}


def scan_functions_directory() -> List[str]:
    """Scan the functions/ directory for Python module files.

    Returns a sorted list of dotted module names (e.g. ``functions.example``),
    excluding __init__.py.
    """
    root = find_project_root()
    if root is None:
        return []

    functions_dir = root / "functions"
    if not functions_dir.is_dir():
        return []

    modules: List[str] = []
    for f in sorted(functions_dir.glob("*.py")):
        if f.name == "__init__.py":
            continue
        modules.append(f"functions.{f.stem}")
    return modules


def _find_module_file(module_name: str, root: Optional[Path]) -> Optional[Path]:
    """Find the source file path for a given module name.

    Handles dotted module names (e.g. ``functions.example`` → ``functions/example.py``)
    and bare names (e.g. ``main`` → ``main.py``).
    Checks the functions/ directory first, then falls back to sys.path.
    """
    path_parts = module_name.split(".")

    if root is not None:
        # If the module name starts with "functions.", look in the functions/ directory.
        if path_parts[0] == "functions" and len(path_parts) == 2:
            candidate = root / "functions" / f"{path_parts[1]}.py"
            if candidate.is_file():
                return candidate
        # Otherwise, look for the module as a dotted path under root.
        candidate = root / Path(*path_parts).with_suffix(".py")
        if candidate.is_file():
            return candidate

    for path in sys.path:
        candidate = Path(path) / Path(*path_parts).with_suffix(".py")
        if candidate.is_file():
            return candidate

    return None


def _remove_module_functions(module_name: str) -> List[str]:
    """Remove all functions belonging to a module from the registry.

    Returns the list of removed function names.
    """
    to_remove: List[str] = []
    for name, func in list(_REGISTRY.items()):
        metadata = getattr(func, "_hojjat_metadata", {})
        if metadata.get("module") == module_name:
            to_remove.append(name)

    for name in to_remove:
        del _REGISTRY[name]
        _LOGGER.pop(name, None)

    return to_remove


def reload_function_modules() -> Dict[str, Any]:
    """Reload all function modules, detecting additions, modifications, and deletions.

    Scans the configured modules (from pyproject.toml) and the functions/
    directory.  Compares file timestamps and sizes to detect changes.

    Uses an atomic backup/restore strategy: all project modules are removed
    from sys.modules and re-imported fresh.  If any module fails to load
    (e.g. syntax error), the entire registry and sys.modules state are
    restored to their pre-refresh values, so the TUI is never left in a
    corrupted or partially updated state.

    Returns a dict with keys:
        added      - list of newly imported module names
        updated    - list of reloaded module names
        removed    - list of removed module names
        errors     - list of human-readable error messages
        summary    - human-readable summary string
    """
    global _LAST_RELOAD_RESULT
    configured = set(read_function_modules())
    discovered = set(scan_functions_directory())
    tracked = set(_LOADED_MODULES)
    all_modules = configured | discovered | tracked

    root = find_project_root()
    if root is not None:
        root_str = str(root)
        if root_str not in sys.path:
            sys.path.insert(0, root_str)

    # --- Backup current state for atomic rollback ---------------------
    backup_registry = dict(_REGISTRY)
    backup_loaded = set(_LOADED_MODULES)
    backup_timestamps = dict(_MODULE_TIMESTAMPS)
    backup_file_paths = dict(_MODULE_FILE_PATHS)
    backup_sys_modules: Dict[str, Any] = {}
    for mod_name in backup_loaded:
        if mod_name in sys.modules:
            backup_sys_modules[mod_name] = sys.modules[mod_name]

    # Determine removed modules (loaded but no longer in all_modules)
    removed: List[str] = sorted(backup_loaded - all_modules)

    # If there are no modules to reload, still clean up removed modules
    # but preserve the rest of the registry. Functions registered via
    # direct imports (not tracked by module discovery) must survive.
    if not all_modules:
        for mod_name in removed:
            _remove_module_functions(mod_name)
            _LOADED_MODULES.discard(mod_name)
            _MODULE_TIMESTAMPS.pop(mod_name, None)
            _MODULE_FILE_PATHS.pop(mod_name, None)

        summary = "No changes detected." if not removed else f"Refresh completed: {len(removed)} removed."
        result = {
            "added": [],
            "updated": [],
            "removed": removed,
            "errors": [],
            "summary": summary,
        }
        _LAST_RELOAD_RESULT = result
        return result

    # --- Clear state for fresh reload ---------------------------------
    _REGISTRY.clear()
    _LOADED_MODULES.clear()
    _MODULE_TIMESTAMPS.clear()
    _MODULE_FILE_PATHS.clear()

    # Remove all project modules from sys.modules so they get re-imported
    # with fresh decorator execution.
    for mod_name in backup_loaded:
        sys.modules.pop(mod_name, None)
    for mod_name in all_modules:
        sys.modules.pop(mod_name, None)

    added: List[str] = []
    updated: List[str] = []
    errors: List[str] = []

    # --- Import / reload every module ---------------------------------
    reload_failed = False

    for mod_name in sorted(all_modules):
        if not mod_name:
            continue

        # Find the source file for timestamp tracking
        file_path = _find_module_file(mod_name, root)

        # If the module file no longer exists, treat it as removed.
        # This handles consumer projects where manage.py imports modules
        # directly (no pyproject.toml) and a module file is deleted.
        if file_path is None:
            removed.append(mod_name)
            _LOADED_MODULES.discard(mod_name)
            _MODULE_TIMESTAMPS.pop(mod_name, None)
            _MODULE_FILE_PATHS.pop(mod_name, None)
            continue

        current_stats = None
        _MODULE_FILE_PATHS[mod_name] = file_path
        try:
            stat = file_path.stat()
            current_stats = (stat.st_mtime, stat.st_size)
        except OSError:
            pass

        try:
            importlib.import_module(mod_name)
            _LOADED_MODULES.add(mod_name)
            if current_stats is not None:
                _MODULE_TIMESTAMPS[mod_name] = current_stats

            # Only report as "updated" if the file actually changed.
            # Modules that were re-imported for atomicity but haven't
            # changed are not reported as updates.
            if mod_name in backup_loaded:
                previous_stats = backup_timestamps.get(mod_name)
                if current_stats != previous_stats:
                    updated.append(mod_name)
            else:
                added.append(mod_name)
        except Exception as e:
            errors.append(f"Failed to load '{mod_name}': {e}")
            logger.warning("Failed to load module '%s': %s", mod_name, e)
            reload_failed = True

    # --- Rollback on any failure --------------------------------------
    if reload_failed:
        # Restore everything from backup
        _REGISTRY.clear()
        _REGISTRY.update(backup_registry)
        _LOADED_MODULES.clear()
        _LOADED_MODULES.update(backup_loaded)
        _MODULE_TIMESTAMPS.clear()
        _MODULE_TIMESTAMPS.update(backup_timestamps)
        _MODULE_FILE_PATHS.clear()
        _MODULE_FILE_PATHS.update(backup_file_paths)

        # Restore sys.modules from backup
        for mod_name in all_modules:
            sys.modules.pop(mod_name, None)
        for mod_name, mod in backup_sys_modules.items():
            sys.modules[mod_name] = mod

        summary = "Refresh failed — previous registry preserved."
        result = {
            "added": [],
            "updated": [],
            "removed": [],
            "errors": errors,
            "summary": summary,
        }
    else:
        summary_parts: List[str] = []
        if added:
            summary_parts.append(f"{len(added)} added")
        if updated:
            summary_parts.append(f"{len(updated)} updated")
        if removed:
            summary_parts.append(f"{len(removed)} removed")
        if errors:
            summary_parts.append(f"{len(errors)} error(s)")
        if not summary_parts:
            summary = "No changes detected."
        else:
            summary = "Refresh completed: " + ", ".join(summary_parts) + "."

        result = {
            "added": added,
            "updated": updated,
            "removed": removed,
            "errors": errors,
            "summary": summary,
        }

    # Cache for UI display
    _LAST_RELOAD_RESULT = result

    return result


def get_reload_summary() -> str:
    """Return a human-readable summary of the last reload operation.

    Returns "No reload has been performed yet." if reload_function_modules()
    has never been called.
    """
    # This is a placeholder; callers should use the summary from
    # reload_function_modules() directly.
    return "No reload summary available."


# Keep last reload result for UI display
_LAST_RELOAD_RESULT: Dict[str, Any] = {
    "added": [],
    "updated": [],
    "removed": [],
    "errors": [],
    "summary": "No reload has been performed yet.",
}


def get_last_reload_result() -> Dict[str, Any]:
    """Return the result dict from the most recent reload_function_modules() call."""
    return dict(_LAST_RELOAD_RESULT)
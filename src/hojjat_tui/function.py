import inspect
import time
import typing as t
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any, Callable, Dict, Optional, Union

if t.TYPE_CHECKING:
    from textual.message import Message

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
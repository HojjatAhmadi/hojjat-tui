import logging
import time
import traceback
from typing import Any, Dict, List, Optional

from hojjat_tui.function import FunctionResult, _REGISTRY, _LOGGER

logger = logging.getLogger("hojjat_tui")

def execute_function(name: str, args: Optional[Dict[str, Any]] = None, kwargs: Optional[Dict[str, Any]] = None) -> FunctionResult:
    """Execute a registered function by name with the given arguments.
    
    Args:
        name: Name of the registered function.
        args: Positional arguments (optional).
        kwargs: Keyword arguments (optional).
    
    Returns:
        FunctionResult containing the outcome of execution.
    """
    if args is None:
        args = []
    if kwargs is None:
        kwargs = {}
    
    start_time = time.time()
    
    if name not in _REGISTRY:
        result = FunctionResult(
            name=name,
            success=False,
            duration=0.0,
            error=f"Function '{name}' is not registered",
            type="error",
        )
        _log_execution(name, result)
        return result
    
    func = _REGISTRY[name]
    
    try:
        output = func(*args, **kwargs)
        duration = time.time() - start_time
        
        result = FunctionResult(
            name=name,
            success=True,
            duration=duration,
            output=output,
            type=_detect_output_type(output),
        )
        
    except Exception as e:
        duration = time.time() - start_time
        result = FunctionResult(
            name=name,
            success=False,
            duration=duration,
            error=f"{type(e).__name__}: {str(e)}",
            type="error",
            metadata={"traceback": traceback.format_exc()},
        )
        logger.error(f"Function '{name}' failed: {e}")
    
    _log_execution(name, result)
    return result

def _detect_output_type(output: Any) -> str:
    """Detect the type of output for rendering."""
    if isinstance(output, str):
        import re
        if re.search(r'^#|^\* |^- |^1\. ', output.strip()):
            return "markdown"
        return "text"
    elif isinstance(output, dict):
        return "json"
    elif isinstance(output, (list, tuple)):
        return "table"
    elif hasattr(output, '__class__'):
        return output.__class__.__name__.lower()
    return "text"

def _log_execution(name: str, result: FunctionResult):
    """Log execution to the centralized log."""
    from datetime import datetime
    
    log_entry = {
        "timestamp": datetime.now().isoformat(),
        "name": name,
        "success": result.success,
        "duration": result.duration,
        "type": result.type,
        "error": result.error,
    }
    
    if name not in _LOGGER:
        _LOGGER[name] = []
    _LOGGER[name].append(log_entry)
    
    # Keep only last 100 entries per function
    if len(_LOGGER[name]) > 100:
        _LOGGER[name] = _LOGGER[name][-100:]

def get_logs() -> Dict[str, List[Dict[str, Any]]]:
    """Get all execution logs."""
    return {k: list(v) for k, v in _LOGGER.items()}
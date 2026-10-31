"""Built-in sample functions for HOJJAT TUI.

These functions demonstrate the registration API and provide
ready-to-use examples for testing the TUI.
"""

import time
import random
from typing import List, Dict, Any
from datetime import datetime

from hojjat_tui.function import hojjat_function, FunctionResult


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


@hojjat_function(
    name="time_info",
    label="Time Info",
    description="Display current time and date information",
    annotations={},
    defaults={},
    required=[],
)
def time_info() -> Dict[str, Any]:
    """Return current time information."""
    now = datetime.now()
    return {
        "current_time": now.strftime("%Y-%m-%d %H:%M:%S"),
        "timestamp": now.timestamp(),
        "weekday": now.strftime("%A"),
        "iso_format": now.isoformat(),
        "day_of_year": now.timetuple().tm_yday,
        "week_of_year": now.isocalendar()[1],
    }


@hojjat_function(
    name="factorial",
    label="Factorial Calculator",
    description="Calculate the factorial of a given number",
    annotations={
        "n": {"type": "int", "description": "Number to calculate factorial of"},
    },
    required=["n"],
)
def factorial(n: int) -> int:
    """Calculate factorial of n."""
    if n < 0:
        raise ValueError("Factorial is not defined for negative numbers")
    result = 1
    for i in range(2, n + 1):
        result *= i
    return result


@hojjat_function(
    name="random_quote",
    label="Random Quote Generator",
    description="Generate a random inspirational quote",
    annotations={},
    defaults={},
    required=[],
)
def random_quote() -> str:
    """Return a random inspirational quote."""
    quotes = [
        "The only way to do great work is to love what you do. — Steve Jobs",
        "Innovation distinguishes between a leader and a follower. — Steve Jobs",
        "Stay hungry, stay foolish. — Steve Jobs",
        "Your time is limited, don't waste it living someone else's life. — Steve Jobs",
        "The future belongs to those who believe in the beauty of their dreams. — Eleanor Roosevelt",
        "The only impossible journey is the one you don't start. — Tony Robbins",
        "In three words, I can sum up everything I've learned about life: it goes on. — Robert Frost",
    ]
    return random.choice(quotes)


@hojjat_function(
    name="ping_test",
    label="Ping Test",
    description="Simulate a ping test and return timing results as a table",
    annotations={
        "host": {"type": "str", "description": "Host to ping"},
        "count": {"type": "int", "description": "Number of pings to send"},
    },
    defaults={"host": "localhost", "count": 3},
    required=["host"],
)
def ping_test(host: str = "localhost", count: int = 3) -> List[Dict[str, Any]]:
    """Simulate a ping test and return timing data."""
    results = []
    for i in range(count):
        # Simulate network latency
        latency = random.uniform(0.1, 50.0)
        results.append({
            "seq": i + 1,
            "host": host,
            "bytes": 64,
            "time_ms": round(latency, 2),
            "ttl": 64,
        })
        time.sleep(0.05)  # Small delay for realism
    return results


@hojjat_function(
    name="system_info",
    label="System Info",
    description="Return basic system information as structured data",
    annotations={},
    defaults={},
    required=[],
)
def system_info() -> Dict[str, Any]:
    """Return system information."""
    import platform
    import os as os_module
    
    return {
        "platform": platform.platform(),
        "python_version": platform.python_version(),
        "architecture": platform.architecture()[0],
        "processor": platform.processor(),
        "hostname": platform.node(),
        "username": os_module.environ.get("USER") or os_module.environ.get("USERNAME", "unknown"),
        "cpu_count": os_module.cpu_count(),
    }


@hojjat_function(
    name="error_demo",
    label="Error Demonstration",
    description="A function that intentionally raises an error to demonstrate error handling",
    annotations={
        "message": {"type": "str", "description": "Error message to use"},
    },
    defaults={"message": "This is an intentional error for demonstration"},
    required=["message"],
)
def error_demo(message: str = "This is an intentional error") -> str:
    """Function that raises an error to demonstrate error handling."""
    raise RuntimeError(message)


def register_builtins():
    """Register all built-in functions.
    
    This ensures the built-in functions are registered when the module
    is imported.
    """
    import sys
    # The functions are registered by the decorators when this module is imported.
    # We just need to ensure the module is loaded.
    # If already loaded, the functions are already registered.
    current_module = sys.modules[__name__]
    for attr_name in dir(current_module):
        attr = getattr(current_module, attr_name)
        if hasattr(attr, "_hojjat_metadata"):
            metadata = attr._hojjat_metadata
            # Ensure it's in the global registry; if already there, skip
            from hojjat_tui.function import _REGISTRY
            if metadata["name"] not in _REGISTRY:
                _REGISTRY[metadata["name"]] = attr
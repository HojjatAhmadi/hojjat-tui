"""Registration module for HOJJAT TUI.

Provides the register_builtins function for optional use when initializing
the application. Demonstrative functions have been removed from the default
runtime registration; users may register their own functions via the
@hojjat_function decorator.
"""

from typing import Any, Dict, List, Optional


def register_builtins() -> None:
    """Register built-in functions (no-op — demonstration functions removed).

    This function is intentionally a no-op. The seven demonstration functions
    (hello, time_info, factorial, random_quote, ping_test, system_info,
    error_demo) are no longer automatically registered on application startup.
    Users may register their own Python functions using the @hojjat_function
    decorator, or re-add these functions as custom additions.
    """
    pass
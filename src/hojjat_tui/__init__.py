"""HOJJAT TUI — a terminal UI for running registered Python functions."""

from hojjat_tui.function import hojjat_function, FunctionResult, register, get_registry
from hojjat_tui.executor import execute_function

# Chain Engine exports
from hojjat_tui.chain import (
    Chain,
    ChainStep,
    ParameterBinding,
    BindingType,
    ChainExecution,
    StepExecutionResult,
    ChainStatus,
    StepStatus,
    ChainValidationError,
    ChainValidator,
    ChainExecutor,
    create_chain,
    add_step,
    literal,
    user_input,
    output_of,
    validate_chain,
    execute_chain,
    save_chain,
    load_chain,
    list_chains,
    delete_chain,
)

__version__ = "0.2.0"

__all__ = [
    "__version__",
    "hojjat_function",
    "FunctionResult",
    "register",
    "get_registry",
    "execute_function",
    # Chain Engine
    "Chain",
    "ChainStep",
    "ParameterBinding",
    "BindingType",
    "ChainExecution",
    "StepExecutionResult",
    "ChainStatus",
    "StepStatus",
    "ChainValidationError",
    "ChainValidator",
    "ChainExecutor",
    "create_chain",
    "add_step",
    "literal",
    "user_input",
    "output_of",
    "validate_chain",
    "execute_chain",
    "save_chain",
    "load_chain",
    "list_chains",
    "delete_chain",
]

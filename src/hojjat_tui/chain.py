"""Chain Engine — Persistent function chaining framework.

This module implements the Chain Engine for HOJJAT TUI, allowing users to:
- Create chains with unique names, labels, and descriptions
- Add ordered function steps with parameter bindings
- Save and reload chain definitions
- Execute chains sequentially with proper dependency handling
- Validate chain configurations before execution
"""

import copy
import inspect
import json
import logging
import time
import typing as t
from dataclasses import dataclass, field
from enum import Enum
from pathlib import Path
from typing import Any, Dict, List, Optional, Union
from uuid import uuid4

from pydantic import BaseModel, Field, field_validator, model_validator

logger = logging.getLogger("hojjat_tui.chain")

# Import from local modules
import sys
from pathlib import Path as _Path
_src_dir = str(_Path(__file__).parent.parent)
if _src_dir not in sys.path:
    sys.path.insert(0, _src_dir)

from hojjat_tui.function import _REGISTRY, get_registry
from hojjat_tui.executor import execute_function, FunctionResult


class BindingType(str, Enum):
    """Supported parameter binding modes."""
    LITERAL = "literal"
    USER_INPUT = "user_input"
    PREVIOUS_STEP = "previous_step"


class StepStatus(str, Enum):
    """Status of a step during execution."""
    PENDING = "pending"
    RUNNING = "running"
    SUCCESS = "success"
    FAILED = "failed"
    SKIPPED = "skipped"


class ChainStatus(str, Enum):
    """Status of a chain execution."""
    PENDING = "pending"
    RUNNING = "running"
    SUCCESS = "success"
    FAILED = "failed"
    PARTIAL = "partial"


class ParameterBinding(BaseModel):
    """Defines how a parameter receives its value."""
    name: str = Field(..., description="Parameter name on the function")
    binding_type: BindingType = Field(..., description="How the value is sourced")
    value: Optional[Any] = Field(default=None, description="For literal binding type")
    prompt: Optional[str] = Field(default=None, description="For user_input binding type")
    source_step_uuid: Optional[str] = Field(default=None, description="For previous_step binding type")
    source_path: Optional[str] = Field(default=None, description="Dot-separated path into the step output")

    def model_dump_safe(self) -> Dict[str, Any]:
        """Serialize to dict, excluding None values."""
        data = self.model_dump()
        return {k: v for k, v in data.items() if v is not None}


class ChainStep(BaseModel):
    """A single step in a chain."""
    uuid: str = Field(default_factory=lambda: str(uuid4()))
    function_name: str = Field(..., description="Name of the registered function")
    label: Optional[str] = Field(default=None, description="Display label for this step")
    order: int = Field(default=0, description="Execution order")
    params: List[ParameterBinding] = Field(default_factory=list)

    model_config = {"arbitrary_types_allowed": True}


class Chain(BaseModel):
    """A complete chain definition."""
    name: str = Field(..., description="Unique technical name")
    label: str = Field(..., description="Display label")
    description: str = Field(default="", description="Human-readable description")
    steps: List[ChainStep] = Field(default_factory=list, description="Ordered list of steps")

    @field_validator("name")
    @classmethod
    def validate_name(cls, v: str) -> str:
        if not v or not v.strip():
            raise ValueError("Chain name cannot be empty")
        if not v.replace("_", "").replace("-", "").isalnum():
            raise ValueError("Chain name must be alphanumeric with underscores or hyphens")
        return v

    def get_step_by_uuid(self, uuid: str) -> Optional[ChainStep]:
        """Find a step by its UUID."""
        for step in self.steps:
            if step.uuid == uuid:
                return step
        return None

    def get_step_by_name(self, name: str) -> Optional[ChainStep]:
        """Find a step by its function name."""
        for step in self.steps:
            if step.function_name == name:
                return step
        return None


class ChainExecution(BaseModel):
    """Result of a chain execution run."""
    chain_name: str
    started_at: float = Field(default_factory=time.time)
    completed_at: Optional[float] = None
    status: ChainStatus = Field(default=ChainStatus.PENDING)
    step_results: Dict[str, "StepExecutionResult"] = Field(default_factory=dict)

    def to_dict(self) -> Dict[str, Any]:
        """Serialize to dictionary."""
        data = self.model_dump()
        # Convert enums to strings
        if "status" in data:
            data["status"] = str(data["status"])
        return data


class StepExecutionResult(BaseModel):
    """Result of executing a single step."""
    step_uuid: str
    function_name: str
    status: StepStatus = Field(default=StepStatus.PENDING)
    started_at: Optional[float] = None
    completed_at: Optional[float] = None
    duration: Optional[float] = None
    output: Optional[Any] = None
    error: Optional[str] = None
    output_summary: Optional[str] = None

    def to_dict(self) -> Dict[str, Any]:
        """Serialize to dictionary."""
        data = self.model_dump()
        if "status" in data:
            data["status"] = str(data["status"])
        return data


class ChainValidationError(Exception):
    """Raised when a chain configuration is invalid."""

    def __init__(self, errors: List[str]):
        self.errors = errors
        super().__init__("; ".join(errors))


class ChainValidator:
    """Validates chain configurations before execution."""

    @staticmethod
    def validate(chain: Chain) -> List[str]:
        """Validate a chain configuration. Returns list of error messages (empty if valid)."""
        errors = []

        # Check for empty chain
        if not chain.steps:
            errors.append("Chain must have at least one step")
            return errors

        registry = get_registry()
        step_uuids = set()
        step_orders = set()

        for i, step in enumerate(chain.steps):
            # Check for duplicate UUIDs
            if step.uuid in step_uuids:
                errors.append(f"Duplicate step UUID: {step.uuid}")

            step_uuids.add(step.uuid)

            # Check for duplicate orders
            if step.order in step_orders:
                errors.append(f"Duplicate step order: {step.order}")

            step_orders.add(step.order)

            # Check function exists
            if step.function_name not in registry:
                errors.append(f"Step {i+1}: function '{step.function_name}' is not registered")
                continue

            func = registry[step.function_name]
            sig = func.get("signature")

            if sig:
                # Check for unknown parameters
                param_names = set(sig.parameters.keys())
                for binding in step.params:
                    if binding.name not in param_names:
                        errors.append(
                            f"Step '{step.function_name}': parameter '{binding.name}' is not a valid parameter"
                        )

                # Check for missing required parameters
                required = func.get("required", [])
                for req_param in required:
                    if req_param not in [b.name for b in step.params]:
                        # Check if it has a default
                        defaults = func.get("defaults", {})
                        if req_param not in defaults:
                            param_obj = sig.parameters.get(req_param)
                            has_default = param_obj and param_obj.default != inspect.Parameter.empty
                            if not has_default:
                                errors.append(
                                    f"Step '{step.function_name}': required parameter '{req_param}' has no binding"
                                )

            # Check for invalid references
            for binding in step.params:
                if binding.binding_type == BindingType.PREVIOUS_STEP:
                    if binding.source_step_uuid:
                        # Check source step exists and is before current step
                        source_step = chain.get_step_by_uuid(binding.source_step_uuid)
                        if not source_step:
                            errors.append(
                                f"Step '{step.function_name}': binding '{binding.name}' references non-existent step UUID"
                            )
                        else:
                            # Check that source step comes before current step (no forward references)
                            if source_step.order >= step.order:
                                errors.append(
                                    f"Step '{step.function_name}': binding '{binding.name}' references a step that comes "
                                    f"after the current step (forward reference not allowed)"
                                )

                # Check literal values are valid
                if binding.binding_type == BindingType.LITERAL:
                    # We can't fully validate this without type info, but check for obvious issues
                    pass

                # Check user_input has a prompt
                if binding.binding_type == BindingType.USER_INPUT:
                    if not binding.prompt:
                        errors.append(
                            f"Step '{step.function_name}': user_input binding for '{binding.name}' has no prompt"
                        )

        return errors


class ChainExecutor:
    """Executes chains with proper step ordering and result propagation."""

    def __init__(self, chain: Chain, user_inputs: Optional[Dict[str, str]] = None):
        self.chain = chain
        self.user_inputs = user_inputs or {}
        self.step_results: Dict[str, StepExecutionResult] = {}

    def execute(self) -> ChainExecution:
        """Execute the chain and return results."""
        execution = ChainExecution(chain_name=self.chain.name)
        execution.status = ChainStatus.RUNNING
        execution.started_at = time.time()

        # Track which steps can still execute
        failed_step_uuids = set()

        for step in self.chain.steps:
            # Check if any dependency has failed
            can_execute = True
            for binding in step.params:
                if binding.binding_type == BindingType.PREVIOUS_STEP and binding.source_step_uuid:
                    if binding.source_step_uuid in failed_step_uuids:
                        can_execute = False
                        break

            if not can_execute:
                execution.step_results[step.uuid] = StepExecutionResult(
                    step_uuid=step.uuid,
                    function_name=step.function_name,
                    status=StepStatus.SKIPPED,
                    started_at=time.time(),
                    completed_at=time.time(),
                    error="Skipped due to earlier step failure",
                )
                failed_step_uuids.add(step.uuid)
                continue

            # Execute the step
            result = self._execute_step(step, execution)
            execution.step_results[step.uuid] = result

            if result.status == StepStatus.FAILED:
                failed_step_uuids.add(step.uuid)

        # Determine overall status
        if failed_step_uuids:
            if len(execution.step_results) == len(failed_step_uuids):
                execution.status = ChainStatus.FAILED
            else:
                execution.status = ChainStatus.PARTIAL
        else:
            execution.status = ChainStatus.SUCCESS

        execution.completed_at = time.time()
        return execution

    def _execute_step(self, step: ChainStep, execution: ChainExecution) -> StepExecutionResult:
        """Execute a single step."""
        result = StepExecutionResult(
            step_uuid=step.uuid,
            function_name=step.function_name,
            status=StepStatus.RUNNING,
            started_at=time.time()
        )

        try:
            # Resolve parameters
            kwargs = {}
            for binding in step.params:
                kwargs[binding.name] = self._resolve_binding(binding, execution)

            # Execute function
            func_result = execute_function(step.function_name, kwargs=kwargs)

            result.status = StepStatus.SUCCESS if func_result.success else StepStatus.FAILED
            result.output = func_result.output
            result.error = func_result.error
            result.duration = func_result.duration

            # Create output summary for persistence
            if func_result.success:
                if isinstance(func_result.output, (dict, list)):
                    result.output_summary = json.dumps(func_result.output, default=str)[:500]
                else:
                    result.output_summary = str(func_result.output)[:500]
            else:
                result.output_summary = None

        except Exception as e:
            logger.exception(f"Step execution failed: {step.function_name}")
            result.status = StepStatus.FAILED
            result.error = str(e)

        result.completed_at = time.time()
        return result

    def _resolve_binding(self, binding: ParameterBinding, execution: ChainExecution) -> Any:
        """Resolve a binding to its value."""
        if binding.binding_type == BindingType.LITERAL:
            return binding.value

        elif binding.binding_type == BindingType.USER_INPUT:
            # Check if we have a pre-supplied value
            key = f"{execution.chain_name}:{binding.name}"
            if key in self.user_inputs:
                return self.user_inputs[key]
            # Use generic key
            if binding.name in self.user_inputs:
                return self.user_inputs[binding.name]
            # Use prompt if available
            if binding.prompt:
                return self.user_inputs.get(binding.prompt, self.user_inputs.get(binding.name))
            return None

        elif binding.binding_type == BindingType.PREVIOUS_STEP:
            step_result = execution.step_results.get(binding.source_step_uuid)
            if step_result and step_result.output is not None:
                output = step_result.output
                # Apply path resolution
                if binding.source_path:
                    output = self._resolve_path(output, binding.source_path)
                return output
            return None

        return None

    @staticmethod
    def _resolve_path(obj: Any, path: str) -> Any:
        """Resolve a dot-separated path into a nested structure."""
        parts = path.split(".")
        for part in parts:
            if obj is None:
                return None
            if isinstance(obj, dict):
                obj = obj.get(part)
            elif isinstance(obj, (list, tuple)):
                try:
                    idx = int(part)
                    obj = obj[idx] if 0 <= idx < len(obj) else None
                except (ValueError, IndexError):
                    return None
            else:
                obj = getattr(obj, part, None)
        return obj


# Module-level convenience functions

def create_chain(name: str, label: str, description: str = "", steps: Optional[List[ChainStep]] = None) -> Chain:
    """Create a new chain definition."""
    return Chain(name=name, label=label, description=description, steps=steps or [])


def add_step(chain: Chain, function_name: str, label: Optional[str] = None,
             params: Optional[List[ParameterBinding]] = None) -> ChainStep:
    """Add a step to a chain and return the new step."""
    step = ChainStep(
        function_name=function_name,
        label=label,
        order=len(chain.steps),
        params=params or []
    )
    chain.steps.append(step)
    return step


def literal(name: str, value: Any) -> ParameterBinding:
    """Create a literal binding for a parameter."""
    return ParameterBinding(
        name=name,
        binding_type=BindingType.LITERAL,
        value=value
    )


def user_input(name: str, prompt: str) -> ParameterBinding:
    """Create a user input binding for a parameter."""
    return ParameterBinding(
        name=name,
        binding_type=BindingType.USER_INPUT,
        prompt=prompt
    )


def output_of(name: str, source_step_uuid: str, path: str = "") -> ParameterBinding:
    """Create a binding that takes output from a previous step.

    Args:
        name: Parameter name to bind
        source_step_uuid: UUID of the source step
        path: Dot-separated path to extract from output (e.g., "data.items.0.name")
    """
    return ParameterBinding(
        name=name,
        binding_type=BindingType.PREVIOUS_STEP,
        source_step_uuid=source_step_uuid,
        source_path=path if path else None
    )


def validate_chain(chain: Chain) -> List[str]:
    """Validate a chain configuration. Returns list of errors (empty if valid)."""
    return ChainValidator.validate(chain)


def execute_chain(chain: Chain, user_inputs: Optional[Dict[str, str]] = None) -> ChainExecution:
    """Execute a chain and return the execution results."""
    return ChainExecutor(chain, user_inputs).execute()


def save_chain(chain: Chain) -> int:
    """Save a chain to the database."""
    steps_data = []
    for step in chain.steps:
        steps_data.append({
            "order": step.order,
            "uuid": step.uuid,
            "function_name": step.function_name,
            "label": step.label,
            "params": [p.model_dump_safe() for p in step.params],
        })

    return Database().save_chain({
        "name": chain.name,
        "label": chain.label,
        "description": chain.description,
        "steps": steps_data,
    })


def load_chain(name: str) -> Optional[Chain]:
    """Load a chain from the database."""
    db = Database()
    data = db.load_chain(name)
    if data is None:
        return None

    chain = Chain(
        name=data["name"],
        label=data["label"],
        description=data.get("description", ""),
    )

    for step_data in data["steps"]:
        step = ChainStep(
            uuid=step_data["uuid"],
            function_name=step_data["function_name"],
            label=step_data.get("label"),
            order=step_data["order"],
        )
        for param_data in step_data["params"]:
            raw_value = param_data.get("value")
            if raw_value is not None:
                try:
                    raw_value = json.loads(raw_value)
                except (json.JSONDecodeError, TypeError):
                    pass
            binding = ParameterBinding(
                name=param_data["name"],
                binding_type=BindingType(param_data["binding_type"]),
                value=raw_value,
                prompt=param_data.get("prompt"),
                source_step_uuid=param_data.get("source_step_uuid"),
                source_path=param_data.get("source_path"),
            )
            step.params.append(binding)
        chain.steps.append(step)

    return chain


def list_chains() -> List[Dict[str, Any]]:
    """List all stored chains."""
    return Database().list_chains()


def delete_chain(name: str) -> bool:
    """Delete a chain by name."""
    return Database().delete_chain(name)


# Need Database import after we define module-level functions
from hojjat_tui.persistence import Database
# Chains

## Chain Overview

Chains allow you to link multiple functions together in a specified execution order. Each step in a chain can execute a registered function, with parameters sourced from literal values, user input, or output from previous steps.

Chains are persisted in the SQLite database and can be created, saved, loaded, and executed through the TUI or CLI.

## Chain Data Model

### `Chain` Model

```python
from hojjat_tui.chain import Chain

chain = Chain(
    name="my_chain",
    label="My Chain",
    description="A chain that does something useful",
    steps=[
        ChainStep(function_name="hello", params=[literal("name", "Alice")]),
    ],
)
```

**Fields:**
- `name` (str): Unique technical name for the chain
- `label` (str): Display label
- `description` (str): Human-readable description
- `steps` (list[ChainStep]): Ordered list of chain steps

### `ChainStep` Model

```python
from hojjat_tui.chain import ChainStep, literal, output_of

step = ChainStep(
    function_name="hello",
    params=[literal("name", "Alice")],
)
```

**Fields:**
- `uuid` (str): Unique step identifier (auto-generated)
- `function_name` (str): Name of the registered function to execute
- `label` (str, optional): Display label for this step
- `order` (int): Execution order (0 = first, 1 = second, etc.)
- `params` (list[ParameterBinding]): Parameter bindings for this step

### `ParameterBinding` Model

```python
from hojjat_tui.chain import ParameterBinding, literal, user_input, output_of
from hojjat_tui.chain import BindingType

# Literal binding — use a fixed value
bind = literal("name", "Alice")

# User input binding — prompt the user at runtime
bind = user_input("name", "Enter your name")

# Previous step binding — use output from an earlier step
bind = output_of("result", "step-uuid-1", "data.key")
```

### `BindingType` Enum

| Member | Description |
|--------|-------------|
| `LITERAL` | Use a fixed value directly |
| `USER_INPUT` | Prompt the user for a value at runtime |
| `PREVIOUS_STEP` | Use output from a previous step in the chain |

### `ParameterBinding` Fields

| Field | Type | Description |
|-------|------|-------------|
| `name` (str) | Parameter name on the function |
| `binding_type` (BindingType) | How the value is sourced |
| `value` (Any, optional) | For LITERAL binding type |
| `prompt` (str, optional) | For USER_INPUT binding type |
| `source_step_uuid` (str, optional) | For PREVIOUS_STEP binding type |
| `source_path` (str, optional) | Dot-separated path into step output |

## Chain Validation

### `validate_chain(chain)`

Validates a chain configuration before execution. Returns a list of error messages (empty if valid).

### Validation Checks

1. **Non-empty chain**: Must have at least one step
2. **Function exists**: Each step's function must be registered in the global registry
3. **Valid parameters**: Each parameter binding must reference a valid function parameter
4. **Required parameters**: All required function parameters must have a binding or default value
5. **No duplicate UUIDs**: Step UUIDs must be unique within a chain
6. **No duplicate step orders**: Step orders must be unique within a chain
7. **No forward references**: A PREVIOUS_STEP binding cannot reference a step that comes after the current step in execution order
8. **USER_INPUT requires prompt**: User input bindings must have a prompt string
9. **Literal values**: No additional validation beyond type checking

### Example: Valid Chain

```python
from hojjat_tui.chain import create_chain, add_step, literal
from hojjat_tui.chain import validate_chain

chain = create_chain("greet", "Greeting Chain", "A chain that greets a user")
add_step(chain, "hello", params=[literal("name", "Alice")])

errors = validate_chain(chain)
print(errors)  # []
```

### Example: Invalid Chain (missing required parameter)

```python
from hojjat_tui.chain import Chain, ChainStep

chain = Chain(
    name="bad-chain",
    label="Bad Chain",
    steps=[
        ChainStep(function_name="factorial", params=[]),  # Missing required 'n' parameter
    ],
)

errors = validate_chain(chain)
# ["Step factorial: required parameter 'n' has no binding"]
```

## Chain Execution

### `execute_chain(chain, user_inputs=None)`

Executes a chain and returns the execution results.

```python
from hojjat_tui.chain import create_chain, add_step, literal
from hojjat_tui.chain import execute_chain

chain = create_chain("demo", "Demo Chain", "A demonstration chain")
add_step(chain, "hello", params=[literal("name", "Alice")])
add_step(chain, "time_info")

execution = execute_chain(chain)
```

**Return Value**: `ChainExecution` object with:
- `chain_name` (str): Name of the chain
- `started_at` (float): Execution start timestamp
- `completed_at` (float, optional): Execution completion timestamp
- `status` (ChainStatus): Overall execution status (PENDING, RUNNING, SUCCESS, FAILED, PARTIAL)
- `step_results` (dict[str, StepExecutionResult]): Per-step results

### `ChainStatus` Enum

| Member | Description |
|--------|-------------|
| `PENDING` | Chain has not been started |
| `RUNNING` | Chain is currently executing |
| `SUCCESS` | All steps completed successfully |
| `FAILED` | All steps failed |
| `PARTIAL` | Some steps succeeded, some failed |

### `StepExecutionResult`

Per-step result with:
- `step_uuid` (str): Step identifier
- `function_name` (str): Function that was executed
- `status` (StepStatus): Step status (PENDING, RUNNING, SUCCESS, FAILED, SKIPPED)
- `started_at` (float, optional): Step start timestamp
- `completed_at` (float, optional): Step completion timestamp
- `duration` (float, optional): Step execution duration
- `output` (Any, optional): Step output value
- `error` (str, optional): Error message if step failed
- `output_summary` (str, optional): Brief summary of output for persistence

## Parameter Binding Types

### LITERAL

Use a fixed value directly. The value is embedded in the chain definition and does not change at runtime.

```python
from hojjat_tui.chain import literal

# Bind the parameter 'name' to the literal value 'Alice'
bind = literal("name", "Alice")
```

**Use case**: Parameters that never change, such as configuration values, fixed identifiers, or test data.

### USER_INPUT

Prompt the user for a value at runtime. The prompt is displayed to the user, who enters a value.

```python
from hojjat_tui.chain import user_input

# Prompt the user for their name
bind = user_input("name", "Enter your name:")
```

**Use case**: Parameters that vary per execution, such as user names, search terms, or interactive choices.

### PREVIOUS_STEP

Use the output from a previous step in the chain as the parameter value. This enables data to flow between steps.

```python
from hojjat_tui.chain import output_of

# Bind a parameter to the output of step with UUID 'step-1', extracting the 'data' key
bind = output_of("result", "step-1", "data")
```

**Use case**: Chains where the output of one function becomes the input of the next, such as:
1. Step 1: Fetch data from API → output saved as `data`
2. Step 2: Transform data → input parameter binds to `data` from step 1
3. Step 3: Display results → input parameter binds to transformed data from step 2

**Source path**: Use `source_path` to extract a nested path from the output, e.g., `output_of("item", "step-1", "data.items.0.name")` to get the `name` field from the first item in `data.items`.

## Creating Chains

### Via Python API

```python
from hojjat_tui.chain import create_chain, add_step, literal, save_chain

# Create a new chain
chain = create_chain(
    name="user-greeting",
    label="User Greeting Chain",
    description="A chain that greets a user by name",
)

# Add steps with parameter bindings
add_step(chain, "hello", params=[literal("name", "Alice")])

# Save the chain to the database
chain_id = save_chain(chain)
print(f"Chain saved with ID: {chain_id}")
```

### Via TUI

1. Navigate to the **Chains** menu
2. Select **New Chain** to open the chain builder
3. Enter a chain name, display label, and optional description
4. Select functions from the registry to add as steps
5. For each step, configure parameter bindings:
   - **Literal**: Use a fixed value
   - **User Input**: Prompt the user for a value
   - **Previous Step**: Use output from an earlier step
6. Save the chain with a unique name
7. The chain is immediately available for execution

### Via CLI

```bash
# Chain creation is primarily via TUI or Python API
# Chains saved to the database are available via the TUI
```

## Loading and Listing Chains

### `load_chain(name)`

Load a chain definition from the database by name.

```python
from hojjat_tui.chain import load_chain

chain = load_chain("user-greeting")
if chain is not None:
    print(f"Loaded chain: {chain.name}")
    print(f"Steps: {len(chain.steps)}")
```

### `list_chains()`

List all saved chains from the database.

```python
from hojjat_tui.chain import list_chains

chains = list_chains()
for chain in chains:
    print(f"- {chain['name']}: {chain['label']}")
```

### `delete_chain(name)`

Delete a chain from the database.

```python
from hojjat_tui.chain import delete_chain

result = delete_chain("user-greeting")
print(f"Chain deleted: {result}")  # True if deleted, False if not found
```

## Chain Execution Example

### Complete Chain Workflow

```python
from hojjat_tui import builtin_functions
from hojjat_tui.chain import (
    create_chain, add_step, literal, output_of,
    save_chain, execute_chain, validate_chain
)
from hojjat_tui.function import get_registry

# Ensure built-in functions are registered
builtin_functions.register_builtins()

# Create a chain that greets a user, then shows the time
chain = create_chain(
    name="greet-and-time",
    label="Greet and Time",
    description="A chain that greets a user and then shows the current time",
)

# Add first step: say hello
add_step(chain, "hello", params=[literal("name", "Alice")])

# Add second step: show time
add_step(chain, "time_info")

# Validate the chain
errors = validate_chain(chain)
if errors:
    print(f"Validation errors: {errors}")
else:
    print("Chain is valid")

# Save the chain
save_chain(chain)
print("Chain saved")

# Execute the chain
execution = execute_chain(chain)

# View results
print(f"Chain status: {execution.status}")
for step_uuid, step_result in execution.step_results.items():
    print(f"Step {step_uuid}: {step_result.status}")
    if step_result.success and step_result.output is not None:
        print(f"  Output: {step_result.output}")
```

### Execution Output

- **Step 1 (hello)**: Outputs `"Hello, Alice!"` (text)
- **Step 2 (time_info)**: Outputs a dict with current time information
- **Overall status**: `ChainStatus.SUCCESS` (if all steps succeed)

### Forward Reference Prevention

Chains prevent forward references — a step cannot reference output from a step that comes after it in the execution order. The validator checks that `source_step.order < current_step.order` for all PREVIOUS_STEP bindings.

## Persistence

### Saving Chains

Chains are persisted in the SQLite database using the `save_chain()` function. The chain definition (name, label, description, steps with parameter bindings) is stored in the `chains` and `chain_steps` tables.

### Loading Chains

Chains are loaded from the database using `load_chain()`. The chain definition is reconstructed from the `chains` and `chain_steps` tables, including all parameter bindings.

### Chain Execution History

Each chain execution is logged in the `chain_executions` and `step_executions` tables. This history includes:
- Chain name and execution timestamp
- Per-step status, output, and errors
- Overall execution success/failure

### Managing Chains

- **Create**: Use TUI chain builder or Python API `save_chain()`
- **List**: Use `list_chains()` or TUI chains menu
- **Load**: Use `load_chain()` or TUI chains menu
- **Delete**: Use `delete_chain()` or TUI chain reset options
- **Reset Database**: Use `python manage.py reset-db` or TUI settings

## Practical Chain Examples

### Example 1: Simple Two-Step Chain

```python
from hojjat_tui.chain import create_chain, add_step, literal

chain = create_chain(
    name="double-hello",
    label="Double Greeting",
    description="Greets the same user twice with different parameters",
)

add_step(chain, "hello", params=[literal("name", "Alice")])
add_step(chain, "hello", params=[literal("name", "Bob")], label="Say hi to Bob")
```

### Example 2: Chain with Output Reference

```python
from hojjat_tui.chain import create_chain, add_step, literal, output_of

chain = create_chain(
    name="process-and-greet",
    label="Process and Greet",
    description="Processes data and then greets the result",
)

# Step 1: factorial
add_step(chain, "factorial", params=[literal("n", 5)])

# Step 2: hello, using output from step 1
add_step(chain, "hello", params=[
    output_of("name", "step-1", "output")
])
```

In this example, step 2 would receive the output from the factorial step, but since `hello` expects a `name` parameter and factorial outputs an integer, the binding would need to be adjusted. A more realistic example:

```python
add_step(chain, "factorial", params=[literal("n", 5)])

# Step 2 uses output from step 1 as a string parameter
add_step(chain, "hello", params=[
    output_of("name", "step-1", "")
])
```

### Example 3: Chain with Mixed Binding Types

```python
from hojjat_tui.chain import create_chain, add_step, literal, user_input, output_of

chain = create_chain(
    name="mixed-bindings",
    label="Mixed Bindings",
    description="A chain demonstrating mixed parameter binding types",
)

# Step 1: factorial with literal parameter
add_step(chain, "factorial", params=[literal("n", 5)])

# Step 2: hello with user input and output reference
add_step(chain, "hello", params=[
    user_input("name", "Enter a name:"),
    output_of("extra", "step-1", "data"),
])
```

### Example 4: Chain with All Binding Types

```python
from hojjat_tui.chain import create_chain, add_step, literal, user_input, output_of
from hojjat_tui.chain import BindingType

chain = create_chain(
    name="all-bindings",
    label="All Binding Types",
    description="A chain demonstrating all binding types",
)

# Step 1: Uses all three binding types
add_step(chain, "custom_function", params=[
    literal("fixed_param", "fixed_value"),           # LITERAL
    user_input("user_param", "Enter a value:"),       # USER_INPUT
    output_of("prev_param", "step-0", "output"),      # PREVIOUS_STEP
])
```

## Troubleshooting

### Common Chain Errors

1. **"Function 'X' is not registered"** — The function name doesn't match a registered function. Check the registry with `get_registry()`.

2. **"Required parameter 'Y' has no binding"** — A required function parameter doesn't have a binding and no default value. Add a binding or provide a default.

3. **"Duplicate step UUID"** — Two steps in the chain have the same UUID. Generate new UUIDs or let the system auto-generate them.

4. **"Forward reference not allowed"** — A PREVIOUS_STEP binding references a step that comes after the current step in execution order. Reorder the steps.

5. **"USER_input binding has no prompt"** — A USER_INPUT binding is missing the prompt string. Add a prompt to the binding.

6. **Chain execution appears to hang** — Check for circular dependencies or steps that take a very long time to execute.

### Debugging Tips

- Use `validate_chain(chain)` before executing to catch configuration errors
- Use `get_registry()` to verify function names are registered correctly
- Use `list_chains()` to verify chains are saved correctly
- Check the SQLite database directly if chains are not persisting as expected
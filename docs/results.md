# Results

## Result Presentation

After executing a function or chain, HOJJAT TUI presents the results using the Rich library. The presentation format depends on the detected output type and the user's preferences.

### Output Types

| Type | Description | Rendering |
|------|-------------|-----------|
| **text** | Plain text output | Displayed as-is |
| **markdown** | Markdown content | Rendered with Rich Markdown |
| **json** | Dict or JSON-compatible objects | Formatted with indentation |
| **table** | List of dicts or list of lists | Rendered as a Rich Table |
| **error** | Error messages | Red panel with error title |
| **info** | Informational messages | Blue panel with info title |
| **chart** | Numeric data (Phase 2) | Horizontal bar chart (text-based) |

### Result Screen

When a function or chain execution completes, the TUI displays a **Result Screen** with the following features:

- **Full output**: The complete result string/representation
- **Table view**: Press **Table** to view as a structured table (if output type supports it)
- **Chart view**: Press **Chart** to view as a text-based bar chart (if output type supports it)
- **Raw view**: Default view showing the full output
- **Explanation**: Disabled mode messages when table/chart is not supported
- **Back**: Press Esc or **Back** to return to the previous screen

### Navigating Results

1. After a function executes, the Result Screen appears automatically
2. The default view is **Raw** (full output text)
3. Press **Table** to switch to table view (if supported)
4. Press **Chart** to switch to chart view (if supported)
5. Press **Back** or **Esc** to return to the main menu

## Table Rendering

### When Table View is Available

The TUI renders output as a table when the result is a `list` of supported structures:

- **List of dicts**: Each dict becomes a row; keys become column headers
- **List of lists/tuples**: Each inner list/tuple becomes a row

### Table Automatic Detection

The `_can_render_table()` method in `ResultScreen` checks:

```python
def _can_render_table(self) -> bool:
    data = self._raw_output
    if not isinstance(data, list) or len(data) == 0:
        return False
    supported = (list, tuple, dict)
    return all(isinstance(row, supported) for row in data)
```

### Practical Table Example

```python
@hojjat_function(
    name="get_users",
    label="Get Users",
    description="Return a list of user records",
)
def get_users() -> list:
    return [
        ["Name", "Age"],          # Header row
        ["Alice", 28],           # Row 2
        ["Bob", 34],             # Row 3
        ["Charlie", 22],         # Row 4
    ]
]
```

When executed, the TUI automatically detects this as a table and renders it with column headers "Name" and "Age".

### Manual Table Format

Functions can also return a list of dicts:

```python
@hojjat_function(
    name="get_user_records",
    label="User Records",
    description="Return user records as dict list",
)
def get_user_records() -> list:
    return [
        {"Name": "Alice", "Age": 28},
        {"Name": "Bob", "Age": 34},
        {"Name": "Charlie", "Age": 22},
    ]
]
```

This produces the same table rendering with "Name" and "Age" columns.

### Table Column Customization

When the output is a list of dicts, the table columns are automatically determined from the first dict's keys. All subsequent dicts must have compatible keys (missing keys are displayed as empty cells).

## Chart Rendering

### When Chart View is Available

The TUI renders output as a chart when the result contains enough numeric data. The chart is a simple text-based horizontal bar chart.

### `_can_render_chart()` Detection

The `_can_render_chart()` method extracts numeric values from the output:

```python
def _can_render_chart(self) -> bool:
    data = self._raw_output
    numeric_values = self._extract_numeric_values(data)
    return len(numeric_values) >= 2
```

The `_extract_numeric_values()` method flattens the data, collecting every int/float value found. It supports:
- Scalar numbers
- Flat lists of numbers
- Lists of tuples/lists whose elements are numeric

### Practical Chart Example

```python
@hojjat_function(
    name="get_monthly_sales",
    label="Monthly Sales",
    description="Return monthly sales figures as a list",
)
def get_monthly_sales() -> list:
    return [120, 180, 150, 220, 300]
```

When executed, the TUI displays a text-based horizontal bar chart:

```
    0   [###############################] 120
    1   [#################################] 180
    2   [#######################         ] 150
    3   [############################### ] 220
    4   [#################################] 300
```

### Chart Rendering Details

The `_render_chart()` method:
1. Extracts all numeric values from the output
2. Finds the maximum value (minimum is 1.0 if all values are 0 or negative)
3. Calculates bar width proportion: `(value / max_val) * 40`
4. Displays each value with its corresponding bar
5. Format: `index: [bar] value`

The bar uses `#` for filled portion and `.` for unfilled portion, with a fixed width of 40 characters.

### Chart Output Format

```
    0   [###############################] 120
    1   [#################################] 180
```

Each line shows:
- The index (right-aligned, 4 characters)
- A horizontal bar (# for filled, . for unfilled)
- The numeric value

### When Chart is Not Supported

If the output doesn't contain enough numeric data (< 2 numeric values), the chart button is disabled and an explanation is displayed:

> "Chart view is not supported for this output — not enough numeric data"

## Error and Info Panels

### Error Panel

When a function execution fails, the result is displayed in a red panel:

```
┌─────────────────────────────────────────────────────────────┐
│ Error: This is an intentional error for demonstration       │
├─────────────────────────────────────────────────────────────┤
│ (Traceback may be included in details)                      │
└─────────────────────────────────────────────────────────────┘
```

### Info Panel

For informational messages, a blue panel is displayed:

```
┌─────────────────────────────────────────────────────────────┐
│ Info: Operation completed successfully                      │
├─────────────────────────────────────────────────────────────┤
│ Details about the successful operation                      │
└─────────────────────────────────────────────────────────────┘
```

## Execution History

### Function Execution Logs

Function executions are logged in the SQLite database. The logs include:
- Function name
- Success/failure status
- Execution duration
- Output type
- Error message (if failed)
- Timestamp

### Chain Execution History

Chain executions are logged with:
- Chain name
- Start and completion timestamps
- Overall status (SUCCESS, FAILED, PARTIAL)
- Per-step results (status, output, error)

### Viewing History

- **TUI**: Navigate to the **Results** menu and select an execution from history
- **CLI**: Use `python manage.py check` to see registered functions, or query the database directly
- **Database**: The `function_logs`, `chain_executions`, and `step_executions` tables store execution history

### Clearing History

- **TUI**: Settings → "Clear Execution History"
- **CLI**: Direct database manipulation or reinitialization
- **Management**: `python manage.py init` (safe to rerun, preserves data) or `python manage.py reset-db` (clears all data)
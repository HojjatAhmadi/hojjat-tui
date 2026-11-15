# Results

## Result Presentation

After executing a function or chain, HOJJAT TUI presents the results using the Rich library. The presentation format depends on the detected output type.

### Output Types

| Type | Description | Rendering |
|------|-------------|-----------|
| **text** | Plain text output | Displayed as-is |
| **markdown** | Markdown content | Rendered with Rich Markdown |
| **json** | Dict or JSON-compatible objects | Formatted with indentation |
| **table** | List of dicts or list of lists | Rendered as a Rich Table |
| **chart** | ChartOutput (bar or line chart rendered as ASCII art) | ASCII bar/line chart |
| **error** | Error messages | Red panel with error title |
| **info** | Informational messages | Blue panel with info title |

### Result Screen

When a function or chain execution completes, the TUI displays a **Result Screen** with the following features:

- **Full output**: The complete result string/representation
- **Table view**: Press **Table** to view as a structured table (if output type supports it)
- **Chart view**: Press **Chart** to view as a text-based bar chart (if output type supports it)
- **Raw view**: Default view showing the full output
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

### Practical Table Example

```python
@hojjat_function(
    name="get_users",
    label="Get Users",
    description="Return a list of user records",
)
def get_users() -> list:
    return [
        ["Name", "Age"],
        ["Alice", 28],
        ["Bob", 34],
        ["Charlie", 22],
    ]
```

When executed, the TUI automatically detects this as a table and renders it with column headers "Name" and "Age", displaying all four user records.

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
```

This produces the same table rendering with "Name" and "Age" columns.

### Table Column Customization

When the output is a list of dicts, the table columns are automatically determined from the first dict's keys. All subsequent dicts must have compatible keys (missing keys are displayed as empty cells).

## Chart Rendering

### When Chart View is Available

The TUI renders output as a chart when the result is a `ChartOutput` instance with `chart_type="bar"` or `chart_type="line"`.

### Chart API

```python
from hojjat_tui.function import hojjat_function, ChartOutput

@hojjat_function(
    name="get_monthly_sales",
    label="Monthly Sales",
    description="Return monthly sales figures as a bar chart.",
)
def get_monthly_sales() -> ChartOutput:
    return ChartOutput(
        chart_type="bar",
        labels=["Jan", "Feb", "Mar", "Apr", "May", "Jun"],
        values=[120, 180, 150, 220, 300, 280],
        title="Monthly Sales",
    )
```

When executed, the TUI automatically detects the `ChartOutput` and renders an ASCII bar chart:

```
    Title: Monthly Sales
    Data points: 6

          Jan   Feb   Mar   Apr   May   Jun
          ------- ------- ------- ------- ------- -------
  100%  |  ██████  ██████  ██████  ██████  ██████  ██████
   80%  |                                   ██████  ██████
   60%  |              ██████         ██████
   40%  |              ██████         ██████
   20%  |              ██████         ██████
    0%  |              120    180    150    220    300    280
```

For a line chart, use `chart_type="line"`:

```python
@hojjat_function(
    name="temperature_trend",
    label="Temperature Trend",
    description="Return daily temperatures as a line chart.",
)
def temperature_trend() -> ChartOutput:
    return ChartOutput(
        chart_type="line",
        labels=["Mon", "Tue", "Wed", "Thu", "Fri", "Sat", "Sun"],
        values=[68, 72, 75, 73, 78, 81, 76],
        title="Weekly Temperature",
    )
```

**Chart API**: `ChartOutput(chart_type="bar"|"line", labels=[...], values=[...], title="...")`

- `chart_type`: Either `"bar"` or `"line"`
- `labels`: Category labels for the x-axis (strings)
- `values`: Numeric values for each label (floats or ints)
- `title`: Optional chart title

Charts require at least one label/value pair, and labels and values must have the same length.

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
- **Database**: The `function_logs`, `chain_executions`, and `step_executions` tables store execution history

### Clearing History

Database data can be cleared through database management or by reinitializing.

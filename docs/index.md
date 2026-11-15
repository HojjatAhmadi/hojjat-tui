# HOJJAT TUI — Documentation

# HOJJAT TUI

**HOJJAT TUI** is a terminal-based user interface (TUI) tool built with Python and [Textual](https://textual.textualize.io/). It provides a registry of user-contributed functions that can run inside the terminal, render structured results, and chain together in sequential workflows.

Register your Python functions with the `@hojjat_function()` decorator, then launch `hojjat-tui` to browse, configure, and execute them from a clean terminal interface.

## Phase Status

All Phase 1 features are complete:

| Phase | Feature | Status |
|-------|---------|--------|
| 1 | Packaging and installation | ✅ Complete |
| 1 | Function registry and execution | ✅ Complete |
| 1 | TUI interface with Textual | ✅ Complete |
| 1 | Management commands and persistence | ✅ Complete |
| 1 | Chain Engine (function chaining) | ✅ Complete |
| 1 | Tests and documentation | ✅ Complete |

## Getting Started

### Installation

See the [Installation Guide](installation.md) for detailed instructions.

### Quick Start

```bash
# Initialize a HOJJAT TUI project (creates manage.py and functions/example.py)
hojjat-tui init

# Launch the TUI
hojjat-tui

# Run a function from CLI
hojjat-tui run <function_name> --param KEY=VALUE
```

### Core Concepts

- **Functions**: Register Python functions with the `@hojjat_function` decorator. Each function can have parameters, defaults, and required markers.
- **Chains**: Link multiple functions together in a specified order. Chains are persisted in the SQLite database.
- **Output Types**: Results are rendered as text, Markdown, tables, JSON, charts, error, or info panels.
- **Parameter Bindings**: Control how parameters receive their values — literal, user input, or output from previous steps.
- **Hot Reload**: Press **R** or **Ctrl+R** (or click **Refresh**) to reload function modules without restarting the TUI.

## Documentation Structure

- [Installation Guide](installation.md) — Setup and development environment
- [Architecture](architecture.md) — System design and component overview
- [Functions](functions.md) — Function registration API
- [Chains](chains.md) — Chain creation, execution, and parameter binding
- [Results](results.md) — Result presentation and rendering details
- [Database](database.md) — SQLite schema and persistence behavior
- [Development](development.md) — Contribution guidelines and development setup

## Project Status

**Current version**: 2.0.1

HOJJAT TUI is a mature Phase 1 tool. All core features — packaging, function registry, TUI interface, management commands, persistence, chain engine, and hot reload — are implemented and tested.

---

## Quick Nav

- [Installation Guide](installation.md)
- [Architecture](architecture.md)
- [Functions API](functions.md)
- [Chains](chains.md)
- [Results](results.md)
- [Database](database.md)
- [Development](development.md)

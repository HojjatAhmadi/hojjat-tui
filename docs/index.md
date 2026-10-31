# HOJJAT TUI — Documentation

![HOJJAT TUI Logo](https://raw.githubusercontent.com/placeholder/hojjat-tui/main/docs/logo.png HOJJAT TUI)

**HOJJAT TUI** is a terminal-based user interface (TUI) tool built with Python and [Textual](https://textual.textualize.io/). It provides a registry of user-contributed functions that can run inside the terminal, render structured results, and chain together in future phases.

## Phase 1 — Packaging, Installation, Function Registry, TUI, Management Commands

| Phase | Feature | Status |
|-------|---------|--------|
| 1 | Packaging and installation | ✅ Complete |
| 1 | Function registry and execution | ✅ Complete |
| 1 | TUI interface with Textual | ✅ Complete |
| 1 | Management commands and persistence | ✅ Complete |
| 1 | Tests and documentation | ✅ Complete |
| 2 | Chain Engine (linking functions together) | ⏳ Pending |

## Getting Started

### Installation

See the [Installation Guide](installation.md) for detailed instructions.

### Quick Start

```bash
# Initialize the database
python manage.py init

# Create an admin user
python manage.py createsuperuser

# Launch the TUI
hojjat-tui
```

### Core Concepts

- **Functions**: Register Python functions with the `@hojjat_function` decorator. Each function can have parameters, defaults, and required markers.
- **Chains**: Link multiple functions together in a specified order. Chains are persisted in the SQLite database.
- **Output Types**: Results are rendered as text, Markdown, tables, JSON, error, or info panels.
- **Parameter Bindings**: Control how parameters receive their values — literal, user input, or output from previous steps.

## Documentation Structure

- [Installation Guide](installation.md) — Setup and development environment
- [Architecture](architecture.md) — System design and component overview
- [Functions](functions.md) — Function registration API and built-in functions
- [Chains](chains.md) — Chain creation, execution, and parameter binding
- [Results](results.md) — Result presentation and rendering details
- [Database](database.md) — SQLite schema and persistence behavior
- [Development](development.md) — Contribution guidelines and development setup

## Project Status

**Current version**: 0.3.0

HOJJAT TUI is in active Phase 1 development. All core features — packaging, function registry, TUI interface, management commands, and persistence — are implemented and tested. The Chain Engine (Phase 2) is pending and will add the ability to link functions together into executable workflows.

---

## Quick Nav

- [Installation Guide](installation.md)
- [Architecture](architecture.md)
- [Functions API](functions.md)
- [Chains](chains.md)
- [Results](results.md)
- [Database](database.md)
- [Development](development.md)
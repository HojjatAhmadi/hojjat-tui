# Installation Guide

## Prerequisites

- Python 3.9 or later
- pip (Python package manager)

## Installing from PyPI

The simplest way to install HOJJAT TUI is via pip:

```bash
pip install hojjat-tui
```

## Installing from Source

### From a Git Repository

```bash
git clone https://github.com/HojjatAhmadi/hojjat-tui.git
cd hojjat-tui
pip install .
```

### From a Downloaded ZIP

```bash
# Download and extract the ZIP, then:
pip install .
```

### Development Installation

For development, you can install the package in "editable" mode so that changes to the source code are immediately reflected:

```bash
python -m pip install -e ".[dev]"
```

This installs the development dependencies (pytest, ruff, black, etc.) and sets up the package for development.

## Verifying the Installation

After installation, verify that the package is correctly installed:

```bash
hojjat-tui --version
```

This should display the current version, e.g., `hojjat-tui version 2.0.1`.

### Check Available Commands

```bash
python manage.py --help
```

### Launch the TUI

```bash
hojjat-tui
```

Or via manage.py:

```bash
python manage.py
```

Both commands execute your project's `manage.py` (which imports your function modules) and start the TUI.

## Project Initialization

On first use of a new project directory, initialize the HOJJAT TUI project structure:

```bash
hojjat-tui init
```

This creates:

```text
MyProject/
├── manage.py
├── functions/
│   ├── __init__.py
│   └── example.py
```

- `manage.py` — the project entry point. Import your function modules here so their `@hojjat_function()` decorators register them before the TUI starts.
- `functions/__init__.py` — marks `functions/` as a Python package.
- `functions/example.py` — example functions demonstrating string, table, bar chart, line chart, input, JSON, and error output patterns.
- No database is created during initialization.

### Configuring the Database Path

The SQLite database path can be customized via the `HOJJAT_TUI_DATA_DIR` environment variable:

```bash
export HOJJAT_TUI_DATA_DIR=/path/to/custom/location
hojjat-tui
```

## Upgrading

To upgrade to the latest version:

```bash
pip install --upgrade hojjat-tui
```

## Uninstallation

```bash
pip uninstall hojjat-tui
```

Note: This does not remove the SQLite database file. To completely remove all data, delete the database file manually.

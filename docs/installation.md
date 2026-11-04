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
git clone https://github.com/placeholder/hojjat-tui.git
cd hojjat-tui
pip install .
```

### From a Downloaded ZIP

```bash
# Download and extract the ZIP, then:
pip install .
```

## Development Installation

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

This should display the current version, e.g., `hojjat-tui version 1.4.7`.

### Check Available Commands

```bash
python manage.py --help
```

### Launch the TUI

```bash
hojjat-tui
```

On first launch, you will see a welcome / login screen. If no user account
exists yet, you will be guided through a first-run account creation flow.
After successful authentication, the main TUI opens.

## Database Initialization

On first run, the SQLite database must be initialized:

```bash
python manage.py init
```

This creates the database at the platform-appropriate location:

- **Windows**: `%APPDATA%\hojjat_tui\hojjat_tui.db`
- **macOS/Linux**: `$XDG_DATA_HOME/hojjat_tui/hojjat_tui.db` (default: `$HOME/.local/share/hojjat_tui/hojjat_tui.db`)

### Configuring the Database Path

The database path can be customized via the `HOJJAT_TUI_DATA_DIR` environment variable:

```bash
export HOJJAT_TUI_DATA_DIR=/path/to/custom/location
hojjat-tui
```

Or via the `--db-path` management command:

```bash
python manage.py init --db-path /custom/path/hojjat_tui.db
```

## Upgrading

To upgrade to the latest version:

```bash
pip install --upgrade hojjat-tui
```

The upgrade is safe to rerun — existing database data is preserved.

## Uninstallation

```bash
pip uninstall hojjat-tui
```

Note: This does not remove the SQLite database file. To completely remove all data, delete the database file manually or reinitialize without data.

## Authentication

HOJJAT TUI requires authentication before accessing the main TUI. The
authentication flow is:

1. **First launch**: If no users exist, the First-Run Account Setup screen is shown.
2. **Subsequent launches**: The Welcome / Login screen is shown.
3. **After login**: The main TUI opens.
4. **Logout**: Press `L` or select Logout from Settings to return to the login screen.

Passwords are hashed with bcrypt (12 rounds) and never stored in plain text.

---

## Windows Notes

On Windows, ensure Python is added to your PATH during installation. The database will be created in your AppData roaming directory, which roams across devices if you use Roaming User Profiles.
# Python Installation

Install and run PuTTY Migration Tools from source using Python.

---

## 📋 Requirements

- **Python 3.8 or higher**
- **pip** (Python package installer)
- **Git** (for cloning the repository)

---

## 🐍 Installation Methods

### Method 1: Git Clone (Recommended)

```bash
# Clone the repository
git clone https://github.com/badguy2003st/putty-migration-tools.git

# Navigate to the project directory
cd putty-migration-tools

# Install dependencies
pip install -r tui/requirements.txt
```

### Method 2: Download ZIP

1. Download ZIP from [GitHub](https://github.com/badguy2003st/putty-migration-tools)
2. Extract to a directory
3. Open terminal in that directory
4. Install dependencies:
   ```bash
   pip install -r tui/requirements.txt
   ```

---

## 📦 Dependencies

The tool requires these Python packages (from `requirements.txt`):

- **textual** (≥0.41.0) - Terminal UI framework
- **rich** (≥13.0.0) - Rich text and console output
- **puttykeys** (≥1.0.3) - PPK file parsing (pure Python)

These will be installed automatically with `pip install -r tui/requirements.txt`.

---

## 🚀 Running from Source

### Launch Interactive TUI

```bash
# From project root directory
python -m tui
```

### Run CLI Commands

```bash
# Convert PPK keys
python -m tui convert

# Export to Bitwarden
python -m tui bitwarden

# Export to Tabby
python -m tui tabby

# Generate SSH config
python -m tui ssh-config

# Get help
python -m tui --help
python -m tui convert --help
```

---

## 🛠️ Development Setup

For development and testing:

```bash
# Install development dependencies
pip install -r tui/requirements-dev.txt
```

This includes:
- **pytest** - Testing framework
- **pytest-cov** - Code coverage
- **pytest-mock** - Mocking support
- **pytest-asyncio** - Async test support
- **black** - Code formatter
- **mypy** - Type checking

### Running Tests

```bash
# Run all tests
pytest

# With coverage report
pytest --cov=tui --cov-report=html

# Run specific test file
pytest tests/test_converter.py
```

---

## 🔧 Platform-Specific Notes

### Windows

- **PuTTY Registry Access**: Required for reading PuTTY sessions
- Ensure PuTTY is installed and has saved sessions

### Linux

- **Limited Features**: Cannot read Windows PuTTY Registry
- Can use converted PPK files and exported sessions
- Full support for `convert --to-ssh` feature

---

## ✅ Verification

Verify the installation:

```bash
# Check version
python -m tui --version
# Output: putty-migrate 1.0.0

# Test TUI launch
python -m tui
# Should open interactive menu

# Test CLI
python -m tui convert --help
# Should show convert command options
```

---

## 🚀 Next Steps

- **[Python TUI Guide](../guides/python/tui.md)** - Interactive usage
- **[Python CLI Guide](../guides/python/cli.md)** - Command-line usage
- **[Development Guide](../development/contributing.md)** - Contributing to the project

---

## 🔄 Updating

To update to the latest version:

```bash
# Navigate to project directory
cd putty-migration-tools

# Pull latest changes
git pull

# Update dependencies
pip install -r tui/requirements.txt --upgrade
```

---

## 🐛 Troubleshooting

### Import Errors

```bash
# If you get "ModuleNotFoundError"
pip install -r tui/requirements.txt

# Check installed packages
pip list | grep textual
pip list | grep puttykeys
```

### Python Version Issues

```bash
# Check Python version
python --version

# Must be 3.8 or higher
# If not, install a newer Python version
```

### Permission Errors (Linux)

```bash
# Use --user flag if you don't have admin rights
pip install --user -r tui/requirements.txt
```

---

## 💻 Prefer Binaries?

For a standalone executable that doesn't require Python:
- **[Binary Installation Guide](binary.md)**

# Contributing Guide

Help improve PuTTY Migration Tools!

---

## 🤝 Ways to Contribute

- 🐛 Report bugs
- 💡 Suggest features
- 📝 Improve documentation
- 🔧 Submit pull requests
- ⭐ Star the repository

---

## 🐛 Bug Reports

Report bugs via [GitHub Issues](https://github.com/badguy2003st/putty-migration-tools/issues).

### Include:

- **Command used**: Full command with all flags
- **Platform**: Windows or Linux version
- **Python version**: `python --version`
- **Error message**: Complete error output
- **Expected behavior**: What should have happened

### Template:

```markdown
**Command:**
`putty-migrate convert --to-ssh`

**Platform:**
Windows 11 / Ubuntu 22.04

**Python Version:**
3.10.5

**Error:**
```
[Full error message here]
```

**Expected:**
Should convert keys and copy to ~/.ssh

**Actual:**
Crashes with permission error
```

---

## 💡 Feature Requests

Suggest features via [GitHub Issues](https://github.com/badguy2003st/putty-migration-tools/issues).

### Include:

- **Use case**: Why you need this feature
- **Proposed solution**: How it should work
- **Alternatives**: Other approaches you've considered

---

## 🔧 Development Setup

### 1. Fork & Clone

```bash
# Fork on GitHub, then:
git clone https://github.com/YOUR-USERNAME/putty-migration-tools.git
cd putty-migration-tools
```

### 2. Install Dependencies

```bash
# Runtime dependencies
pip install -r tui/requirements.txt

# Development dependencies
pip install -r tui/requirements-dev.txt
```

### 3. Create Branch

```bash
git checkout -b feature/my-feature
# or
git checkout -b fix/my-bugfix
```

---

## 📝 Code Guidelines

### Style

- Follow **PEP 8**
- Use **type hints**
- Write **docstrings**
- Keep functions **focused**

```python
from typing import List, Optional

def convert_ppk_file(
    ppk_path: Path,
    output_dir: Path,
    password: Optional[str] = None
) -> ConversionResult:
    """Convert a single PPK file to OpenSSH format.
    
    Args:
        ppk_path: Path to the .ppk file
        output_dir: Directory for converted keys
        password: Optional password for encrypted PPKs
        
    Returns:
        ConversionResult with success status and output path
    """
    # Implementation
```

### Testing

```bash
# Run tests
pytest

# With coverage
pytest --cov=tui --cov-report=html

# Specific test
pytest tests/test_converter.py -v
```

### Formatting

```bash
# Format code
black tui/

# Type checking
mypy tui/
```

---

## 🚀 Pull Request Process

### 1. Make Changes

- Write **focused** commits
- **Test** your changes
- **Document** new features

### 2. Create Pull Request

- **Title**: Clear, descriptive (`Fix: Handle empty PPK files`)
- **Description**: What, why, how
- **Link issues**: `Fixes #123`

### 3. Review Process

- Maintainers will review
- Address feedback
- Keep branch updated

### Example PR Description:

```markdown
## What
Adds support for password-protected PPK files in batch conversion.

## Why
Users reported failures when converting encrypted PPKs (#45).

## How
- Added `--password` flag to CLI
- Updated `batch_convert_ppk_files()` to pass password
- Added tests for encrypted PPKs

## Testing
- [x] Manual testing with encrypted PPK
- [x] Unit tests added
- [x] All existing tests pass

Fixes #45
```

---

## 🧪 Testing

### Run Tests

```bash
# All tests
pytest

# Specific file
pytest tests/test_converter.py

# With output
pytest -v

# Stop on first failure
pytest -x
```

### Write Tests

```python
import pytest
from pathlib import Path
from tui.core.converter import convert_ppk_file

def test_convert_ppk_basic():
    """Test basic PPK conversion."""
    ppk_path = Path("tests/fixtures/test.ppk")
    output_dir = Path("tests/output")
    
    result = convert_ppk_file(ppk_path, output_dir)
    
    assert result.success
    assert result.output_file.exists()
    assert result.output_file.stat().st_mode & 0o777 == 0o600
```

---

## 📁 Project Structure

Understanding the codebase:

```
tui/
├── __main__.py          # Entry point, CLI routing
├── main.py              # Legacy entry point
├── cli/                 # CLI command implementations
│   ├── convert_ppk.py
│   ├── export_bitwarden.py
│   ├── export_tabby.py
│   └── export_ssh_config.py
├── core/                # Business logic
│   ├── converter.py     # PPK conversion
│   ├── registry.py      # Windows Registry reading
│   ├── bitwarden_export.py
│   └── ...
├── ui/                  # TUI (Textual)
│   ├── app.py           # Main TUI app
│   ├── styles.tcss      # TUI styling
│   └── screens/         # TUI screens
└── utils/               # Utilities
    ├── platform.py      # Platform detection
    ├── security.py      # File permissions
    └── bitwarden.py     # Bitwarden helpers
```

See **[Architecture Guide](architecture.md)** for details.

---

## 🚀 Next Steps

- **[Architecture Guide](architecture.md)** - Code structure
- **[Building Guide](building.md)** - Create binaries
- **[GitHub Repository](https://github.com/badguy2003st/putty-migration-tools)** - View code

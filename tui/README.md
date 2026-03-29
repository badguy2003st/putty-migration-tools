# PuTTY Migration Tools - TUI Module

Python-based Text User Interface and core library for PuTTY migration tools.

## 🎯 Features

- **Pure Python Implementation** - No PowerShell execution policy issues
- **Cross-Platform** - Works on Windows, Linux, macOS
- **Two-Phase Key Processing** - Intelligent deduplication using SHA256
- **Smart Authentication Detection** - Handles Password/Key/Pageant scenarios
- **Fuzzy Matching** - Auto-matches Pageant sessions to available keys
- **Security-First** - Memory cleanup, secure permissions, temp file management

## 📁 Project Structure

```
tui/
├── __init__.py              # Package initialization
├── __main__.py              # Entry point (python -m tui)
├── requirements.txt         # Python dependencies
├── requirements-dev.txt     # Development dependencies
│
├── core/                    # Business logic modules
│   ├── __init__.py
│   ├── auth_detection.py    # Authentication method detection
│   ├── fuzzy_match.py       # Fuzzy key matching for Pageant
│   ├── key_registry.py      # SHA256-based deduplication
│   ├── registry.py          # Windows Registry reader
│   └── ssh_config.py        # SSH config generator
│
├── utils/                   # Utility modules
│   ├── __init__.py
│   ├── platform.py          # OS detection helpers
│   └── security.py          # Security utilities
│
└── cli/                     # Command-line interfaces
    ├── __init__.py
    └── export_ssh_config.py # SSH config export CLI
```

## 🚀 Quick Start

### Installation

```bash
# Install dependencies
cd putty-migration-tools
pip install -r tui/requirements.txt

# Or use the package manager
pip install textual rich
```

### Usage

#### SSH Config Export (CLI)

```bash
# Basic usage (exports to ~/.ssh/config)
python -m tui

# With custom options
python -m tui --ppk-dir ~/my_keys --output ~/my_ssh_config

# Dry run (preview only)
python -m tui --dry-run

# Non-interactive mode
python -m tui --non-interactive
```

#### As a Python Library

```python
from tui.core.ssh_config import SSHConfigGenerator, write_ssh_config

# Create generator
generator = SSHConfigGenerator(
    ppk_keys_dir="./ppk_keys",
    ssh_dir="~/.ssh",
    interactive=True
)

# Generate SSH config entries
entries = generator.generate()

# Write to file
write_ssh_config(entries, output_file="~/.ssh/config")
```

## 🔐 Security Features

All modules implement security best practices:

### 1. **Variable Cleanup**
```python
# Automatic cleanup at function end
finally:
    del sensitive_data
    import gc
    gc.collect()
```

### 2. **Secure Temporary Files**
```python
from tui.utils.security import create_secure_temp_dir

temp_dir = create_secure_temp_dir()
# Automatically cleaned up on exit via atexit
```

### 3. **File Permissions**
```python
from tui.utils.security import secure_file_permissions

# Private key: 600 (owner only)
secure_file_permissions("~/.ssh/id_rsa", is_private=True)

# Public key: 644 (readable by all)
secure_file_permissions("~/.ssh/id_rsa.pub", is_private=False)
```

### 4. **Secure String Handling**
```python
from tui.utils.security import SecureString

password = SecureString("sensitive_data")
# Use password.get() when needed
value = password.get()
# Memory zeroed automatically when deleted
del password
```

## 📖 Two-Phase Key Processing

The system processes keys in two phases to avoid duplicates:

### Local PPK File Conversion
```
./ppk_keys/
├── production.ppk    →  ~/.ssh/production
├── staging.ppk       →  ~/.ssh/staging
└── database.ppk      →  ~/.ssh/database
```

All keys in `./ppk_keys/` are processed FIRST and registered with SHA256 hashes.

### Registry Session Migration
```
PuTTY Registry:
├── prod-server → C:\Keys\production.ppk  (DUPLICATE - reused!)
├── new-server  → E:\Keys\newkey.ppk      (NEW - converted)
└── vpn-gateway → (Pageant)               (FUZZY MATCHED)
```

Registry keys are checked against local keys. Duplicates reuse existing conversions.

## 🎭 Authentication Scenarios

### Scenario 1: Password Only
```python
# PuTTY session with password auth
session = {"PublicKeyFile": "", "AuthKI": 1}
auth = detect_auth_method(session)
# auth.method == "password"
```

**SSH Config Output:**
```ssh
Host server-name
    HostName example.com
    User admin
    # Authentication: Password
    ServerAliveInterval 60
```

### Scenario 2: Direct Key
```python
# PuTTY session with key file
session = {"PublicKeyFile": "C:\\Keys\\my.ppk", "AuthKI": 0}
auth = detect_auth_method(session)
# auth.method == "key"
# auth.key_file == "C:\\Keys\\my.ppk"
```

**SSH Config Output:**
```ssh
Host server-name
    HostName example.com
    User admin
    IdentityFile ~/.ssh/my_key
    # Converted from: C:\Keys\my.ppk
    ServerAliveInterval 60
```

### Scenario 3: Pageant (with Fuzzy Matching)
```python
# PuTTY session using Pageant
session = {"PublicKeyFile": "", "AuthKI": 0}
auth = detect_auth_method(session)
# auth.method == "pageant"

# System attempts to match session name to available keys
# E.g., "vpn-gateway" → "vpn_gateway.ppk" (90% confidence)
```

**SSH Config Output (auto-matched):**
```ssh
Host vpn-gateway
    HostName example.com
    User admin
    IdentityFile ~/.ssh/vpn_gateway
    # Originally used Pageant
    # Auto-matched: vpn_gateway.ppk (90%)
    ServerAliveInterval 60
```

**SSH Config Output (no match):**
```ssh
Host unknown-server
    HostName example.com
    User admin
    # Originally used Pageant (no matching key found)
    # TODO: Add your key with: IdentityFile ~/.ssh/your_key
    ServerAliveInterval 60
```

## 🧪 Testing

### Manual Testing

```bash
# Test on your Windows machine with real PuTTY sessions
python -m tui --dry-run

# This will:
# 1. Read your PuTTY sessions from Registry
# 2. Detect authentication methods
# 3. Show preview without writing files
```

### Unit Tests

```bash
# Install dev dependencies
pip install -r tui/requirements-dev.txt

# Run tests (planned for v1.1.0)
pytest tests/

# With coverage
pytest --cov=tui tests/
```

## 🔧 Development

### Adding New Features

1. **Core Logic** → Add to `tui/core/`
2. **Utilities** → Add to `tui/utils/`
3. **CLI Tools** → Add to `tui/cli/`
4. **TUI Screens** → Add to `tui/ui/screens/`

### Code Style

```bash
# Format code with black
black tui/

# Type checking with mypy
mypy tui/
```

## ⚠️ Platform Notes

### Windows
- ✅ Full functionality (Registry access via `winreg`)
- ✅ Can read PuTTY sessions
- ✅ Can detect all authentication methods

### Linux/macOS
- ⚠️ Cannot read PuTTY sessions from Windows Registry
- ✅ Can convert PPK files using TUI or CLI
- ✅ Can export to Bitwarden/Tabby/SSH Config
- ✅ Can be used as library for other tools

## 📚 API Reference

### Core Modules

#### `tui.core.registry`
- `read_putty_sessions()` - Read PuTTY sessions from Registry
- `PuttySession` - Data class for session info
- `split_user_at_host()` - Parse user@host notation

#### `tui.core.auth_detection`
- `detect_auth_method(session_data)` - Detect authentication type
- `AuthInfo` - Data class for auth details
- `format_auth_info(auth)` - Human-readable auth description

#### `tui.core.key_registry`
- `KeyRegistry` - SHA256-based deduplication tracker
- `KeyInfo` - Data class for key metadata
- `.calculate_hash(ppk_path)` - SHA256 hash of PPK file
- `.find_duplicate(ppk_path)` - Check for duplicates

#### `tui.core.fuzzy_match`
- `fuzzy_match_key(session_name, keys)` - Match session to keys
- `get_best_match(...)` - Get best match above threshold
- `KeyMatch` - Data class for match results

#### `tui.core.ssh_config`
- `SSHConfigGenerator` - Main conversion class
- `SSHConfigEntry` - SSH config entry data class
- `write_ssh_config(entries, output)` - Write config file

### Utility Modules

#### `tui.utils.platform`
- `get_platform()` - Detect OS
- `is_windows()`, `is_linux()`, `is_macos()` - Platform checks
- `check_python_version()` - Version verification

#### `tui.utils.security`
- `SecureString` - Memory-safe string storage
- `secure_file_permissions(path)` - Set 600/644 permissions
- `create_secure_temp_dir()` - Temp directory with auto-cleanup
- `show_security_reminder()` - Display cleanup recommendations

## 🐛 Troubleshooting

### "PuTTY Registry reading is only supported on Windows"
- **Cause:** Running on Linux/macOS
- **Solution:** Use bash scripts or manually create SSH config

### "winreg module not available"
- **Cause:** Python installation issue
- **Solution:** Reinstall Python or use a different Python distribution

### "Cannot access PuTTY Registry"
- **Cause:** Permissions issue or PuTTY not installed
- **Solution:** Run as your regular user (not admin), install PuTTY

### Import errors
- **Cause:** Missing dependencies
- **Solution:** `pip install -r tui/requirements.txt`

## 📄 License

MIT License - see LICENSE file for details.

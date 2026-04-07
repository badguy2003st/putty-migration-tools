# TUI Guide (Python Version)

Interactive Terminal User Interface when running from source.

---

## 🚀 Starting the TUI

Launch the interactive interface from the project directory:

```bash
# From putty-migration-tools directory
python -m tui
```

---

## 📋 Features

The Python version provides the **same TUI features** as the binary version:

- 🔑 Convert PPK Keys (with password dialog - v1.1.0)
- 📤 Export Sessions
- 📦 Export All to ZIP / 📥 Import All from ZIP (v1.1.1 - platform-specific)
- 💾 Export Log (v1.1.0)
- ⚙️ Settings
- ℹ️ About

### Main Menu (v1.1.1 Platform-Specific)

**Windows:**
- 📦 Export All to ZIP ← NEW!

**Linux:**
- 📥 Import All from ZIP ← NEW!

### Encrypted PPK Support (v1.1.0)

**Auto-create & load passwords:**
- TUI automatically creates `ppk_keys/passwords.txt` on first run
- Loads passwords automatically on each conversion
- Shows interactive password dialog if passwords don't work

**Password Dialog:**
- **Try Password** - Enter manually and retry
- **Skip File** - Continue with next file
- **Cancel & Edit** - Stop to edit passwords.txt

**Automatic Re-encryption (v1.1.0):** 🔐
- Encrypted PPKs → Encrypted OpenSSH (automatic, transparent)
- Password preserved from passwords.txt or manual dialog
- No user action required - security by default!

**Scrollable Log:**
- Supports 500+ lines (no more truncation!)
- Color-coded icons for different error types
- Export log button to save timestamped .txt file

For **detailed TUI usage** including password dialog workflow, see:
- **[Binary TUI Guide](../binary/tui.md)** - All features work identically

---

## 🔧 Differences from Binary

### Running Commands

**Binary:**
```bash
putty-migrate
```

**Python:**
```bash
python -m tui
```

### Dependencies

**Binary:** No dependencies (standalone)

**Python:** Requires installation:
```bash
pip install -r tui/requirements.txt
```

### Platform Notes

- **Windows**: Full PuTTY Registry access
- **Linux**: Limited to converted sessions (no Windows Registry)

---

## 🐛 Troubleshooting

### "ModuleNotFoundError: No module named 'textual'"

```bash
# Install dependencies
pip install -r tui/requirements.txt
```

### "Terminal too small for TUI"

Resize terminal to at least 80x24, or use CLI:
```bash
python -m tui --help
```

### Import Errors

```bash
# Verify Python version (3.8+)
python --version

# Reinstall dependencies
pip install -r tui/requirements.txt --upgrade
```

---

## 🚀 Next Steps

- **[Python CLI Guide](cli.md)** - Command-line usage
- **[Binary TUI Guide](../binary/tui.md)** - Detailed feature documentation
- **[Installation Guide](../../installation/python.md)** - Setup instructions

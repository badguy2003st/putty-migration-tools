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

- 🔑 Convert PPK Keys
- 📤 Export Sessions
- 📋 Export to SSH Config
- ⚙️ Settings
- ℹ️ About

For **detailed TUI usage**, see:
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

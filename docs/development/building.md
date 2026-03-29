# Building Binaries

Create standalone executables with PyInstaller.

---

## 📋 Prerequisites

- **Python 3.8+**
- **PyInstaller**
- **All dependencies installed**

```bash
pip install pyinstaller
pip install -r tui/requirements.txt
```

---

## 🔨 Build Process

### Using build.py (Recommended)

```bash
# Build for current platform
python build.py

# Specify version
python build.py --version 1.0.1

# Debug build (with console output)
python build.py --debug
```

### Manual PyInstaller

```bash
# Windows
pyinstaller --onefile --name putty-migrate-v1.0.0-windows tui/__main__.py

# Linux
pyinstaller --onefile --name putty-migrate-v1.0.0-linux tui/__main__.py
```

---

## ⚙️ build.py Options

The `build.py` script automates the build process:

### Features

- ✅ Auto-detects platform (Windows/Linux)
- ✅ Includes hidden imports
- ✅ Bundles data files (styles.tcss)
- ✅ Sets correct binary name
- ✅ UPX compression (if available)
- ✅ Tests built binary

### Command Line

```bash
# Standard build
python build.py

# Custom version
python build.py --version 1.0.1

# Debug build (no compression, verbose)
python build.py --debug
```

---

## 📦 What Gets Built

### Output Structure

```
dist/
└── putty-migrate-v1.0.0-windows.exe    # Windows
    # or
    putty-migrate-v1.0.0-linux          # Linux
```

### Binary Size

- **Windows**: ~15-20 MB
- **Linux**: ~18-25 MB

Includes:
- Python runtime
- All dependencies (textual, puttykeys, rich)
- Application code
- TUI styles

---

## 🔍 Build Configuration

The `build.py` script configures:

### Hidden Imports

```python
hidden_imports = [
    'textual',
    'textual.app',
    'textual.widgets',
    'puttykeys',
    'cryptography',
    'cryptography.hazmat',
    # Windows only
    'winreg',
]
```

### Data Files

```python
# Include TUI styles
--add-data 'tui/ui/styles.tcss;tui/ui'  # Windows
--add-data 'tui/ui/styles.tcss:tui/ui'  # Linux
```

### Optimizations

- `--onefile` - Single executable
- `--strip` - Remove debug symbols (Linux)
- `--upx-dir` - UPX compression (if available)

---

## 🧪 Testing the Binary

### Automatic Testing

The `build.py` script tests automatically:

```bash
# Runs after successful build
putty-migrate-v1.0.0-windows.exe --version
```

### Manual Testing

```bash
# Version check
./dist/putty-migrate-v1.0.0-linux --version

# Help
./dist/putty-migrate-v1.0.0-linux --help

# Test TUI
./dist/putty-migrate-v1.0.0-linux

# Test CLI commands
./dist/putty-migrate-v1.0.0-linux convert --dry-run
```

---

## 🐛 Troubleshooting

### "Module not found" in binary

**Solution:** Add to hidden imports in `build.py`:

```python
hidden_imports.append('missing_module')
```

### Binary size too large

**Solutions:**
- Install UPX: Compresses by ~40%
- Use `--exclude-module` for unused modules
- Consider alternatives to heavy dependencies

### "styles.tcss not found"

**Solution:** Verify data files are included:

```python
--add-data 'tui/ui/styles.tcss;tui/ui'
```

### Windows SmartScreen warning

**Solution:**
- Code signing (paid certificate)
- Or users click "More info" → "Run anyway"

---

## 📋 Release Checklist

### Before Building

- [ ] Update version in `__main__.py`
- [ ] Update `CHANGELOG.md`
- [ ] Test all features work from source
- [ ] Run `pytest` - all tests pass
- [ ] Update documentation if needed

###During Build

- [ ] Build for Windows
- [ ] Build for Linux
- [ ] Test both binaries
- [ ] Verify file sizes reasonable
- [ ] Check `--help` output correct

### After Building

- [ ] Create GitHub Release
- [ ] Upload binaries
- [ ] Add release notes
- [ ] Update README download links
- [ ] Tag release in Git

---

## 🚀 CI/CD Build

### GitHub Actions

```yaml
name: Build Binaries

on:
  push:
    tags:
      - 'v*'

jobs:
  build-windows:
    runs-on: windows-latest
    steps:
      - uses: actions/checkout@v3
      - uses: actions/setup-python@v4
        with:
          python-version: '3.10'
      
      - name: Install dependencies
        run: |
          pip install pyinstaller
          pip install -r tui/requirements.txt
      
      - name: Build
        run: python build.py --version ${{ github.ref_name }}
      
      - name: Upload
        uses: actions/upload-artifact@v3
        with:
          name: windows-binary
          path: dist/*.exe
  
  build-linux:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v3
      - uses: actions/setup-python@v4
        with:
          python-version: '3.10'
      
      - name: Install dependencies
        run: |
          pip install pyinstaller
          pip install -r tui/requirements.txt
      
      - name: Build
        run: python build.py --version ${{ github.ref_name }}
      
      - name: Upload
        uses: actions/upload-artifact@v3
        with:
          name: linux-binary
          path: dist/putty-migrate-*
```

---

## 🚀 Next Steps

- **[Contributing Guide](contributing.md)** - Development workflow
- **[Architecture Guide](architecture.md)** - Code structure

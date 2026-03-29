# Building Binaries

Create standalone native executables with Nuitka compiler.

---

## 📋 Prerequisites

- **Python 3.8+**
- **Nuitka** (Python-to-C compiler)
- **C Compiler**:
  - **Windows**: MinGW64 (auto-downloaded by Nuitka)
  - **Linux**: GCC (usually pre-installed)
- **All dependencies installed**

```bash
pip install nuitka ordered-set
pip install -r tui/requirements.txt
```

---

## 🔨 Build Process

### Using build.py (Recommended)

```bash
# Build for current platform
python build.py

# Specify version
python build.py --version 1.0.3

# Debug build (with verbose output)
python build.py --debug
```

**First Build Note:** 
- Windows: Downloads MinGW64 compiler (~100 MB) automatically
- Takes 20-25 minutes for first build
- Subsequent builds: ~10-15 minutes (compiler cached)

### Manual Nuitka

```bash
# Windows
python -m nuitka --onefile --assume-yes-for-downloads \
  --output-dir=dist --output-filename=putty-migrate-v1.0.3-windows.exe \
  --windows-console-mode=force \
  --include-package=tui --include-package=textual \
  --include-package=puttykeys --include-package=cryptography \
  --include-package=rich --include-package-data=rich \
  --include-package-data=textual \
  putty_migrate.py

# Linux
python -m nuitka --onefile --assume-yes-for-downloads \
  --output-dir=dist --output-filename=putty-migrate-v1.0.3-linux \
  --include-package=tui --include-package=textual \
  --include-package=puttykeys --include-package=cryptography \
  --include-package=rich --include-package-data=rich \
  --include-package-data=textual \
  putty_migrate.py
```

---

## ⚙️ build.py Options

The `build.py` script automates the Nuitka build process:

### Features

- ✅ Auto-detects platform (Windows/Linux)
- ✅ Includes all required packages
- ✅ Bundles data files (styles.tcss, rich unicode data)
- ✅ Sets correct binary name
- ✅ Native compilation (Python → C → machine code)
- ✅ Single file executable (--onefile)
- ✅ Tests built binary

### Command Line

```bash
# Standard build
python build.py

# Custom version
python build.py --version 1.0.3

# Debug build (verbose Nuitka output)
python build.py --debug
```

---

## 📦 What Gets Built

### Output Structure

```
dist/
└── putty-migrate-v1.0.3-windows.exe    # Windows (~20 MB)
    # or
    putty-migrate-v1.0.3-linux          # Linux (~18 MB)
```

### Binary Size

- **Windows**: ~20 MB (native exe, all dependencies embedded)
- **Linux**: ~18 MB (native ELF binary)

**Includes:**
- Native compiled Python runtime
- All dependencies (textual, puttykeys, rich, cryptography)
- Application code (compiled to C)
- TUI styles (styles.tcss)
- Rich unicode data files
- All system libraries (MinGW DLLs embedded on Windows)

**No temporary extraction!** Everything runs directly from the single file.

---

## 🔍 Build Configuration

The `build.py` script configures Nuitka with:

### Package Inclusion

```python
--include-package=tui              # Main application package
--include-package=textual          # TUI framework
--include-package=puttykeys        # PPK parser
--include-package=cryptography     # SSH operations
--include-package=rich             # Terminal formatting
--include-package-data=rich        # Rich unicode data files
--include-package-data=textual     # Textual data files
--follow-import-to=rich            # Follow all rich imports
```

### Data Files

```python
# Include TUI styles
--include-data-files=tui/ui/styles.tcss=tui/ui/styles.tcss
```

### Platform-Specific Options

**Windows:**
```python
--windows-console-mode=force       # Console application (not GUI)
--windows-icon-from-ico=icon.ico   # Application icon (if available)
```

**Linux:**
```python
# Uses system GCC compiler
# No special flags needed
```

### Optimizations

- `--onefile` - Single executable (no DLL extraction)
- `--assume-yes-for-downloads` - Auto-download MinGW64
- `--enable-plugin=anti-bloat` - Reduce binary size
- `--nofollow-import-to=tkinter` - Exclude unused GUI
- `--nofollow-import-to=pytest` - Exclude test framework

---

## 🧪 Testing the Binary

### Automatic Testing

The `build.py` script tests automatically:

```bash
# Runs after successful build
putty-migrate-v1.0.3-windows.exe --version
# Output: PuTTY Migration Tools 1.0.3
```

### Manual Testing

```bash
# Version check
./dist/putty-migrate-v1.0.3-linux --version

# Help
./dist/putty-migrate-v1.0.3-linux --help

# Test TUI
./dist/putty-migrate-v1.0.3-linux

# Test CLI commands
./dist/putty-migrate-v1.0.3-linux convert --dry-run
./dist/putty-migrate-v1.0.3-linux bitwarden --help
```

---

## 🐛 Troubleshooting

### "Module not found" in binary

**Solution:** Add to package includes in `build.py`:

```python
cmd.append('--include-package=missing_module')
```

### "No module named 'rich._unicode_data'"

**Solution:** Already fixed v1.0.3+. Ensure you have:

```python
--include-package-data=rich
--follow-import-to=rich
```

### Binary size too large

**Normal!** Nuitka binaries are larger than PyInstaller but:
- ✅ No runtime extraction
- ✅ Better reliability
- ✅ Faster startup
- ✅ Native performance

### First build takes forever (Windows)

**Normal!** First build downloads MinGW64 (~100 MB) and takes 20-25 minutes.

**Subsequent builds:** ~10-15 minutes (compiler cached).

### "Failed to load Python DLL python311.dll"

**Fixed in v1.0.3!** Nuitka embeds everything - no external DLLs needed.

### Windows SmartScreen warning

**Solution:**
- Code signing (paid certificate)
- Or users click "More info" → "Run anyway"
- Nuitka binaries are native exe files, more trusted than PyInstaller

---

## 📊 Nuitka vs PyInstaller

| Feature | Nuitka (v1.0.3+) | PyInstaller (v1.0.0-v1.0.2) |
|---------|------------------|----------------------------|
| **Compilation** | Python → C → Native | Bundles interpreter |
| **Binary Type** | True native exe | Python bytecode + interpreter |
| **File Count** | Single file | Single file (but extracts to temp) |
| **Runtime** | No extraction | Extracts to temp dir |
| **DLL Loading** | All embedded | Runtime loading (can fail) |
| **Reliability** | ✅ Excellent | ⚠️ DLL issues on Windows |
| **Build Time** | 20-25 min (Win), 10-12 min (Linux) | 1-2 minutes |
| **Binary Size** | ~20 MB | ~16 MB |
| **Performance** | Native C speed | Python interpreter |
| **Security** | No temp extraction | Temp dir security concerns |

**Verdict:** Nuitka is slower to build but produces more reliable binaries.

---

## 📋 Release Checklist

### Before Building

- [ ] Update version in code
- [ ] Update `CHANGELOG.md`
- [ ] Test all features work from source
- [ ] Run tests
- [ ] Update documentation if needed
- [ ] Commit all changes

### During Build

- [ ] Build for Windows (20-25 min)
- [ ] Build for Linux (10-12 min)
- [ ] Test both binaries
- [ ] Verify file sizes (~20 MB Win, ~18 MB Linux)
- [ ] Check `--help` output correct
- [ ] Test TUI launches
- [ ] Test all CLI commands

### After Building

- [ ] Create Git tag
- [ ] Push tag to trigger GitHub Actions
- [ ] Monitor build progress (~25-30 min)
- [ ] Verify GitHub Release created
- [ ] Download and test release binaries
- [ ] Update README download links if needed

---

## 🚀 CI/CD Build

### GitHub Actions

The `.github/workflows/release.yml` uses Nuitka:

```yaml
name: Build and Release

on:
  push:
    tags:
      - 'v*'

env:
  FORCE_JAVASCRIPT_ACTIONS_TO_NODE24: true

jobs:
  build:
    name: Build ${{ matrix.os }}
    runs-on: ${{ matrix.os }}
    strategy:
      matrix:
        include:
          - os: windows-latest
            platform: windows
          - os: ubuntu-latest
            platform: linux
    
    steps:
      - uses: actions/checkout@v4
      
      - uses: actions/setup-python@v5
        with:
          python-version: '3.11'
      
      - name: Install dependencies
        run: |
          pip install nuitka ordered-set
          pip install -r tui/requirements.txt
      
      - name: Build with Nuitka
        run: python build.py --version ${{ steps.get_version.outputs.version }}
        timeout-minutes: 30
      
      - name: Upload artifact
        uses: actions/upload-artifact@v4
        with:
          name: putty-migrate-${{ matrix.platform }}
          path: dist/*
```

**Build Times on GitHub Actions:**
- Windows: ~23-25 minutes
- Linux: ~10-12 minutes
- Total (parallel): ~25 minutes

---

## 🔄 Reverting to PyInstaller

If you need to revert to PyInstaller (not recommended):

```bash
# Restore backups
cp build.py.pyinstaller.backup build.py
cp .github/workflows/release.yml.pyinstaller.backup .github/workflows/release.yml

# See BACKUP_INFO.md for full instructions
```

---

## 🚀 Next Steps

- **[Contributing Guide](contributing.md)** - Development workflow
- **[Architecture Guide](architecture.md)** - Code structure
- **[Installation Guide](../installation/binary.md)** - Using binaries

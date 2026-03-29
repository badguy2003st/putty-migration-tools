# Backup Information

## Migration from PyInstaller to Nuitka

**Date:** 2026-03-29
**Reason:** PyInstaller Windows binary had persistent DLL loading issues

## Backed Up Files

1. **build.py.pyinstaller.backup** - Original PyInstaller build script
2. **.github/workflows/release.yml.pyinstaller.backup** - Original workflow file

## Changes Made

### build.py
- **Before:** PyInstaller-based compilation
- **After:** Nuitka-based compilation
- **Key Differences:**
  - PyInstaller: Packages Python + app → extracts at runtime
  - Nuitka: Compiles Python → C → native executable
  - No runtime DLL loading issues
  - Single file executable (--onefile mode)
  - Native Windows console mode (--windows-console-mode=force)

### Why Nuitka?

**Problems with PyInstaller (v1.0.0 - v1.0.2):**
- Windows: `Failed to load Python DLL 'python311.dll'` error
- Issue persisted across --onefile and --onedir modes
- Caused by Windows memory protection / antivirus / temp directory issues

**Nuitka Advantages:**
- Native compilation (no runtime extraction)
- No DLL loading at runtime
- Better compatibility with Windows security features
- Single executable file
- Slightly better performance

## Restoration

To restore PyInstaller build:
```cmd
copy build.py.pyinstaller.backup build.py
copy .github\workflows\release.yml.pyinstaller.backup .github\workflows\release.yml
```

## Testing

After migration, test with:
```cmd
python build.py --version 1.0.3-test
dist\putty-migrate-v1.0.3-test-windows.exe --version
dist\putty-migrate-v1.0.3-test-windows.exe --help
```

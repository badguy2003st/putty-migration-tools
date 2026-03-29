# Changelog

All notable changes to this project will be documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.0.0/),
and this project adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

---

## [1.0.0] - 2026-03-28

### 🎉 Initial Release - Production Ready

First stable release of PuTTY Migration Tools with complete TUI and CLI interfaces.

### Added

#### Interactive TUI (Terminal User Interface)
- **Main Menu** with intuitive navigation
- **PPK Conversion Screen** with real-time progress
- **Bitwarden Export Screen** with validation
- **Tabby Export Screen** for terminal configuration
- **SSH Config Generator** for OpenSSH compatibility
- **Installation Screen** for dependency management
- Cross-platform support (Windows, Linux)

#### CLI Commands
- **`putty-migrate convert`** - Convert PPK keys to OpenSSH format
  - Support for batch conversion
  - Custom input/output directories
  - `--to-ssh` flag to copy keys to `~/.ssh` (Linux only)
  - Conflict handling modes: rename, overwrite, skip
  - Dry-run mode for previewing changes
  - Verbose output option
  
- **`putty-migrate bitwarden`** - Export to Bitwarden vault
  - Automatic PuTTY Registry reading (Windows)
  - SSH key authentication detection
  - Bitwarden Type 5 (SSH Key) format
  - Auto-conversion of PPK files
  - Export validation
  
- **`putty-migrate tabby`** - Export to Tabby terminal
  - Session export from PuTTY Registry
  - Merge with existing Tabby configs
  - SSH session filtering
  - JSON validation
  
- **`putty-migrate ssh-config`** - Generate OpenSSH config
  - PuTTY session migration
  - Key path resolution
  - Pageant authentication detection

#### Core Features
- **PPK to OpenSSH Conversion** using pure Python (`puttykeys` library)
- **Public Key Extraction** directly from PPK files
- **Bitwarden SSH Key Export** (Type 5 items)
- **Tabby Configuration Generator**
- **SSH Config Generator** with host aliases
- **Fuzzy Key Matching** for automatic key-session association
- **Authentication Method Detection** (key, password, Pageant)
- **Automatic File Permissions** (600 for private keys, 644 for public keys)

#### Linux-Specific Features
- **~/.ssh Import Dialog** in TUI
- **Conflict Resolution** (rename with numeric suffix, overwrite with backup, skip)
- **Automatic Backup Creation** when overwriting existing keys
- **Secure Permission Management**

#### Developer Features
- Comprehensive error handling
- User-friendly error messages
- Progress callbacks for long operations
- Async/await support for better performance
- Modular architecture for easy extension

### Technical Details

#### Dependencies
- **textual** >= 0.41.0 - TUI framework
- **puttykeys** >= 1.0.3 - Pure Python PPK parsing
- **cryptography** - SSH key operations (transitive dependency)
- Python 3.8+

#### Architecture
```
tui/
├── cli/          # CLI command modules
├── core/         # Backend business logic
├── ui/           # TUI screens and widgets
└── utils/        # Platform detection, security
```

#### Platform Support
- **Windows**: Full support (PuTTY Registry reading)
- **Linux**: Full support (includes ~/.ssh import)

### Security

- Private keys always set to 600 permissions
- Public keys set to 644 permissions
- Automatic backup creation before overwriting
- Session data cleared from memory after export
- No passwords stored in export files

### Documentation

- Comprehensive `README.md` with examples
- `TESTING.md` with detailed test scenarios
- `CHANGELOG.md` for version tracking
- Inline code documentation
- CLI `--help` for all commands



### Known Issues

- **Windows**: Some PuTTY sessions with special characters may not export correctly
- **Linux**: SSH import requires write permissions to `~/.ssh`

### Future Plans

See [GitHub Issues](https://github.com/badguy2003st/putty-migration-tools/issues) for planned features.

Potential future enhancements:
- SSH config merging (not just generation)
- Key passphrase support

---

## [1.0.3] - 2026-03-29

### 🔧 Changed - Major Build System Migration

#### Compiler Migration: PyInstaller → Nuitka
- **Native Compilation**: Python code now compiled to C for better performance and reliability
- **Single File Executables**: True standalone binaries (no archive extraction)
- **Entry Point**: Moved to `putty_migrate.py` (outside tui package) for better module resolution

#### Technical Improvements
- Native Python-to-C compilation using Nuitka
- MinGW64 compiler for Windows (auto-downloaded during build)
- GCC compiler for Linux (system native)
- Build time: ~20-25 minutes (Windows), ~10-12 minutes (Linux)
- Binary size: ~20 MB (slightly larger but fully self-contained)
- `--windows-console-mode=force` for proper console tool behavior

### 🐛 Fixed - Critical Runtime Issues

#### Windows DLL Loading
- **Fixed**: "Failed to load Python DLL python311.dll" error
- **Fixed**: Runtime DLL loading failures on fresh Windows installations
- **Fixed**: Missing system library dependencies

#### Module Loading
- **Fixed**: Missing `rich._unicode_data.unicode17-0-0` module
- **Fixed**: Runtime module import errors in textual/rich
- **Added**: Explicit `--include-package-data=rich` flag
- **Added**: Explicit `--include-package-data=textual` flag

#### Build System
- **Fixed**: Temp directory extraction issues
- **Fixed**: Platform-specific DLL path resolution
- **Fixed**: All PyInstaller onefile/onedir extraction problems
- **Fixed**: Unicode encoding errors in build script (GitHub Actions compatibility)

### 📦 Distribution Changes

#### Before (v1.0.0-v1.0.2)
- Windows: ZIP archive containing exe + _internal folder (~16 MB)
- Linux: TAR.GZ archive containing binary + dependencies (~14 MB)
- Required extraction before use

#### Now (v1.0.3+)
- Windows: Single `putty-migrate-v1.0.3-windows.exe` (~20 MB)
- Linux: Single `putty-migrate-v1.0.3-linux` (~18 MB)
- No extraction needed - download and run!

### 🔐 Security & Reliability

- No runtime DLL loading (all embedded)
- No temp directory extraction (security improvement)
- Reduced attack surface (single file vs multiple DLLs)
- Native compilation reduces runtime overhead

### 📖 Developer Notes

#### Build Process
```bash
# Install Nuitka
pip install nuitka ordered-set

# Build
python build.py --version 1.0.3

# First build downloads MinGW64 (~100 MB) on Windows
# Subsequent builds are cached and faster
```

#### Backup Files Created
- `build.py.pyinstaller.backup` - Original PyInstaller build script
- `.github/workflows/release.yml.pyinstaller.backup` - Original workflow
- `BACKUP_INFO.md` - Restoration instructions if needed

### ⚠️ Breaking Changes

**None** - All command-line interfaces and functionality remain identical.

### 🎯 Tested Platforms

- ✅ Windows 11 (local build successful)
- ✅ Windows Server 2022 (GitHub Actions - 23m45s)
- ✅ Ubuntu Latest (GitHub Actions - 11m40s)

### 📝 Known Issues

#### Build System
- First build on fresh system takes longer due to compiler download
- Binary size increased by ~4 MB compared to PyInstaller
- Node.js 20 deprecation warnings in GitHub Actions (cosmetic only)

#### PPK v3 Format Not Supported ⚠️ **CRITICAL**

**Problem**: PuTTY 0.75+ (released February 2021) uses PPK v3 format by default with Argon2id encryption. This format is **not supported** by the `puttykeys` library v1.0.3.

**Impact**: ~90% of users with recent PuTTY installations have PPK v3 keys.

**Error Message**: "Unsupported key type. Only RSA and Ed25519 keys are supported." (misleading - actually a format version issue)

**Workaround**: Users must convert PPK v3 to PPK v2 in PuTTYgen:
1. Open PuTTYgen → Load `.ppk` file
2. **Key** menu → **Parameters for saving key files...**
3. Set **PPK file version: 2**
4. Click **OK** → **Save private key**

**Direct OpenSSH export from PuTTYgen**: Not recommended (may cause formatting issues)

**Future Fix**: PPK v3 support planned for v1.0.4 (mid-April 2026). See `PPK_V3_IMPLEMENTATION_PLAN.md`.

**Documentation**: Detailed instructions in [Troubleshooting Guide](docs/troubleshooting.md#-unsupported-key-type-despite-rsaed25519-key).

**Test Files**: Located in `test/ppk_keys/` with both v2 (working) and v3 (not working) samples.

#### Other Limitations
- **TUI Password Prompt**: Not available for encrypted PPK files (CLI `--password` flag works)
- **DSA Keys**: Not supported (deprecated and insecure)
- **ECDSA Keys** (except Ed25519): Not supported by puttykeys library
- **Password on Unencrypted Keys**: Shows confusing error instead of ignoring password

---

## [Unreleased]

### Planned for v1.0.4 (mid-April 2026)

#### Major Features
- **PPK v3 Support** - Argon2id decryption for modern PuTTY keys
- **TUI Password Prompt** - Interactive password input for encrypted keys
- **Multi-Password File Support** - `--password-file` flag for batch operations
- **Re-encryption Support** - `--keep-encryption` flag to maintain key encryption
- **Smart Password Handling** - Gracefully handle password on unencrypted keys

See `PPK_V3_IMPLEMENTATION_PLAN.md` for complete implementation plan.

---

No unreleased changes yet.

---

## Release Notes Format

### Version Number Convention

- **Major.Minor.Patch** (e.g., 1.0.0)
- **Major**: Breaking changes or major new features
- **Minor**: New features, backward compatible
- **Patch**: Bug fixes, minor improvements

### Categories

- **Added**: New features
- **Changed**: Changes to existing functionality
- **Deprecated**: Features that will be removed
- **Removed**: Removed features
- **Fixed**: Bug fixes
- **Security**: Security-related changes

---

**Repository**: https://github.com/badguy2003st/putty-migration-tools  
**License**: MIT  
**Maintainer**: badguy2003st

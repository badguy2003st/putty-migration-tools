# Changelog

All notable changes to this project will be documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.0.0/),
and this project adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

---

## [1.1.3] - 2026-04-30

### Removed

- Removed all vestigial `puttykeys` library references from active code
  - Removed conditional `import puttykeys` from `converter.py` and `bitwarden_export.py`
  - Removed `check_puttykeys_available()` function from `converter.py`
  - Removed puttykeys availability check gate from `conversion.py` UI screen that blocked conversion when puttykeys was not installed
  - Removed legacy `puttykeys.PublicKey.from_string()` fallback from `bitwarden_export.py`

### Fixed

- Fixed PPK conversion failing on Linux when `puttykeys` library was not installed — the native PPK parser (introduced in v1.1.0) now handles all conversions without any external dependency check
- Fixed misleading "puttykeys library not found" error message in the TUI conversion screen

### Changed

- Updated outdated docstrings and comments in `converter.py`, `bitwarden_export.py`, `ppk_parser.py`, and `ppk_v2_crypto.py` to accurately reference the native PPK implementation instead of the removed `puttykeys` library
- Enabled pip dependency caching in GitHub Actions for faster CI builds (Windows and Linux)
- Added Nuitka artifact caching to avoid re-downloading MinGW compiler on Windows and reuse compiler cache on Linux
- Enabled parallel Nuitka compilation with `--jobs=4` for faster binary builds on both platforms
- Added `NUITKA_JOBS` environment variable support to `build.py` for configurable parallel compilation

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

## [1.1.0] - 2026-03-30

### Added

#### PPK v3 Support - Major Feature
- **Encrypted PPK v3 keys** - Full support for PuTTY 0.75+ key format
- **Argon2id key derivation** - Secure KDF with automatic backend selection
- **Performance optimization** - 590x speedup with argon2-cffi-bindings (0.1s vs 60s per key)
- **3-tier fallback system**:
  1. argon2-cffi-bindings via ctypes (fastest, ~0.1s, Nuitka-compatible)
  2. argon2-cffi via standard import (fast, ~0.1s, Python-only)
  3. argon2pure (slow, ~60s, universal fallback with warning)

#### CLI Enhancements
- **Multi-password file support** - Try multiple passwords automatically with `--password-file`
- **Password file format** - Simple text file with one password per line, supports comments (#)
- **Smart password reporting** - Shows which password worked in verbose mode

### Changed

#### Core Improvements
- **Unified PPK parser** - Single parser for both PPK v2 and PPK v3 formats
- **Improved blob parsing** - Better whitespace handling for robustness
- **Automatic backend selection** - Transparent performance optimization
- **Smart password handling** - Automatically ignores password on unencrypted keys (no error)

#### Build System
- **Nuitka package inclusion** - Added `--include-package=_argon2_cffi_bindings` for fast Argon2
- **CI/CD optimization** - GitHub Actions installs argon2-cffi-bindings for fast builds
- **Binary size** - Increased to ~25 MB (Windows) / ~23 MB (Linux) due to Argon2 bindings

### Technical Details

#### Argon2id Implementation
- **Correct IV derivation** - IV comes from Argon2id output (bytes 32-48), not zeros
- **80-byte KDF output** - 32 (AES key) + 16 (IV) + 32 (MAC key)
- **ctypes-based bindings** - Direct C library calls for Nuitka compatibility
- **Cross-platform** - Works on Windows (.pyd) and Linux (.so)

#### Performance
- **argon2-cffi-bindings**: 0.1s per key (recommended)
- **argon2-cffi**: 0.1s per key (Python-only fallback)
- **argon2pure**: 60s per key (universal fallback, shows warning)
- **Batch conversion**: ~575 keys/minute with fast backend

### Fixed

#### PPK v3 Compatibility
- **Encryption support** - Decrypts AES-256-CBC encrypted private keys
- **Format detection** - Auto-detects PPK v2 vs v3
- **Error messages** - Clear errors for wrong passwords or corrupt files

### Security

- All existing security features maintained
- Argon2id provides stronger key derivation than PPK v2's SHA-1
- Constant-time MAC verification (when implemented)

### Documentation

- Updated CHANGELOG.md with v1.0.4 details
- Updated README.md with PPK v3 support and performance notes
- Added performance optimization instructions
- Removed misleading "PPK v3 not supported" warnings

### Known Issues

#### MAC Verification
- MAC verification implemented but not strictly enforced
- Wrong passwords are caught during RSA parsing with clear errors
- Future versions may enforce MAC validation before decryption

#### Unsupported Key Types
- **Ed25519 PPK v3**: Not yet implemented (coming in future release)
- **DSA keys**: Not supported (deprecated and insecure)
- **ECDSA keys** (except Ed25519): Not supported by underlying library

### Upgrade Notes

#### For Binary Users
- Download latest release from GitHub
- No configuration changes needed
- Fast performance automatically enabled

#### For Python Users
```bash
# Install dependencies (includes argon2-cffi-bindings for performance)
pip install -r tui/requirements.txt
```

### Testing

- All 5 test files pass (3 PPK v2, 2 PPK v3)
- Multi-password file tested with test-passwords.txt
- Test password: "test"
- Located in `test/ppk_keys/`

### CLI Examples

#### Multi-Password File
```bash
# Create password file
cat > passwords.txt << 'EOF'
# Try common passwords
password123
mypassword
test
EOF

# Convert with password file
putty-migrate convert --password-file passwords.txt -v

# Output shows which password worked:
# ✓ key1.ppk (password #3)
# ✓ key2.ppk (unencrypted)
```

### Future Features (v1.2.0)

- TUI password prompt for encrypted keys
- Re-encryption support (`--keep-encryption`)
- Batch re-encryption with new passwords

---

## [1.1.0] - 2026-03-30

### 🎉 Major Release - Custom PPK Parser (No External Dependencies!)

**Headline:** 99.9%+ coverage of real-world PPK files with custom implementation!

### Added

#### Custom PPK Parser
- **Custom PPK v2 parser** (`ppk_v2_crypto.py`) - Pure Python implementation
  - SHA-1 key derivation for encrypted keys
  - HMAC-SHA1 MAC verification
  - No external PPK library dependencies!
- **Complete ECDSA support** for all 3 NIST curves:
  - ✅ P-256 (nistp256) - v2 + v3
  - ✅ P-384 (nistp384) - v2 + v3
  - ✅ P-521 (nistp521) - v2 + v3
- **Ed25519 PPK v2 support** - Was previously only v3
- **Ed448 detection** - Clear error with Ed25519 recommendation (library limitation)

#### Enhanced Error Detection (Phase 4)
- **SSH2 PUBLIC KEY detection** - Skip with helpful "remove .pub files" message
- **OpenSSH format detection** - "Already converted" message
- **SSH-1 protocol detection** - Obsolete format warning (deprecated ~2001)
- **DSA key detection** - Deprecated warning with recommendation
- **Unsupported key type validation** - Clear error with supported list

#### Security Features (v1.1.0)
- **🔐 Encryption Preservation** - Encrypted PPKs stay encrypted (secure by default!)
  - Original password automatically re-used for OpenSSH key
  - Manual passwords from dialog also preserved
  - CLI `--no-encryption` flag to opt-out
  - Prevents accidental key exposure

#### TUI Enhancements
- **Interactive password dialog** - Retry wrong passwords without restart
- **Automatic re-encryption** - Encrypted keys stay encrypted (transparent to user)
- **Cross-platform SSH import** - Works on Windows + Linux with OpenSSH
- **Scrollable log output** - RichLog widget supports 500+ lines
- **Export log button** - Save conversion log to timestamped file (`conversion_log_YYYYMMDD_HHMMSS.txt`)
- **Smart error formatting** - Context-specific icons and guidance:
  - ⚠️ Ed448 → "Use Ed25519 instead"
  - ❌ DSA → "Generate new key"
  - ⏭ Public keys → "Remove .pub files"
  - 🔒 Password → "Add to passwords.txt"
- **Multi-line error display** - Long errors wrapped intelligently

#### CLI Enhancements
- **Auto-load passwords.txt** - Automatically loads `ppk_keys/passwords.txt` if exists
- **Multi-password support** - Try multiple passwords with `--password-file`
- **Password index reporting** - Shows which password worked in verbose mode
- **`--no-encryption` flag** - Disable automatic re-encryption (encrypted → unencrypted)

### Changed

#### Architecture
- **Unified PPK architecture** - Parallel v2 + v3 crypto modules
- **ppk_parser.py** - Routes to `ppk_v2_crypto` or `ppk_v3_crypto` based on version
- **ppk_v3_crypto.py** - Enhanced Ed25519/ECDSA with SSH string parsing
- **Structural error preservation** - Ed448/DSA errors not masked by "passwords failed"

#### Dependencies
- ❌ **Removed puttykeys>=1.0.3** - Completely replaced with custom parser!
- ✅ **Kept argon2pure + argon2-cffi-bindings** - For PPK v3 support
- ✅ **Kept cryptography** - For key serialization
- ✅ **Kept textual + rich** - For TUI

### Removed

- **puttykeys library** - Custom implementation provides more features and better error handling

### Fixed

#### Error Handling
- **Ed448 error masking** - Structural errors now preserved in multi-password logic
- **SSH2 PUBLIC KEY detection** - Case-insensitive pattern matching
- **Password on unencrypted keys** - No longer shows confusing error
- **TUI log truncation** - Errors no longer cut off at 50 characters
- **Multi-line error display** - Long messages wrapped properly

#### TUI Issues
- **Non-scrollable log** - Now uses RichLog widget with scroll support
- **Password retry logic** - Better handling of structural vs. password errors
- **Export capability** - Users can now save logs for troubleshooting

### Technical Details

#### Supported Key Types (v1.1.0)

| Algorithm | PPK v2 | PPK v3 | Coverage |
|-----------|--------|--------|----------|
| RSA       | ✅     | ✅     | ~90% |
| Ed25519   | ✅     | ✅     | ~9% |
| ECDSA P-256 | ✅   | ✅     | <1% |
| ECDSA P-384 | ✅   | ✅     | <1% |
| ECDSA P-521 | ✅   | ✅     | <1% |
| Ed448     | ⚠️     | ⚠️     | Library limitation |
| DSA       | ❌     | ❌     | Deprecated (intentional) |

**Total Coverage: 99.9%+ of real-world PPK files!**

#### PPK v2 Implementation Details
- **KDF**: SHA-1 based (different from v3's Argon2id!)
- **MAC**: HMAC-SHA1 (different from v3's HMAC-SHA256!)
- **Encryption**: AES-256-CBC
- **Format**: SSH wire protocol parsing

#### Testing
- ✅ 12/12 integration tests passed
- ✅ Phase 1-3 implementation tests (RSA, Ed25519, ECDSA)
- ✅ All key types validated end-to-end

### Performance

- **PPK v2**: Instant (SHA-1 KDF)
- **PPK v3 unencrypted**: Instant
- **PPK v3 encrypted**: 0.1s (with argon2-cffi-bindings) or 60s (argon2pure fallback)

### Security

- All existing security features maintained
- PPK v2 uses SHA-1 KDF (PuTTY's original design, not our choice)
- PPK v3 uses modern Argon2id (strongly recommended)

### Migration Notes

#### From v1.0.x to v1.1.0

**No Breaking Changes!** All existing workflows continue to work.

**New Capabilities:**
- ECDSA keys now work (P-256/384/521)
- PPK v2 Ed25519 keys now work
- Better TUI experience (scrollable log, export button)
- CLI auto-loads passwords.txt

**Removed Dependency:**
```bash
# No longer needed:
pip uninstall puttykeys

# Reinstall requirements:
pip install -r tui/requirements.txt
```

### Known Issues

#### Ed448 Support
- **Status**: Blocked by cryptography library
- **Error**: "Ed448 OpenSSH serialization not yet supported"
- **Workaround**: Use Ed25519 (same 128-bit security level)
- **Issue Tracker**: https://github.com/pyca/cryptography/issues/...

#### DSA Keys
- **Status**: Intentionally not supported
- **Reason**: Deprecated since 2015, cryptographically insecure
- **Workaround**: Generate new RSA or Ed25519 key

---

## [1.1.1] - 2026-04-07

### 🎉 Major Feature - Complete Export/Import Workflow

**Headline:** Windows → Linux migration made easy with one-click export and selective import!

### Added

#### Complete Export/Import Workflow
- **Windows: Export All to ZIP** - One-click migration package creation
  - Converts all PPK keys to OpenSSH format (with password support)
  - Generates SSH config for all sessions
  - Generates Tabby terminal config
  - Generates Bitwarden vault export
  - Packages everything in timestamped ZIP file
  - Includes MANIFEST.json metadata and README.txt instructions
  
- **Linux: Import All from ZIP** - Install Windows migration package
  - Interactive checkbox selection for import components
  - SSH Keys import to ~/.ssh with conflict handling (rename/overwrite/skip)
  - SSH Config merge to ~/.ssh/config with automatic backup
  - Bitwarden export handling (auto-import or manual instructions)
  - Direct ZIP processing (no manual extraction needed)
  - BW_SESSION environment variable check for secure auto-import
  - Auto-detection of ZIP files in common locations (Downloads, home, cwd)

#### CLI Commands
- **`putty-migrate export-all`** - Windows export to ZIP
  - `-o, --output` - Custom output file path
  - `--password-file` - Password file for encrypted PPKs
  - `--dry-run` - Preview without creating ZIP
  - `-v, --verbose` - Verbose output
  
- **`putty-migrate import-all`** - Linux import from ZIP
  - `--ssh-keys` - Import SSH keys to ~/.ssh
  - `--ssh-config` - Import SSH config
  - `--bitwarden` - Handle Bitwarden export
  - `--all` - Import everything
  - `--conflict MODE` - Conflict handling: rename/overwrite/skip
  - `--bw-auto-import` - Automatically run `bw import` command
  - `--dry-run` - Preview without importing
  - `-v, --verbose` - Verbose output

#### TUI Enhancements
- **Platform-specific main menu buttons**
  - Windows: "📦 Export All to ZIP"
  - Linux: "📥 Import All from ZIP"
- **Optimized import screen layout** - ~35% height reduction
  - Horizontal checkbox layout for grouped ~/.ssh options
  - SSH Keys + SSH Config displayed side-by-side
  - Bitwarden separate below
  - Removed progress bar (operations are fast enough)
  - Increased log height (6 → 10 lines for better visibility)
- **Export Log button** - Save import/export logs to timestamped files
- **Compact container layouts** - `height: auto` CSS prevents excessive spacing
- **Conditional option visibility** - Conflict/Bitwarden modes only show when relevant

### Changed

#### UI/UX Improvements
- Main menu now shows platform-specific export/import options
- Import screen containers use `height: auto` for compact display
- SSH Keys and SSH Config checkboxes now displayed horizontally (grouped ~/.ssh area)
- Bitwarden displayed separately for clear separation
- Import log optimized for better visibility

#### Backend Improvements
- Bitwarden import instructions now include `bw sync` command
- BW_SESSION validation prevents unauthorized imports
- Automatic `bw sync` after successful auto-import
- Temp directory cleanup improved

### Fixed

#### Critical Bug Fixes
- **🐛 Rename algorithm for .pub files** - Number now inserted BEFORE .pub extension
  - **Before:** `unraid31.pub` → `unraid31.pub.2` ❌ (SSH can't pair private/public keys!)
  - **After:** `unraid31.pub` → `unraid31.2.pub` ✅ (SSH compatible pairing maintained!)
  - **Impact:** Affects all users using rename mode with public keys
  
- **Container height issues** - Added `height: auto` to prevent excessive vertical spacing in import screen
- **BW_SESSION validation** - Now checks environment variable before attempting Bitwarden auto-import
- **Bitwarden sync** - Automatically runs `bw sync` after successful import to update vault

### Technical Details

#### ZIP Package Structure
```
putty-migration-export-YYYYMMDD-HHMMSS.zip
├── README.txt                    # Import instructions
├── MANIFEST.json                 # Metadata (version, date, counts)
├── openssh_keys/
│   ├── key1
│   ├── key1.pub
│   ├── key2
│   ├── key2.pub
│   └── ...
├── ssh-config                    # OpenSSH config file
├── tabby-config.json            # Tabby terminal config
└── bitwarden-export.json        # Bitwarden Type 5 export
```

#### MANIFEST.json Format
Contains metadata including:
- Version and export timestamp
- File counts (PPK files, SSH keys, sessions)
- Encryption status (encrypted vs unencrypted keys)
- Compatibility information
- Error/warning messages

#### Import Options (Linux)
- ✅ SSH Keys to ~/.ssh (with conflict handling)
- ✅ SSH Config to ~/.ssh/config (with backup)
- ✅ Bitwarden Vault (auto-import or manual)

### Security

- **ZIP security:** ZIP files contain sensitive SSH keys - handle securely
- **BW_SESSION validation:** Prevents unauthorized Bitwarden imports
- **Automatic file permissions:** 600 for private keys, 644 for public keys on Linux import
- **Backup creation:** Config files backed up before merge
- **Temp directory cleanup:** Secure cleanup after import
- **No cloud uploads:** All processing remains local

### Documentation

- Updated CHANGELOG.md with v1.1.1 details
- Updated README.md with export/import workflow section
- Updated CLI guides for binary and Python usage
- Updated TUI guides with platform-specific buttons
- Updated .gitignore with ZIP export pattern

### Dependencies

**No new dependencies!** Uses Python stdlib:
- `zipfile` - ZIP creation/extraction
- `tempfile` - Temporary directory handling
- `shutil` - File operations
- `json` - MANIFEST handling
- `subprocess` - bw CLI integration (optional)

### Performance

- **Export operation:** ~1-2 seconds for typical workload (15 keys, 20 sessions)
- **Import operation:** ~1 second for typical workload
- **No progress bar:** Operations complete fast enough without UI overhead

### Known Issues

- **ZIP file size:** Typical export ~50-100 KB (compressed keys + configs)
- **Large key collections:** May take longer (20+ keys with encryption)

### Upgrade Notes

#### For Binary Users
- Download latest release from GitHub
- No configuration changes needed
- New export/import features automatically available

#### For Python Users
```bash
git pull origin main
pip install -r tui/requirements.txt  # No new dependencies
python -m tui
```

### Testing

- ✅ Windows export tested with 15 PPK files (mixed encrypted/unencrypted)
- ✅ Linux import tested with all checkbox combinations
- ✅ Conflict handling validated (rename/overwrite/skip modes)
- ✅ Bitwarden auto-import tested with BW_SESSION environment variable
- ✅ ZIP structure validated across Windows/Linux platforms
- ✅ Public key rename bug fix validated
- ✅ Container layout optimization verified

### CLI Examples

#### Windows Export
```bash
# TUI (interactive)
putty-migrate

# CLI with default output
putty-migrate export-all

# CLI with custom output
putty-migrate export-all -o my-export-2026-04-07.zip

# With password file
putty-migrate export-all --password-file ppk_keys/passwords.txt

# Dry run (preview)
putty-migrate export-all --dry-run -v
```

#### Linux Import
```bash
# TUI (interactive with auto-detection)
putty-migrate

# CLI - import everything
putty-migrate import-all export.zip --all

# CLI - selective import
putty-migrate import-all export.zip --ssh-keys --ssh-config

# CLI - with conflict handling
putty-migrate import-all export.zip --ssh-keys --conflict rename

# CLI - with Bitwarden auto-import (requires BW_SESSION)
putty-migrate import-all export.zip --all --bw-auto-import

# Dry run
putty-migrate import-all export.zip --all --dry-run
```

---

## [1.1.2] - 2026-04-16

### 🔧 Fixed - Platform-Specific Line Endings

#### Key Export Format Fix
- **Fixed**: Keys are now exported in the correct format for the current system
  - **Windows**: CRLF (`\r\n`) line endings
  - **Linux**: LF (`\n`) line endings
- **Impact**: Resolves issues with key files having incorrect line endings when exported on Windows
- **Technical**: Uses platform-aware line ending conversion based on `sys.platform`

---

## [Unreleased]

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

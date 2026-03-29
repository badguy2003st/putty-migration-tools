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

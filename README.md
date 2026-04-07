# 🔑 PuTTY Migration Tools

[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](https://opensource.org/licenses/MIT)
[![Python 3.8+](https://img.shields.io/badge/python-3.8+-blue.svg)](https://www.python.org/downloads/)
[![Platform](https://img.shields.io/badge/platform-Windows%20%7C%20Linux-lightgrey)](https://github.com/badguy2003st/putty-migration-tools)

Modern migration tools for PuTTY sessions and SSH keys. Migrate from PuTTY to **Bitwarden**, **Tabby**, or standard **OpenSSH** with both an interactive TUI and powerful CLI.

---

## ✨ Features

- 🖥️ **Interactive TUI** - Beautiful terminal interface for guided migrations
- ⌨️ **Powerful CLI** - Full automation with `convert`, `bitwarden`, `tabby`, `ssh-config` commands
- 📦 **Complete Export/Import** - Windows → ZIP → Linux workflow (v1.1.1)
-  **Bitwarden Export** - Store SSH keys in Bitwarden vault with SSH Agent support
- 📁 **PPK → OpenSSH Conversion** - Pure Python, cross-platform key conversion (PPK v2 & v3)
- 🔐 **Encryption Preservation** - Encrypted PPKs stay encrypted (v1.1.0 - secure by default!)
- ⚡ **Fast Performance** - 590x speedup for PPK v3 encrypted keys with automatic optimization
- ⚙️ **SSH Config Generation** - Create OpenSSH config from PuTTY sessions
- 🎨 **Tabby Terminal Export** - Import sessions into Tabby terminal
- 🐧 **Linux ~/.ssh Import** - Direct import with intelligent conflict handling (rename/overwrite/skip)
- 🔒 **Security First** - Automatic file permissions (600/644), backup creation, no cloud uploads

---

## 📥 Quick Start (Binary - Recommended)

### 1. Download

Get the latest binary from [Releases](https://github.com/badguy2003st/putty-migration-tools/releases):

- **Windows**: `putty-migrate-vX.X.X-windows.exe`
- **Linux**: `putty-migrate-vX.X.X-linux`

### 2. Run

**Interactive TUI:**
```bash
# Windows
putty-migrate.exe

# Linux
chmod +x putty-migrate-v1.0.0-linux
./putty-migrate-v1.0.0-linux
```

**CLI Commands:**
```bash
# Convert PPK keys
putty-migrate convert

# Convert with password
putty-migrate convert --password mypassword

# Convert with password file (v1.1.0)
putty-migrate convert --password-file passwords.txt -v

# Disable re-encryption (encrypted PPKs become unencrypted)
putty-migrate convert --no-encryption

# Export to Bitwarden
putty-migrate bitwarden --auto-convert

# Export to Tabby
putty-migrate tabby

# Generate SSH config
putty-migrate ssh-config

# Get help
putty-migrate --help
```

---

## 🔄 Export/Import Workflow (v1.1.1)

### Windows → Linux Migration

**Step 1: Export on Windows**
```bash
# Interactive TUI\
putty-migrate

# CLI
putty-migrate export-all

# CLI with custom output
putty-migrate export-all -o my-migration.zip
```

**Creates:** `putty-migration-export-YYYYMMDD-HHMMSS.zip` containing:
- ✅ Converted OpenSSH keys (all PPK files)
- ✅ SSH configuration (OpenSSH format)
- ✅ Tabby terminal config
- ✅ Bitwarden vault export
- ✅ MANIFEST.json metadata
- ✅ README.txt with instructions

**Step 2: Transfer ZIP to Linux**
```bash
# Copy via SCP, USB, or any method
scp putty-migration-export-*.zip user@linux-host:~/
```

**Step 3: Import on Linux**
```bash
# Interactive TUI (auto-detects ZIP)
putty-migrate

# CLI - import everything
putty-migrate import-all export.zip --all

# CLI - selective import
putty-migrate import-all export.zip --ssh-keys --ssh-config

# With conflict handling
putty-migrate import-all export.zip --ssh-keys --conflict rename
```

**Import Options:**
- **SSH Keys** → `~/.ssh/` (with conflict handling: rename/overwrite/skip)
- **SSH Config** → `~/.ssh/config` (with automatic backup)
- **Bitwarden** → Auto-import or manual instructions

---

## 📖 Documentation

### Installation
- **[Binary Installation](docs/installation/binary.md)** - Windows & Linux setup
- **[Python Installation](docs/installation/python.md)** - Run from source

### Binary Usage (Recommended)
- **[TUI Guide](docs/guides/binary/tui.md)** - Interactive terminal interface
- **[CLI Guide](docs/guides/binary/cli.md)** - Command-line automation

### Feature Guides
- **[PPK Conversion](docs/guides/convert-ppk.md)** - Convert .ppk to OpenSSH format
- **[Bitwarden Export](docs/guides/bitwarden.md)** - Export to Bitwarden SSH vault & Agent
- **[Tabby Export](docs/guides/tabby.md)** - Import to Tabby terminal
- **[SSH Config](docs/guides/ssh-config.md)** - Generate OpenSSH config files

### Advanced Topics
- **[Conflict Handling](docs/advanced/conflict-handling.md)** - Linux ~/.ssh conflict modes
- **[Automation & Scripting](docs/advanced/automation.md)** - CI/CD integration, batch scripts
- **[Security Best Practices](docs/advanced/security.md)** - File permissions, key rotation

### Development
- **[Contributing](docs/development/contributing.md)** - How to contribute
- **[Architecture](docs/development/architecture.md)** - Code structure
- **[Building](docs/development/building.md)** - Create binaries with PyInstaller

### Support
- **[Troubleshooting](docs/troubleshooting.md)** - Common issues & solutions
- **[TESTING.md](TESTING.md)** - Comprehensive testing guide
- **[CHANGELOG.md](CHANGELOG.md)** - Version history

---

## 🐍 Python Version

Run from source for development or custom modifications:

```bash
# Install
git clone https://github.com/badguy2003st/putty-migration-tools.git
cd putty-migration-tools
pip install -r tui/requirements.txt

# Optional: Install for 590x faster PPK v3 encryption
pip install argon2-cffi-bindings

# Run TUI
python -m tui

# Run CLI
python -m tui convert
```

**Documentation:**
- **[Python Installation Guide](docs/installation/python.md)**
- **[Python TUI Guide](docs/guides/python/tui.md)**
- **[Python CLI Guide](docs/guides/python/cli.md)**

### Performance

PPK v3 encrypted keys are automatically optimized for performance:

- **With argon2-cffi-bindings (default):** ~0.1s per key (590x faster)
- **Fallback to argon2pure:** ~60s per key (if bindings unavailable)

The tool includes fast binaries by default and automatically selects the best backend available.

---

## 🔒 Security

- **Local processing only** - No cloud uploads, all operations offline
- **Encryption preservation (v1.1.0)** - Encrypted PPKs stay encrypted with original password
- **Automatic permissions** - Private keys: 600, Public keys: 644
- **Backup safety** - Creates `.bak` files in overwrite mode
- **Memory cleanup** - Sensitive data cleared after operations

See **[Security Guide](docs/advanced/security.md)** for detailed best practices.

---

## ⚠️ Known Limitations

### Supported Key Formats (v1.1.0)

| Algorithm | PPK v2 | PPK v3 | Coverage |
|-----------|--------|--------|----------|
| RSA       | ✅     | ✅     | ~90% of keys |
| Ed25519   | ✅     | ✅     | ~9% of keys |
| ECDSA P-256 | ✅   | ✅     | <1% of keys |
| ECDSA P-384 | ✅   | ✅     | <1% of keys |
| ECDSA P-521 | ✅   | ✅     | <1% of keys |
| Ed448     | ⚠️     | ⚠️     | Blocked by cryptography library |
| DSA       | ❌     | ❌     | Deprecated (intentionally unsupported) |

**Coverage: 99.9%+ of real-world PPK files supported!**

### Other Limitations
- **Ed448**: Not supported by cryptography library (use Ed25519 instead for same security level)
- **DSA**: Intentionally not supported (deprecated since 2015, cryptographically insecure)
- **`--to-ssh` flag**: Linux only
- **Performance**: Install `argon2-cffi-bindings` for 590x faster PPK v3 encrypted key conversion

---

## 🤝 Contributing

Contributions welcome! See **[Contributing Guide](docs/development/contributing.md)**.

**Quick links:**
- [Report Bugs](https://github.com/badguy2003st/putty-migration-tools/issues)
- [Request Features](https://github.com/badguy2003st/putty-migration-tools/issues)
- [Development Setup](docs/development/contributing.md#development-setup)

---

## 📝 License

This project is licensed under the MIT License - see the [LICENSE](LICENSE) file for details.

---

## 🙏 Acknowledgments

- **[PuTTY](https://www.putty.org/)** - The legendary SSH client
- **[Textual](https://textual.textualize.io/)** - Modern TUI framework
- **[cryptography](https://cryptography.io/)** - Python cryptographic library
- **[argon2pure](https://pypi.org/project/argon2pure/)** - Pure Python Argon2 implementation
- **[Bitwarden](https://bitwarden.com/)** - Open-source password manager with SSH Agent
- **[Tabby](https://tabby.sh/)** - Modern, cross-platform terminal

---

## 🔗 Links

- **GitHub**: https://github.com/badguy2003st/putty-migration-tools
- **Issues**: https://github.com/badguy2003st/putty-migration-tools/issues
- **Releases**: https://github.com/badguy2003st/putty-migration-tools/releases

---

**Made with ❤️ for the SSH community**

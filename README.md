# 🔑 PuTTY Migration Tools

[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](https://opensource.org/licenses/MIT)
[![Python 3.8+](https://img.shields.io/badge/python-3.8+-blue.svg)](https://www.python.org/downloads/)
[![Platform](https://img.shields.io/badge/platform-Windows%20%7C%20Linux-lightgrey)](https://github.com/badguy2003st/putty-migration-tools)

Modern migration tools for PuTTY sessions and SSH keys. Migrate from PuTTY to **Bitwarden**, **Tabby**, or standard **OpenSSH** with both an interactive TUI and powerful CLI.

---

## ✨ Features

- 🖥️ **Interactive TUI** - Beautiful terminal interface for guided migrations
- ⌨️ **Powerful CLI** - Full automation with `convert`, `bitwarden`, `tabby`, `ssh-config` commands
- 🔐 **Bitwarden Export** - Store SSH keys in Bitwarden vault with SSH Agent support
- 📁 **PPK → OpenSSH Conversion** - Pure Python, cross-platform key conversion
- ⚙️ **SSH Config Generation** - Create OpenSSH config from PuTTY sessions
- 🎨 **Tabby Terminal Export** - Import sessions into Tabby terminal
- 🐧 **Linux ~/.ssh Import** - Direct import with intelligent conflict handling (rename/overwrite/skip)
- 🔒 **Security First** - Automatic file permissions (600/644), backup creation, no cloud uploads

---

## 📥 Quick Start (Binary - Recommended)

### 1. Download

Get the latest binary from [Releases](https://github.com/badguy2003st/putty-migration-tools/releases):

- **Windows**: `putty-migrate-v1.0.0-windows.exe`
- **Linux**: `putty-migrate-v1.0.0-linux`

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

# Run TUI
python -m tui

# Run CLI
python -m tui convert
```

**Documentation:**
- **[Python Installation Guide](docs/installation/python.md)**
- **[Python TUI Guide](docs/guides/python/tui.md)**
- **[Python CLI Guide](docs/guides/python/cli.md)**

---

## 🔒 Security

- **Local processing only** - No cloud uploads, all operations offline
- **Automatic permissions** - Private keys: 600, Public keys: 644
- **Backup safety** - Creates `.bak` files in overwrite mode
- **Memory cleanup** - Sensitive data cleared after operations

See **[Security Guide](docs/advanced/security.md)** for detailed best practices.

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
- **[puttykeys](https://pypi.org/project/puttykeys/)** - Pure Python PPK parser
- **[Bitwarden](https://bitwarden.com/)** - Open-source password manager with SSH Agent
- **[Tabby](https://tabby.sh/)** - Modern, cross-platform terminal

---

## 🔗 Links

- **GitHub**: https://github.com/badguy2003st/putty-migration-tools
- **Issues**: https://github.com/badguy2003st/putty-migration-tools/issues
- **Releases**: https://github.com/badguy2003st/putty-migration-tools/releases

---

**Made with ❤️ for the SSH community**

# Binary Installation

Download and install pre-built binaries for Windows or Linux.

---

## 📥 Download

Get the latest release from:
**[GitHub Releases](https://github.com/badguy2003st/putty-migration-tools/releases)**

Available binaries:
- `putty-migrate-v1.0.0-windows.exe` - Windows executable
- `putty-migrate-v1.0.0-linux` - Linux executable

---

## 🪟 Windows Setup

### 1. Download the Binary
```powershell
# Download from GitHub Releases
# https://github.com/badguy2003st/putty-migration-tools/releases
```

### 2. Run the Binary
```powershell
# Option 1: Direct execution (from Downloads folder)
.\putty-migrate-v1.0.0-windows.exe

# Option 2: Rename for convenience
Rename-Item putty-migrate-v1.0.0-windows.exe putty-migrate.exe
.\putty-migrate.exe
```

### 3. Optional: Add to PATH
For system-wide access:

```powershell
# Move to a permanent location
mkdir C:\Tools
Move-Item putty-migrate.exe C:\Tools\

# Add to PATH (PowerShell as Admin)
$env:Path += ";C:\Tools"
[Environment]::SetEnvironmentVariable("Path", $env:Path, "Machine")

# Now use from anywhere:
putty-migrate --version
```

---

## 🐧 Linux Setup

### 1. Download the Binary
```bash
# Download from GitHub Releases
wget https://github.com/badguy2003st/putty-migration-tools/releases/download/v1.0.0/putty-migrate-v1.0.0-linux
```

### 2. Make Executable
```bash
chmod +x putty-migrate-v1.0.0-linux

# Rename for convenience
mv putty-migrate-v1.0.0-linux putty-migrate
```

### 3. Run the Binary
```bash
# Run from current directory
./putty-migrate

# Or specify path
/path/to/putty-migrate --version
```

### 4. Optional: Install System-Wide
```bash
# Move to /usr/local/bin for system-wide access
sudo mv putty-migrate /usr/local/bin/

# Now use from anywhere:
putty-migrate --version
```

---

## ✅ Verification

Test that the binary works:

### Windows
```powershell
putty-migrate --version
# Output: putty-migrate 1.0.0

putty-migrate --help
# Shows available commands
```

### Linux
```bash
putty-migrate --version
# Output: putty-migrate 1.0.0

putty-migrate --help
# Shows available commands
```

---

## 🚀 Next Steps

- **[TUI Guide](../guides/binary/tui.md)** - Interactive interface usage
- **[CLI Guide](../guides/binary/cli.md)** - Command-line usage
- **[Feature Guides](../guides/)** - Detailed feature documentation

---

## 🔒 Security Notes

### Windows SmartScreen
Windows may show a warning for unsigned binaries:

1. Click "More info"
2. Click "Run anyway"

This is normal for new releases. Future versions may include code signing.

### Linux Permissions
The binary needs execute permissions (`chmod +x`) to run.

---

## ⚙️ Requirements

- **Windows**: Windows 10 or later (for PuTTY Registry access)
- **Linux**: Any modern distribution (for converted sessions)
- **No Python required** - Standalone binary includes all dependencies

---

## 🐍 Prefer Python?

If you want to run from source instead:
- **[Python Installation Guide](python.md)**

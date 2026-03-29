# CLI Guide (Binary Version)

Command-line interface for automation and scripting.

---

## 📖 Overview

The CLI provides powerful automation capabilities for all features.

```bash
putty-migrate COMMAND [OPTIONS]
```

**Available Commands:**
- `convert` - Convert PPK keys to OpenSSH format
- `bitwarden` - Export to Bitwarden SSH Key vault
- `tabby` - Export to Tabby terminal
- `ssh-config` - Generate SSH config file

---

## 🔑 convert - PPK Conversion

Convert `.ppk` files to OpenSSH format.

### Basic Usage

```bash
# Convert all PPK files (default directories)
putty-migrate convert
```

### Options

```bash
-i, --input DIR          PPK keys directory (default: ./ppk_keys)
-o, --output DIR         Output directory (default: ./openssh_keys)
--to-ssh                 Copy to ~/.ssh (Linux only)
--conflict MODE          Conflict resolution: rename|overwrite|skip (default: rename)
--password PASS          Password for encrypted PPK files
--dry-run                Preview without writing files
-v, --verbose            Verbose output
-h, --help               Show help message
```

### Examples

```bash
# Basic conversion
putty-migrate convert

# Custom input/output directories
putty-migrate convert -i C:\Keys -o C:\Converted

# Convert and copy to ~/.ssh (Linux)
putty-migrate convert --to-ssh

# Handle conflicts with rename mode
putty-migrate convert --to-ssh --conflict rename

# Overwrite existing keys (creates backups)
putty-migrate convert --to-ssh --conflict overwrite

# Skip if files exist
putty-migrate convert --to-ssh --conflict skip

# Dry run (preview only)
putty-migrate convert --dry-run

# Encrypted PPK files
putty-migrate convert --password "MySecretPassword"

# Verbose output
putty-migrate convert -v
```

### Output

**Standard Conversion:**
```
🔍 Found 3 PPK file(s)

🔄 Converting PPK files...
  [1/3] server.ppk
  [2/3] database.ppk
  [3/3] backup.ppk

══════════════════════════════════════════════════════════
  CONVERSION SUMMARY
══════════════════════════════════════════════════════════
✅ Successful: 3/3
══════════════════════════════════════════════════════════

✅ Converted keys saved to: ./openssh_keys
```

**Linux with --to-ssh:**
```
📁 Copying keys to ~/.ssh (conflict mode: rename)...

📋 SSH Copy Results:
   ✓ server (copied)
   ✓ server.pub (copied)
   ✓ database.1 (renamed)
   ✓ database.1.pub (renamed)

✅ Keys are now in ~/.ssh/
```

---

## 🔐 bitwarden - Bitwarden Export

Export PuTTY sessions to Bitwarden format.

### Basic Usage

```bash
# Export (requires converted OpenSSH keys)
putty-migrate bitwarden
```

### Options

```bash
-o, --output FILE        Output JSON file (default: bitwarden-export.json)
--ppk-dir DIR            PPK directory (default: ./ppk_keys)
--openssh-dir DIR        OpenSSH directory (default: ./openssh_keys)
--auto-convert           Auto-convert PPK files first
--auto-import            Automatically import to Bitwarden
--non-interactive        No prompts - export only
-v, --verbose            Verbose output
-h, --help               Show help message
```

### Examples

```bash
# Basic export (needs converted keys)
putty-migrate bitwarden

# Auto-convert PPKs first, then export
putty-migrate bitwarden --auto-convert

# Custom output file
putty-migrate bitwarden -o my-vault.json

# Custom directories
putty-migrate bitwarden --ppk-dir ./keys --openssh-dir ./converted

# Auto-import to Bitwarden
putty-migrate bitwarden --auto-import

# Non-interactive mode (for scripts)
putty-migrate bitwarden --non-interactive

# Verbose output
putty-migrate bitwarden --auto-convert -v
```

### Output

```
══════════════════════════════════════════════════════════
  PuTTY → Bitwarden SSH Key Export
══════════════════════════════════════════════════════════

📖 Reading PuTTY sessions from Registry...
   Found 10 session(s)

🔍 Filtering sessions with SSH key authentication...
   5 session(s) with SSH keys

📦 Generating Bitwarden export...

══════════════════════════════════════════════════════════
  EXPORT COMPLETE
══════════════════════════════════════════════════════════
  File: bitwarden-export.json
  Size: 12.4 KB
══════════════════════════════════════════════════════════

📥 Import to Bitwarden:

  1. Login to Bitwarden CLI:
     bw login

  2. Unlock vault:
     bw unlock

  3. Import the file:
     bw import bitwardenjson bitwarden-export.json

  4. Sync with web vault:
     bw sync

✅ Your SSH keys will be available in Bitwarden SSH Agent!
```

### Import to Bitwarden

After export, import using Bitwarden CLI:

```bash
# 1. Login
bw login

# 2. Unlock
bw unlock

# 3. Import
bw import bitwardenjson bitwarden-export.json

# 4. Sync
bw sync
```

**Configure SSH Agent:**
- See: [Bitwarden SSH Agent Guide](https://bitwarden.com/help/ssh-agent/#configure-bitwarden-ssh-agent)

---

## 🖥️ tabby - Tabby Terminal Export

Export PuTTY sessions to Tabby terminal format.

### Basic Usage

```bash
# Export all SSH sessions
putty-migrate tabby
```

### Options

```bash
-o, --output FILE        Output JSON file (default: tabby-config.json)
--merge FILE             Merge with existing Tabby config
-v, --verbose            Verbose output
-h, --help               Show help message
```

### Examples

```bash
# Basic export
putty-migrate tabby

# Custom output file
putty-migrate tabby -o my-tabby.json

# Merge with existing Tabby config
putty-migrate tabby --merge ~/.config/tabby/config.json

# Verbose output
putty-migrate tabby -v
```

### Output

```
══════════════════════════════════════════════════════════
  PuTTY → Tabby Terminal Export
══════════════════════════════════════════════════════════

📖 Reading PuTTY sessions from Registry...
   Found 10 session(s)

🔍 Found 8 SSH session(s)

📦 Generating Tabby configuration...

══════════════════════════════════════════════════════════
  EXPORT COMPLETE
══════════════════════════════════════════════════════════
  File: tabby-config.json
  Size: 8.2 KB
  Sessions: 8
══════════════════════════════════════════════════════════

📥 Import to Tabby:

  1. Open Tabby terminal
  2. Go to Settings → Plugins
  3. Install the "home" plugin (tabby-home)
  4. Restart Tabby if prompted
  5. Go to Tabby Home tab
  6. Click "Import Connection" (top right)
  7. Select: tabby-config.json

✅ Your PuTTY sessions will appear in Tabby!
```

---

## ⚙️ ssh-config - SSH Config Generator

Generate OpenSSH config file from PuTTY sessions.

### Basic Usage

```bash
# Generate SSH config
putty-migrate ssh-config
```

### Options

```bash
--ppk-dir DIR            PPK directory (default: ./ppk_keys)
--ssh-dir DIR            SSH directory (default: ~/.ssh)
--output FILE            Output file (default: ~/.ssh/config)
--no-backup              Don't backup existing SSH config
--non-interactive        Don't prompt for Pageant matches
--dry-run                Preview without writing files
-h, --help               Show help message
```

### Examples

```bash
# Basic generation
putty-migrate ssh-config

# Custom directories
putty-migrate ssh-config --ppk-dir ./keys --ssh-dir ~/.ssh

# Custom output location
putty-migrate ssh-config --output ~/.ssh/config.d/putty

# Don't backup existing config
putty-migrate ssh-config --no-backup

# Non-interactive mode
putty-migrate ssh-config --non-interactive

# Dry run (preview only)
putty-migrate ssh-config --dry-run
```

### Output

**Dry Run:**
```
🔍 DRY RUN MODE - Preview of SSH config:

Host production-server
    HostName 192.168.1.10
    User admin
    Port 22
    IdentityFile ~/.ssh/production

Host dev-server
    HostName dev.example.com
    User developer
    IdentityFile ~/.ssh/dev_key

ℹ️  Dry run complete. No files were modified.
   Remove --dry-run to write the SSH config.
```

**Actual Run:**
```
══════════════════════════════════════════════════════════
  SUMMARY
══════════════════════════════════════════════════════════
  Keys Processed:
    ✅ From ppk_keys/: 3
    🆕 From Registry:  2
    📋 Total Unique:   5

  Sessions Processed:
    📋 Total:         8
══════════════════════════════════════════════════════════

📖 Next steps:
   1. Review the generated SSH config:
      cat ~/.ssh/config

   2. Test SSH connection:
      ssh <host-alias>

   3. Convert PPK keys if needed:
      putty-migrate convert
```

---

## 🤖 Automation Examples

### Batch Processing Script (Bash)

```bash
#!/bin/bash
# Migrate all PuTTY configurations

# 1. Convert PPK keys and copy to ~/.ssh
putty-migrate convert --to-ssh --conflict rename

# 2. Export to Bitwarden
putty-migrate bitwarden --auto-convert --non-interactive

# 3. Generate SSH config
putty-migrate ssh-config --non-interactive

# 4. Export to Tabby
putty-migrate tabby

echo "✅ Migration complete!"
```

### PowerShell Script (Windows)

```powershell
# Automated PuTTY migration
$ErrorActionPreference = "Stop"

# Convert PPK keys
& putty-migrate convert -v

# Export to Bitwarden
& putty-migrate bitwarden --auto-convert

# Export to Tabby
& putty-migrate tabby -o "C:\Backups\tabby-backup.json"

Write-Host "✅ All exports complete!" -ForegroundColor Green
```

### CI/CD Integration (GitHub Actions)

```yaml
name: Backup PuTTY Sessions

on:
  schedule:
    - cron: '0 2 * * 0'  # Weekly backup

jobs:
  backup:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v3
      
      - name: Download PuTTY Migration Tools
        run: |
          wget https://github.com/badguy2003st/putty-migration-tools/releases/download/v1.0.0/putty-migrate-v1.0.0-linux
          chmod +x putty-migrate-v1.0.0-linux
      
      - name: Export configurations
        run: |
          ./putty-migrate-v1.0.0-linux convert --dry-run
          ./putty-migrate-v1.0.0-linux tabby -o backup.json
      
      - name: Upload artifacts
        uses: actions/upload-artifact@v3
        with:
          name: putty-backups
          path: backup.json
```

---

## 💡 Tips & Best Practices

1. **Use --dry-run first** to preview changes
2. **Combine with --verbose** for troubleshooting
3. **Script with --non-interactive** for automation
4. **Always backup** before using `--conflict overwrite`
5. **Use --auto-convert** with bitwarden for convenience

---

## 🚀 Next Steps

- **[TUI Guide](tui.md)** - Interactive interface
- **[PPK Conversion Guide](../convert-ppk.md)** - Detailed conversion info
- **[Bitwarden Guide](../bitwarden.md)** - Complete Bitwarden workflow
- **[Tabby Guide](../tabby.md)** - Tabby setup guide
- **[Automation Guide](../../advanced/automation.md)** - Advanced scripting

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
--password PASS          Password for single encrypted PPK
--password-file FILE     File with passwords to try (v1.1.0)
--no-encryption          Disable re-encryption (v1.1.0: encrypted → unencrypted)
--dry-run                Preview without writing files
-v, --verbose            Verbose output (shows which password worked)
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

# Encrypted PPK with single password
putty-migrate convert --password "MySecretPassword"

# Encrypted PPK with password file (v1.1.0)
putty-migrate convert --password-file passwords.txt -v

# Verbose output (shows which password worked)
putty-migrate convert -v

# Disable re-encryption (v1.1.0: keys become unencrypted)
putty-migrate convert --no-encryption
```

### Re-encryption (v1.1.0) 🔐

**Default Behavior (Secure!):**
Encrypted PPK keys stay encrypted in OpenSSH format.

```bash
# Encrypted PPK → Encrypted OpenSSH (automatic!)
putty-migrate convert --password mypassword

# Result: OpenSSH key is re-encrypted with same password
```

**Disable Re-encryption:**
```bash
# Encrypted PPK → Unencrypted OpenSSH
putty-migrate convert --password mypassword --no-encryption
```

**Multi-Password with Re-encryption:**
```bash
# Each key re-encrypted with its successful password
putty-migrate convert --password-file passwords.txt

# key1.ppk (password #1) → key1 (encrypted with password #1)
# key2.ppk (password #3) → key2 (encrypted with password #3)
# key3.ppk (unencrypted) → key3 (unencrypted)
```

### Encrypted PPK Files (v1.1.0)

#### Auto-Load passwords.txt

The CLI automatically loads `ppk_keys/passwords.txt` if it exists:

**Setup:**
```bash
# 1. Create passwords.txt
cat > ppk_keys/passwords.txt << 'EOF'
password123
mySecretPass
#hashtagPassword
EOF

# 2. Run conversion (auto-loads passwords.txt)
putty-migrate convert

# Output:
# ✅ Auto-loaded 3 password(s) from passwords.txt
# [1/5] server.ppk
# [2/5] database.ppk...
```

**Format Rules:**
- One password per line
- No comments (# is part of password!)
- Empty lines ignored
- Spaces are preserved

#### Custom Password File

Use a different password file:

```bash
# Specify custom file
putty-migrate convert --password-file ~/my-passwords.txt -v

# Verbose shows which password worked:
# ✓ server.ppk (password #2)
# ✓ database.ppk (unencrypted)
# ✓ production.ppk (password #1)
```

#### Password Priority

When multiple password sources are available:

1. **--password** (CLI argument) - Highest priority, overrides all
2. **--password-file** (custom file) - If specified, skips auto-load
3. **passwords.txt** (auto-load) - Default if exists
4. **No password** - Only unencrypted keys work

**Examples:**
```bash
# Use auto-loaded passwords.txt
putty-migrate convert

# Override with custom file
putty-migrate convert --password-file ~/other.txt

# Override with single password
putty-migrate convert --password "direct_password"
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

## 📦 export-all - Export All to ZIP (v1.1.1)

### Windows Only

Create complete migration package with all PuTTY data in one command.

### Basic Usage

```bash
# Auto-generated filename (putty-migration-export-YYYYMMDD-HHMMSS.zip)
putty-migrate export-all

# Custom output file
putty-migrate export-all -o my-export.zip
```

### Options

```bash
-o, --output FILE        Output ZIP file (default: auto-generated timestamp)
--password-file FILE     Password file for encrypted PPKs (default: ./ppk_keys/passwords.txt)
--dry-run                Preview without creating ZIP
-v, --verbose            Verbose output with detailed progress
-h, --help               Show help message
```

### What Gets Exported

The ZIP package contains:
- ✅ **openssh_keys/** - All PPK files converted to OpenSSH format
- ✅ **ssh-config** - OpenSSH configuration for all sessions
- ✅ **tabby-config.json** - Tabby terminal configuration
- ✅ **bitwarden-export.json** - Bitwarden vault export (Type 5)
- ✅ **MANIFEST.json** - Metadata (counts, encryption status, timestamps)
- ✅ **README.txt** - Import instructions for Linux

### Examples

```bash
# Basic export with auto-generated filename
putty-migrate export-all

# Output: putty-migration-export-20260407-170000.zip

# Custom output location
putty-migrate export-all -o C:\Backups\putty-full-export.zip

# With password file for encrypted PPKs
putty-migrate export-all --password-file C:\secure\passwords.txt

# Dry run (preview without creating ZIP)
putty-migrate export-all --dry-run

# Verbose output (see each step)
putty-migrate export-all -v
```

### Output

```
📦 Creating Export Package...

✅ Loaded 3 password(s)
✅ Converted 15 PPK keys (3 encrypted, 12 unencrypted)
✅ Generated SSH Config (18 sessions)
✅ Generated Tabby config (18 hosts)
✅ Generated Bitwarden export (18 items)
✅ Created ZIP archive

══════════════════════════════════════════════════════════
  EXPORT COMPLETE
══════════════════════════════════════════════════════════
  ZIP File: putty-migration-export-20260407-170000.zip
  Size: 45.2 KB
  
  Contents:
  • 15 SSH keys (3 encrypted, 12 unencrypted)
  • 18 session configurations
  • Tabby terminal config
  • Bitwarden vault export
══════════════════════════════════════════════════════════

📋 Next Steps:
  1. Copy ZIP to your Linux machine:
     scp putty-migration-export-*.zip user@linux:~/
  
  2. Import on Linux:
     putty-migrate import-all export.zip --all
```

---

## 📥 import-all - Import from ZIP (v1.1.1)

### Linux Only

Import Windows export package with selective component import.

### Basic Usage

```bash
# Import everything
putty-migrate import-all export.zip --all

# Selective import
putty-migrate import-all export.zip --ssh-keys --ssh-config
```

### Options

```bash
ZIP_FILE                 Input ZIP file (required)
--ssh-keys               Import SSH keys to ~/.ssh
--ssh-config             Import SSH config to ~/.ssh/config
--bitwarden              Handle Bitwarden export
--all                    Import everything (implies all above)
--conflict MODE          Conflict handling: rename|overwrite|skip (default: rename)
--bw-auto-import         Automatically run 'bw import' command (requires BW_SESSION)
--dry-run                Preview without importing
-v, --verbose            Verbose output
-h, --help               Show help message
```

### What Can Be Imported

Choose any combination:
- ✅ **SSH Keys** → `~/.ssh/` (with conflict handling)
- ✅ **SSH Config** → `~/.ssh/config` (with backup)
- ✅ **Bitwarden** → Auto-import or manual instructions

### Examples

```bash
# Import everything with default settings
putty-migrate import-all putty-migration-export-20260407-170000.zip --all

# Import only SSH keys (rename conflicts)
putty-migrate import-all export.zip --ssh-keys --conflict rename

# Import only SSH config
putty-migrate import-all export.zip --ssh-config

# Import SSH keys + config (skip conflicts)
putty-migrate import-all export.zip --ssh-keys --ssh-config --conflict skip

# Import with Bitwarden auto-import (requires BW_SESSION)
export BW_SESSION=$(bw unlock --raw)
putty-migrate import-all export.zip --all --bw-auto-import

# Dry run (preview)
putty-migrate import-all export.zip --all --dry-run

# Verbose output
putty-migrate import-all export.zip --all -v
```

### Conflict Modes (SSH Keys)

#### Rename (Default)
```bash
putty-migrate import-all export.zip --ssh-keys --conflict rename
```
- Existing: `unraid31`, `unraid31.pub`
- Imported as: `unraid31.2`, `unraid31.2.pub`
- **Safe:** Original files preserved

#### Overwrite
```bash
putty-migrate import-all export.zip --ssh-keys --conflict overwrite
```
- Existing files backed up as `.bak`
- Imported files replace originals
- **Careful:** Review backups before deleting

#### Skip
```bash
putty-migrate import-all export.zip --ssh-keys --conflict skip
```
- Existing files untouched
- Only new keys imported
- **Safe:** No overwrites

### Bitwarden Import

#### Manual Import (Default)
```bash
putty-migrate import-all export.zip --bitwarden
```
- Copies `bitwarden-export.json` to current directory
- Shows manual import instructions:
  ```
  Run:
    bw import bitwardenjson bitwarden-export.json
    bw sync
  ```

#### Auto-Import (Requires BW_SESSION)
```bash
# 1. Unlock Bitwarden first
export BW_SESSION=$(bw unlock --raw)

# 2. Import with auto-import flag
putty-migrate import-all export.zip --bitwarden --bw-auto-import
```
- Automatically runs `bw import`
- Automatically runs `bw sync`
- Shows success/failure status

### Output

```
📥 Importing from ZIP...

✅ Extracted package
✅ Validated structure (v1.1.1, 15 keys, 18 sessions)

Import Options:
  • SSH Keys (rename mode)
  • SSH Config
  • Bitwarden (manual)

🔑 Importing SSH keys...
   Copied 15 key pairs to ~/.ssh/
   3 renamed (conflicts)

⚙️  Importing SSH config...
   Added 18 entries to ~/.ssh/config
   Backup: ~/.ssh/config.bak

🔐 Bitwarden export ready...
   File: bitwarden-export.json

══════════════════════════════════════════════════════════
  IMPORT COMPLETE
══════════════════════════════════════════════════════════

SSH Keys:
  • 15 key pairs imported to ~/.ssh/
  • 3 renamed (conflicts)
  • Permissions: 600 (private), 644 (public)

SSH Config:
  • 18 entries added
  • Backup: ~/.ssh/config.bak

Bitwarden:
  • File ready: bitwarden-export.json
  • Run: bw import bitwardenjson bitwarden-export.json
         bw sync
══════════════════════════════════════════════════════════
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

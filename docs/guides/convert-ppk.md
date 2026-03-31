# PPK Conversion Guide

Complete guide to converting PuTTY Private Key (PPK) files to OpenSSH format.

---

## 📖 Overview

### What are PPK Files?

PPK (PuTTY Private Key) is PuTTY's proprietary format for SSH private keys. While secure and feature-rich, PPK files are only compatible with PuTTY and related tools.

### Why Convert to OpenSSH?

OpenSSH format is the universal standard for SSH keys:
- ✅ Works with native `ssh` command (Linux, Windows 10+)
- ✅ Compatible with VS Code, IDEs, and development tools
- ✅ Supported by Git, Docker, and cloud platforms
- ✅ Can be stored in Bitwarden SSH Agent
- ✅ Industry standard format

---

## 🚀 Basic Conversion

### Binary Version

```bash
# Convert all PPK files in ./ppk_keys/
putty-migrate convert
```

### Python Version

```bash
# Same functionality
python -m tui convert
```

### What Happens?

1. Scans `./ppk_keys/` directory for `.ppk` files
2. Converts each to OpenSSH format (pure Python, no external tools)
3. Outputs to `./openssh_keys/` directory
4. Generates both private key and `.pub` public key
5. Sets secure permissions (600 for private, 644 for public)

---

## 📁 Directory Structure

```
putty-migration-tools/
├── ppk_keys/              # Place your .ppk files here
│   ├── server.ppk
│   ├── database.ppk
│   └── backup.ppk
│
└── openssh_keys/          # Converted keys output here
    ├── server             # Private key (600)
    ├── server.pub         # Public key (644)
    ├── database
    ├── database.pub
    ├── backup
    └── backup.pub
```

---

## ⚙️ Advanced Options

### Custom Directories

```bash
# Custom input and output paths
putty-migrate convert -i /path/to/ppk -o /path/to/output

# Example: Windows
putty-migrate convert -i C:\Keys\PPK -o C:\Keys\OpenSSH

# Example: Linux
putty-migrate convert -i ~/Documents/keys -o ~/converted
```

### Encrypted PPK Files (v1.1.0)

#### Method 1: passwords.txt (Recommended)

The tool automatically creates and uses `ppk_keys/passwords.txt`:

**Location:** `ppk_keys/passwords.txt`

**Format:**
```
One password per line (no comments allowed)
All characters including # are part of the password
Empty lines are ignored

mypassword123
#hashtagPassword
password with spaces
```

**First-Time Setup:**
```bash
# Run tool once to create template
putty-migrate convert
# → Creates ppk_keys/ and passwords.txt template

# Edit the file and add your passwords
notepad ppk_keys\passwords.txt  # Windows
nano ppk_keys/passwords.txt     # Linux
```

**Auto-Load Behavior:**
- **CLI**: Automatically loads if exists
- **TUI**: Automatically loads if exists
- Tries all passwords sequentially
- Shows which password worked (with `-v`)

#### Method 2: TUI Password Dialog

If passwords.txt doesn't contain the right password, TUI shows an interactive dialog:

**Options:**
1. **Try Password** - Enter password manually and retry
2. **Skip This File** - Skip and continue with next file
3. **Cancel & Edit** - Stop batch, edit passwords.txt

**Workflow:**
1. Add .ppk files to `ppk_keys/`
2. Run TUI: `putty-migrate`
3. Select "Convert PPK Keys"
4. If password needed → Dialog shows
5. Enter password or choose option

#### Method 3: CLI Flags

**Direct Password:**
```bash
# Single password for all encrypted files
putty-migrate convert --password "YourPassword"
```

**Custom Password File:**
```bash
# Use different file (one password per line)
putty-migrate convert --password-file ~/my-passwords.txt -v

# Verbose shows which password worked:
# ✓ server.ppk (password #2)
# ✓ database.ppk (unencrypted)
```

**Password Priority:**
1. `--password` (CLI argument) - Highest priority
2. `--password-file` (custom file) - If specified
3. `passwords.txt` (auto-load) - Default
4. No password - Only unencrypted keys work

**Security Note:** Avoid passwords in shell history - use passwords.txt or TUI dialog

### Dry Run (Preview)

Preview what will be converted without making changes:

```bash
putty-migrate convert --dry-run
```

Output:
```
🔍 DRY RUN MODE - Preview:

  server.ppk → openssh_keys/server
  database.ppk → openssh_keys/database
  backup.ppk → openssh_keys/backup

ℹ️  Files would be written to: ./openssh_keys
Remove --dry-run to perform actual conversion
```

---

## 🐧 Linux: Copy to ~/.ssh

On Linux, you can automatically copy converted keys to `~/.ssh/`:

```bash
putty-migrate convert --to-ssh
```

This enables immediate use with the native `ssh` command.

### Conflict Handling

When a key already exists in `~/.ssh/`, you have three options:

#### 1. Rename Mode (Default)

Adds numeric suffix to avoid overwriting:

```bash
putty-migrate convert --to-ssh --conflict rename
```

**Result:**
```
~/.ssh/
├── mykey           # Original (untouched)
├── mykey.pub       # Original (untouched)
├── mykey.1         # New (from conversion)
├── mykey.1.pub     # New
├── server.2        # New (already had .1)
└── server.2.pub
```

**Use Case:** Keep both old and new versions for comparison or transition period.

#### 2. Overwrite Mode

Replaces existing keys with automatic backups:

```bash
putty-migrate convert --to-ssh --conflict overwrite
```

**Result:**
```
~/.ssh/
├── mykey           # NEW (replaced)
├── mykey.pub       # NEW (replaced)
├── mykey.bak       # Original backup
├── mykey.pub.bak   # Original backup
├── server
├── server.pub
├── server.bak
└── server.pub.bak
```

**Use Case:** Replacing old keys with new ones, with safety backups.

⚠️ **Warning:** Always verify backups before deleting!

#### 3. Skip Mode

Don't copy if file already exists:

```bash
putty-migrate convert --to-ssh --conflict skip
```

**Result:**
```
~/.ssh/
├── mykey           # Original (kept, not replaced)
└── mykey.pub       # Original (kept, not replaced)

openssh_keys/
├── mykey           # NEW key only saved here
└── mykey.pub
```

**Use Case:** Only add new keys, don't touch existing ones.

---

## 📊 Output & Verification

### Standard Output

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

### Verify Conversion

```bash
# Check file permissions
ls -l openssh_keys/
# Private keys should be 600 (-rw-------)
# Public keys should be 644 (-rw-r--r--)

# View public key
cat openssh_keys/server.pub
# Should show "ssh-rsa AAAA..." or "ssh-ed25519 AAAA..."

# Test with SSH (if copied to ~/.ssh)
ssh -i ~/.ssh/server user@hostname
```

---

## 🔒 Security Best Practices

### File Permissions

The tool automatically sets:
- **Private keys**: `600` (owner read/write only)
- **Public keys**: `644` (readable by all, writable by owner)

**Never** make private keys world-readable!

### Original PPK Files

After successful conversion:

1. ✅ **Verify** all converted keys work
2. ✅ **Backup** original `.ppk` files securely
3. ✅ **Test** SSH connections with new keys
4. ✅ **Delete** original `.ppk` files only after verification

```bash
# Create secure backup
tar -czf ppk-backup-$(date +%Y%m%d).tar.gz ppk_keys/
gpg --encrypt ppk-backup-*.tar.gz

# After testing, optionally remove originals
# rm -rf ppk_keys/*.ppk  # Only when you're sure!
```

### Encrypted Storage

Consider encrypting converted keys:

```bash
# Encrypt private key with GPG
gpg --encrypt --recipient you@example.com openssh_keys/server

# Decrypt when needed
gpg --decrypt openssh_keys/server.gpg > ~/.ssh/server
chmod 600 ~/.ssh/server
```

---

## 🐛 Troubleshooting

### "No .ppk files found"

**Solution:**
```bash
# Create directory and add files
mkdir -p ppk_keys
cp /path/to/*.ppk ppk_keys/

# Verify
ls ppk_keys/
```

### "Conversion failed: Invalid PPK file"

**Causes:**
- Corrupted PPK file
- Unsupported PPK format version
- File is not actually a PPK file

**Solution:**
```bash
# Check file type
file ppk_keys/mykey.ppk
# Should show "PuTTY Private Key File"

# Try opening in PuTTYgen to verify
# If PuTTYgen can't open it, file is corrupt

# Re-export from PuTTY if needed
```

### "Password required"

If PPK is encrypted but no password provided:

```bash
# Use TUI for interactive prompt
putty-migrate  # Select convert, enter password in UI

# Or provide via CLI
putty-migrate convert --password "YourPassword"
```

### Permission Denied (Linux)

```bash
# Fix ~/.ssh permissions
chmod 700 ~/.ssh

# Fix individual key permissions
chmod 600 ~/.ssh/your_private_key
chmod 644 ~/.ssh/your_private_key.pub
```

---

## 💡 Tips & Tricks

### Batch Processing

```bash
# Convert and immediately copy to ~/.ssh
putty-migrate convert --to-ssh --conflict rename -v
```

### Integration with Git

After conversion:

```bash
# Use new SSH key with Git
git config core.sshCommand "ssh -i ~/.ssh/github"

# Or add to ~/.ssh/config:
echo "Host github.com
    IdentityFile ~/.ssh/github" >> ~/.ssh/config
```

### Automation

```bash
#!/bin/bash
# Automated key conversion and backup

# Convert
putty-migrate convert --to-ssh --conflict rename

# Backup originals
tar -czf ~/Backups/ppk-$(date +%Y%m%d).tar.gz ppk_keys/

# Test connection
if ssh -i ~/.ssh/server user@host echo "OK"; then
    echo "✅ Conversion successful!"
else
    echo "❌ Test failed, check logs"
fi
```

---

## 🚀 Next Steps

- **[Bitwarden Guide](bitwarden.md)** - Store keys in Bitwarden vault
- **[SSH Config Guide](ssh-config.md)** - Create OpenSSH config
- **[Tabby Guide](tabby.md)** - Import to Tabby terminal
- **[CLI Guide](binary/cli.md)** - All CLI options

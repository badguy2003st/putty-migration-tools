# SSH Config Generation Guide

Generate OpenSSH config files from PuTTY sessions for native `ssh` command usage.

---

## 📖 Overview

OpenSSH config files (`~/.ssh/config`) allow you to create aliases for SSH connections, making them accessible via the native `ssh` command.

### Benefits

- ✅ Works with native `ssh` command (Windows 10+, Linux)
- ✅ Compatible with all SSH tools (Git, VS Code, Docker, etc.)
- ✅ No GUI required - perfect for servers
- ✅ Universal standard format
- ✅ Easy to version control

---

## 🚀 Generate SSH Config

### Binary Version

```bash
# Generate SSH config file
putty-migrate ssh-config

# Dry run (preview only)
putty-migrate ssh-config --dry-run

# Custom output location
putty-migrate ssh-config --output ~/.ssh/config.d/putty
```

### Python Version

```bash
# Same functionality
python -m tui ssh-config
python -m tui ssh-config --dry-run
```

### What Happens?

The tool:
1. Reads PuTTY sessions from Windows Registry
2. Matches sessions with converted SSH keys
3. Generates OpenSSH config entries
4. Writes to `~/.ssh/config` (or custom location)
5. Creates backup if file exists

---

## 📝 Generated Config Format

### Example Config

```ssh-config
# Generated from PuTTY session: Production Server
Host production-server
    HostName 192.168.1.10
    User admin
    Port 22
    IdentityFile ~/.ssh/production

# Generated from PuTTY session: Development
Host dev-server
    HostName dev.example.com
    User developer
    Port 2222
    IdentityFile ~/.ssh/dev_key

# Generated from PuTTY session: Backup Server
Host backup
    HostName backup.company.com
    User root
    IdentityFile ~/.ssh/backup
```

### Using the Config

```bash
# Connect using alias
ssh production-server
ssh dev-server
ssh backup

# Instead of full command:
# ssh -i ~/.ssh/production admin@192.168.1.10
```

---

## ⚙️ Advanced Options

### Custom Directories

```bash
# Specify custom PPK and SSH directories
putty-migrate ssh-config \
  --ppk-dir ./keys \
  --ssh-dir ~/.ssh \
  --output ~/.ssh/config
```

### Dry Run (preview)

Preview the config without writing files:

```bash
putty-migrate ssh-config --dry-run
```

Output:
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
    Port 2222
    IdentityFile ~/.ssh/dev_key

ℹ️  Dry run complete. No files were modified.
   Remove --dry-run to write the SSH config.
```

### No Backup

Skip backup creation (use with caution):

```bash
putty-migrate ssh-config --no-backup
```

### Non-Interactive Mode

For automation - skip all prompts:

```bash
putty-migrate ssh-config --non-interactive
```

---

## 📁 Config File Management

### Default Location

- **Linux**: `~/.ssh/config`
- **Windows**: `C:\Users\YourName\.ssh\config`

### Backup Strategy

The tool automatically backs up existing config:

```
~/.ssh/
├── config           # Current config (updated)
└── config.backup    # Previous config (backup)
```

### Multiple Config Files

You can organize configs into separate files:

```bash
# Generate PuTTY-specific config
putty-migrate ssh-config --output ~/.ssh/config.d/putty

# Include in main config:
echo "Include config.d/*" >> ~/.ssh/config
```

Directory structure:
```
~/.ssh/
├── config           # Main config with Include directive
└── config.d/
    ├── putty        # PuTTY sessions
    ├── personal     # Personal servers
    └── work         # Work servers
```

---

## 🔑 SSH Key Integration

### Prerequisites

Convert PPK keys before generating config:

```bash
# Convert PPK keys
putty-migrate convert

# Linux: Copy to ~/.ssh
putty-migrate convert --to-ssh --conflict rename

# Then generate config
putty-migrate ssh-config
```

### Key Matching

The tool automatically matches:
1. **PPK files** in `./ppk_keys/` → Suggests OpenSSH equivalent
2. **Registry key paths** → Converts to OpenSSH paths
3. **Pageant keys** → Prompts for key file location (interactive)

---

## 📊 Example Output

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

## 🎯 Usage Examples

### Basic Connection

```bash
# After config generation
ssh production-server
# Automatically uses: admin@192.168.1.10 with ~/.ssh/production key
```

### With Git

```bash
# Configure Git to use SSH config
git clone ssh://git@production-server/repo.git

# Or set remote
git remote add origin ssh://git@dev-server/path/to/repo.git
```

### With VS Code Remote

VS Code automatically uses `~/.ssh/config`:

1. Install "Remote - SSH" extension
2. Open Command Palette (Ctrl+Shift+P)
3. Select "Remote-SSH: Connect to Host..."
4. Your aliases appear in the list!

### With SCP/SFTP

```bash
# Copy files using alias
scp file.txt production-server:/path/to/destination

# SFTP
sftp production-server
```

---

## 🔧 Advanced SSH Config Options

### Add Custom Options

Edit generated config to add more options:

```ssh-config
Host production-server
    HostName 192.168.1.10
    User admin
    Port 22
    IdentityFile ~/.ssh/production
    
    # Add custom options:
    ServerAliveInterval 60
    ServerAliveCountMax 3
    Compression yes
    ForwardAgent yes
```

### Wildcards and Patterns

```ssh-config
# Match multiple hosts
Host *.example.com
    User developer
    IdentityFile ~/.ssh/company_key

# Specific override
Host production.example.com
    User admin
    IdentityFile ~/.ssh/prod_key
```

### ProxyJump (Bastion Hosts)

```ssh-config
# Jump through bastion
Host internal-server
    HostName 10.0.1.50
    User admin
    ProxyJump bastion

Host bastion
    HostName bastion.example.com
    User jump
```

---

## 🐛 Troubleshooting

### "PuTTY Registry not accessible"

**Cause:** Tool requires Windows for Registry reading.

**Solution:**
- Ensure you're on Windows
- Verify PuTTY is installed
- Check PuTTY has saved sessions

### "No sessions found to export"

**Solution:**
```bash
# Verify PuTTY sessions exist
reg query "HKCU\Software\SimonTatham\PuTTY\Sessions"

# Check sessions are SSH protocol (not Serial, etc.)
```

### "Permission denied" when connecting

**Solution:**
```bash
# Fix config file permissions
chmod 644 ~/.ssh/config

# Fix key permissions
chmod 600 ~/.ssh/your_key
chmod 644 ~/.ssh/your_key.pub

# Fix ~/.ssh directory
chmod 700 ~/.ssh
```

### Config Not Being Used

**Solution:**
```bash
# Verify SSH reads the config
ssh -v production-server 2>&1 | grep "config"

# Check config syntax
ssh -G production-server
# Should show resolved config for this host
```

### Key Not Found

```bash
# Verify key paths in config
cat ~/.ssh/config | grep IdentityFile

# Check keys exist
ls -la ~/.ssh/

# Convert PPK if needed
putty-migrate convert --to-ssh
```

---

## 💡 Tips & Best Practices

### Use Short Aliases

```ssh-config
# Bad: long and hard to remember
Host production-server-on-aws-east

# Good: short and memorable
Host prod
    HostName production-server-on-aws-east.example.com
```

### Group Related Servers

```ssh-config
# Development servers
Host dev-* staging-*
    User developer
    IdentityFile ~/.ssh/dev_key

# Production servers
Host prod-*
    User admin
    IdentityFile ~/.ssh/prod_key
    StrictHostKeyChecking yes
```

### Version Control

```bash
# Keep config in Git
cd ~/.ssh
git init
echo "*.pem" >> .gitignore
echo "*_key" >> .gitignore
git add config
git commit -m "Add SSH config"

# Or use dotfiles repo
```

### Regular Backups

```bash
# Backup before regenerating
cp ~/.ssh/config ~/.ssh/config.$(date +%Y%m%d)

# Then regenerate
putty-migrate ssh-config
```

---

## 🔄 Workflow

### Complete Setup

```bash
# 1. Convert PPK keys
put ty-migrate convert --to-ssh --conflict rename

# 2. Generate SSH config
putty-migrate ssh-config

# 3. Test connection
ssh production-server

# 4. Customize config if needed
vim ~/.ssh/config
```

---

## 🆚 SSH Config vs Other Solutions

### vs PuTTY
- ✅ Works without GUI
- ✅ Platform-independent format
- ✅ Better for automation
- ❌ No saved passwords (use keys!)

### vs Tabby
- ✅ Lightweight (no GUI needed)
- ✅ Works on servers
- ❌ No visual management
- ❌ Manual editing required

### vs Bitwarden SSH Agent
- ✅ Simple, file-based
- ✅ No external services
- ❌ No cross-device sync
- ❌ Manual key management

**Best Approach:** Use config for basics, combine with Tabby (GUI) or Bitwarden (sync) as needed!

---

## 🚀 Next Steps

- **[PPK Conversion Guide](convert-ppk.md)** - Convert keys for SSH config
- **[Bitwarden Guide](bitwarden.md)** - Alternative with SSH Agent
- **[Tabby Guide](tabby.md)** - GUI terminal with session management
- **[CLI Guide](binary/cli.md)** - All CLI options

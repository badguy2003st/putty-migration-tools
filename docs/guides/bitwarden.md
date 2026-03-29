# Bitwarden Export Guide

Export PuTTY sessions to Bitwarden SSH Key vault with SSH Agent integration.

---

## 📖 Overview

Bitwarden now supports SSH Key storage (Type 5 items) and provides an integrated SSH Agent for seamless authentication.

### Benefits

- ✅ Centralized SSH key management
- ✅ Cross-device synchronization
- ✅ Built-in SSH Agent
- ✅ Secure vault storage
- ✅ No need to manage `~/.ssh` manually

---

## 📋 Prerequisites

### 1. Bitwarden CLI

Install the Bitwarden command-line tool:

**Windows:**
```powershell
# Using winget (recommended)
winget install Bitwarden.CLI

# Or using Chocolatey
choco install bitwarden-cli
```

**Linux:**
```bash
# Using npm (recommended)
npm install -g @bitwarden/cli

# Or direct download from official website
wget "https://bitwarden.com/download/?app=cli&platform=linux" -O bw.zip
unzip bw.zip
chmod +x bw
sudo mv bw /usr/local/bin/
bw --version
```

### 2. Converted OpenSSH Keys

Bitwarden requires OpenSSH format (not PPK):

```bash
# If you haven't converted yet:
putty-migrate convert

# Or use auto-convert during export:
putty-migrate bitwarden --auto-convert
```

---

## 🚀 Export Process

### Binary Version

```bash
# Basic export (requires converted keys in ./openssh_keys/)
putty-migrate bitwarden

# Auto-convert PPKs first
putty-migrate bitwarden --auto-convert

# Custom output file
putty-migrate bitwarden -o my-vault.json
```

### Python Version

```bash
# Same commands, different prefix
python -m tui bitwarden --auto-convert
```

### What Gets Exported?

The tool:
1. Reads PuTTY sessions from Windows Registry
2. Filters sessions using SSH key authentication
3. Matches sessions with converted OpenSSH keys
4. Generates `bitwarden-export.json` with:
   - Session name as item name
   - SSH private key
   - SSH public key
   - Hostname/username metadata

---

## 📥 Import to Bitwarden

After generating the export file, import it to your Bitwarden vault:

### Step 1: Login

```bash
bw login
# Enter your master password
```

### Step 2: Unlock Vault

```bash
bw unlock
# Copy the export session key
```

### Step 3: Import

```bash
# Import the generated JSON
bw import bitwardenjson bitwarden-export.json
```

### Step 4: Sync

```bash
# Sync with web vault
bw sync
```

### Verify Import

```bash
# List SSH keys in vault
bw list items --search "ssh"

# Or view in web vault: https://vault.bitwarden.com
```

---

## 🔐 Configure Bitwarden SSH Agent

After importing keys, enable the SSH Agent for seamless authentication.

### Official Documentation

**Complete setup guide:**  
[Bitwarden SSH Agent Configuration](https://bitwarden.com/help/ssh-agent/#configure-bitwarden-ssh-agent)

### Quick Setup Overview

1. **Enable SSH Agent** in Bitwarden desktop/browser settings
2. **Configure SSH** to use Bitwarden agent
3. **Test authentication** with your servers

The official guide covers:
- Platform-specific setup (Windows/Linux)
- SSH agent socket configuration
- Key selection and management
- Troubleshooting common issues

---

## ⚙️ Advanced Options

### Auto-Convert PPK Files

```bash
# Convert PPKs and export in one command
putty-migrate bitwarden --auto-convert
```

This will:
1. Scan `./ppk_keys/` for PPK files
2. Convert all to OpenSSH format
3. Export sessions with matching keys

### Custom Directories

```bash
# Specify custom paths
putty-migrate bitwarden \
  --ppk-dir ./my-keys \
  --openssh-dir ./converted \
  -o vault-backup.json
```

### Non-Interactive Mode

For automation/scripts:

```bash
# Skip all prompts
putty-migrate bitwarden --auto-convert --non-interactive
```

### Auto-Import

```bash
# Automatically import after export (requires bw CLI in PATH)
putty-migrate bitwarden --auto-convert --auto-import
```

---

## 📊 Example Output

```
══════════════════════════════════════════════════════════
  PuTTY → Bitwarden SSH Key Export
══════════════════════════════════════════════════════════

📖 Reading PuTTY sessions from Registry...
   Found 10 session(s)

🔍 Filtering sessions with SSH key authentication...
   5 session(s) with SSH keys

🔄 Auto-converting 3 PPK file(s)...
  [1/3] server.ppk
  [2/3] database.ppk
  [3/3] backup.ppk
   ✅ Converted: 3/3

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

---

## 🔒 Security Considerations

### Vault Encryption

- Bitwarden uses end-to-end encryption
- Your master password encrypts all vault data
- SSH keys are encrypted at rest and in transit

### Export File Security

The generated `bitwarden-export.json` contains:
- ✅ Encrypted within JSON structure (when imported)
- ⚠️ **Plaintext before import** - protect this file!

**Best practices:**
```bash
# Secure the export file
chmod 600 bitwarden-export.json

# Import immediately
bw import bitwardenjson bitwarden-export.json

# Delete after successful import
rm bitwarden-export.json
```

### SSH Agent Security

- SSH Agent runs locally, locked with your vault
- Keys are only accessible when vault is unlocked
- Auto-lock settings protect idle sessions

---

## 🐛 Troubleshooting

### "No sessions with SSH key authentication found"

**Cause:** PuTTY sessions use password auth, not key auth.

**Solution:**
1. Open PuTTY
2. Load your session
3. Go to Connection → SSH → Auth
4. Set "Private key file for authentication" to your `.ppk` file
5. Save the session
6. Run export again

### "OpenSSH directory not found"

**Cause:** Keys haven't been converted yet.

**Solution:**
```bash
# Use auto-convert
putty-migrate bitwarden --auto-convert

# Or convert first manually
putty-migrate convert
putty-migrate bitwarden
```

### "bw import failed"

**Causes:**
- Bitwarden CLI not installed
- Not logged in to Bitwarden
- Invalid export file format

**Solution:**
```bash
# Install Bitwarden CLI
npm install -g @bitwarden/cli

# Login
bw login

# Verify export file
cat bitwarden-export.json | jq .
# Should show valid JSON structure
```

### "Keys not appearing in SSH Agent"

**Solution:**
1. Verify import was successful (check web vault)
2. Enable SSH Agent in Bitwarden settings
3. Restart Bitwarden application
4. Check SSH Agent configuration
5. See: [Official SSH Agent Guide](https://bitwarden.com/help/ssh-agent/)

---

## 💡 Tips & Best Practices

### Organize Your Vault

After import:
- Create a folder called "SSH Keys" in Bitwarden
- Move all imported keys to this folder
- Add notes/tags for server identification

### Test Before Deleting PPKs

```bash
# 1. Export and import
putty-migrate bitwarden --auto-convert
bw import bitwardenjson bitwarden-export.json

# 2. Enable SSH Agent

# 3. Test connections
ssh user@server  # Should use Bitwarden SSH Agent

# 4. Only then remove PPK files
```

### Regular Backups

```bash
# Export your Bitwarden vault regularly
bw export --format json --output bitwarden-backup-$(date +%Y%m%d).json

# Encrypt the backup
gpg --encrypt bitwarden-backup-*.json
```

### Key Rotation

When rotating SSH keys:
1. Generate new key in Bitwarden (or convert new PPK)
2. Add to servers (`.ssh/authorized_keys`)
3. Test new key
4. Remove old key from servers and Bitwarden

---

## 🔄 Workflow Comparison

### Traditional SSH Keys
1. Store keys in `~/.ssh/`
2. Manage permissions manually
3. Copy keys between devices
4. Remember key locations
5. No synchronization

### Bitwarden SSH Agent
1. Store keys in Bitwarden vault
2. Automatic permission handling
3. Automatic sync across devices
4. Centralized key management
5. Searchable, organized vault

---

## 🚀 Next Steps

- **[Configure SSH Agent](https://bitwarden.com/help/ssh-agent/#configure-bitwarden-ssh-agent)** - Official guide
- **[PPK Conversion Guide](convert-ppk.md)** - Convert more keys
- **[SSH Config Guide](ssh-config.md)** - Alternative to Bitwarden
- **[Tabby Guide](tabby.md)** - Terminal integration

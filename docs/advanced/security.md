# Security Best Practices

Security guidelines for SSH key management and migration.

---

## 🔒 SSH Key Security

### File Permissions

**Critical:** Always set correct permissions on SSH keys.

```bash
# Private keys - owner read/write only
chmod 600 ~/.ssh/id_rsa
chmod 600 ~/.ssh/mykey

# Public keys - readable by all
chmod 644 ~/.ssh/id_rsa.pub
chmod 644 ~/.ssh/mykey.pub

# ~/.ssh directory
chmod 700 ~/.ssh

# SSH config file
chmod 644 ~/.ssh/config
```

**The tool sets these automatically**, but verify:
```bash
ls -la ~/.ssh/
```

### Key Storage

**Do:**
- ✅ Store private keys in `~/.ssh/ ` with 600 permissions
- ✅ Use encrypted PPK files (password-protected)
- ✅ Keep backups in encrypted archives
- ✅ Use SSH key passphrases

**Don't:**
- ❌ Never commit private keys to Git
- ❌ Never share private keys via email/chat
- ❌ Never store keys in cloud without encryption
- ❌ Never use world-readable permissions

---

## 🔐 Password Management

### PPK Passwords

```bash
# Good: Use password manager or TUI prompt
putty-migrate  # TUI will prompt interactively

# Avoid: Password in command line (visible in shell history)
putty-migrate convert --password "MyPassword"  # ❌

# Better: Read from file
putty-migrate convert --password "$(cat ~/.ppk-password)"  # Still risky

# Best: Use TUI for passwords
```

### Bitwarden Export

The exported JSON contains keys in plaintext until imported:

```bash
# Secure the export file immediately
chmod 600 bitwarden-export.json

# Import as soon as possible
bw import bitwardenjson bitwarden-export.json

# Delete after successful import
shred -u bitwarden-export.json  # Secure delete
```

---

## 🛡️ During Migration

### Backup Strategy

```bash
# 1. Backup BEFORE migration
tar -czf ~/backups/ssh-backup-$(date +%Y%m%d).tar.gz ~/.ssh/
chmod 600 ~/backups/ssh-backup-*.tar.gz

# 2. Encrypt backups
gpg --encrypt --recipient you@example.com ~/backups/ssh-backup-*.tar.gz

# 3. Store securely (offline, encrypted USB, etc.)
```

### Dry Run First

Always test before making changes:

```bash
# Preview what will happen
putty-migrate convert --dry-run
putty-migrate ssh-config --dry-run

# Then execute
putty-migrate convert
```

### Verification

```bash
# After conversion, test keys
ssh -i ~/.ssh/newkey -T git@github.com

# Verify permissions
ls -la ~/.ssh/ | grep "^-rw-------"  # Should show private keys

# Check SSH config syntax
ssh -G hostname  # Shows resolved config
```

---

## 🗑️ Cleanup

### Remove Old Keys Securely

```bash
# Secure delete (Linux)
shred -u -n 10 old_key.ppk

# Or use srm (if available)
srm -v old_key.ppk

# Windows: Use SDelete
sdelete -p 10 old_key.ppk
```

### Export Files

```bash
# After importing to Bitwarden/Tabby
shred -u bitwarden-export.json
shred -u tabby-config.json

# Or encrypt before storing
gpg --encrypt bitwarden-export.json
rm bitwarden-export.json
```

---

## 🔑 Key Rotation

Regular key rotation improves security:

```bash
# 1. Generate new key
ssh-keygen -t ed25519 -C "your@email.com"

# 2. Add to servers
ssh-copy-id -i ~/.ssh/new_key user@server

# 3. Test new key
ssh -i ~/.ssh/new_key user@server

# 4. Update SSH config
vim ~/.ssh/config  # Point to new key

# 5. Remove old key from servers
# On server: edit ~/.ssh/authorized_keys

# 6. Delete old key
shred -u ~/.ssh/old_key ~/.ssh/old_key.pub
```

---

## 🌐 Network Security

### SSH Hardening

```ssh-config
# ~/.ssh/config security options
Host *
    # Use strong key exchange algorithms
    KexAlgorithms curve25519-sha256,diffie-hellman-group-exchange-sha256
    
    # Strong ciphers only
    Ciphers chacha20-poly1305@openssh.com,aes256-gcm@openssh.com
    
    # Strong MAC algorithms
    MACs hmac-sha2-512-etm@openssh.com,hmac-sha2-256-etm@openssh.com
    
    # Disable weak options
    HostKeyAlgorithms ssh-ed25519,rsa-sha2-512,rsa-sha2-256
    
    # Connection hardening
    ServerAliveInterval 60
    ServerAliveCountMax 3
    TCPKeepAlive yes
```

### Agent Forwarding

```ssh-config
# Be careful with ForwardAgent
Host trusted-server
    ForwardAgent yes  # Only for trusted hosts

Host *
    ForwardAgent no  # Default: disabled
```

---

## 📋 Security Checklist

### Before Migration
- [ ] Backup all SSH keys and PPK files
- [ ] Encrypt backups
- [ ] Test all current connections
- [ ] Document which keys are used where

### During Migration
- [ ] Use `--dry-run` first
- [ ] Set correct file permissions (600/644)
- [ ] Verify converted keys work
- [ ] Keep original PPKs until verified

### After Migration
- [ ] Test all SSH connections
- [ ] Verify file permissions
- [ ] Secure delete old keys
- [ ] Update documentation
- [ ] Remove export files (or encrypt)

---

## 🚨 Incident Response

### Compromised Key

If a key is compromised:

```bash
# 1. Immediately revoke from all servers
# SSH to each server and remove from authorized_keys
ssh server "sed -i '/compromised_key_string/d' ~/.ssh/authorized_keys"

# 2. Generate new key
ssh-keygen -t ed25519 -f ~/.ssh/new_key

# 3. Deploy new key
ssh-copy-id -i ~/.ssh/new_key user@server

# 4. Securely delete compromised key
shred -u ~/.ssh/compromised_key*

# 5. Update Bitwarden/Tabby/SSH config
# 6. Notify relevant parties
```

---

## 🔍 Auditing

### Review Access

```bash
# List all public keys in use
find ~/.ssh -name "*.pub" -exec cat {} \;

# Check which keys are loaded in SSH agent
ssh-add -l

# Review SSH config
cat ~/.ssh/config

# Check active SSH connections
ss -tn | grep :22
```

### Log Review

```bash
# Check SSH authentication logs
# Linux
sudo tail -f /var/log/auth.log | grep ssh

# View failed authentication attempts
sudo grep "Failed password" /var/log/auth.log
```

---

## 💡 Best Practices Summary

1. **Permissions**: Always 600 for private keys, 644 for public
2. **Passphrases**: Use them on all private keys
3. **Backups**: Encrypted, offline storage
4. **Rotation**: Change keys regularly (every 6-12 months)
5. **Verification**: Test before deleting old keys
6. **Cleanup**: Secure delete sensitive files
7. **Monitoring**: Regular audits of key usage
8. **Documentation**: Keep track of what keys access what

---

## 🚀 Next Steps

- **[PPK Conversion Guide](../guides/convert-ppk.md)** - Secure conversion workflow
- **[Conflict Handling](conflict-handling.md)** - Safe file management
- **[Automation Guide](automation.md)** - Secure automation practices

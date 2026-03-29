Conflict Handling - Linux ~/.ssh

Managing key conflicts when copying to `~/.ssh/` on Linux.

---

## 📖 Overview

When using `putty-migrate convert --to-ssh` on Linux, the tool may encounter existing SSH keys in `~/.ssh/`. Three conflict resolution modes handle these situations.

---

## 🔧 Conflict Modes

### 1. Rename Mode (Default)

**Behavior:** Adds numeric suffix (.1, .2, .3, ...) to new keys if files already exist.

**Command:**
```bash
putty-migrate convert --to-ssh --conflict rename
```

**Example:**
```
~/.ssh/
├── mykey           # Original file (kept)
├── mykey.pub       # Original file (kept)
├── mykey.1         # New file from conversion
├── mykey.1.pub     # New file from conversion
├── server.2        # New file (already had .1)
└── server.2.pub    # New file
```

**Use Case:**
- Keep both old and new keys
- Transition period between keys
- Compare keys before switching
- Safety during migration

**Pros:**
- ✅ No data loss
- ✅ Safe default
- ✅ Can test both keys

**Cons:**
- ❌ Creates multiple files
- ❌ Manual cleanup needed later

---

### 2. Overwrite Mode

**Behavior:** Replaces existing files with automatic `.bak` backups.

**Command:**
```bash
putty-migrate convert --to-ssh --conflict overwrite
```

**Example:**
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

**Use Case:**
- Replace outdated keys
- Clean migration (no .1, .2 files)
- You're confident in the new keys

**Pros:**
- ✅ Clean ~/.ssh directory
- ✅ Automatic backups created
- ✅ Easy to restore if needed

**Cons:**
- ⚠️ Replaces active keys
- ⚠️ Must verify backups exist

**Safety:**
```bash
# Always verify backups after  overwrite
ls -la ~/.ssh/*.bak

# Restore if needed
mv ~/.ssh/mykey.bak ~/.ssh/mykey
mv ~/.ssh/mykey.pub.bak ~/.ssh/mykey.pub
```

---

### 3. Skip Mode

**Behavior:** Don't copy files if they already exist.

**Command:**
```bash
putty-migrate convert --to-ssh --conflict skip
```

**Example:**
```
~/.ssh/
├── mykey           # Original (kept, not replaced)
└── mykey.pub       # Original (kept, not replaced)

openssh_keys/
├── mykey           # New key saved here only
└── mykey.pub       # Not copied to ~/.ssh
```

**Use Case:**
- Only add new keys (not in ~/.ssh yet)
- Don't touch existing keys
- Manual key management

**Pros:**
- ✅ Never overwrites anything
- ✅ Safest mode
- ✅ Existing keys untouched

**Cons:**
- ❌ New keys not installed
- ❌ Manual copy needed for new keys

---

## 📊 Decision Matrix

| Scenario | Recommended Mode | Reason |
|----------|-----------------|---------|
| First-time migration | `rename` | Safest, allows comparison |
| Replacing old PPK keys | `overwrite` | Clean replacement with backups |
| Testing migration | `rename` | Can test both sets |
| Adding new keys only | `skip` | Won't touch existing |
| Production systems | `rename` | Maximum safety |
| Clean slate wanted | `overwrite` | Fresh start with backups |

---

## 💡 Best Practices

### Before Migration

```bash
# Backup entire ~/.ssh directory
tar -czf ~/.ssh-backup-$(date +%Y%m%d).tar.gz ~/.ssh/

# List current keys
ls -la ~/.ssh/*.pub
```

### During Migration

```bash
# Use dry-run first
putty-migrate convert --dry-run

# Then use appropriate mode
putty-migrate convert --to-ssh --conflict rename
```

### After Migration

```bash
# Verify permissions
ls -la ~/.ssh/
# Private keys should be 600
# Public keys should be 644

# Test connections
ssh -i ~/.ssh/server.1 user@host  # If using rename mode
```

### Cleanup (Rename Mode)

```bash
# After testing, remove old keys
rm ~/.ssh/mykey  # Old key
rm ~/.ssh/mykey.pub

# Rename new key to standard name
mv ~/.ssh/mykey.1 ~/.ssh/mykey
mv ~/.ssh/mykey.1.pub ~/.ssh/mykey.pub
```

### Cleanup (Overwrite Mode)

```bash
# After verifying new keys work, remove backups
rm ~/.ssh/*.bak
```

---

## 🐛 Troubleshooting

### Multiple Numbered Keys (.1, .2, .3...)

**Cause:** Multiple conversions in rename mode.

**Solution:**
```bash
# Clean up old versions
rm ~/.ssh/*.1 ~/.ssh/*.2

# Or perform one final conversion with overwrite
putty-migrate convert --to-ssh --conflict overwrite
```

### Backup Files Accumulating

**Cause:** Multiple overwrites.

**Solution:**
```bash
# Remove old backups after verification
rm ~/.ssh/*.bak

# Or rotate backups
mkdir ~/ssh-backups
mv ~/.ssh/*.bak ~/ssh-backups/
```

### Wrong Key Being Used

**Cause:** Multiple keys with similar names.

**Solution:**
```bash
# Explicitly specify key in SSH config
echo "Host myserver
    IdentityFile ~/.ssh/mykey.1" >> ~/.ssh/config

# Or use -i flag
ssh -i ~/.ssh/mykey.1 user@host
```

---

## 🔒 Security Considerations

### File Permissions

All modes preserve secure permissions:
- **Private keys**: `600` (rw-------)
- **Public keys**: `644` (rw-r--r--)
- **Backup files**: Inherit from originals

Verify:
```bash
ls -la ~/.ssh/ | grep -E '(rw----|rw-r--r--)'
```

### Backup Security

**Overwrite mode** creates `.bak` files:
- ✅ Same permissions as originals
- ⚠️ Not encrypted
- ⚠️ Remove after verification

```bash
# Secure backups before removal
shred -u ~/.ssh/*.bak  # Secure delete (Linux)
```

---

## 🚀 Next Steps

- **[PPK Conversion Guide](../guides/convert-ppk.md)** - Full conversion documentation
- **[CLI Guide](../guides/binary/cli.md)** - All CLI options
- **[Security Guide](security.md)** - SSH security best practices

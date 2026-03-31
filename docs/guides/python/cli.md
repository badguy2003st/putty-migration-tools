# CLI Guide (Python Version)

Command-line interface when running from source.

---

## 📖 Overview

The CLI provides the **same commands** as the binary version:

```bash
python -m tui COMMAND [OPTIONS]
```

**Available Commands:**
- `convert` - Convert PPK keys to OpenSSH format
- `bitwarden` - Export to Bitwarden SSH Key vault
- `tabby` - Export to Tabby terminal
- `ssh-config` - Generate SSH config file

---

## 🔑 Quick Examples

### convert
```bash
# Basic conversion (auto-loads ppk_keys/passwords.txt)
python -m tui convert

# With password file (v1.1.0)
python -m tui convert --password-file passwords.txt -v

# With options
python -m tui convert --to-ssh --conflict rename
python -m tui convert --dry-run

# Re-encryption (v1.1.0): Encrypted PPKs stay encrypted!
python -m tui convert --password mypassword  # Auto re-encrypts
python -m tui convert --no-encryption        # Disable re-encryption
```

### Encrypted PPK Files (v1.1.0)

**Auto-load passwords.txt:**
```bash
# 1. Create passwords.txt
cat > ppk_keys/passwords.txt << 'EOF'
mypassword
anotherpass
EOF

# 2. Run (auto-loads automatically)
python -m tui convert
# ✅ Auto-loaded 2 password(s) from passwords.txt
```

**Password priority is identical to binary version:**
- See [Binary CLI Guide](../binary/cli.md#encrypted-ppk-files-v110) for full details

### bitwarden
```bash
# Export to Bitwarden
python -m tui bitwarden

# Auto-convert PPKs first
python -m tui bitwarden --auto-convert
```

### tabby
```bash
# Export to Tabby
python -m tui tabby

# Custom output
python -m tui tabby -o my-config.json
```

### ssh-config
```bash
# Generate SSH config
python -m tui ssh-config

# Dry run
python -m tui ssh-config --dry-run
```

---

## 📖 Full Documentation

For **complete CLI documentation** with all options and examples, see:
- **[Binary CLI Guide](../binary/cli.md)** - All commands work identically

---

## 🔧 Differences from Binary

### Command Prefix

**Binary:**
```bash
putty-migrate convert
```

**Python:**
```bash
python -m tui convert
```

### Everything else is identical!

All flags, options, and behaviors are the same.

---

## 🤖 Automation Example (Python)

```bash
#!/bin/bash
# Automated migration using Python version

# Convert PPK keys
python -m tui convert --to-ssh --conflict rename

# Export to Bitwarden
python -m tui bitwarden --auto-convert --non-interactive

# Generate SSH config
python -m tui ssh-config --non-interactive

# Export to Tabby
python -m tui tabby

echo "✅ Migration complete!"
```

---

## 🚀 Next Steps

- **[Python TUI Guide](tui.md)** - Interactive interface
- **[Binary CLI Guide](../binary/cli.md)** - Full CLI documentation
- **[Feature Guides](../)** - Detailed feature documentation

# Testing Guide - PuTTY Migration Tools

This guide covers testing scenarios for the PuTTY Migration Tools, with a focus on the SSH Import Feature (Linux only).

---

## Prerequisites

### For CLI Testing

**All Platforms:**
- Python 3.8+
- PuTTY installed (Windows for Registry access)
- Sample PPK files in `./ppk_keys/`

**Linux Only:**
- SSH keys in `~/.ssh/` for conflict testing

### For TUI Testing

- Terminal with minimum 80x24 resolution
- All CLI prerequisites

---

## CLI Command Testing

### 1. Convert Command

```bash
# Basic conversion
python -m tui convert

# Custom directories
python -m tui convert -i ./my_ppk_keys -o ./my_openssh_keys

# Dry run (preview only)
python -m tui convert --dry-run

# Verbose output
python -m tui convert -v
```

**Expected Results:**
- PPK files converted to OpenSSH format
- Public keys generated (.pub files)
- Secure permissions set (600 for private, 644 for public)
- Summary shows success/failure counts

### 2. Convert with SSH Import (Linux Only)

```bash
# Copy to ~/.ssh with rename mode (default)
python -m tui convert --to-ssh

# Overwrite mode (creates backups)
python -m tui convert --to-ssh --conflict overwrite

# Skip mode (don't copy if exists)
python -m tui convert --to-ssh --conflict skip
```

**Expected Results:**
- Keys copied to `~/.ssh/`
- Conflicts handled per mode
- Summary shows copy results

### 3. Bitwarden Export Command

```bash
# Basic export
python -m tui bitwarden

# Custom output file
python -m tui bitwarden -o my-export.json

# Auto-convert PPK files first
python -m tui bitwarden --auto-convert

# Verbose output
python -m tui bitwarden -v
```

**Expected Results:**
- JSON file created
- Valid Bitwarden import format
- Instructions shown for import

### 4. Tabby Export Command

```bash
# Basic export
python -m tui tabby

# Custom output
python -m tui tabby -o my-tabby.json

# Merge with existing config
python -m tui tabby --merge ~/.config/tabby/config.json
```

**Expected Results:**
- JSON file created
- Valid Tabby format
- Import instructions shown

### 5. Help System

```bash
# Global help
python -m tui --help

# Command-specific help
python -m tui convert --help
python -m tui bitwarden --help
python -m tui tabby --help
python -m tui ssh-config --help

# Version
python -m tui --version
```

**Expected Results:**
- Comprehensive help text
- Examples shown
- All options documented

---

## SSH Import Feature Testing (Linux Only)

### Setup Test Environment

```bash
# Create test keys in ~/.ssh
cd ~/.ssh
ssh-keygen -t rsa -f test_oracle -N ""
ssh-keygen -t rsa -f test_production -N ""
ssh-keygen -t ed25519 -f test_backup -N ""

# Verify
ls -la test_*
```

---

### Scenario A: Rename Mode (Default)

**Goal:** Test numeric suffix when keys already exist

**Steps:**
1. Ensure `test_oracle` exists in `~/.ssh/`
2. Create a PPK file named `test_oracle.ppk` in `./ppk_keys/`
3. Run: `python -m tui convert --to-ssh --conflict rename`

**Expected Results:**
```
~/.ssh/test_oracle       (original, unchanged)
~/.ssh/test_oracle.pub   (original, unchanged)
~/.ssh/test_oracle.1     (NEW, from conversion)
~/.ssh/test_oracle.1.pub (NEW, from conversion)
```

**Verify:**
```bash
ls -la ~/.ssh/test_oracle*
# Should show 4 files:
# test_oracle, test_oracle.pub, test_oracle.1, test_oracle.1.pub
```

**Permissions Check:**
```bash
stat -c '%a %n' ~/.ssh/test_oracle.1
# Should show: 600 /home/user/.ssh/test_oracle.1

stat -c '%a %n' ~/.ssh/test_oracle.1.pub
# Should show: 644 /home/user/.ssh/test_oracle.1.pub
```

---

### Scenario B: Overwrite Mode

**Goal:** Test backup creation and file replacement

**Steps:**
1. Ensure `test_production` exists in `~/.ssh/`
2. Create a PPK file named `test_production.ppk`
3. Run: `python -m tui convert --to-ssh --conflict overwrite`

**Expected Results:**
```
~/.ssh/test_production       (NEW, replaced)
~/.ssh/test_production.pub   (NEW, replaced)
~/.ssh/test_production.bak   (BACKUP of original)
~/.ssh/test_production.pub.bak (BACKUP of original)
```

**Verify:**
```bash
# Check backups exist
ls -la ~/.ssh/test_production*.bak

# Verify content differs
diff ~/.ssh/test_production ~/.ssh/test_production.bak
# Should show differences (keys are different)
```

---

### Scenario C: Skip Mode

**Goal:** Test that existing files are not modified

**Steps:**
1. Ensure `test_backup` exists in `~/.ssh/`
2. Note current file size/modification time
3. Create a PPK file named `test_backup.ppk`
4. Run: `python -m tui convert --to-ssh --conflict skip`

**Expected Results:**
- `~/.ssh/test_backup` unchanged
- `~/.ssh/test_backup.pub` unchanged
- No `.bak` files created
- Summary shows "skipped" for this key

**Verify:**
```bash
# Check modification time (should NOT change)
stat ~/.ssh/test_backup

# Verify no new files created
ls -la ~/.ssh/test_backup*
# Should show only test_backup and test_backup.pub
```

---

### Scenario D: Multiple Conflicts

**Goal:** Test mixed conflict scenarios

**Setup:**
```bash
cd ~/.ssh
ssh-keygen -t rsa -f multi_test1 -N ""
ssh-keygen -t rsa -f multi_test2 -N ""
# multi_test3 will NOT exist
```

**Steps:**
1. Create three PPK files:
   - `multi_test1.ppk` (will conflict)
   - `multi_test2.ppk` (will conflict)
   - `multi_test3.ppk` (no conflict)
2. Run: `python -m tui convert --to-ssh --conflict rename`

**Expected Results:**
```
~/.ssh/multi_test1       (original)
~/.ssh/multi_test1.1     (NEW, renamed)
~/.ssh/multi_test2       (original)
~/.ssh/multi_test2.1     (NEW, renamed)
~/.ssh/multi_test3       (NEW, copied directly)
```

**Verify:**
```bash
ls -la ~/.ssh/multi_test* | wc -l
# Should show 8 files total (3 original pairs + 2 renamed + 1 new pair)
```

---

## TUI Testing

### Launch TUI

```bash
# From project root
python -m tui

# Should show main menu with options:
# - Convert PPK Keys
# - Export to Bitwarden
# - Export to Tabby
# - Generate SSH Config
# - Install Dependencies
```

### Test Conversion Screen

1. Select "Convert PPK Keys"
2. Verify PPK files are listed
3. Click "Convert All"
4. Check progress indicators
5. Verify success message

**Linux Only:**
6. Click "Copy to ~/.ssh"
7. Select conflict mode in dialog
8. Verify copy results

### Test Export Screens

1. **Bitwarden:**
   - Select "Export to Bitwarden"
   - Verify sessions listed
   - Check export file created
   - Validate JSON structure

2. **Tabby:**
   - Select "Export to Tabby"
   - Verify SSH sessions only
   - Check export file created
   - Validate JSON structure

---

## Automated Testing

### Unit Tests (if implemented)

```bash
# Run all tests
python -m pytest

# Run specific test
python -m pytest test_converter.py::test_conflict_rename

# With coverage
python -m pytest --cov=tui
```

---

## Common Issues

### Issue: "PPK directory not found"

**Solution:**
```bash
mkdir -p ./ppk_keys
# Place .ppk files in this directory
```

### Issue: "--to-ssh not supported on Windows"

**Reason:** SSH import to `~/.ssh` only works on Linux  
**Solution:** Use the converted files from `./openssh_keys/` instead

### Issue: "Permission denied" when copying to ~/.ssh

**Solution:**
```bash
# Check ~/.ssh permissions
chmod 700 ~/.ssh

# Re-run the command
python -m tui convert --to-ssh
```

### Issue: TUI doesn't launch

**Possible causes:**
1. Terminal too small (minimum 80x24)
2. Textual not installed
3. Python version < 3.8

**Solution:**
```bash
# Check terminal size
tput cols; tput lines

# Install Textual
pip install textual

# Check Python version
python --version
```

---

## Performance Testing

### Large Batch Conversion

```bash
# Create 100 test PPK files
for i in {1..100}; do
    cp sample.ppk ./ppk_keys/test_key_$i.ppk
done

# Time the conversion
time python -m tui convert

# Expected: < 30 seconds for 100 keys
```

---

## Security Testing

### Verify File Permissions

```bash
# After conversion
ls -la ./openssh_keys/

# Private keys should be 600
# Public keys should be 644

# After SSH import
ls -la ~/.ssh/

# All private keys should be 600
```

### Verify Backup Creation

```bash
# Run with overwrite mode
python -m tui convert --to-ssh --conflict overwrite

# Check backups exist
ls -la ~/.ssh/*.bak

# Verify backup content matches original
```

---

## Regression Testing Checklist

Before each release, verify:

- [ ] `python -m tui --help` works
- [ ] `python -m tui --version` shows correct version
- [ ] All subcommands have `--help`
- [ ] TUI launches without errors
- [ ] PPK conversion works
- [ ] Public key extraction works
- [ ] File permissions are correct (600/644)
- [ ] SSH import dialog works (Linux)
- [ ] All conflict modes work correctly
- [ ] Bitwarden export validates
- [ ] Tabby export validates
- [ ] Error messages are user-friendly

---

## Bug Reports

When reporting bugs, include:

1. **Command used:** Full command line
2. **Platform:** OS and version
3. **Python version:** `python --version`
4. **Error message:** Full error output
5. **Expected behavior:** What should happen
6. **Actual behavior:** What actually happened

**Example:**
```
Command: python -m tui convert --to-ssh
Platform: Ubuntu 22.04
Python: 3.10.6
Error: AttributeError: 'NoneType' object has no attribute 'exists'
Expected: Keys copied to ~/.ssh
Actual: Crash with traceback
```

---

## Contributing Tests

When adding new features, provide:

1. Unit tests for core functionality
2. Integration tests for workflows
3. Documentation in this TESTING.md
4. Example test cases

---

**Last Updated:** 2026-03-28  
**Version:** 1.0.0

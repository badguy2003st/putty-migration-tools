# Troubleshooting Guide

Common issues and solutions.

---

## 🖥️ Platform Issues

### Windows: "PuTTY Registry not accessible"

**Causes:**
- PuTTY not installed
- No saved sessions
- Permission issues

**Solutions:**
```powershell
# Verify PuTTY is installed
where putty.exe

# Check if sessions exist
reg query "HKCU\Software\SimonTatham\PuTTY\Sessions"

# Run as Administrator if needed
```

### Linux: "--to-ssh only works on Linux"

**Solution:** The `--to-ssh` flag is Linux-specific.

On Windows, keys are saved to `openssh_keys/` - manually copy to `C:\Users\YourName\.ssh\` if needed.

---

## 🔑 Conversion Issues

### "No .ppk files found"

**Solution:**
```bash
# Create directory
mkdir ppk_keys

# Add your .ppk files
cp /path/to/*.ppk ppk_keys/

# Verify
ls ppk_keys/
```

### "Conversion failed: Invalid PPK format"

**Causes:**
- Corrupted file
- Not actually a PPK file
- Unsupported PPK version

**Solutions:**
```bash
# Check file type
file mykey.ppk

# Test in PuTTYgen
# If PuTTYgen can't open it, re-export from PuTTY

# Try verbose mode
putty-migrate convert -v
```

### "Password required" for encrypted PPK

**Solutions:**
```bash
# Use CLI with password flag
putty-migrate convert --password "YourPassword"
```

**Note:** TUI password prompt is planned for v1.0.4.

### ⚠️ "Unsupported key type" despite RSA/Ed25519 Key

**Most Common Cause:** PPK v3 format (not supported in v1.0.3)

#### Check Your PPK Version

Open your `.ppk` file in a text editor and check the first line:

- `PuTTY-User-Key-File-2: ssh-rsa` → ✅ **Supported** (PPK v2)
- `PuTTY-User-Key-File-3: ssh-rsa` → ❌ **Not Supported** (PPK v3)

#### Background

**PuTTY 0.75+** (released February 2021) uses PPK v3 format by default with Argon2id key derivation for better security against brute-force attacks. However, this format is not supported by the `puttykeys` library v1.0.3.

**Impact:** ~90% of users with recent PuTTY installations have PPK v3 keys.

#### Solution: Convert PPK v3 → PPK v2

**Method 1: In PuTTYgen (Recommended)**

1. Open **PuTTYgen.exe**
2. Click **Load** and select your `.ppk` file
3. Enter your passphrase if prompted
4. Go to menu: **Key** → **Parameters for saving key files...**
5. Under "PPK file version", select **2**
6. Click **OK**
7. Click **Save private key**
8. Now use PuTTY Migration Tools with the v2 file

**Method 2: Command Line (puttygen)**

```cmd
REM Convert v3 to v2
puttygen mykey-v3.ppk -O private -o mykey-v2.ppk

REM Then use migration tool
putty-migrate convert -i . -o openssh_keys
```

#### Alternative: Direct Export to OpenSSH (Not Recommended)

While PuTTYgen can export directly to OpenSSH format (**Conversions** → **Export OpenSSH key**), this may cause formatting issues. Converting to PPK v2 first, then using this tool is more reliable.

#### Future Support

PPK v3 support is planned for **v1.0.4** (mid-April 2026). See `PPK_V3_IMPLEMENTATION_PLAN.md` for details.

---

## 🎨 TUI Issues

### "Terminal too small for TUI"

**Error:**
```
⚠️  Terminal too small for TUI (minimum 80x24)
   Current size: 60x20
```

**Solutions:**
- Resize terminal to at least 80×24
- Or use CLI: `putty-migrate convert --help`

### TUI won't launch / Import errors

**Solutions:**
```bash
# Check Python version
python --version  # Must be 3.8+

# Install dependencies
pip install -r tui/requirements.txt

# Verify textual installed
pip list | grep textual

# If still fails, use CLI
putty-migrate convert
```

---

## 📤 Export Issues

### Bitwarden: "No sessions with SSH key authentication"

**Cause:** Sessions use password auth, not keys.

**Solution:**
1. Open PuTTY
2. Load session
3. Connection → SSH → Auth → Set private key file
4. Save session
5. Run export again

### Bitwarden: "bw import failed"

**Solutions:**
```bash
# Install Bitwarden CLI
npm install -g @bitwarden/cli

# Login
bw login

# Unlock
bw unlock

# Verify export file
cat bitwarden-export.json | jq .
```

### Tabby: "Cannot find Import Connection button"

**Cause:** tabby-home plugin not installed.

**Solution:**
1. Settings → Plugins
2. Search "home"
3. Install **tabby-home**
4. Restart Tabby
5. Look for "Tabby Home" tab

---

## 🔐 Permission Issues

### Linux: "Permission denied" copying to ~/.ssh

**Solutions:**
```bash
# Fix ~/.ssh permissions
chmod 700 ~/.ssh

# Fix individual keys
chmod 600 ~/.ssh/mykey
chmod 644 ~/.ssh/mykey.pub
```

### "Permission denied" running binary (Linux)

**Solution:**
```bash
chmod +x putty-migrate-v1.0.0-linux
./putty-migrate-v1.0.0-linux
```

---

## 🌐 Connection Issues

### SSH: "Permission denied (publickey)"

**Solutions:**
```bash
# Verify key permissions
ls -la ~/.ssh/mykey  # Should be -rw------- (600)

# Test key
ssh -i ~/.ssh/mykey -vvv user@host

# Check SSH config
ssh -G hostname

# Verify public key on server
cat ~/.ssh/authorized_keys  # On server
```

### SSH Config not being used

**Solutions:**
```bash
# Verify config permissions
chmod 644 ~/.ssh/config

# Test config is read
ssh -v hostname 2>&1 | grep config

# Verify syntax
ssh -G hostname
```

---

## 🐛 Build Issues

### PyInstaller: "Module not found"

**Solution:** Add to `build.py`:
```python
hidden_imports.append('missing_module')
```

### Binary: "styles.tcss not found"

**Solution:** Verify in `build.py`:
```python
--add-data 'tui/ui/styles.tcss;tui/ui'
```

---

## 💡 Getting Help

### Check Logs

```bash
# Run with verbose flag
putty-migrate convert -v

# Run with debug
python -m tui convert -v 2>&1 | tee debug.log
```

### Report Bugs

**Include:**
1. Command used (full)
2. Platform & Python version
3. Complete error output
4. Expected vs actual behavior

**Report at:** [GitHub Issues](https://github.com/badguy2003st/putty-migration-tools/issues)

---

## 📚 Further Help

- **[Installation Guide](installation/binary.md)** - Setup issues
- **[CLI Guide](guides/binary/cli.md)** - Command options
- **[Security Guide](advanced/security.md)** - Permission issues
- **[Conflict Handling](advanced/conflict-handling.md)** - Linux ~/.ssh conflicts

# TUI Guide (Binary Version)

Interactive Terminal User Interface for PuTTY Migration Tools.

---

## 🚀 Starting the TUI

Launch the interactive interface with no arguments:

### Windows
```powershell
putty-migrate.exe

# Or if added to PATH:
putty-migrate
```

### Linux
```bash
./putty-migrate

# Or if installed system-wide:
putty-migrate
```

---

## 📋 Main Menu

Upon launch, you'll see the main menu with these options:

### Windows (v1.1.1)
```
🔧 PuTTY Migration Tools

✅ Textual UI available
✅ Windows - Registry access available
✅ Found X PuTTY session(s)

1. 🔑 Convert PPK Keys
2. 📤 Export Sessions
3. 📦 Export All to ZIP        ← NEW in v1.1.1!
4. ⚙️  Settings
5. ℹ️  About
6. ❌ Exit
```

### Linux (v1.1.1)
```
🔧 PuTTY Migration Tools

✅ Textual UI available
✅ Linux/macOS platform
✅ Found X PuTTY session(s)

1. 🔑 Convert PPK Keys
2. 📤 Export Sessions
3. 📥 Import All from ZIP      ← NEW in v1.1.1!
4. ⚙️  Settings
5. ℹ️  About
6. ❌ Exit
```

### Navigation
- **Tab/Shift+Tab**: Navigate between buttons
- **Enter/Space**: Select/activate option
- **Q**: Quit application
- **ESC**: Go back to previous screen

---

## 🔑 Convert PPK Keys

Converts `.ppk` files to OpenSSH format.

### Prerequisites
- Place your `.ppk` files in the `ppk_keys/` directory
- For encrypted PPKs: Add passwords to `ppk_keys/passwords.txt` (auto-created)
- The TUI will automatically scan for files

### Workflow

1. **Select "Convert PPK Keys"** from main menu

2. **Review Files**
   - The TUI displays all `.ppk` files found
   - Shows file size for each key

3. **Choose Output Format**:
   - **OpenSSH Files** (default) - Individual `.key` files in `openssh_keys/`
   - **Bitwarden Import** - Direct export to Bitwarden vault
   - **SSH Config** - Generate SSH config entries

4. **Start Conversion**
   - Click "▶ Start Conversion"
   - Live progress bar shows conversion status
   - Scrollable log displays results (500+ lines supported)

### Encrypted PPK Files (v1.1.0)

#### Automatic Password Loading

The TUI automatically creates and loads `ppk_keys/passwords.txt`:

**First Run:**
1. TUI detects missing directories
2. Creates `ppk_keys/` and `passwords.txt` template
3. Shows notification:
   ```
   📁 Setup Complete
   
   ✓ Created: ppk_keys/
   ✓ Created: passwords.txt
   
   Next steps:
   • Copy .ppk files to ppk_keys/
   • For encrypted PPKs: Edit passwords.txt
   • Then use 'Convert PPK Keys' menu
   ```

**Format (passwords.txt):**
```
One password per line (no comments allowed)
All characters including # are part of the password
Empty lines are ignored

mypassword123
#hashtagPassword
password with spaces
```

**Auto-Load Behavior:**
- Automatically loads `ppk_keys/passwords.txt`
- Tries all passwords for each encrypted file
- Shows count: "Loaded 3 password(s) from passwords.txt"

#### Automatic Re-encryption (v1.1.0) 🔐

**Security by Default:**
Encrypted PPK keys stay encrypted after conversion!

**Behavior:**
- ✅ Encrypted PPK → Encrypted OpenSSH (automatic, transparent)
- ✅ Password preserved from passwords.txt or manual dialog
- ✅ Unencrypted PPK → Unencrypted OpenSSH (no change)

**Examples:**
```
PPK Files:
  server.ppk (encrypted, password: "test123")
  database.ppk (unencrypted)

After Conversion:
  → server (OpenSSH, encrypted with "test123") ✅
  → server.pub (public key, unencrypted) ✅
  → database (OpenSSH, unencrypted) ✅
  → database.pub (public key, unencrypted) ✅
```

**No User Action Required:**
- Completely automatic and transparent
- Works with both passwords.txt and manual dialog
- Prevents accidental key exposure

#### Interactive Password Dialog

If passwords.txt doesn't contain the right password, an interactive dialog appears:

```
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
🔒 Password Required [2/5]

File: production-server.ppk

⚠️  Tried 2 password(s) from passwords.txt
   None of them worked for this file

Enter password or choose an option:
┏━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━┓
┃ Type password here...                  ┃
┗━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━┛

[✓ Try Password]  [⏭ Skip This File]  [✕ Cancel & Edit]

💡 Tip: Edit ppk_keys/passwords.txt to add passwords
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
```

**Options:**

1. **✓ Try Password**
   - Enter password in text field
   - Press `Enter` or click button
   - If wrong → Dialog shows again with new attempt
   - If correct → Conversion continues automatically

2. **⏭ Skip This File**
   - Current file marked as "Skipped by user"
   - Batch continues with next file
   - Good when you don't know the password

3. **✕ Cancel & Edit passwords.txt**
   - Stops entire batch immediately
   - Shows helpful message: "Edit ppk_keys/passwords.txt"
   - Re-run conversion when ready
   - Good when you want to add multiple passwords

**Keyboard Shortcuts:**
- `Enter` in password field → Try Password
- `ESC` → Cancel & Edit

### Log Output & Export (v1.1.0)

#### Scrollable Log

The conversion log is now fully scrollable:
- ✅ **Supports 500+ lines** (no more truncation!)
- ✅ **Color-coded icons** (✅ success, ⚠️ warning, ❌ error, 🔒 password, ⏭ skip)
- ✅ **Multi-line errors** - Long messages wrapped intelligently
- ✅ **Context-specific guidance** for each error type

**Navigation:**
- **Mouse wheel:** Scroll up/down
- **↑/↓ arrow keys:** Line-by-line scrolling
- **Page Up/Down:** Scroll by page
- **Auto-scroll:** Automatically scrolls to bottom during conversion

**Log Example:**
```
Conversion Log:
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
✅ server.ppk → openssh_keys
✅ database.ppk → openssh_keys
🔒 encrypted.ppk: Password required
   → Add password to passwords.txt
⚠️  Ed448-test.ppk: Ed448 not supported
   → Use Ed25519 instead
⏭  server.pub: Public key (skip)
   → Remove .pub files from ppk_keys/
❌ dsa-key.ppk: DSA deprecated
   → Generate new RSA or Ed25519 key
```

#### Export Log Button (v1.1.0)

Save the conversion log to a text file:

**Steps:**
1. Run a conversion (log populates)
2. Click **💾 Export Log** button (enabled after conversion)
3. File saved with timestamp: `conversion_log_YYYYMMDD_HHMMSS.txt`
4. Notification shows:
   ```
   Export Complete
   
   Log exported successfully!
   
   File: C:\...\conversion_log_20260330_043000.txt
   Lines: 25
   ```

**Exported File Format:**
```
PPK Migration Tools - Conversion Log
Generated: 2026-03-30 04:30:00

✅ key1.ppk → openssh_keys
✅ key2.ppk → openssh_keys
🔒 encrypted.ppk: Password required
   → Check/update passwords.txt
...
```

**Use Cases:**
- Share conversion results with team
- Troubleshooting with logs
- Keep record of migrations
- Report bugs with detailed logs

### Linux: Copy to ~/.ssh

On Linux, you'll be prompted to copy converted keys to `~/.ssh/`:

**Conflict Resolution Options:**
- **Rename** (default): Adds `.1`, `.2` suffix if file exists
- **Overwrite**: Replaces existing files (creates `.bak` backups)
- **Skip**: Don't copy if file already exists

**Example Output:**
```
Keys created in ~/.ssh:
━━━━━━━━━━━━━━━━━━━━
  🔑 mykey         (600) [no conflict]
  🔓 mykey.pub     (644)

  🔑 server.1      (600) [renamed - original kept]
  🔓 server.1.pub  (644)
```

---

## � Export Sessions

Export PuTTY sessions to modern formats.

### Prerequisites (Windows Only)
- PuTTY installed with saved sessions
- Sessions stored in Windows Registry

### Workflow

1. **Select "Export Sessions"** from main menu

2. **Review Sessions**
   - Table shows all PuTTY sessions
   - Columns: Name, Hostname, Username, Port, Auth Method
   - Auth types: 🔒 Password, 🔑 Key, 🔐 Pageant

3. **Choose Export Format**:
   - **SSH Config** - OpenSSH config file format
   - **Tabby JSON** - For Tabby terminal import

4. **Set Output Path** (optional)
   - Leave empty for defaults:
     - SSH Config: `~/.ssh/config`
     - Tabby: `./tabby-config.json`

5. **Export**
   - Click "▶ Export Sessions"
   - Review summary
   - Follow import instructions

---

## 🔐 Bitwarden Export (from Convert Screen)

Export SSH keys directly to Bitwarden format.

### Workflow

1. Go to **Convert PPK Keys** screen
2. Select **"Bitwarden Import"** format
3. Click **Start Conversion**

The TUI will:
1. Auto-convert all PPK files to OpenSSH
2. Read PuTTY sessions with SSH key authentication
3. Generate `bitwarden-export.json`
4. Show import instructions

### Import to Bitwarden

After export, use Bitwarden CLI:

```bash
bw login
bw unlock
bw import bitwardenjson bitwarden-export.json
bw sync
```

**Next**: Configure Bitwarden SSH Agent
- See: [Bitwarden SSH Agent Guide](https://bitwarden.com/help/ssh-agent/#configure-bitwarden-ssh-agent)

---

## ⚙️ Settings

View system information and dependencies:
- Platform detection (Windows/Linux)
- Textual UI status
- PuTTY session count
- Dependency checks

---

## ℹ️ About

Displays version information and feature list.

---

## 🎨 UI Features

### Progress Tracking
- Live progress bars during conversion
- File-by-file status updates
- Success/failure counts

### Log Output
- Scrollable log area
- Color-coded messages (✅/⚠️/❌)
- Detailed error information

### Notifications
- Pop-up notifications for completion
- Error alerts with actionable information
- Auto-dismiss or click to close

---

## ⌨️ Keyboard Shortcuts

### Global
- **Tab**: Next element
- **Shift+Tab**: Previous element
- **ESC**: Go back / Close dialog
- **Q**: Quit (from main menu)

### Buttons
- **Enter** or **Space**: Activate button

### Lists/Tables
- **↑/↓**: Navigate items
- **Page Up/Down**: Scroll pages

---

## 🐛 Troubleshooting

### "Terminal too small for TUI"
```
⚠️  Terminal too small for TUI (minimum 80x24)
   Current size: 60x20
```

**Solution:**
- Resize your terminal window to at least 80 columns × 24 rows
- Or use CLI commands: `putty-migrate --help`

### "No .ppk files found"
**Solution:**
- Place `.ppk` files in the `ppk_keys/` directory
- The directory is created automatically on first run

### "No PuTTY sessions found" (Windows)
**Solutions:**
- Ensure PuTTY is installed
- Save at least one session in PuTTY
- Run as Administrator if needed

### TUI Crashes / Import Errors
**Solution:**
```bash
# Verify dependencies (if using Python version)
pip install textual cryptography rich argon2pure

# Or use the binary (no dependencies needed)
```

---

## 💡 Tips

1. **Batch Processing**: The TUI processes all files at once - perfect for migrating many keys
2. **Safety First**: Original `.ppk` files are never modified, only copied/converted
3. **Dry Run**: Use CLI `--dry-run` flag to preview before actual conversion
4. **Backups**: On Linux overwrite mode, `.bak` backups are always created

---

## 🚀 Next Steps

- **[CLI Guide](cli.md)** - Command-line automation
- **[PPK Conversion Guide](../convert-ppk.md)** - Detailed conversion info
- **[Bitwarden Guide](../bitwarden.md)** - Complete Bitwarden workflow
- **[Tabby Guide](../tabby.md)** - Tabby terminal setup

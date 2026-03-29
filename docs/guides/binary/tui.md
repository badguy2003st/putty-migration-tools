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

```
🔧 PuTTY Migration Tools

✅ Textual UI available
✅ Windows - Registry access available
✅ Found X PuTTY session(s)

1. 🔑 Convert PPK Keys
2. 📤 Export Sessions
3. 📋 Export to SSH Config
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
   - Log output displays results

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

## 📤 Export Sessions

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
pip install textual puttykeys rich

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

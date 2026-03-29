# Tabby Terminal Export Guide

Export PuTTY sessions to Tabby terminal for modern SSH session management.

---

## 📖 Overview

[Tabby](https://tabby.sh/) is a modern, highly customizable terminal with excellent SSH session management, theming, and cross-platform support.

### Why Tabby?

- 🎨 Beautiful, customizable interface
- 📁 Session management and organization
- 🔄 Profile sync across devices
- 🔌 Plugin ecosystem
- ⌨️ Advanced keyboard shortcuts
- 🖥️ Multi-pane support

---

## 🚀 Export Process

### Binary Version

```bash
# Export all SSH sessions
putty-migrate tabby

# Custom output file
putty-migrate tabby -o my-tabby.json

# Merge with existing Tabby config
putty-migrate tabby --merge ~/.config/tabby/config.json
```

### Python Version

```bash
# Same commands, different prefix
python -m tui tabby
python -m tui tabby -o custom.json
```

### What Gets Exported?

The tool:
1. Reads PuTTY sessions from Windows Registry
2. Filters to SSH sessions only (non-SSH sessions are skipped)
3. Generates `tabby-config.json` with:
   - Connection profiles
   - Hostnames and ports
   - Usernames
   - SSH key paths (if configured)

---

## 📥 Import to Tabby

### Prerequisites

**Install the tabby-home Plugin:**

The import functionality requires the **tabby-home** plugin.

### Step 1: Install tabby-home Plugin

1. Open **Tabby**
2. Go to **Settings** (⚙️ icon)
3. Click **Plugins** in the left sidebar
4. Search for **"home"** in the plugin list
5. Find **tabby-home** plugin
6. Click **Install**
7. **Restart Tabby** if prompted

### Step 2: Import Configuration

1. After plugin installation, look for the **Tabby Home** tab
2. Click on the **Tabby Home** tab (should appear in your tabs)
3. In the top-right corner, click **"Import Connection"** button
4. Select your generated `tabby-config.json` file
5. Confirm the import

### Step 3: Verify Import

- Your PuTTY sessions should now appear in Tabby's connection list
- Click on any session to test the connection
- Sessions can be customized further in Tabby's settings

---

## ⚙️ Advanced Options

### Merge with Existing Config

If you already have Tabby sessions configured:

```bash
# Merge new sessions with existing config
putty-migrate tabby --merge ~/.config/tabby/config.json
```

This will:
- Keep your existing Tabby sessions
- Add new PuTTY sessions
- Avoid duplicates (by session name)

### Custom Output Location

```bash
# Save to specific location
putty-migrate tabby -o /path/to/tabby-export.json

# Windows example
putty-migrate tabby -o C:\Backups\tabby-config.json

# Linux example
putty-migrate tabby -o ~/Documents/tabby-backup.json
```

---

## 📊 Example Output

```
══════════════════════════════════════════════════════════
  PuTTY → Tabby Terminal Export
══════════════════════════════════════════════════════════

📖 Reading PuTTY sessions from Registry...
   Found 10 session(s)

🔍 Found 8 SSH session(s)

📦 Generating Tabby configuration...

══════════════════════════════════════════════════════════
  EXPORT COMPLETE
══════════════════════════════════════════════════════════
  File: tabby-config.json
  Size: 8.2 KB
  Sessions: 8
══════════════════════════════════════════════════════════

📥 Import to Tabby:

  1. Open Tabby terminal
  2. Go to Settings → Plugins
  3. Install the "home" plugin (tabby-home)
  4. Restart Tabby if prompted
  5. Go to Tabby Home tab
  6. Click "Import Connection" (top right)
  7. Select: tabby-config.json

✅ Your PuTTY sessions will appear in Tabby!
```

---

## 🖼️ Generated Config Format

The exported `tabby-config.json` contains connection profiles in Tabby format:

```json
{
  "version": 1,
  "profiles": [
    {
      "type": "ssh",
      "name": "Production Server",
      "options": {
        "host": "192.168.1.10",
        "port": 22,
        "user": "admin",
        "privateKey": "~/.ssh/production"
      }
    },
    {
      "type": "ssh",
      "name": "Development",
      "options": {
        "host": "dev.example.com",
        "port": 2222,
        "user": "developer"
      }
    }
  ]
}
```

---

## 🔑 SSH Key Configuration

### Sessions with SSH Keys

If your PuTTY sessions use SSH key authentication:

1. **Convert PPK files first:**
   ```bash
   putty-migrate convert --to-ssh  # Linux
   putty-migrate convert           # Windows
   ```

2. **Export to Tabby:**
   ```bash
   putty-migrate tabby
   ```

3. **After import**, configure key paths in Tabby:
   - Open session settings in Tabby
   - Set "Private Key" field to your converted key location
   - Example: `~/.ssh/server` or `C:\Users\YourName\.ssh\server`

### Automatic Key Path Detection

The tool attempts to detect key paths from PuTTY sessions:
- If PPK file is specified, it suggests the OpenSSH equivalent
- You may need to manually update paths after import

---

## 🎨 Customizing Sessions in Tabby

After import, you can customize each session:

### Appearance
- 🎨 Custom colors per session
- 🖼️ Background images
- 🔤 Font size and family

### Behavior
- 🚀 Run commands on startup
- 📂 Set working directory
- 🔄 Auto-reconnect settings

### Organization
- 📁 Group sessions into folders
- 🏷️ Add tags for filtering
- ⭐ Mark favorites

---

## 🐛 Troubleshooting

### "Cannot find Import Connection button"

**Cause:** tabby-home plugin not installed.

**Solution:**
1. Settings → Plugins → Search "home"
2. Install **tabby-home**
3. Restart Tabby
4. Look for "Tabby Home" tab

### "No SSH sessions found"

**Cause:** PuTTY sessions are not configured as SSH.

**Solution:**
- Verify sessions in PuTTY are SSH protocol
- Check sessions are saved in Windows Registry
- Try export again

### "Import failed / Invalid JSON"

**Solution:**
```bash
# Validate JSON file
cat tabby-config.json | jq .
# Or on Windows:
type tabby-config.json | jq .

# Re-export if needed
putty-migrate tabby -o tabby-config-new.json
```

### Sessions Imported but Not Connecting

**Solution:**
1. Check hostname is reachable: `ping hostname`
2. Verify SSH port is accessible
3. Update SSH key paths in Tabby session settings
4. Test with native ssh: `ssh user@hostname`

### "Plugin not found"

**Possible Issue:** Plugin registry not updated.

**Solution:**
1. Restart Tabby
2. Settings → Plugins → Click refresh
3. Search again for "home"
4. Manually install from: https://github.com/Eugeny/tabby-home

---

## 💡 Tips & Best Practices

### Organize Before Import

```bash
# Export to review first
putty-migrate tabby -o preview.json

# Review the JSON
cat preview.json

# When satisfied, import to Tabby
```

### Regular Backups

Tabby can sync profiles, but manual backups are good practice:

```bash
# Regular exports
putty-migrate tabby -o "backups/tabby-$(date +%Y%m%d).json"
```

### Combine with Other Tools

```bash
# Export to multiple formats
putty-migrate convert --to-ssh      # Convert keys
putty-migrate tabby                  # Tabby terminal
putty-migrate ssh-config             # SSH config for native ssh
putty-migrate bitwarden --auto-convert  # Bitwarden vault
```

### Multi-Device Setup

1. Export on Windows machine (where PuTTY runs)
2. Copy `tabby-config.json` to other devices
3. Import on each device's Tabby installation
4. Or use Tabby's built-in profile sync feature

---

## 🔄 Workflow

### Complete Migration Workflow

```bash
# 1. Convert PPK keys
putty-migrate convert

# 2. Export to Tabby
putty-migrate tabby

# 3. Open Tabby
# 4. Install tabby-home plugin
# 5. Import via Tabby Home → Import Connection

# 6. Test connections
# 7. Customize as needed in Tabby settings
```

---

## 🆚 Tabby vs Traditional SSH

### Traditional `ssh` Command
- ✅ Lightweight and fast
- ✅ Universal (installed everywhere)
- ❌ No GUI
- ❌ Manual session management
- ❌ Limited customization

### Tabby Terminal
- ✅ Beautiful GUI
- ✅ Session bookmarks and organization
- ✅ Themes and customization
- ✅ Multi-pane layouts
- ❌ Requires installation
- ❌ GUI-only (not for servers)

**Best Approach:** Use both!
- Tabby for interactive work
- Native `ssh` for scripts and servers

---

## 🚀 Next Steps

- **[Tabby Official Docs](https://tabby.sh/)** - Learn more about Tabby
- **[SSH Config Guide](ssh-config.md)** - Alternative OpenSSH approach
- **[Bitwarden Guide](bitwarden.md)** - Centralized key management
- **[PPK Conversion Guide](convert-ppk.md)** - Convert more keys

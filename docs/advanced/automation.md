# Automation & Scripting

Automate PuTTY migrations with scripts and CI/CD pipelines.

---

## 🤖 Shell Scripts

### Bash (Linux)

```bash
#!/bin/bash
# Complete PuTTY migration script

set -e  # Exit on error

echo "🚀 Starting PuTTY migration..."

# 1. Convert PPK keys and copy to ~/.ssh
echo "📦 Converting PPK keys..."
putty-migrate convert --to-ssh --conflict rename -v

# 2. Export to Bitwarden
echo "🔐 Exporting to Bitwarden..."
putty-migrate bitwarden --auto-convert --non-interactive

# 3. Generate SSH config
echo "⚙️ Generating SSH config..."
putty-migrate ssh-config --non-interactive

# 4. Export to Tabby
echo "🖥️ Exporting to Tabby..."
putty-migrate tabby -o ~/backups/tabby-$(date +%Y%m%d).json

# 5. Backup original PPKs
echo "💾 Backing up PPK files..."
tar -czf ~/backups/ppk-backup-$(date +%Y%m%d).tar.gz ppk_keys/

echo "✅ Migration complete!"
echo "📂 Backups saved to: ~/backups/"
```

### PowerShell (Windows)

```powershell
# Complete PuTTY migration script
$ErrorActionPreference = "Stop"

Write-Host "🚀 Starting PuTTY migration..." -ForegroundColor Green

try {
    # 1. Convert PPK keys
    Write-Host "📦 Converting PPK keys..."
    & putty-migrate convert -v
    
    # 2. Export to Bitwarden
    Write-Host "🔐 Exporting to Bitwarden..."
    & putty-migrate bitwarden --auto-convert --non-interactive
    
    # 3. Export to Tabby
    Write-Host "🖥️ Exporting to Tabby..."
    $date = Get-Date -Format "yyyyMMdd"
    & putty-migrate tabby -o "C:\Backups\tabby-$date.json"
    
    # 4. Backup PPK files
    Write-Host "💾 Backing up PPK files..."
    Compress-Archive -Path "ppk_keys\*" -DestinationPath "C:\Backups\ppk-backup-$date.zip"
    
    Write-Host "✅ Migration complete!" -ForegroundColor Green
    Write-Host "📂 Backups saved to: C:\Backups\"
}
catch {
    Write-Host "❌ Error: $_" -ForegroundColor Red
    exit 1
}
```

---

## 🔄 CI/CD Integration

### GitHub Actions

```yaml
name: Backup PuTTY Sessions

on:
  schedule:
    - cron: '0 2 * * 0'  # Weekly on Sunday at 2 AM
  workflow_dispatch:  # Manual trigger

jobs:
  backup:
    runs-on: ubuntu-latest
    
    steps:
      - name: Checkout repository
        uses: actions/checkout@v3
      
      - name: Download PuTTY Migration Tools
        run: |
          wget https://github.com/badguy2003st/putty-migration-tools/releases/download/v1.0.0/putty-migrate-v1.0.0-linux
          chmod +x putty-migrate-v1.0.0-linux
          mv putty-migrate-v1.0.0-linux putty-migrate
      
      - name: Convert and export
        run: |
          ./putty-migrate convert --dry-run
          ./putty-migrate tabby -o putty-backup.json
      
      - name: Upload artifacts
        uses: actions/upload-artifact@v3
        with:
          name: putty-backups-${{ github.run_number }}
          path: |
            putty-backup.json
            openssh_keys/
          retention-days: 90
      
      - name: Commit to backup branch
        run: |
          git config user.name "GitHub Actions"
          git config user.email "actions@github.com"
          git checkout -b backup-$(date +%Y%m%d) || git checkout backup-$(date +%Y%m%d)
          git add putty-backup.json
          git commit -m "Backup: $(date +%Y-%m-%d)"
          git push origin backup-$(date +%Y%m%d)
```

### GitLab CI

```yaml
# .gitlab-ci.yml
stages:
  - backup

backup-putty:
  stage: backup
  image: ubuntu:latest
  
  before_script:
    - apt-get update && apt-get install -y wget
  
  script:
    - wget https://github.com/badguy2003st/putty-migration-tools/releases/download/v1.0.0/putty-migrate-v1.0.0-linux
    - chmod +x putty-migrate-v1.0.0-linux
    - ./putty-migrate-v1.0.0-linux tabby -o backup.json
  
  artifacts:
    paths:
      - backup.json
      - openssh_keys/
    expire_in: 3 months
  
  only:
    - schedules
```

---

## 📅 Scheduled Backups

### Cron (Linux)

```bash
# Edit crontab
crontab -e

# Add weekly backup (Sunday 2 AM)
0 2 * * 0 /usr/local/bin/putty-migrate tabby -o ~/backups/tabby-$(date +\%Y\%m\%d).json

# Add monthly full migration (1st of month, 3 AM)
0 3 1 * * /home/user/scripts/migrate-putty.sh
```

### Windows Task Scheduler

```powershell
# Create scheduled task
$action = New-ScheduledTaskAction -Execute "putty-migrate.exe" -Argument "tabby -o C:\Backups\tabby.json"
$trigger = New-ScheduledTaskTrigger -Weekly -DaysOfWeek Sunday -At 2am
$settings = New-ScheduledTaskSettingsSet -StartWhenAvailable

Register-ScheduledTask -TaskName "PuTTY Backup" -Action $action -Trigger $trigger -Settings $settings
```

---

## 🔗 Integration Examples

### Ansible Playbook

```yaml
---
- name: Migrate PuTTY configurations
  hosts: workstations
  tasks:
    - name: Download PuTTY Migration Tools
      get_url:
        url: https://github.com/badguy2003st/putty-migration-tools/releases/download/v1.0.0/putty-migrate-v1.0.0-linux
        dest: /tmp/putty-migrate
        mode: '0755'
    
    - name: Convert PPK keys
      command: /tmp/putty-migrate convert --to-ssh --conflict rename
      args:
        chdir: "/home/{{ ansible_user }}"
    
    - name: Generate SSH config
      command: /tmp/putty-migrate ssh-config --non-interactive
      args:
        chdir: "/home/{{ ansible_user }}"
```

### Docker Container

```dockerfile
FROM python:3.10-slim

# Install dependencies
RUN pip install textual>=0.41.0 rich>=13.0.0 puttykeys>=1.0.3

# Copy source
COPY putty-migration-tools /app
WORKDIR /app

# Entry point
ENTRYPOINT ["python", "-m", "tui"]
CMD ["--help"]
```

Usage:
```bash
# Build
docker build -t putty-migrate .

# Run
docker run -v /path/to/ppk_keys:/app/ppk_keys putty-migrate convert
```

---

## 🧪 Testing Scripts

### Validate Before Production

```bash
#!/bin/bash
# Test migration script

# 1. Dry run
echo "Testing conversion..."
if putty-migrate convert --dry-run; then
    echo "✅ Conversion test passed"
else
    echo "❌ Conversion test failed"
    exit 1
fi

# 2. Test export
echo "Testing export..."
if putty-migrate tabby --dry-run 2>/dev/null; then
    echo "✅ Export test passed"
else
    echo "❌ Export test failed"
    exit 1
fi

echo "✅ All tests passed!"
```

---

## 💡 Best Practices

### Error Handling

```bash
#!/bin/bash
# Robust error handling

convert_keys() {
    if putty-migrate convert --to-ssh --conflict rename -v; then
        echo "✅ Conversion successful"
        return 0
    else
        echo "❌ Conversion failed"
        return 1
    fi
}

# Run with error handling
if ! convert_keys; then
    echo "Sending alert..."
    # Send notification (email, Slack, etc.)
    exit 1
fi
```

### Logging

```bash
#!/bin/bash
# Complete logging

LOG_FILE="migration-$(date +%Y%m%d-%H%M%S).log"

{
    echo "=== Migration started at $(date) ==="
    
    putty-migrate convert --to-ssh -v
    putty-migrate bitwarden --auto-convert -v
    putty-migrate tabby -v
    
    echo "=== Migration completed at $(date) ==="
} 2>&1 | tee "$LOG_FILE"

echo "📝 Log saved to: $LOG_FILE"
```

### Notifications

```bash
#!/bin/bash
# Email notification

RESULT=$(putty-migrate convert --to-ssh 2>&1)
STATUS=$?

if [ $STATUS -eq 0 ]; then
    echo "$RESULT" | mail -s "✅ PuTTY Migration Success" admin@example.com
else
    echo "$RESULT" | mail -s "❌ PuTTY Migration Failed" admin@example.com
fi
```

---

## 🚀 Next Steps

- **[CLI Guide](../guides/binary/cli.md)** - All CLI options
- **[Security Guide](security.md)** - Security best practices
- **[Conflict Handling](conflict-handling.md)** - Manage key conflicts

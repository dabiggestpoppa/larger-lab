# Workspace Backup & Portability Guide

## Quick Start

### Backup Everything (USB + Git + Cloud)
```powershell
.\backup-workspace.ps1 -FullBackup
```

### Restore on New Computer
```powershell
# From USB drive (auto-detected)
.\restore-workspace.ps1 -Source USB

# From Git only
.\restore-workspace.ps1 -Source Git

# From both
.\restore-workspace.ps1 -Source Both -DriveLetter E
```

### One-Command Setup on New Computer
```powershell
curl -fsSL https://raw.githubusercontent.com/dabiggestpoppa/larger-lab/main/quick-setup.ps1 | pwsh -File -
```

---

## Backup Options

| Command | What it does |
|---------|--------------|
| `.\backup-workspace.ps1` | USB sync only |
| `.\backup-workspace.ps1 -PushGit` | USB + Git push |
| `.\backup-workspace.ps1 -CloudSync` | USB + Cloud (rclone) |
| `.\backup-workspace.ps1 -FullBackup` | USB + Git + Cloud |

---

## What Gets Backed Up

### USB Sync (`usb-mesh.ps1`)
- `data/` - Market data
- `models/` - Trained models
- `backtests/` - Backtest results
- `strategies/` - Strategy code
- `notebooks/` - Jupyter notebooks
- `nautilus/data/` - Nautilus data

### Git Backup
- All code, configs, documentation
- `pyproject.toml`, `requirements.txt`
- Skills lock file
- Workspace settings

### Cloud Sync (rclone)
- Critical config files
- `data/` directory

---

## Restore Options

| Source | When to use |
|--------|-------------|
| **Git** | Fresh computer, no USB |
| **USB** | Have USB drive with data |
| **Both** | USB + latest code from Git |

---

## Requirements

### For Backup
- USB drive (formatted, labeled)
- rclone configured (optional, for cloud sync)
- Git credentials set up

### For Restore
- PowerShell 5.1+
- Git installed
- Node.js 24+ (for OpenClaw)
- Python 3.12+ (for uv)

---

## Cloud Server Setup

To provision a cloud VM with this workspace:

```bash
# On the VM
curl -fsSL https://raw.githubusercontent.com/dabiggestpoppa/larger-lab/main/usb-cloud/agent-setup.sh | bash
```

Or use the Kamatera setup:
```powershell
.\kamatera-setup.ps1 -ApiKey "YOUR_KEY" -ApiSecret "YOUR_SECRET"
```

---

## File Reference

| File | Purpose |
|------|---------|
| `backup-workspace.ps1` | Main backup script |
| `restore-workspace.ps1` | Restore on new machine |
| `quick-setup.ps1` | One-command fresh setup |
| `usb-mesh.ps1` | USB sync utility |
| `usb-cloud/agent-setup.sh` | Cloud VM setup |
| `usb-cloud/kamatera-setup.ps1` | Kamatera provisioning |
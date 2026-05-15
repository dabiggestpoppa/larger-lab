# backup-workspace.ps1 - Complete workspace backup to USB + Git + Cloud
# Usage: .\backup-workspace.ps1 [-PushGit] [-CloudSync]
# Note: Run with -ExecutionPolicy Bypass if blocked:
# powershell -ExecutionPolicy Bypass -File backup-workspace.ps1 -PushGit

param(
    [switch]$PushGit,
    [switch]$CloudSync,
    [switch]$FullBackup
)

# Auto-detect workspace root
$ScriptDir = Split-Path -Parent $MyInvocation.MyCommand.Path
$WorkspaceRoot = $ScriptDir
$StorageDir = "agent-storage"
$LogFile = "$WorkspaceRoot\usb-cloud\backup.log"

function Write-Log {
    param([string]$Message, [string]$Level = "INFO")
    $ts = Get-Date -Format "yyyy-MM-dd HH:mm:ss"
    $line = "[$ts] [$Level] $Message"
    Write-Host $line
    Add-Content -Path $LogFile -Value $line -ErrorAction SilentlyContinue
}

function Get-USBDrives {
    Get-WmiObject Win32_LogicalDisk | Where-Object { $_.DriveType -eq 2 } | ForEach-Object {
        @{
            Letter = $_.DeviceID
            Label = $_.VolumeName
            FreeGB = [math]::Round($_.FreeSpace / 1GB, 1)
        }
    }
}

function Invoke-GitBackup {
    Write-Log "Starting Git backup..."
    Push-Location $WorkspaceRoot
    
    # Check for changes
    $status = git status --porcelain
    if ($status) {
        Write-Log "Changes detected, committing..."
        git add -A
        $commitMsg = "Backup: $(Get-Date -Format 'yyyy-MM-dd HH:mm')"
        git commit -m $commitMsg
        if ($LASTEXITCODE -eq 0) {
            Write-Log "Commit created: $commitMsg"
            git push origin master
            if ($LASTEXITCODE -eq 0) {
                Write-Log "Pushed to GitHub successfully"
            } else {
                Write-Log "Git push failed" "ERROR"
            }
        }
    } else {
        Write-Log "No changes to commit"
    }
    Pop-Location
}

function Invoke-USBBackup {
    Write-Log "Starting USB backup..."
    $usb = Get-USBDrives
    if ($usb.Count -eq 0) {
        Write-Log "No USB drives detected!" "ERROR"
        return
    }
    
    foreach ($drive in $usb) {
        $destBase = "$($drive.Letter)\$StorageDir"
        if (!(Test-Path $destBase)) {
            Write-Log "Running USB setup first..." "WARN"
            & "$WorkspaceRoot\usb-cloud\usb-mesh.ps1" setup
        }
        
        # Sync critical directories
        $syncPaths = @("data", "models", "backtests", "strategies", "notebooks", "nautilus\data")
        foreach ($relPath in $syncPaths) {
            $source = Join-Path $WorkspaceRoot $relPath
            $dest = Join-Path $destBase $relPath
            if (Test-Path $source) {
                $parent = Split-Path $dest -Parent
                if (!(Test-Path $parent)) { New-Item -ItemType Directory -Path $parent -Force | Out-Null }
                robocopy "$source" "$dest" /MIR /MT:8 /R:2 /W:5 /NP /NFL /NDL | Out-Null
                if ($LASTEXITCODE -le 7) {
                    Write-Log "Synced: $relPath -> $($drive.Letter)"
                }
            }
        }
        
        # Copy critical config files
        $configFiles = @("pyproject.toml", "requirements.txt", "skills-lock.json", "CLAUDE.md", "AGENTS.md", "SOUL.md")
        foreach ($file in $configFiles) {
            $src = Join-Path $WorkspaceRoot $file
            if (Test-Path $src) {
                Copy-Item $src "$destBase\$file" -Force
            }
        }
    }
    Write-Log "USB backup complete"
}

function Invoke-CloudBackup {
    Write-Log "Starting cloud backup..."
    & "$WorkspaceRoot\usb-cloud\usb-mesh.ps1" cloud-sync
    Write-Log "Cloud backup complete"
}

# Main execution
Write-Log "========================================="
Write-Log "Workspace Backup Started"
Write-Log "========================================="

if ($FullBackup -or $PushGit) {
    Invoke-GitBackup
}

Invoke-USBBackup

if ($FullBackup -or $CloudSync) {
    Invoke-CloudBackup
}

Write-Log "========================================="
Write-Log "Backup Complete!"
Write-Log "========================================="
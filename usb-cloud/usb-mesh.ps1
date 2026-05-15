# usb-mesh.ps1 - USB Cloud Storage Mesh
param(
    [Parameter(Position=0)]
    [ValidateSet("setup", "sync", "status", "cloud-sync", "auto")]
    [string]$Action = "status"
)

$Config = @{
    StorageDir    = "agent-storage"
    WorkspaceRoot = "C:\Users\wifik\Desktop\projects\larger-lab"
    SyncPaths     = @("data", "models", "backtests", "strategies", "nautilus\data", "notebooks")
    LocalOnly     = @(".venv", "node_modules", ".git", "nautilus_trader")
    CloudTargets  = @("gdrive:agent-backup", "mega:agent-backup")
    LogFile       = "C:\Users\wifik\Desktop\projects\larger-lab\usb-cloud\mesh.log"
}

function Write-Log {
    param([string]$Message, [string]$Level = "INFO")
    $ts = Get-Date -Format "yyyy-MM-dd HH:mm:ss"
    $line = "[$ts] [$Level] $Message"
    Write-Host $line
    Add-Content -Path $Config.LogFile -Value $line -ErrorAction SilentlyContinue
}

function Get-USBDrives {
    $drives = @()
    Get-WmiObject Win32_LogicalDisk | Where-Object { $_.DriveType -eq 2 } | ForEach-Object {
        $drives += @{
            Letter     = $_.DeviceID
            Label      = $_.VolumeName
            SizeGB     = [math]::Round($_.Size / 1GB, 1)
            FreeGB     = [math]::Round($_.FreeSpace / 1GB, 1)
            UsedGB     = [math]::Round(($_.Size - $_.FreeSpace) / 1GB, 1)
            FileSystem = $_.FileSystem
        }
    }
    return $drives
}

function Invoke-Setup {
    Write-Log "Setting up USB Cloud Storage Mesh..."
    $usb = Get-USBDrives
    if ($usb.Count -eq 0) { Write-Log "No USB drives detected!" "ERROR"; return }
    foreach ($drive in $usb) {
        $storagePath = "$($drive.Letter)\$($Config.StorageDir)"
        if (!(Test-Path $storagePath)) {
            New-Item -ItemType Directory -Path $storagePath -Force | Out-Null
            Write-Log "Created: $storagePath"
        }
        foreach ($subDir in $Config.SyncPaths) {
            $fullPath = Join-Path $storagePath $subDir
            if (!(Test-Path $fullPath)) { New-Item -ItemType Directory -Path $fullPath -Force | Out-Null }
        }
        "USB Cloud Storage Mesh`nInitialized: $(Get-Date)`nDrive: $($drive.Letter)`nLabel: $($drive.Label)" |
            Set-Content "$storagePath\usb-cloud-mesh.txt"
        Write-Log "Configured: $($drive.Letter) ($($drive.Label))"
    }
    $cacheDir = Join-Path $Config.WorkspaceRoot "usb-cloud\cache"
    if (!(Test-Path $cacheDir)) { New-Item -ItemType Directory -Path $cacheDir -Force | Out-Null }
    Write-Log "Setup complete."
}

function Invoke-Sync {
    Write-Log "Starting workspace -> USB sync..."
    $usb = Get-USBDrives
    if ($usb.Count -eq 0) { Write-Log "No USB drives detected!" "ERROR"; return }
    foreach ($drive in $usb) {
        $destBase = "$($drive.Letter)\$($Config.StorageDir)"
        if (!(Test-Path $destBase)) { Write-Log "Not found on $($drive.Letter), run setup first" "WARN"; continue }
        foreach ($relPath in $Config.SyncPaths) {
            $source = Join-Path $Config.WorkspaceRoot $relPath
            $dest   = Join-Path $destBase $relPath
            if (!(Test-Path $source)) { Write-Log "Skip (not found): $relPath" "WARN"; continue }
            $parent = Split-Path $dest -Parent
            if (!(Test-Path $parent)) { New-Item -ItemType Directory -Path $parent -Force | Out-Null }
            Write-Log "Syncing: $relPath -> $($drive.Letter)"
            $proc = Start-Process -FilePath "robocopy" -ArgumentList "`"$source`"", "`"$dest`"", "/MIR", "/MT:8", "/R:2", "/W:5", "/NP", "/NFL", "/NDL" -Wait -PassThru -NoNewWindow
            if ($proc.ExitCode -le 7) { Write-Log "OK: $relPath -> $($drive.Letter)" } else { Write-Log "ERROR: $relPath -> $($drive.Letter) exit=$($proc.ExitCode)" "ERROR" }
        }
    }
    Write-Log "Sync complete."
}

function Invoke-CloudSync {
    Write-Log "Starting cloud sync..."
    $rclone = Get-Command rclone -ErrorAction SilentlyContinue
    if (!$rclone) { Write-Log "rclone not found. Install from https://rclone.org" "ERROR"; return }
    $criticalFiles = @("CLAUDE.md", "SOUL.md", "AGENTS.md", "TOOLS.md", "PROJECT_PROGRESS.md", "pyproject.toml", "requirements.txt")
    foreach ($target in $Config.CloudTargets) {
        Write-Log "Syncing to $target..."
        foreach ($file in $criticalFiles) {
            $source = Join-Path $Config.WorkspaceRoot $file
            if (Test-Path $source) {
                & rclone copy $source $target/workspace/ --transfers 4 --quiet 2>&1
                if ($LASTEXITCODE -eq 0) { Write-Log "  OK: $file" } else { Write-Log "  FAIL: $file" "ERROR" }
            }
        }
        $dataDir = Join-Path $Config.WorkspaceRoot "data"
        if (Test-Path $dataDir) { & rclone sync $dataDir "$target/data/" --transfers 8 --quiet 2>&1; Write-Log "  OK: data/" }
    }
    Write-Log "Cloud sync complete."
}

function Invoke-Status {
    $usb = Get-USBDrives
    $wsSize = 0
    if (Test-Path $Config.WorkspaceRoot) { $wsSize = (Get-ChildItem $Config.WorkspaceRoot -Recurse -File -ErrorAction SilentlyContinue | Measure-Object -Property Length -Sum).Sum }
    Write-Host ""; Write-Host "============================================================"
    Write-Host "  USB Cloud Storage Mesh - Status"
    Write-Host "============================================================"
    Write-Host " Workspace: $($Config.WorkspaceRoot)"
    Write-Host " Workspace Size: $([math]::Round($wsSize / 1GB, 2)) GB"
    Write-Host "------------------------------------------------------------"
    if ($usb.Count -eq 0) { Write-Host " WARNING: No USB drives detected" } else {
        foreach ($drive in $usb) {
            $pct = [math]::Round(($drive.UsedGB / $drive.SizeGB) * 100, 1)
            Write-Host " Drive $($drive.Letter) [$($drive.Label)]"
            Write-Host "   Total: $($drive.SizeGB) GB | Free: $($drive.FreeGB) GB | Used: $pct%"
            Write-Host "   Storage: $($drive.Letter)\$($Config.StorageDir)"; Write-Host ""
        }
    }
    Write-Host "------------------------------------------------------------"
    Write-Host " Cloud Targets:"; foreach ($t in $Config.CloudTargets) { Write-Host "   $t" }
    Write-Host "============================================================"; Write-Host ""
}

function Invoke-Auto {
    Write-Log "Auto mode..."
    $usb = Get-USBDrives
    if ($usb.Count -eq 0) { Write-Log "No USB drives connected." "WARN"; return }
    foreach ($drive in $usb) { $sp = "$($drive.Letter)\$($Config.StorageDir)"; if (!(Test-Path $sp)) { Invoke-Setup; break } }
    Invoke-Sync
    $statusFile = Join-Path $Config.WorkspaceRoot "usb-cloud\status.json"
    $usb | ConvertTo-Json -Depth 3 | Set-Content $statusFile
    Write-Log "Status written to $statusFile"
}

switch ($Action) {
    "setup"      { Invoke-Setup }
    "sync"       { Invoke-Sync }
    "status"     { Invoke-Status }
    "cloud-sync" { Invoke-CloudSync }
    "auto"       { Invoke-Auto }
    default      { Invoke-Status }
}

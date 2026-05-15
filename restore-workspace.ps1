# restore-workspace.ps1 - Restore workspace on new computer from USB or Git
# Usage: .\restore-workspace.ps1 -Source USB -DriveLetter E
#        .\restore-workspace.ps1 -Source Git -RepoUrl https://github.com/dabiggestpoppa/larger-lab

param(
    [Parameter(Mandatory=$true)]
    [ValidateSet("USB", "Git", "Both")]
    [string]$Source,
    
    [string]$DriveLetter,
    [string]$RepoUrl = "https://github.com/dabiggestpoppa/larger-lab",
    [string]$Branch = "master"
)

# Auto-detect workspace root
$ScriptDir = Split-Path -Parent $MyInvocation.MyCommand.Path
$WorkspaceRoot = $ScriptDir
$StorageDir = "agent-storage"
$LogFile = "$WorkspaceRoot\usb-cloud\restore.log"

function Write-Log {
    param([string]$Message, [string]$Level = "INFO")
    $ts = Get-Date -Format "yyyy-MM-dd HH:mm:ss"
    $line = "[$ts] [$Level] $Message"
    Write-Host $line
    if (Test-Path (Split-Path $LogFile)) {
        Add-Content -Path $LogFile -Value $line -ErrorAction SilentlyContinue
    }
}

function Install-Dependencies {
    Write-Log "Installing dependencies..."
    
    # Install uv if not present
    if (!(Get-Command uv -ErrorAction SilentlyContinue)) {
        Write-Log "Installing uv..."
        irm https://astral.sh/uv/install.ps1 | iex
    }
    
    # Install Python dependencies
    if (Test-Path "$WorkspaceRoot\pyproject.toml") {
        Write-Log "Installing Python packages with uv..."
        Push-Location $WorkspaceRoot
        uv sync
        Pop-Location
    }
    
    # Install Node.js dependencies if package.json exists
    if (Test-Path "$WorkspaceRoot\package.json") {
        Write-Log "Installing npm packages..."
        Push-Location $WorkspaceRoot
        npm install
        Pop-Location
    }
}

function Install-OpenClaw {
    Write-Log "Installing OpenClaw..."
    if (!(Get-Command openclaw -ErrorAction SilentlyContinue)) {
        npm install -g openclaw@latest
    }
    
    # Configure OpenClaw
    $configDir = "$env:USERPROFILE\.openclaw"
    if (!(Test-Path $configDir)) {
        New-Item -ItemType Directory -Path $configDir -Force | Out-Null
    }
    
    # Copy workspace config if exists
    if (Test-Path "$WorkspaceRoot\usb-cloud\openclaw.json") {
        Copy-Item "$WorkspaceRoot\usb-cloud\openclaw.json" "$configDir\openclaw.json" -Force
    }
}

function Restore-FromGit {
    Write-Log "Restoring from Git..."
    
    if (Test-Path $WorkspaceRoot) {
        Write-Log "Workspace exists, pulling latest..."
        Push-Location $WorkspaceRoot
        git fetch origin
        git reset --hard origin/$Branch
        Pop-Location
    } else {
        Write-Log "Cloning repository..."
        git clone $RepoUrl $WorkspaceRoot
        Push-Location $WorkspaceRoot
        git checkout $Branch
        Pop-Location
    }
    
    Write-Log "Git restore complete"
}

function Restore-FromUSB {
    param([string]$Drive)
    
    Write-Log "Restoring from USB ($Drive)..."
    
    $usbPath = "$Drive\$StorageDir"
    if (!(Test-Path $usbPath)) {
        Write-Log "USB storage not found at $usbPath" "ERROR"
        return
    }
    
    # Restore directories
    $syncPaths = @("data", "models", "backtests", "strategies", "notebooks")
    foreach ($relPath in $syncPaths) {
        $src = Join-Path $usbPath $relPath
        $dest = Join-Path $WorkspaceRoot $relPath
        if (Test-Path $src) {
            Write-Log "Restoring: $relPath"
            robocopy "$src" "$dest" /MIR /MT:8 /R:2 /W:5 /NP /NFL /NDL | Out-Null
        }
    }
    
    Write-Log "USB restore complete"
}

# Main execution
Write-Log "========================================="
Write-Log "Workspace Restore Started"
Write-Log "========================================="

# Create workspace directory
if (!(Test-Path $WorkspaceRoot)) {
    New-Item -ItemType Directory -Path $WorkspaceRoot -Force | Out-Null
}

if ($Source -eq "Git" -or $Source -eq "Both") {
    Restore-FromGit
}

if ($Source -eq "USB" -or $Source -eq "Both") {
    if (-not $DriveLetter) {
        $drives = Get-WmiObject Win32_LogicalDisk | Where-Object { $_.DriveType -eq 2 }
        if ($drives.Count -eq 0) {
            Write-Log "No USB drives detected!" "ERROR"
            exit 1
        }
        $DriveLetter = $drives[0].DeviceID
        Write-Log "Auto-detected USB: $DriveLetter"
    }
    Restore-FromUSB -Drive $DriveLetter
}

Install-Dependencies
Install-OpenClaw

Write-Log "========================================="
Write-Log "Restore Complete!"
Write-Log "========================================="
Write-Log ""
Write-Log "Next steps:"
Write-Log "1. Run 'uv sync' to install Python dependencies"
Write-Log "2. Run 'npm install' if using Node.js tools"
Write-Log "3. Configure .env with your API keys"
Write-Log "4. Run backup-workspace.ps1 -PushGit to push any changes"
# quick-setup.ps1 - One-command setup on new computer
# Usage: curl -fsSL https://raw.githubusercontent.com/dabiggestpoppa/larger-lab/main/quick-setup.ps1 | pwsh -File -

param(
    [string]$RepoUrl = "https://github.com/dabiggestpoppa/larger-lab",
    [string]$Branch = "master",
    [string]$WorkspacePath = "C:\Users\$env:USERNAME\Desktop\projects\larger-lab"
)

Write-Host "========================================="
Write-Host "  Quick Workspace Setup"
Write-Host "========================================="

# Install prerequisites
Write-Host "[1/5] Installing prerequisites..."

# Install uv (Python package manager)
if (!(Get-Command uv -ErrorAction SilentlyContinue)) {
    Write-Host "  Installing uv..."
    irm https://astral.sh/uv/install.ps1 | iex
}

# Install Node.js if not present
if (!(Get-Command node -ErrorAction SilentlyContinue)) {
    Write-Host "  Installing Node.js 24..."
    curl -fsSL https://deb.nodesource.com/setup_24.x | bash - 2>$null
    # Note: On Windows, download from https://nodejs.org
}

# Install OpenClaw
Write-Host "[2/5] Installing OpenClaw..."
if (!(Get-Command openclaw -ErrorAction SilentlyContinue)) {
    npm install -g openclaw@latest
}

# Clone workspace
Write-Host "[3/5] Cloning workspace..."
if (!(Test-Path $WorkspacePath)) {
    git clone $RepoUrl $WorkspacePath
    Push-Location $WorkspacePath
    git checkout $Branch
    Pop-Location
} else {
    Write-Host "  Workspace already exists at $WorkspacePath"
}

# Install dependencies
Write-Host "[4/5] Installing dependencies..."
Push-Location $WorkspacePath
uv sync
Pop-Location

# Configure OpenClaw
Write-Host "[5/5] Configuring OpenClaw..."
$configDir = "$env:USERPROFILE\.openclaw"
if (!(Test-Path $configDir)) {
    New-Item -ItemType Directory -Path $configDir -Force | Out-Null
}

$config = @{
    agents = @{
        defaults = @{
            workspace = $WorkspacePath
            model = "poolside/laguna-m.1:free"
        }
    }
    gateway = @{
        mode = "local"
        port = 18789
        bind = "loopback"
    }
} | ConvertTo-Json -Depth 5

$config | Set-Content "$configDir\openclaw.json"

Write-Host ""
Write-Host "========================================="
Write-Host "  Setup Complete!"
Write-Host "========================================="
Write-Host ""
Write-Host "Workspace: $WorkspacePath"
Write-Host ""
Write-Host "Next steps:"
Write-Host "  1. Create .env file with your API keys"
Write-Host "  2. Run: backup-workspace.ps1 -PushGit"
Write-Host "  3. Open VS Code: code $WorkspacePath"
Write-Host ""
# kamatera-setup.ps1 - Provision Kamatera VM for agent workspace
# Usage: .\kamatera-setup.ps1 -ApiKey "your-api-key" -ApiSecret "your-api-secret"

param(
    [Parameter(Mandatory=$true)]
    [string]$ApiKey,
    
    [Parameter(Mandatory=$true)]
    [string]$ApiSecret,
    
    [string]$ServerName = "larger-lab-agent",
    [string]$Datacenter = "US-NY2",
    [string]$Image = "Ubuntu 24.04",
    [string]$Cpu = "2B",
    [int]$Ram = 4096,
    [int]$DiskSize = 50
)

$CloudCli = ".\cloudcli.exe"

Write-Host "============================================="
Write-Host "  Kamatera Agent Rig Setup"
Write-Host "============================================="

# Check if cloudcli exists
if (-not (Test-Path $CloudCli)) {
    Write-Host "Downloading cloudcli..."
    Invoke-WebRequest -Uri "https://cloudcli.cloudwm.com/binaries/latest/cloudcli-windows-amd64.zip" -OutFile "cloudcli.zip"
    Expand-Archive -Path "cloudcli.zip" -DestinationPath "."
}

# List available options first
Write-Host "`n[1/3] Checking available server options..."
& $CloudCli server options --datacenter --image --cpu --ram --disk --api-clientid $ApiKey --api-secret $ApiSecret 2>&1 | Out-Null

# Create the server
Write-Host "`n[2/3] Creating server: $ServerName"
$createArgs = @(
    "server", "create",
    "--name", $ServerName,
    "--datacenter", $Datacenter,
    "--image", $Image,
    "--cpu", $Cpu,
    "--ram", $Ram,
    "--disk", "id=0,size=$DiskSize",
    "--network", "id=0,name=wan,ip=auto",
    "--password", "TempPass123!",
    "--api-clientid", $ApiKey,
    "--api-secret", $ApiSecret,
    "--wait"
)

& $CloudCli @createArgs

if ($LASTEXITCODE -eq 0) {
    Write-Host "`n[3/3] Server created successfully!" -ForegroundColor Green
    
    # Get server info
    Write-Host "`nServer details:"
    & $CloudCli server info --name $ServerName --api-clientid $ApiKey --api-secret $ApiSecret
    
    Write-Host "`nNext steps:"
    Write-Host "  1. SSH into the server: ssh root@SERVER_IP"
    Write-Host "  2. Install OpenClaw: curl -fsSL https://openclaw.sh | bash"
    Write-Host "  3. Clone workspace: git clone https://github.com/dabiggestpoppa/larger-lab.git"
    Write-Host "  4. Set up SSH tunnel: ssh -L 18789:127.0.0.1:18789 root@SERVER_IP"
} else {
    Write-Host "Failed to create server" -ForegroundColor Red
}
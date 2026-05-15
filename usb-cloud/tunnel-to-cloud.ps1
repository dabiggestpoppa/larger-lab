# tunnel-to-cloud.ps1 — SSH tunnel to Hetzner cloud VM
# Usage: .\tunnel-to-cloud.ps1 [start|stop|status]

param(
    [Parameter(Position=0)]
    [ValidateSet("start", "stop", "status")]
    [string]$Action = "start"
)

$SSH_KEY = "$env:USERPROFILE\.ssh\larger-lab"
$SERVER_IP = ""  # Will be filled after provisioning
$LOCAL_PORT = 18789
$REMOTE_PORT = 18789

# Read IP from config if exists
$configFile = Join-Path $PSScriptRoot "cloud-ip.txt"
if (Test-Path $configFile) {
    $SERVER_IP = (Get-Content $configFile).Trim()
}

switch ($Action) {
    "start" {
        if ([string]::IsNullOrEmpty($SERVER_IP)) {
            Write-Host "ERROR: No server IP found. Run hetzner-setup.sh first or set cloud-ip.txt"
            exit 1
        }
        Write-Host "Starting SSH tunnel to $SERVER_IP`:$REMOTE_PORT ..."
        Write-Host "Local access: ws://127.0.0.1:$LOCAL_PORT"
        Write-Host "Press Ctrl+C to stop."
        ssh -N -L "${LOCAL_PORT}:127.0.0.1:${REMOTE_PORT}" -i "$SSH_KEY" "root@${SERVER_IP}"
    }
    "stop" {
        Get-Process ssh -ErrorAction SilentlyContinue | Where-Object {
            $_.CommandLine -like "*larger-lab*"
        } | Stop-Process -Force
        Write-Host "Tunnel stopped."
    }
    "status" {
        $tunnel = Get-Process ssh -ErrorAction SilentlyContinue | Where-Object {
            $_.CommandLine -like "*larger-lab*"
        }
        if ($tunnel) {
            Write-Host "Tunnel is RUNNING (PID: $($tunnel.Id))"
        } else {
            Write-Host "Tunnel is NOT running."
        }
    }
}

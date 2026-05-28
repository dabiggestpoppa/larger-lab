# OC2 Gateway Watchdog
# Keeps OpenClaw gateway running. Run this in the background.
# Checks every 30 seconds. Restarts gateway if port 18790 is not listening.

param(
    [int]$CheckIntervalSeconds = 30,
    [int]$GatewayPort = 18790,
    [string]$LogFile = "C:\Users\wifik\AppData\Local\Temp\openclaw\watchdog.log"
)

function Write-Log {
    param([string]$Message)
    $ts = Get-Date -Format "yyyy-MM-dd HH:mm:ss"
    $line = "[$ts] $Message"
    Add-Content -Path $LogFile -Value $line -ErrorAction SilentlyContinue
    Write-Output $line
}

Write-Log "OC2 Watchdog started. Checking port $GatewayPort every ${CheckIntervalSeconds}s."

while ($true) {
    try {
        $tcp = New-Object System.Net.Sockets.TcpClient
        $connect = $tcp.BeginConnect("127.0.0.1", $GatewayPort, $null, $null)
        $wait = $connect.AsyncWaitHandle.WaitOne(3000, $false)
        if ($wait -and $tcp.Connected) {
            $tcp.Close()
            # Gateway is healthy
        } else {
            $tcp.Close()
            Write-Log "Gateway NOT responding on port $GatewayPort. Restarting..."
            
            # Kill any stale openclaw node processes
            Get-Process -Name "node" -ErrorAction SilentlyContinue | 
                Where-Object { $_.CommandLine -match "openclaw" } | 
                Stop-Process -Force -ErrorAction SilentlyContinue
            
            Start-Sleep -Seconds 2
            
            # Start gateway in background
            Start-Process -FilePath "openclaw" -ArgumentList "gateway run --port $GatewayPort" -WindowStyle Hidden
            Write-Log "Gateway restart initiated."
            
            # Wait for it to come up
            Start-Sleep -Seconds 10
        }
    } catch {
        Write-Log "Error checking gateway: $($_.Exception.Message)"
    }
    
    Start-Sleep -Seconds $CheckIntervalSeconds
}

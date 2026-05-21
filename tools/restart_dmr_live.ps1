# Kill existing DMR Live process
$dmr = Get-Process python -ErrorAction SilentlyContinue | Where-Object { $_.CommandLine -match 'dmr_live' }
if ($dmr) {
    Write-Output "Stopping DMR Live (PID $($dmr.Id))..."
    $dmr | Stop-Process -Force
    Start-Sleep -Seconds 3
} else {
    # Check by PID 5764
    $p = Get-Process -Id 5764 -ErrorAction SilentlyContinue
    if ($p) {
        Write-Output "Stopping PID 5764..."
        $p | Stop-Process -Force
        Start-Sleep -Seconds 3
    }
}

# Start fresh
Write-Output "Starting DMR Live v2.2 with 3 pairs..."
Start-Process -FilePath 'python' -ArgumentList 'C:\Users\wifik\Desktop\projects\larger-lab\quant-lab\mt5\dmr_live_v2.py' -WindowStyle Hidden
Start-Sleep -Seconds 5

# Verify
$procs = Get-Process python -ErrorAction SilentlyContinue
$found = $false
foreach ($p in $procs) {
    if ($p.Id -eq 5764 -or ($p.CommandLine -match 'dmr_live')) {
        Write-Output "DMR Live running: PID $($p.Id), Mem: $([math]::Round($p.WorkingSet64/1MB,1))MB"
        $found = $true
    }
}
if (-not $found) {
    Write-Output "DMR Live started (process may take a moment to appear in process list)"
}

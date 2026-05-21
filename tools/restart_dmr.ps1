$proc = Get-Process python -ErrorAction SilentlyContinue | Where-Object {$_.CommandLine -match 'dmr_live'}
if ($proc) {
    Write-Output "DMR already running: PID $($proc.Id)"
} else {
    Write-Output "Starting DMR Live..."
    Start-Process -FilePath 'python' -ArgumentList 'C:\Users\wifik\Desktop\projects\larger-lab\quant-lab\mt5\dmr_live_v2.py' -WindowStyle Hidden
    Start-Sleep -Seconds 5
    $proc = Get-Process python -ErrorAction SilentlyContinue | Where-Object {$_.CommandLine -match 'dmr_live'}
    if ($proc) {
        Write-Output "DMR started: PID $($proc.Id)"
    } else {
        Write-Output "DMR start command issued (process may take a moment to appear)"
    }
}

$procs = @(4016, 6280, 11592)
foreach ($pid in $procs) {
    $proc = Get-CimInstance Win32_Process -Filter "ProcessId=$pid" -ErrorAction SilentlyContinue
    if ($proc) {
        Write-Host "PID $pid : $($proc.CommandLine)"
    } else {
        Write-Host "PID $pid : NOT RUNNING"
    }
}

Write-Host "`n--- DMR Log Files ---"
$logDir = "C:\Users\wifik\Desktop\projects\larger-lab\quant-lab\mt5\logs"
if (Test-Path $logDir) {
    Get-ChildItem $logDir | Sort-Object LastWriteTime -Descending | Select-Object -First 5 Name, @{N='Size';E={$_.Length}}, LastWriteTime | Format-Table -AutoSize
} else {
    Write-Host "No logs directory"
}

Write-Host "`n--- DMR Live Script ---"
$liveScript = "C:\Users\wifik\Desktop\projects\larger-lab\quant-lab\mt5\dmr_live_v2.py"
if (Test-Path $liveScript) {
    $lines = Get-Content $liveScript -Tail 5
    Write-Host "Last 5 lines of dmr_live_v2.py:"
    $lines | ForEach-Object { Write-Host $_ }
}

Write-Host "`n--- DMR Config ---"
$configFile = "C:\Users\wifik\Desktop\projects\larger-lab\quant-lab\mt5\dmr_config.json"
if (Test-Path $configFile) {
    Get-Content $configFile | Write-Host
}

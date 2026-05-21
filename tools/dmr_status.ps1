Write-Host "=== DMR STATUS CHECK ==="
Write-Host ""

# Check DMR-related Python processes
$dmrPIDs = @(4016, 6280, 11592)
foreach ($pid in $dmrPIDs) {
    $proc = Get-CimInstance Win32_Process -Filter "ProcessId=$pid" -ErrorAction SilentlyContinue
    if ($proc) {
        $cmd = $proc.CommandLine
        if ($cmd.Length -gt 200) { $cmd = $cmd.Substring(0, 200) + "..." }
        Write-Host "PID $pid : RUNNING"
        Write-Host "  CMD: $cmd"
    } else {
        Write-Host "PID $pid : NOT RUNNING"
    }
}

Write-Host ""

# Check for dmr_live processes
Get-Process python -ErrorAction SilentlyContinue | ForEach-Object {
    $proc = Get-CimInstance Win32_Process -Filter "ProcessId=$($_.Id)" -ErrorAction SilentlyContinue
    if ($proc.CommandLine -match "dmr") {
        Write-Host "DMR Process PID $($_.Id): $($proc.CommandLine.Substring(0, [Math]::Min(200, $proc.CommandLine.Length)))"
    }
}

Write-Host ""

# Check DMR log
$logFile = "C:\Users\wifik\Desktop\projects\larger-lab\quant-lab\mt5\logs\dmr_live.log"
if (Test-Path $logFile) {
    Write-Host "=== Last 20 lines of DMR log ==="
    Get-Content $logFile -Tail 20 | ForEach-Object { Write-Host $_ }
} else {
    Write-Host "No DMR log found at expected path"
    # Try to find any recent log
    Get-ChildItem "C:\Users\wifik\Desktop\projects\larger-lab\quant-lab" -Recurse -Filter "*.log" -ErrorAction SilentlyContinue | Sort-Object LastWriteTime -Descending | Select-Object -First 3 FullName, LastWriteTime | Format-Table -AutoSize
}

Write-Host ""
Write-Host "=== DMR DB Status ==="
$dbPath = "C:\Users\wifik\Desktop\projects\larger-lab\quant-lab\mt5\dmr_live.db"
if (Test-Path $dbPath) {
    $db = Get-Item $dbPath
    Write-Host "DB Size: $($db.Length) bytes"
    Write-Host "Last Write: $($db.LastWriteTime)"
} else {
    Write-Host "DB not found"
}

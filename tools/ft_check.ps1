$ft = Get-Process -Id 4016 -ErrorAction SilentlyContinue
if ($ft) {
    Write-Output "Forward test PID 4016: RUNNING | Mem: $([math]::Round($ft.WorkingSet64/1MB,1))MB | Started: $($ft.StartTime)"
} else {
    Write-Output "Forward test PID 4016: NOT RUNNING"
}

# Check all python processes
Get-Process -Name "python" -ErrorAction SilentlyContinue | Select-Object Id, @{N='MemMB';E={[math]::Round($_.WorkingSet64/1MB,1)}}, StartTime | Format-Table -AutoSize | Out-String

# Check if MT5 is running
$mt5 = Get-Process -Name "Terminal64" -ErrorAction SilentlyContinue
if ($mt5) {
    Write-Output "MT5 Terminal64: RUNNING | PID: $($mt5.Id) | Mem: $([math]::Round($mt5.WorkingSet64/1MB,1))MB"
} else {
    Write-Output "MT5 Terminal64: NOT RUNNING"
}

# Check state file
$stateFile = "C:\Users\wifik\Desktop\projects\larger-lab\quant-lab\mt5\dmr_forward_test_state.json"
if (Test-Path $stateFile) {
    Write-Output "State file: $(Get-Content $stateFile)"
}

# Check log file
$logFile = "C:\Users\wifik\Desktop\projects\larger-lab\quant-lab\mt5\dmr_forward_test_log.csv"
if (Test-Path $logFile) {
    Write-Output "Log file exists: $(Get-Content $logFile -Tail 5)"
} else {
    Write-Output "No log file found"
}

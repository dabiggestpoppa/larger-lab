Start-Sleep -Seconds 5
$pyProcs = Get-Process -Name "python" -ErrorAction SilentlyContinue | Sort-Object StartTime -Descending | Select-Object -First 3
$pyProcs | ForEach-Object { Write-Output "Python PID=$($_.Id) Mem=$([math]::Round($_.WorkingSet64/1MB,1))MB Started=$($_.StartTime)" }

$stateFile = "C:\Users\wifik\Desktop\projects\larger-lab\quant-lab\mt5\dmr_live_state.json"
if (Test-Path $stateFile) { Write-Output "Live state: $(Get-Content $stateFile)" } else { Write-Output "No live state file" }

$logFile = "C:\Users\wifik\Desktop\projects\larger-lab\quant-lab\mt5\dmr_live_log.csv"
if (Test-Path $logFile) { Write-Output "Live log: $(Get-Content $logFile)" } else { Write-Output "No live log yet" }

# Check if there's a window title we can see
$procs = Get-Process -Name "python" -ErrorAction SilentlyContinue | Where-Object { $_.StartTime -gt (Get-Date).AddMinutes(-5) }
foreach ($p in $procs) {
    try {
        $mainWindow = $p.MainWindowTitle
        Write-Output "Window title: $mainWindow"
    } catch {
        Write-Output "PID $($p.Id): no window title"
    }
}

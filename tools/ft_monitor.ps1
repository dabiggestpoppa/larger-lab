Start-Sleep -Seconds 10
Get-Process -Name "python" -ErrorAction SilentlyContinue | Sort-Object StartTime -Descending | Select-Object -First 5 Id, @{N='MemMB';E={[math]::Round($_.WorkingSet64/1MB,1)}}, StartTime | Format-Table -AutoSize | Out-String
$stateFile = "C:\Users\wifik\Desktop\projects\larger-lab\quant-lab\mt5\dmr_live_state.json"
if (Test-Path $stateFile) { Write-Output "State: $(Get-Content $stateFile)" } else { Write-Output "No state file" }
$logFile = "C:\Users\wifik\Desktop\projects\larger-lab\quant-lab\mt5\dmr_live_log.csv"
if (Test-Path $logFile) { Write-Output "Log: $(Get-Content $logFile)" } else { Write-Output "No log file yet" }

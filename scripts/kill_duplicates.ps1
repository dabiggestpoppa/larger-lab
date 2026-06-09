# KILL_DUPLICATES.PS1 — Run this to permanently eliminate duplicate processes
# Usage: powershell -ExecutionPolicy Bypass -File scripts/kill_duplicates.ps1

$targets = @("cerebus_live_bridge", "signal_bot", "telegram_gateway", "twin_bridge")

Write-Host "=== KILLING ALL DUPLICATE TRADING PROCESSES ===" -ForegroundColor Red

# Kill ALL instances of target scripts
foreach ($target in $targets) {
    $procs = Get-CimInstance Win32_Process -Filter "Name = 'python.exe'" | Where-Object { $_.CommandLine -match $target }
    foreach ($proc in $procs) {
        Write-Host "Killing PID $($proc.ProcessId) : $($proc.CommandLine.Substring(0, [Math]::Min(80, $proc.CommandLine.Length)))"
        Stop-Process -Id $proc.ProcessId -Force -ErrorAction SilentlyContinue
    }
}

Start-Sleep -Seconds 3

# Verify
$remaining = Get-CimInstance Win32_Process -Filter "Name = 'python.exe'" | Where-Object { $_.CommandLine -match ($targets -join "|") }
Write-Host "`nRemaining processes: $($remaining.Count)" -ForegroundColor $(if($remaining.Count -eq 0){"Green"}else{"Red"})

# Now start ONE of each using ONLY venv python
$venv = "C:\Users\wifik\Desktop\projects\larger-lab\.venv\Scripts\python.exe"
$base = "C:\Users\wifik\Desktop\projects\larger-lab"

Write-Host "`n=== STARTING CLEAN INSTANCES ===" -ForegroundColor Green

# Bridge (using clean_bridge.py with singleton enforcement)
Start-Process -WindowStyle Hidden -FilePath $venv -ArgumentList "$base\quant-lab\mt5\clean_bridge.py","--symbols","EURJPY.PRO,EURNZD.PRO,GBPNZD.PRO,EURAUD.PRO,GBPAUD.PRO,GBPCAD.PRO,FR40.PRO","--lot-size","0.01" -WorkingDirectory "$base\quant-lab\mt5"
Write-Host "Bridge started (clean_bridge.py)"
Start-Sleep -Seconds 5

# Signal Bot
Start-Process -WindowStyle Hidden -FilePath $venv -ArgumentList "$base\scripts\signal_bot.py" -WorkingDirectory "$base"
Write-Host "Signal bot started"
Start-Sleep -Seconds 3

# Telegram
Start-Process -WindowStyle Hidden -FilePath $venv -ArgumentList "$base\scripts\telegram_gateway.py" -WorkingDirectory "$base"
Write-Host "Telegram started"
Start-Sleep -Seconds 5

# Final status
$final = Get-CimInstance Win32_Process -Filter "Name = 'python.exe'" | Where-Object { $_.CommandLine -match ($targets -join "|") }
Write-Host "`n=== FINAL STATUS ===" -ForegroundColor Cyan
foreach ($target in $targets) {
    $count = ($final | Where-Object { $_.CommandLine -match $target }).Count
    $color = if($count -eq 1){"Green"}elseif($count -eq 0){"Yellow"}else{"Red"}
    Write-Host "  $target : $count instances" -ForegroundColor $color
}

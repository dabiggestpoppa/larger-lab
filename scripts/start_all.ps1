# START_ALL.PS1 — Start all trading engines and servers
# Usage: powershell -ExecutionPolicy Bypass -File scripts/start_all.ps1
$ErrorActionPreference = "Continue"
$env:PYTHONIOENCODING = "utf-8"

$base = "C:\Users\wifik\Desktop\projects\larger-lab"
$venv = "$base\.venv\Scripts\python.exe"

Write-Host "=== KILLING EXISTING PYTHON PROCESSES ===" -ForegroundColor Yellow
Get-Process python -ErrorAction SilentlyContinue | Stop-Process -Force
Start-Sleep -Seconds 3

Write-Host "`n=== STARTING OCE BACKEND ===" -ForegroundColor Green
$p1 = Start-Process -FilePath $venv -ArgumentList "-m","oce.backend.main" -WorkingDirectory $base -WindowStyle Hidden -PassThru
Write-Host "  OCE Backend: PID $($p1.Id)"
Start-Sleep -Seconds 10
$oce = Get-NetTCPConnection -State Listen -LocalPort 8000 -ErrorAction SilentlyContinue
if ($oce) { Write-Host "  OCE Backend UP (port 8000)" } else { Write-Host "  OCE Backend NOT UP" }

Write-Host "`n=== STARTING CLEAN BRIDGE ===" -ForegroundColor Green
$p2 = Start-Process -FilePath $venv -ArgumentList "$base\quant-lab\mt5\clean_bridge.py","--symbols","EURJPY.PRO,EURNZD.PRO,GBPNZD.PRO,EURAUD.PRO,GBPAUD.PRO,GBPCAD.PRO,FR40.PRO","--lot-size","0.01" -WorkingDirectory "$base\quant-lab\mt5" -WindowStyle Hidden -PassThru
Write-Host "  Bridge: PID $($p2.Id)"
Start-Sleep -Seconds 10

Write-Host "`n=== STARTING SIGNAL BOT ===" -ForegroundColor Green
$p3 = Start-Process -FilePath $venv -ArgumentList "$base\scripts\signal_bot.py" -WorkingDirectory $base -WindowStyle Hidden -PassThru
Write-Host "  Signal Bot: PID $($p3.Id)"
Start-Sleep -Seconds 8

Write-Host "`n=== STARTING TELEGRAM GATEWAY ===" -ForegroundColor Green
$p4 = Start-Process -FilePath $venv -ArgumentList "$base\scripts\telegram_gateway.py" -WorkingDirectory $base -WindowStyle Hidden -PassThru
Write-Host "  Telegram: PID $($p4.Id)"
Start-Sleep -Seconds 10

Write-Host "`n=== STATUS ===" -ForegroundColor Cyan
Get-CimInstance Win32_Process -Filter "Name='python.exe'" | ForEach-Object {
    $cmd = $_.CommandLine
    if ($cmd.Length -gt 120) { $cmd = $cmd.Substring(0, 120) + "..." }
    Write-Host "  PID $($_.ProcessId): $cmd"
}

Write-Host "`n=== PORTS ==="
Get-NetTCPConnection -State Listen -ErrorAction SilentlyContinue | Where-Object { $_.LocalPort -in 8000,3000 } | Select-Object LocalPort, OwningProcess | Format-Table -AutoSize

Write-Host "`nDone!" -ForegroundColor Green

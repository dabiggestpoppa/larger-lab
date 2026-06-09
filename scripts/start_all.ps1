# START_ALL.PS1 — Start all trading engines and servers
# Uses WMI to create truly detached processes
$ErrorActionPreference = "Continue"
$env:PYTHONIOENCODING = "utf-8"

$base = "C:\Users\wifik\Desktop\projects\larger-lab"
$venv = "$base\.venv\Scripts\python.exe"

Write-Host "=== KILLING EXISTING PYTHON PROCESSES ===" -ForegroundColor Yellow
Get-Process python -ErrorAction SilentlyContinue | Stop-Process -Force
Start-Sleep -Seconds 3

# Helper: create detached process via WMI
function Start-DetachedProcess {
    param([string]$ExePath, [string]$Arguments, [string]$WorkingDir)
    $cmdLine = "`"$ExePath`" $Arguments"
    try {
        $result = Invoke-WmiMethod -Class Win32_Process -Name Create -ArgumentList $cmdLine, $WorkingDir
        if ($result.ReturnValue -eq 0) {
            Write-Host "  Started PID $($result.ProcessId): $Arguments"
        } else {
            Write-Host "  FAILED to start (ReturnValue: $($result.ReturnValue)): $Arguments" -ForegroundColor Red
        }
    } catch {
        Write-Host "  ERROR starting: $_" -ForegroundColor Red
    }
}

Write-Host "`n=== STARTING OCE BACKEND ===" -ForegroundColor Green
Start-DetachedProcess -ExePath $venv -Arguments "-m oce.backend.main" -WorkingDir $base
Start-Sleep -Seconds 10
$oce = Get-NetTCPConnection -State Listen -LocalPort 8000 -ErrorAction SilentlyContinue
if ($oce) { Write-Host "  OCE Backend UP (port 8000, PID $($oce.OwningProcess))" } else { Write-Host "  OCE Backend NOT UP" }

Write-Host "`n=== STARTING CLEAN BRIDGE ===" -ForegroundColor Green
Start-DetachedProcess -ExePath $venv -Arguments "`"$base\quant-lab\mt5\clean_bridge.py`" --symbols EURJPY.PRO,EURNZD.PRO,GBPNZD.PRO,EURAUD.PRO,GBPAUD.PRO,GBPCAD.PRO,FR40.PRO --lot-size 0.01" -WorkingDir "$base\quant-lab\mt5"
Start-Sleep -Seconds 10

Write-Host "`n=== STARTING SIGNAL BOT ===" -ForegroundColor Green
Start-DetachedProcess -ExePath $venv -Arguments "`"$base\scripts\signal_bot.py`"" -WorkingDir $base
Start-Sleep -Seconds 8

Write-Host "`n=== STARTING TELEGRAM GATEWAY ===" -ForegroundColor Green
Start-DetachedProcess -ExePath $venv -Arguments "`"$base\scripts\telegram_gateway.py`"" -WorkingDir $base
Start-Sleep -Seconds 10

Write-Host "`n=== FINAL STATUS ===" -ForegroundColor Cyan
Write-Host "Python processes:"
Get-CimInstance Win32_Process -Filter "Name='python.exe'" | ForEach-Object {
    $cmd = $_.CommandLine
    if ($cmd.Length -gt 120) { $cmd = $cmd.Substring(0, 120) + "..." }
    Write-Host "  PID $($_.ProcessId): $cmd"
}

Write-Host "`nListening ports:"
Get-NetTCPConnection -State Listen -ErrorAction SilentlyContinue | Where-Object { $_.LocalPort -in 3000,3001,3002,8000,8001 } | Select-Object LocalPort, OwningProcess | Format-Table -AutoSize

Write-Host "`nDone!" -ForegroundColor Green

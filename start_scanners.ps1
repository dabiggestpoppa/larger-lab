$ErrorActionPreference = "Continue"
$env:PYTHONIOENCODING = "utf-8"
$venv = "C:\Users\wifik\Desktop\projects\larger-lab\.venv\Scripts\python.exe"
$repo = "C:\Users\wifik\Desktop\projects\larger-lab"

$services = @(
    @{Name="OCE";        Args=@("-m","oce.backend.main")},
    @{Name="Telegram";   Args=@("scripts/telegram_gateway.py")},
    @{Name="CEREBUS";    Args=@("quant-lab/ml/run_cerebus_live.py","--interval","300","--engine","both")},
    @{Name="MLR";        Args=@("quant-lab/mlr_validation/mlr_scanner.py")},
    @{Name="Signal";     Args=@("scripts/signal_bot.py")}
)

# Kill existing
Get-Process python -ErrorAction SilentlyContinue | Stop-Process -Force -ErrorAction SilentlyContinue
Start-Sleep -Seconds 3

# Start each
$pids = @()
foreach ($svc in $services) {
    Write-Host "Starting $($svc.Name)..."
    $proc = Start-Process -FilePath $venv -ArgumentList $svc.Args -WorkingDirectory $repo -WindowStyle Hidden -PassThru
    $pids += [PSCustomObject]@{Name=$svc.Name; PID=$proc.Id}
    Start-Sleep -Seconds 2
}

# Save PIDs
$pids | ConvertTo-Json | Set-Content "$repo\.scanner_pids.json"
Write-Host "`nAll $($services.Count) scanners started."

# Verify after 5 seconds
Start-Sleep -Seconds 5
Write-Host "`nVerifying..."
foreach ($p in $pids) {
    $proc = Get-Process -Id $p.PID -ErrorAction SilentlyContinue
    if ($proc) { Write-Host "  OK: $($p.Name) (PID $($p.PID))" }
    else { Write-Host "  DEAD: $($p.Name) (PID $($p.PID))" }
}

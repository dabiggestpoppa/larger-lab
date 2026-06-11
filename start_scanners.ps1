$ErrorActionPreference = "Continue"
$env:PYTHONIOENCODING = "utf-8"
$venv = "C:\Users\wifik\Desktop\projects\larger-lab\.venv\Scripts\python.exe"
$repo = "C:\Users\wifik\Desktop\projects\larger-lab"

$services = @(
    @{Name="OCE Backend"; Args=@("-m","oce.backend.main")},
    @{Name="Telegram Gateway"; Args=@("scripts/telegram_gateway.py")},
    @{Name="CEREBUS Live"; Args=@("quant-lab/ml/run_cerebus_live.py","--interval","300","--engine","both")},
    @{Name="MLR Scanner"; Args=@("quant-lab/mlr_validation/mlr_scanner.py")},
    @{Name="Signal Bot"; Args=@("scripts/signal_bot.py")}
)

$pids = @()
foreach ($svc in $services) {
    Write-Host "Starting $($svc.Name)..."
    $proc = Start-Process -FilePath $venv -ArgumentList $svc.Args -WorkingDirectory $repo -WindowStyle Hidden -PassThru
    $pids += $proc.Id
    Write-Host "  PID: $($proc.Id)"
    Start-Sleep -Seconds 2
}

$pids | Set-Content "$repo\.scanner_pids.txt"
Write-Host "`nAll $($services.Count) services started."

Start-Sleep -Seconds 3
Write-Host "`nRunning processes:"
Get-Process python -ErrorAction SilentlyContinue | Select-Object Id, ProcessName, @{N='CmdLine';E={(Get-CimInstance Win32_Process -Filter "ProcessId=$($_.Id)").CommandLine}} | Format-Table -AutoSize -Wrap

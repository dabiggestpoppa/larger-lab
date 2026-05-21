$procs = Get-Process python -ErrorAction SilentlyContinue
foreach ($p in $procs) {
    $cmd = (Get-CimInstance Win32_Process -Filter "ProcessId=$($p.Id)").CommandLine
    if ($cmd -match "dmr_live") {
        Write-Host "Killing PID $($p.Id): $($cmd.Substring(0, [Math]::Min(100, $cmd.Length)))"
        Stop-Process -Id $p.Id -Force
    }
}
Start-Sleep -Seconds 2
Write-Host "Starting DMR..."
Start-Process -FilePath "python" -ArgumentList "C:\Users\wifik\Desktop\projects\larger-lab\quant-lab\mt5\dmr_live_v2.py" -WorkingDirectory "C:\Users\wifik\Desktop\projects\larger-lab" -WindowStyle Hidden
Start-Sleep -Seconds 3
$newProc = Get-Process python -ErrorAction SilentlyContinue | Where-Object { (Get-CimInstance Win32_Process -Filter "ProcessId=$($p.Id)").CommandLine -match "dmr_live" }
if ($newProc) { Write-Host "DMR started OK" } else { Write-Host "DMR may not have started" }

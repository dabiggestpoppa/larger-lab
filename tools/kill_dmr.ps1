$procs = Get-Process python -ErrorAction SilentlyContinue
foreach ($p in $procs) {
    $cmd = (Get-CimInstance Win32_Process -Filter "ProcessId=$($p.Id)").CommandLine
    if ($cmd -match "dmr_live_v2") {
        Write-Host "Killing DMR process PID $($p.Id): $cmd"
        Stop-Process -Id $p.Id -Force
    } else {
        Write-Host "Keeping PID $($p.Id): $($cmd.Substring(0, [Math]::Min(80, $cmd.Length)))"
    }
}

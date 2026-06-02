# Clean up duplicate processes for stable 24/7 runtime
$pythonProcs = Get-Process python -EA 0 | ForEach-Object {
    $cmd = (Get-CimInstance Win32_Process -Filter "ProcessId = $($_.Id)").CommandLine
    [PSCustomObject]@{Pid=$_.Id; Cmd=$cmd}
}

$groups = @{}
foreach ($p in $pythonProcs) {
    $key = "other"
    if ($p.Cmd -match "telegram_gateway") { $key = "telegram_gateway" }
    elseif ($p.Cmd -match "obsidian_vault_sync") { $key = "obsidian_vault_sync" }
    elseif ($p.Cmd -match "gateway_watchdog") { $key = "gateway_watchdog" }
    elseif ($p.Cmd -match "oc2_gateway") { $key = "oc2_gateway" }
    elseif ($p.Cmd -match "cerebus_live_bridge") { $key = "cerebus_live_bridge" }
    elseif ($p.Cmd -match "symmetry_trap_executor") { $key = "symmetry_trap_executor" }
    elseif ($p.Cmd -match "cerebus_guardian") { $key = "cerebus_guardian" }
    elseif ($p.Cmd -match "p90_cascade") { $key = "p90_cascade" }
    elseif ($p.Cmd -match "uvicorn|oce.backend.main") { $key = "oce_backend" }
    
    if (!$groups[$key]) { $groups[$key] = @() }
    $groups[$key] += $p
}

$killed = 0
foreach ($svc in $groups.Keys) {
    $procs = $groups[$svc]
    if ($procs.Count -gt 1) {
        Write-Host "$($svc): $($procs.Count) instances — keeping PID $($procs[0].Pid), killing $($procs.Count-1)"
        foreach ($p in $procs | Select-Object -Skip 1) {
            Stop-Process -Id $p.Pid -Force -EA 0
            Write-Host "  Killed PID $($p.Pid)"
            $killed++
        }
    } elseif ($procs.Count -eq 1) {
        Write-Host "$($svc): 1 instance (PID $($procs[0].Pid)) OK"
    } else {
        Write-Host "$($svc): 0 instances DOWN"
    }
}
Write-Host "`nCleaned up $killed duplicate processes"

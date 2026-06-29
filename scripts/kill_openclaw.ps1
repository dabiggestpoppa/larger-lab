$procs = Get-NetTCPConnection -State Listen -ErrorAction SilentlyContinue | Where-Object { $_.LocalPort -eq 18790 }
foreach ($p in $procs) {
    Stop-Process -Id $p.OwningProcess -Force -ErrorAction SilentlyContinue
    Write-Output "Killed PID $($p.OwningProcess) on port 18790"
}
if (-not $procs) { Write-Output "Port 18790 not in use" }

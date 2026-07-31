$procs = Get-Process python -ErrorAction SilentlyContinue | Where-Object CommandLine -match run_cerebus_unified
foreach ($proc in $procs) {
    Stop-Process -Id $proc.Id -Force
}

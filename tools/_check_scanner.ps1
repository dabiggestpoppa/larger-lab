$procs = Get-Process python -ErrorAction SilentlyContinue
foreach ($proc in $procs) {
    $cmd = (Get-CimInstance Win32_Process -Filter "ProcessId=$($proc.Id)").CommandLine
    if ($cmd -match "run_cerebus_unified") {
        Write-Output $proc.Id
        break
    }
}

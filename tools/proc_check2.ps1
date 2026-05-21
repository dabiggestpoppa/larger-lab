Get-Process python -ErrorAction SilentlyContinue | ForEach-Object {
    $cmd = (Get-CimInstance Win32_Process -Filter "ProcessId=$($_.Id)").CommandLine
    Write-Host "PID $($_.Id): $($cmd.Substring(0, [Math]::Min(120, $cmd.Length)))"
}

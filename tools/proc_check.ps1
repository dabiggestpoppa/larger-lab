Get-Process python -ErrorAction SilentlyContinue | ForEach-Object {
    $p = Get-CimInstance Win32_Process -Filter "ProcessId=$($_.Id)" -ErrorAction SilentlyContinue
    if ($p) {
        $c = $p.CommandLine
        if ($c.Length -gt 150) { $c = $c.Substring(0, 150) + "..." }
        Write-Host "PID $($_.Id): $c"
    }
}

$ids = @(1628, 7048)
foreach ($id in $ids) {
    $p = Get-CimInstance Win32_Process -Filter "ProcessId=$id" -ErrorAction SilentlyContinue
    if ($p) {
        $c = $p.CommandLine
        if ($c.Length -gt 150) { $c = $c.Substring(0, 150) + "..." }
        Write-Host "PID $id : $c"
    } else {
        Write-Host "PID $id : NOT FOUND"
    }
}

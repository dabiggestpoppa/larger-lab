$ports = @(8000, 8001, 3000, 3001, 9000)
foreach ($p in $ports) {
    try {
        $r = Invoke-WebRequest -Uri "http://localhost:$p/health" -TimeoutSec 3 -ErrorAction Stop
        Write-Output "Port $p : OK ($($r.StatusCode))"
    } catch {
        $msg = $_.Exception.Message
        if ($msg.Length -gt 80) { $msg = $msg.Substring(0,80) }
        Write-Output "Port $p : DOWN ($msg)"
    }
}

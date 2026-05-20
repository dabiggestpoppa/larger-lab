$checks = @(
    @{Port=8000; Path="/"},
    @{Port=8001; Path="/"},
    @{Port=3000; Path="/"},
    @{Port=3001; Path="/"},
    @{Port=9000; Path="/"}
)
foreach ($c in $checks) {
    $p = $c.Port
    $path = $c.Path
    try {
        $r = Invoke-WebRequest -Uri "http://localhost:$p$path" -TimeoutSec 3 -ErrorAction Stop
        Write-Output "Port $p : OK ($($r.StatusCode))"
    } catch {
        $code = $_.Exception.Response.StatusCode.value__
        if ($code) {
            Write-Output "Port $p : Responding (HTTP $code)"
        } else {
            Write-Output "Port $p : DOWN"
        }
    }
}

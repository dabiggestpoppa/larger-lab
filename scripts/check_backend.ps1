try {
    $r = Invoke-WebRequest -Uri 'http://localhost:8000/health' -TimeoutSec 5 -ErrorAction Stop
    Write-Output "STATUS: $($r.StatusCode)"
    Write-Output $r.Content
} catch {
    Write-Output "ERROR: $($_.Exception.Message)"
}

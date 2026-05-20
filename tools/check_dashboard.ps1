Start-Sleep -Seconds 3
try {
    $r = Invoke-WebRequest -Uri 'http://localhost:8002/api/status' -TimeoutSec 5 -UseBasicParsing
    Write-Output "Dashboard: UP (HTTP $($r.StatusCode))"
    $data = $r.Content | ConvertFrom-Json
    Write-Output "Config: $($data.config | ConvertTo-Json -Depth 2)"
} catch {
    Write-Output "Dashboard: DOWN ($($_.Exception.Message))"
}

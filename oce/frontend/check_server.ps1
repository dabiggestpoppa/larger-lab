$ErrorActionPreference = "Stop"
try {
    $r = Invoke-WebRequest -Uri "http://localhost:3000" -UseBasicParsing -TimeoutSec 5
    Write-Output "STATUS: $($r.StatusCode)"
    Write-Output "LENGTH: $($r.Content.Length)"
    if ($r.Content -match '<title>(.*?)</title>') {
        Write-Output "TITLE: $($Matches[1])"
    }
    # Save the HTML so we can see it
    $r.Content | Out-File -FilePath "C:\Users\wifik\Desktop\projects\larger-lab\oce\frontend\rendered.html" -Encoding utf8
    Write-Output "HTML saved to rendered.html"
} catch {
    Write-Output "ERROR: $_"
}

$tvPath = "$env:LOCALAPPDATA\TradingView\TradingView.exe"
Write-Output "TV exe: $tvPath"
Write-Output "Exists: $(Test-Path $tvPath)"

if (Test-Path $tvPath) {
    Write-Output "Launching TradingView with debug port 9222..."
    Start-Process -FilePath $tvPath -ArgumentList "--remote-debugging-port=9222"
    Start-Sleep -Seconds 5
    Write-Output "TradingView launched. Checking debug port..."
    try {
        $r = Invoke-WebRequest -Uri 'http://localhost:9222/json/version' -TimeoutSec 5 -UseBasicParsing
        Write-Output "Debug port ACTIVE: $($r.Content)"
    } catch {
        Write-Output "Debug port not yet available: $($_.Exception.Message)"
    }
} else {
    Write-Output "TradingView.exe not found at expected path!"
    Get-ChildItem "$env:LOCALAPPDATA\TradingView" -ErrorAction SilentlyContinue | Select-Object Name | ForEach-Object { Write-Output $_.Name }
}

# Check if TradingView is running with debug port
try {
    $r = Invoke-WebRequest -Uri 'http://localhost:9222/json/version' -TimeoutSec 3 -UseBasicParsing
    Write-Output "TV debug port 9222: ACTIVE"
    Write-Output $r.Content
} catch {
    Write-Output "TV debug port 9222: NOT AVAILABLE ($($_.Exception.Message))"
}

# Check current TV processes
Write-Output "---TV PROCESSES---"
Get-Process -Name "TradingView" -ErrorAction SilentlyContinue | Select-Object Id, ProcessName, @{N='MemMB';E={[math]::Round($_.WorkingSet64/1MB,1)}}, CommandLine | Format-List | Out-String

# Check all TV-related processes
Get-Process | Where-Object { $_.ProcessName -like "*trading*" -or $_.ProcessName -like "*Trading*" -or $_.ProcessName -like "*bridge*" -or $_.ProcessName -like "*Bridge*" } | Select-Object Id, ProcessName, @{N='MemMB';E={[math]::Round($_.WorkingSet64/1MB,1)}}, Path | Format-Table -AutoSize | Out-String

# Check if port 9222 is open
try {
    $r = Invoke-WebRequest -Uri 'http://localhost:9222/json/version' -TimeoutSec 3 -UseBasicParsing
    Write-Output "CDP port 9222: ACTIVE"
    Write-Output $r.Content
} catch {
    Write-Output "CDP port 9222: NOT AVAILABLE"
}

# Check chrome processes (TradingView web might be in browser)
Get-Process -Name "chrome" -ErrorAction SilentlyContinue | Select-Object Id, @{N='MemMB';E={[math]::Round($_.WorkingSet64/1MB,1)}} | Format-Table -AutoSize | Out-String

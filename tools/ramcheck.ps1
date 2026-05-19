$os = Get-CimInstance Win32_OperatingSystem
$total = [math]::Round($os.TotalVisibleMemorySize/1MB, 2)
$free = [math]::Round($os.FreePhysicalMemory/1MB, 2)
$used = [math]::Round($total - $free, 2)
$pct = [math]::Round(($used/$total)*100, 1)
Write-Output "RAM: ${used}GB / ${total}GB (${pct}% used, ${free}GB free)"
Write-Output ""
Write-Output "Top 15 processes by memory:"
Get-Process | Sort-Object WorkingSet64 -Descending | Select-Object -First 15 Name, @{N='MemMB';E={[math]::Round($_.WorkingSet64/1MB,1)}}, CPU | Format-Table -AutoSize
Write-Output ""
Write-Output "Node.js processes:"
Get-Process -Name node -ErrorAction SilentlyContinue | Select-Object Id, @{N='MemMB';E={[math]::Round($_.WorkingSet64/1MB,1)}}, StartTime | Format-Table -AutoSize
Write-Output ""
Write-Output "Python processes:"
Get-Process -Name python -ErrorAction SilentlyContinue | Select-Object Id, @{N='MemMB';E={[math]::Round($_.WorkingSet64/1MB,1)}}, StartTime | Format-Table -AutoSize

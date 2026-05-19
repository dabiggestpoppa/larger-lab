$os = Get-CimInstance Win32_OperatingSystem
$totalGB = [math]::Round($os.TotalVisibleMemorySize/1MB, 1)
$freeGB = [math]::Round($os.FreePhysicalMemory/1MB, 1)
$usedGB = $totalGB - $freeGB
$pct = [math]::Round($usedGB/$totalGB*100, 1)
Write-Output "RAM: ${usedGB}GB / ${totalGB}GB (${pct}% used, ${freeGB}GB free)"
Write-Output ""
Write-Output "Top 10 processes by memory:"
Get-Process | Sort-Object WorkingSet64 -Descending | Select-Object -First 10 Name, @{N='MemMB';E={[math]::Round($_.WorkingSet64/1MB,1)}} | Format-Table -AutoSize

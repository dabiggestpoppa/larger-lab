$os = Get-CimInstance Win32_OperatingSystem
$totalGB = [math]::Round($os.TotalVisibleMemorySize/1MB,1)
$freeGB = [math]::Round($os.FreePhysicalMemory/1MB,1)
$usedGB = [math]::Round($totalGB - $freeGB,1)
$pct = [math]::Round($usedGB/$totalGB*100,1)
Write-Output "RAM: ${usedGB}GB / ${totalGB}GB (${pct}% used, ${freeGB}GB free)"
$cpu = (Get-CimInstance Win32_Processor).LoadPercentage
Write-Output "CPU: ${cpu}%"
$disk = Get-CimInstance Win32_LogicalDisk -Filter "DeviceID='C:'"
$diskFree = [math]::Round($disk.FreeSpace/1GB,1)
Write-Output "Disk C: ${diskFree}GB free"
Write-Output "---TOP10---"
Get-Process | Sort-Object WorkingSet64 -Descending | Select-Object -First 10 Name, @{N='MemMB';E={[math]::Round($_.WorkingSet64/1MB,1)}} | Format-Table -AutoSize | Out-String
Write-Output "---SERVICES---"
Get-Process -Name 'python','node','mt5' -ErrorAction SilentlyContinue | Select-Object Id, Name, @{N='MemMB';E={[math]::Round($_.WorkingSet64/1MB,1)}}, StartTime | Format-Table -AutoSize | Out-String

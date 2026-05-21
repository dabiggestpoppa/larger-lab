$os = Get-CimInstance Win32_OperatingSystem
$free = [math]::Round($os.FreePhysicalMemory/1MB,1)
$total = [math]::Round($os.TotalVisibleMemorySize/1MB,1)
$pct = [math]::Round(($total - $free)/$total*100,1)
Write-Output "RAM: ${free}GB free / ${total}GB (${pct}% used)"
Get-PSDrive C | Select-Object @{N='DiskFreeGB';E={[math]::Round($_.Free/1GB,1)}}, @{N='DiskUsedGB';E={[math]::Round($_.Used/1GB,1)}}
Write-Output "--- Processes ---"
Get-Process python,node -ErrorAction SilentlyContinue | Format-Table Id,ProcessName,@{N='MemMB';E={[math]::Round($_.WorkingSet64/1MB,1)}} -AutoSize

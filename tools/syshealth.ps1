$os = Get-CimInstance Win32_OperatingSystem
$free = [math]::Round($os.FreePhysicalMemory/1MB, 1)
$total = [math]::Round($os.TotalVisibleMemorySize/1MB, 1)
$used = [math]::Round($total - $free, 1)
$pct = [math]::Round(($used/$total)*100, 1)
Write-Output "RAM: $used GB / $total GB ($pct% used, $free GB free)"

$disk = Get-CimInstance Win32_LogicalDisk -Filter "DeviceID='C:'"
$dFree = [math]::Round($disk.FreeSpace/1GB, 1)
$dTotal = [math]::Round($disk.Size/1GB, 1)
Write-Output "Disk C: $dFree GB free / $dTotal GB total"

$cpu = (Get-CimInstance Win32_Processor).LoadPercentage
Write-Output "CPU: $cpu%"

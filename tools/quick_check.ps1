$os = Get-CimInstance Win32_OperatingSystem
$usedGB = [math]::Round(($os.TotalVisibleMemorySize - $os.FreePhysicalMemory)/1MB, 1)
$totalGB = [math]::Round($os.TotalVisibleMemorySize/1MB, 1)
$pctUsed = [math]::Round(($os.TotalVisibleMemorySize - $os.FreePhysicalMemory)/$os.TotalVisibleMemorySize*100, 1)
$freeGB = [math]::Round($os.FreePhysicalMemory/1MB, 1)
Write-Host "RAM: $pctUsed% used ($usedGB GB / $totalGB GB) | Free: $freeGB GB"

$disk = Get-CimInstance Win32_LogicalDisk -Filter "DeviceID='C:'"
$diskFree = [math]::Round($disk.FreeSpace/1GB, 1)
Write-Host "Disk C: $diskFree GB free"

Write-Host "`n--- Python Processes ---"
Get-Process python -ErrorAction SilentlyContinue | ForEach-Object {
    $proc = Get-CimInstance Win32_Process -Filter "ProcessId=$($_.Id)" -ErrorAction SilentlyContinue
    if ($proc) {
        $cmd = $proc.CommandLine
        if ($cmd.Length -gt 120) { $cmd = $cmd.Substring(0, 120) + "..." }
        Write-Host "PID $($_.Id): $cmd"
    }
}

Write-Host "`n--- Port Checks ---"
foreach ($p in @(8000,8001,8002,18790,3000,3001)) {
    $tcp = New-Object System.Net.Sockets.TcpClient
    try {
        $tcp.Connect('127.0.0.1', $p)
        Write-Host "Port $p : OPEN"
        $tcp.Close()
    } catch {
        Write-Host "Port $p : CLOSED"
    }
}

Write-Host "`n--- MT5 ---"
$mt5 = Get-Process -Name 'mt5' -ErrorAction SilentlyContinue
if ($mt5) { Write-Host "MT5: RUNNING (PID $($mt5.Id))" } else { Write-Host "MT5: NOT RUNNING" }

Write-Host "`n--- DMR DB ---"
$dbPath = "C:\Users\wifik\Desktop\projects\larger-lab\quant-lab\mt5\dmr_live.db"
if (Test-Path $dbPath) {
    $dbSize = (Get-Item $dbPath).Length
    Write-Host "DMR DB: EXISTS ($dbSize bytes)"
} else {
    Write-Host "DMR DB: NOT FOUND"
}

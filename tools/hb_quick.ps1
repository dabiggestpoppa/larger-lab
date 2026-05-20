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

Write-Output "---SERVICES---"
try { $r = Invoke-WebRequest -Uri 'http://localhost:8000/health' -TimeoutSec 3 -UseBasicParsing; Write-Output "OCE backend :8000 - UP" } catch { Write-Output "OCE backend :8000 - DOWN" }
try { $r = Invoke-WebRequest -Uri 'http://localhost:8001/health' -TimeoutSec 3 -UseBasicParsing; Write-Output "SRRA API :8001 - UP" } catch { Write-Output "SRRA API :8001 - DOWN" }
try { $r = Invoke-WebRequest -Uri 'http://localhost:3000' -TimeoutSec 3 -UseBasicParsing; Write-Output "OCE frontend :3000 - UP" } catch { Write-Output "OCE frontend :3000 - DOWN" }
try { $r = Invoke-WebRequest -Uri 'http://localhost:3001' -TimeoutSec 3 -UseBasicParsing; Write-Output "SRRA frontend :3001 - UP" } catch { Write-Output "SRRA frontend :3001 - DOWN" }
try { $r = Invoke-WebRequest -Uri 'http://localhost:9000' -TimeoutSec 3 -UseBasicParsing; Write-Output "Agent env :9000 - UP" } catch { Write-Output "Agent env :9000 - DOWN" }

Write-Output "---DMR LIVE---"
$ft = Get-Process -Id 7212 -ErrorAction SilentlyContinue
if ($ft) { Write-Output "DMR live (PID 7212): RUNNING | Mem: $([math]::Round($ft.WorkingSet64/1MB,1))MB" } else { Write-Output "DMR live (PID 7212): NOT RUNNING" }
$stateFile = "C:\Users\wifik\Desktop\projects\larger-lab\quant-lab\mt5\dmr_live_state.json"
if (Test-Path $stateFile) { Write-Output "State: $(Get-Content $stateFile)" } else { Write-Output "No state file" }

Write-Output "---TOP MEMORY---"
Get-Process | Sort-Object WorkingSet64 -Descending | Select-Object -First 5 Name, @{N='MemMB';E={[math]::Round($_.WorkingSet64/1MB,1)}} | Format-Table -AutoSize | Out-String

$logFile = "C:\Users\wifik\Desktop\projects\larger-lab\tools\phase10-monitor.log"
$timestamp = Get-Date -Format "yyyy-MM-dd HH:mm:ss"
$phase10 = Get-ChildItem "C:\Users\wifik\Desktop\projects\larger-lab\oce" -Filter "*PHASE10*" -Recurse -ErrorAction SilentlyContinue
$ccEntries = Get-Content "C:\Users\wifik\Desktop\projects\larger-lab\shared-conversations\team-chat.md" -ErrorAction SilentlyContinue | Select-String "\[CC\]" | Select-Object -Last 3
$health = try { (Invoke-WebRequest -Uri "http://127.0.0.1:18790/health" -TimeoutSec 3 -UseBasicParsing).Content } catch { "DOWN" }
Add-Content -Path $logFile -Value "$timestamp | OC2: $health | Phase10: $(if($phase10){'FOUND'}else{'not yet'}) | CC entries: $($ccEntries.Count)"
if ($phase10) { Add-Content -Path $logFile -Value "PHASE 10 PLAN FOUND: $($phase10.FullName)" }

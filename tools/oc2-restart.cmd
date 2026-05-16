@echo off
echo Restarting OC2 Gateway...
taskkill /PID 15212 /F 2>nul
timeout /t 2 /nobreak >nul
set "OPENCLAW_HOME=C:\Users\wifik\Desktop\projects\larger-lab\.openclaw-2"
start "" /min "C:\Program Files\nodejs\node.exe" "C:\Users\wifik\AppData\Roaming\npm\node_modules\openclaw\dist\index.js" gateway run --port 18790 --allow-unconfigured
echo OC2 restarted. Waiting for health check...
timeout /t 8 /nobreak >nul
powershell -Command "try { $r = Invoke-RestMethod -Uri 'http://127.0.0.1:18790/health' -TimeoutSec 5; Write-Host 'OC2 Status:' $r.status } catch { Write-Host 'OC2 FAIL' }"

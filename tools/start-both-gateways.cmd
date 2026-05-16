@echo off
rem Start both OpenClaw gateways cleanly
rem Kills any existing gateway processes first to prevent duplicates

echo Stopping any existing gateway processes...
taskkill /F /IM node.exe 2>nul
timeout /t 2 /nointerrupt >nul

echo Starting OC1 Gateway (port 18789)...
start "" /min cmd.exe /c "C:\Users\wifik\.openclaw\gateway.cmd"

echo Starting OC2 Gateway (port 18790)...
start "" /min cmd.exe /c "C:\Users\wifik\Desktop\projects\larger-lab\.openclaw-2\gateway.cmd"

echo Starting Watchdog...
start "" /min cmd.exe /c "C:\Users\wifik\Desktop\projects\larger-lab\tools\gateway-watchdog.cmd"

echo.
echo Both gateways started.
echo Check status: cmd /c "C:\Users\wifik\Desktop\projects\larger-lab\tools\gateway-status.cmd"

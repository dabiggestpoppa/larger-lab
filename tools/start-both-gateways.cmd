@echo off
rem ============================================================
rem  Start Both OpenClaw Gateways (OC1 + OC2)
rem  OC1: port 18789, @finalstrawclawbot
rem  OC2: port 18790, @OC2BLRBOT
rem ============================================================

echo [INFO] Killing any existing gateway processes...
taskkill /F /IM node.exe /FI "WINDOWTITLE eq openclaw*" 2>nul
timeout /t 2 /nobreak >nul

echo [INFO] Clearing stale restart intents...
del /F /Q "%USERPROFILE%\.openclaw\gateway-restart-intent.json" 2>nul
del /F /Q "%USERPROFILE%\.openclaw-2\gateway-restart-intent.json" 2>nul
del /F /Q "%USERPROFILE%\.openclaw-2\.openclaw\gateway-restart-intent.json" 2>nul

echo.
echo [INFO] Starting OC1 (port 18789)...
start "OC1 Gateway" /MIN cmd /c "C:\Users\wifik\.openclaw\gateway.cmd"
timeout /t 8 /nobreak >nul

echo [INFO] Starting OC2 (port 18790)...
start "OC2 Gateway" /MIN cmd /c "C:\Users\wifik\Desktop\projects\larger-lab\.openclaw-2\gateway.cmd"
timeout /t 8 /nobreak >nul

echo.
echo [INFO] Checking gateway status...
netstat -ano | findstr "18789 18790"

echo.
echo [INFO] Both gateways started. Use 'tools\stop-both-gateways.cmd' to stop.

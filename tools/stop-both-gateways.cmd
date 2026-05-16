@echo off
rem ============================================================
rem  Stop Both OpenClaw Gateways (OC1 + OC2)
rem ============================================================

echo [INFO] Stopping all OpenClaw gateway processes...
taskkill /F /IM node.exe /FI "WINDOWTITLE eq OC1 Gateway*" 2>nul
taskkill /F /IM node.exe /FI "WINDOWTITLE eq OC2 Gateway*" 2>nul
taskkill /F /IM node.exe 2>nul

echo [INFO] Both gateways stopped.
netstat -ano | findstr "18789 18790"

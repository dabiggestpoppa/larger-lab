@echo off
rem Stop all OpenClaw gateway processes cleanly

echo Stopping OC1 Gateway (port 18789)...
taskkill /F /IM node.exe /FI "COMMANDLINE eq *openclaw*18789*" 2>nul

echo Stopping OC2 Gateway (port 18790)...
taskkill /F /IM node.exe /FI "COMMANDLINE eq *openclaw*18790*" 2>nul

echo Stopping Watchdog...
taskkill /F /IM cmd.exe /FI "COMMANDLINE eq *gateway-watchdog*" 2>nul

echo Stopping any remaining gateway cmd processes...
taskkill /F /IM cmd.exe /FI "COMMANDLINE eq *openclaw*gateway*" 2>nul

echo All gateway processes stopped.

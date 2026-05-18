@echo off
REM OC2 Emergency Reboot Script
REM Kills stale processes and restarts gateway cleanly

echo ============================================
echo  OC2 Emergency Reboot
echo  %date% %time%
echo ============================================

echo [1/4] Killing stale node processes...
taskkill /F /IM node.exe 2>nul
timeout /t 3 /nobreak >nul

echo [2/4] Checking port 18790...
netstat -ano | findstr ":18790" | findstr "LISTENING" >nul 2>&1
if %ERRORLEVEL% equ 0 (
    echo Port 18790 still in use, forcing...
    for /f "tokens=5" %%a in ('netstat -ano ^| findstr ":18790" ^| findstr "LISTENING"') do (
        taskkill /F /PID %%a 2>nul
    )
    timeout /t 2 /nobreak >nul
)

echo [3/4] Starting OpenClaw gateway...
start /B openclaw gateway run --port 18790

echo [4/4] Waiting for gateway to come up...
timeout /t 10 /nobreak >nul

netstat -ano | findstr ":18790" | findstr "LISTENING" >nul 2>&1
if %ERRORLEVEL% equ 0 (
    echo ============================================
    echo  Gateway restarted successfully
    echo ============================================
) else (
    echo ============================================
    echo  WARNING: Gateway may not be up yet
    echo  Check logs manually
    echo ============================================
)

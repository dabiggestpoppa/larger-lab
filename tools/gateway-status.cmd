@echo off
rem Check OpenClaw gateway status

echo ============================================
echo   OpenClaw Gateway Status
echo ============================================
echo.

rem Check OC1
netstat -ano | findstr "LISTENING" | findstr "18789" >nul 2>&1
if %ERRORLEVEL% EQU 0 (
    echo [OC1] Port 18789: RUNNING
) else (
    echo [OC1] Port 18789: STOPPED
)

rem Check OC2
netstat -ano | findstr "LISTENING" | findstr "18790" >nul 2>&1
if %ERRORLEVEL% EQU 0 (
    echo [OC2] Port 18790: RUNNING
) else (
    echo [OC2] Port 18790: STOPPED
)

echo.
echo Running gateway processes:
tasklist /FI "IMAGENAME eq node.exe" /FO TABLE 2>nul
echo.
echo Scheduled tasks:
schtasks /query /tn "OpenClaw-1-Gateway" /fo LIST 2>nul | findstr "Status"
schtasks /query /tn "OpenClaw-2-Gateway" /fo LIST 2>nul | findstr "Status"
echo ============================================

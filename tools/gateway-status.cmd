@echo off
rem ============================================================
rem  Check OpenClaw Gateway Status
rem ============================================================

echo === OpenClaw Gateway Status ===
echo.

echo [OC1 - Port 18789 - @finalstrawclawbot]
netstat -ano | findstr "18789" >nul 2>&1
if %errorlevel%==0 (
    echo   Status: RUNNING
    for /f "tokens=5" %%a in ('netstat -ano ^| findstr "18789.*LISTENING"') do echo   PID: %%a
) else (
    echo   Status: STOPPED
)

echo.
echo [OC2 - Port 18790 - @OC2BLRBOT]
netstat -ano | findstr "18790" >nul 2>&1
if %errorlevel%==0 (
    echo   Status: RUNNING
    for /f "tokens=5" %%a in ('netstat -ano ^| findstr "18790.*LISTENING"') do echo   PID: %%a
) else (
    echo   Status: STOPPED
)

echo.
echo [All Node Processes]
tasklist /FI "IMAGENAME eq node.exe" /FO TABLE 2>nul

@echo off
rem OpenClaw Gateway Watchdog
rem Ensures both OC1 and OC2 gateways stay running
:loop
rem Check OC1 (port 18789)
netstat -ano | findstr "18789" >nul 2>&1
if %ERRORLEVEL% NEQ 0 (
    echo [%date% %time%] OC1 gateway not detected, starting...
    start "" /min cmd.exe /c "C:\Users\wifik\.openclaw\gateway.cmd"
    timeout /t 5 /nointerrupt >nul
)

rem Check OC2 (port 18790)
netstat -ano | findstr "18790" >nul 2>&1
if %ERRORLEVEL% NEQ 0 (
    echo [%date% %time%] OC2 gateway not detected, starting...
    start "" /min cmd.exe /c "C:\Users\wifik\Desktop\projects\larger-lab\.openclaw-2\gateway.cmd"
    timeout /t 5 /nointerrupt >nul
)

rem Check every 60 seconds
timeout /t 60 /nointerrupt >nul
goto loop

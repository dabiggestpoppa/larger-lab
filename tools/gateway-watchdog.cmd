@echo off
rem OpenClaw Gateway Watchdog v2
rem Ensures OC1 and OC2 gateways stay running
rem Fixed: proper process checking, max restart limit, no infinite spawn

setlocal enabledelayedexpansion
set "MAX_RESTARTS=5"
set "RESTART_COUNT_OC1=0"
set "RESTART_COUNT_OC2=0"
set "CHECK_INTERVAL=60"

:loop
rem --- Check OC1 (port 18789) ---
netstat -ano | findstr "LISTENING" | findstr "18789" >nul 2>&1
if %ERRORLEVEL% NEQ 0 (
    if !RESTART_COUNT_OC1! LSS %MAX_RESTARTS% (
        echo [%date% %time%] OC1 gateway not detected on port 18789, starting... (!RESTART_COUNT_OC1!/%MAX_RESTARTS%)
        start "" /min cmd.exe /c "C:\Users\wifik\.openclaw\gateway.cmd"
        set /a RESTART_COUNT_OC1+=1
        timeout /t 10 /nointerrupt >nul
    ) else (
        echo [%date% %time%] OC1 gateway: max restarts reached (%MAX_RESTARTS%). Manual intervention needed.
    )
) else (
    set "RESTART_COUNT_OC1=0"
)

rem --- Check OC2 (port 18790) ---
netstat -ano | findstr "LISTENING" | findstr "18790" >nul 2>&1
if %ERRORLEVEL% NEQ 0 (
    if !RESTART_COUNT_OC2! LSS %MAX_RESTARTS% (
        echo [%date% %time%] OC2 gateway not detected on port 18790, starting... (!RESTART_COUNT_OC2!/%MAX_RESTARTS%)
        start "" /min cmd.exe /c "C:\Users\wifik\Desktop\projects\larger-lab\.openclaw-2\gateway.cmd"
        set /a RESTART_COUNT_OC2+=1
        timeout /t 10 /nointerrupt >nul
    ) else (
        echo [%date% %time%] OC2 gateway: max restarts reached (%MAX_RESTARTS%). Manual intervention needed.
    )
) else (
    set "RESTART_COUNT_OC2=0"
)

rem --- Wait before next check ---
timeout /t %CHECK_INTERVAL% /nointerrupt >nul
goto loop

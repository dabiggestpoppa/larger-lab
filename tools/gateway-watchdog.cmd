@echo off
rem OpenClaw Gateway Watchdog v3 - OC2 Only
rem Ensures OC2 gateway stays running
rem OC1 removed - only OC2 bot remains

setlocal enabledelayedexpansion
set "MAX_RESTARTS=5"
set "RESTART_COUNT_OC2=0"
set "CHECK_INTERVAL=60"

:loop
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

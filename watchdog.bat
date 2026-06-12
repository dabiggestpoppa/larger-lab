@echo off
:loop
cd /d C:\Users\wifik\Desktop\projects\larger-lab

:: Check OCE Backend
tasklist /FI "IMAGENAME eq python.exe" /FI "WINDOWTITLE eq OCE*" 2>nul | find /I "python.exe" >nul
if errorlevel 1 start "OCE" /B .venv\Scripts\python.exe -m oce.backend.main

:: Check CEREBUS Unified Scanner (desktop alerts, no Telegram spam)
tasklist /FI "IMAGENAME eq python.exe" /FI "WINDOWTITLE eq CEREBUS*" 2>nul | find /I "python.exe" >nul
if errorlevel 1 start "CEREBUS" /B .venv\Scripts\python.exe quant-lab/ml/run_cerebus_unified.py --interval 300

:: Wait 120 seconds before checking again
timeout /t 120 /nobreak >nul
goto loop

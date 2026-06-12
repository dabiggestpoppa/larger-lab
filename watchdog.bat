@echo off
:loop
cd /d C:\Users\wifik\Desktop\projects\larger-lab

:: Check OCE Backend
tasklist /FI "IMAGENAME eq python.exe" /FI "WINDOWTITLE eq OCE*" 2>nul | find /I "python.exe" >nul
if errorlevel 1 start "OCE" /B .venv\Scripts\python.exe -m oce.backend.main

:: Check Telegram Gateway (only one instance)
tasklist /FI "IMAGENAME eq python.exe" /FI "WINDOWTITLE eq TG*" 2>nul | find /I "python.exe" >nul
if errorlevel 1 start "TG" /B .venv\Scripts\python.exe scripts/telegram_gateway.py

:: Check CEREBUS Unified Scanner (only one instance)
tasklist /FI "IMAGENAME eq python.exe" /FI "WINDOWTITLE eq CEREBUS*" 2>nul | find /I "python.exe" >nul
if errorlevel 1 start "CEREBUS" /B .venv\Scripts\python.exe quant-lab/ml/run_cerebus_unified.py --interval 300

:: Check Signal Bot (only one instance)
tasklist /FI "IMAGENAME eq python.exe" /FI "WINDOWTITLE eq SIGNAL*" 2>nul | find /I "python.exe" >nul
if errorlevel 1 start "SIGNAL" /B .venv\Scripts\python.exe scripts/signal_bot.py

:: Wait 120 seconds before checking again (reduced frequency)
timeout /t 120 /nobreak >nul
goto loop

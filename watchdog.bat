@echo off
:loop
cd /d C:\Users\wifik\Desktop\projects\larger-lab

:: Check OCE Backend
tasklist /FI "IMAGENAME eq python.exe" /FI "WINDOWTITLE eq OCE*" 2>nul | find /I "python.exe" >nul
if errorlevel 1 start "OCE" /B .venv\Scripts\python.exe -m oce.backend.main

:: Check Telegram Gateway  
tasklist /FI "IMAGENAME eq python.exe" /FI "WINDOWTITLE eq TG*" 2>nul | find /I "python.exe" >nul
if errorlevel 1 start "TG" /B .venv\Scripts\python.exe scripts/telegram_gateway.py

:: Check CEREBUS Live
tasklist /FI "IMAGENAME eq python.exe" /FI "WINDOWTITLE eq CEREBUS*" 2>nul | find /I "python.exe" >nul
if errorlevel 1 start "CEREBUS" /B .venv\Scripts\python.exe quant-lab/ml/run_cerebus_live.py --interval 300 --engine both

:: Check MLR Scanner
tasklist /FI "IMAGENAME eq python.exe" /FI "WINDOWTITLE eq MLR*" 2>nul | find /I "python.exe" >nul
if errorlevel 1 start "MLR" /B .venv\Scripts\python.exe quant-lab/mlr_validation/mlr_scanner.py

:: Check Signal Bot
tasklist /FI "IMAGENAME eq python.exe" /FI "WINDOWTITLE eq SIGNAL*" 2>nul | find /I "python.exe" >nul
if errorlevel 1 start "SIGNAL" /B .venv\Scripts\python.exe scripts/signal_bot.py

:: Wait 60 seconds before checking again
timeout /t 60 /nobreak >nul
goto loop

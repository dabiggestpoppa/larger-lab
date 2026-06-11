@echo off
cd /d C:\Users\wifik\Desktop\projects\larger-lab
set PYTHONIOENCODING=utf-8

echo Starting CEREBUS 24/7 Scanners...
echo.

:: Kill any existing python processes first
taskkill /F /IM python.exe /T 2>nul
taskkill /F /IM pythonw.exe /T 2>nul
timeout /t 3 /nobreak >nul

:: Start OCE Backend
echo [1/5] Starting OCE Backend...
start "OCE Backend" /B "C:\Users\wifik\Desktop\projects\larger-lab\.venv\Scripts\python.exe" -m oce.backend.main
timeout /t 2 /nobreak >nul

:: Start Telegram Gateway
echo [2/5] Starting Telegram Gateway...
start "Telegram Gateway" /B "C:\Users\wifik\Desktop\projects\larger-lab\.venv\Scripts\python.exe" scripts/telegram_gateway.py
timeout /t 2 /nobreak >nul

:: Start CEREBUS Live Scanner (Guardian + ST/P90)
echo [3/5] Starting CEREBUS Live Scanner...
start "CEREBUS Live" /B "C:\Users\wifik\Desktop\projects\larger-lab\.venv\Scripts\python.exe" quant-lab/ml/run_cerebus_live.py --interval 300 --engine both
timeout /t 3 /nobreak >nul

:: Start MLR Scanner
echo [4/5] Starting MLR Scanner...
start "MLR Scanner" /B "C:\Users\wifik\Desktop\projects\larger-lab\.venv\Scripts\python.exe" quant-lab/mlr_validation/mlr_scanner.py
timeout /t 2 /nobreak >nul

:: Start Signal Bot
echo [5/5] Starting Signal Bot...
start "Signal Bot" /B "C:\Users\wifik\Desktop\projects\larger-lab\.venv\Scripts\python.exe" scripts/signal_bot.py
timeout /t 2 /nobreak >nul

echo.
echo All 5 scanners started.
echo.
echo To stop all scanners:
echo   taskkill /F /IM python.exe /T

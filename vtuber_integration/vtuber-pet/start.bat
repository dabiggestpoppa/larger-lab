@echo off
REM VTuber Desktop Pet Launcher
REM Launches a transparent always-on-top pywebview overlay

cd /d "%~dp0"

echo ========================================
echo   VTuber Desktop Pet Launcher
echo ========================================
echo.

REM Check if OCE backend is running
python -c "import socket; s=socket.socket(); s.settimeout(2); r=s.connect_ex(('127.0.0.1',8000)); s.close(); exit(0 if r==0 else 1)" 2>nul
if %ERRORLEVEL% neq 0 (
    echo [!] OCE Backend not running on port 8000
    echo [!] Please start OCE backend first
    pause
    exit /b 1
)
echo [+] OCE Backend: OK

REM Check if VTuber is running
python -c "import socket; s=socket.socket(); s.settimeout(2); r=s.connect_ex(('127.0.0.1',12393)); s.close(); exit(0 if r==0 else 1)" 2>nul
if %ERRORLEVEL% neq 0 (
    echo [!] VTuber not running on port 12393
    echo [!] Starting VTuber...
    cd /d "C:\Users\wifik\Desktop\projects\larger-lab\vtuber_integration\Open-LLM-VTuber"
    Start-Job -ScriptBlock { cd "C:\Users\wifik\Desktop\projects\larger-lab\vtuber_integration\Open-LLM-VTuber"; & ".\.venv\Scripts\python.exe" "run_server.py" } | Out-Null
    echo [*] VTuber starting...
    timeout /t 20 /nobreak >nul
)
echo [+] VTuber: OK

REM Launch the Python desktop pet
echo [*] Launching VTuber Desktop Pet (pywebview)...
echo [+] Controls: Alt+V=toggle, Alt+P=pin, Alt+R=reload, Alt+Q=close
echo [+] Drag title bar to move, bottom-right corner to resize

REM Use the larger-lab Python venv
cd /d "c:\Users\wifik\Desktop\projects\larger-lab"
Start "" ".\.venv\Scripts\python.exe" "vtuber_integration\desktop_pet.py"

echo.
echo [+] Desktop Pet launched!
exit /b 0
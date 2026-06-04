@echo off
REM Start all servers as detached background processes
REM This script keeps servers running after VS Code closes

echo Starting OC2 Gateway (port 18790)...
cd /d "%USERPROFILE%\.openclaw-2\.openclaw"
start "OC2 Gateway" /b openclaw gateway run --port 18790

echo Starting OCE Backend (port 8000)...
cd /d "C:\Users\wifik\Desktop\projects\larger-lab"
start "OCE Backend" /b cmd /c ".venv\Scripts\python.exe -m uvicorn oce.backend.main:app --host 0.0.0.0 --port 8000"

echo Starting OCE Frontend (port 3000)...
cd /d "C:\Users\wifik\Desktop\projects\larger-lab\oce\frontend"
start "OCE Frontend" /b cmd /c "npx next dev -p 3000"

echo Starting SRRA-OPH Frontend (port 3001)...
cd /d "C:\Users\wifik\Desktop\projects\larger-lab\srrs_opc\frontend"
start "SRRA-OPH Frontend" /b cmd /c "npx next dev -p 3001"

echo All servers started. Check ports 18790, 8000, 3000, 3001
timeout /t 5 /nobreak >nul
netstat -ano | findstr -E ":(18790|8000|3000|3001)" | findstr "LISTENING"
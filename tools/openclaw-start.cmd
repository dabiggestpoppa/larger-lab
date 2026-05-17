@echo off
REM OpenClaw Gateway Start Script
REM Single clean startup - no duplicates, no conflicts

echo ============================================
echo  OpenClaw Gateway Startup
echo ============================================

set "OPENCLAW_HOME=%~dp0..\.openclaw-2"
set "WORKSPACE=%~dp0.."
set "NODE_EXE=C:\Program Files\nodejs\node.exe"
set "OPENCLAW_JS=%APPDATA%\npm\node_modules\openclaw\dist\index.js"
set "PORT=18790"

REM Step 1: Kill any existing OpenClaw process
echo [1/4] Checking for existing processes...
taskkill /F /IM node.exe /FI "WINDOWTITLE eq *openclaw*" 2>nul
powershell -Command "Get-Process -Name 'node' -ErrorAction SilentlyContinue | Where-Object { $_.CommandLine -match 'openclaw' } | Stop-Process -Force -ErrorAction SilentlyContinue" 2>nul
timeout /t 3 /nobreak >nul

REM Step 2: Verify port is free
echo [2/4] Checking port %PORT%...
netstat -ano | findstr ":%PORT%" | findstr "LISTENING" >nul 2>&1
if %ERRORLEVEL% equ 0 (
    echo WARNING: Port %PORT% still in use. Waiting for TIME_WAIT to clear...
    timeout /t 5 /nobreak >nul
)

REM Step 3: Verify config exists
echo [3/4] Verifying config...
if not exist "%OPENCLAW_HOME%\openclaw.json" (
    echo ERROR: Config not found at %OPENCLAW_HOME%\openclaw.json
    exit /b 1
)

REM Step 4: Start gateway
echo [4/4] Starting OpenClaw gateway on port %PORT%...
echo.
cd /d "%WORKSPACE%"
"%NODE_EXE%" "%OPENCLAW_JS%" gateway run --port %PORT% --allow-unconfigured

echo.
echo OpenClaw gateway stopped.

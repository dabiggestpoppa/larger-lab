@echo off
REM ===========================================================================
REM  start_all_servers.cmd - Boot the full Larger-Lab stack
REM  -------------------------------------------------------------------------
REM    OCE Backend        Continuity Core API        http://localhost:8000
REM    API Server         SRRA-OPH                    http://localhost:8001
REM    PO Bot             Telegram gateway            (needs TELEGRAM_TOKEN)
REM    OCE Frontend       Next.js shell
REM    SRRA-OPH Frontend  Next.js
REM
REM  Each service opens in its own titled console window. Close a window to
REM  stop that service. Re-running while services are up starts duplicates;
REM  the OCE backend singleton terminates the old backend instance first.
REM
REM  Usage:
REM    start_all_servers.cmd          Boot everything
REM    set DRYRUN=1 & start_all_servers.cmd   Preview without launching
REM ===========================================================================
setlocal
set "ROOT=C:\Users\wifik\Desktop\projects\larger-lab"
set "PYEXE=.venv\Scripts\python.exe"

if not exist "%ROOT%\.venv\Scripts\python.exe" (
    echo [ERROR] venv interpreter not found: %ROOT%\.venv\Scripts\python.exe
    echo         Create it with:  python -m venv "%ROOT%\.venv"
    exit /b 1
)

REM Dry-run mode: print each launch line instead of executing it.
set "RUN=start"
if defined DRYRUN set "RUN=echo [dry-run]"

echo Starting Larger-Lab stack from %ROOT%
echo.

REM --- OCE Backend (Continuity Core API, :8000) ---
%RUN% "OCE Backend" cmd /c "cd /d %ROOT% && %PYEXE% -m oce.backend.main"

REM --- SRRA-OPH API Server (:8001) ---
%RUN% "API Server" cmd /c "cd /d %ROOT% && %PYEXE% srrs_opc/frontend/api_server.py"

REM --- PO Telegram Bot (only if a token is configured in .env) ---
findstr /b "TELEGRAM_TOKEN" "%ROOT%\.env" >nul 2>&1
if errorlevel 1 (
    echo [SKIP] PO Bot: no TELEGRAM_TOKEN in %ROOT%\.env - add one and re-run
) else (
    %RUN% "PO Bot" cmd /c "cd /d %ROOT% && %PYEXE% scripts/telegram_gateway.py"
)

REM --- OCE Frontend (Next.js) ---
%RUN% "OCE Frontend" cmd /c "cd /d %ROOT%\oce\frontend && npm run dev"

REM --- SRRA-OPH Frontend (Next.js) ---
%RUN% "SRRA Frontend" cmd /c "cd /d %ROOT%\srrs_opc\frontend && npm run dev"

echo.
echo All services launching in their own windows - check each window for status.
endlocal

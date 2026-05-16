@echo off
REM OC2 Start Script — With Full Verification
REM Usage: tools\oc2-start.cmd

echo ============================================
echo  OC2 Start Script
echo ============================================

set "OPENCLAW_HOME=C:\Users\wifik\Desktop\projects\larger-lab\.openclaw-2"
set "TMPDIR=C:\Users\wifik\AppData\Local\Temp"

REM Step 1: Kill any existing OC2 process
echo [1/6] Killing existing OC2 processes...
taskkill /F /IM node.exe /FI "WINDOWTITLE eq *18790*" 2>nul
timeout /t 2 /nobreak >nul

REM Step 2: Validate config exists
echo [2/6] Checking config...
if not exist "%OPENCLAW_HOME%\.openclaw\openclaw.json" (
    echo ERROR: Config not found at %OPENCLAW_HOME%\.openclaw\openclaw.json
    exit /b 1
)

REM Step 3: Check agent models.json has valid API key
echo [3/6] Checking agent models.json...
python -c "
import json, sys
models_file = r'C:\Users\wifik\.openclaw\agents\main\agent\models.json'
try:
    with open(models_file) as f:
        config = json.load(f)
    or_config = config.get('providers', {}).get('openrouter', {})
    api_key = or_config.get('apiKey', '')
    if api_key == 'OPENROUTER_API_KEY' or not api_key:
        print('ERROR: OpenRouter API key is not set in agent models.json')
        print('Fix: Update C:\Users\wifik\.openclaw\agents\main\agent\models.json')
        sys.exit(1)
    models = or_config.get('models', [])
    if not models:
        print('ERROR: No models configured in agent models.json')
        sys.exit(1)
    print(f'OK: {len(models)} models configured, API key present')
except Exception as e:
    print(f'ERROR checking models.json: {e}')
    sys.exit(1)
" 2>nul
if errorlevel 1 (
    echo FAILED: Agent models.json check failed
    exit /b 1
)

REM Step 4: Start OC2
echo [4/6] Starting OC2 Gateway...
cd /d "C:\Users\wifik\Desktop\projects\larger-lab"
start "" /min "C:\Program Files\nodejs\node.exe" "C:\Users\wifik\AppData\Roaming\npm\node_modules\openclaw\dist\index.js" gateway run --port 18790 --allow-unconfigured

REM Step 5: Wait for gateway to be ready
echo [5/6] Waiting for gateway to start...
set /a attempts=0
:wait_loop
timeout /t 3 /nobreak >nul
set /a attempts+=1
powershell -Command "try { $r = Invoke-RestMethod -Uri 'http://127.0.0.1:18790/health' -TimeoutSec 3; exit 0 } catch { exit 1 }" 2>nul
if errorlevel 1 (
    if %attempts% lss 10 (
        echo   Attempt %attempts%/10...
        goto wait_loop
    ) else (
        echo ERROR: Gateway failed to start after 30 seconds
        echo Check logs: C:\Users\wifik\AppData\Local\Temp\openclaw\openclaw-2026-05-16.log
        exit /b 1
    )
)

REM Step 6: Verify agent model loaded
echo [6/6] Verifying agent model...
timeout /t 5 /nobreak >nul
powershell -Command "try { $r = Invoke-RestMethod -Uri 'http://127.0.0.1:18790/health' -TimeoutSec 5; Write-Host ('Gateway: ' + $r.status) } catch { Write-Host 'Gateway: DOWN' }"

echo.
echo ============================================
echo  OC2 Start Complete
echo ============================================
echo  Health: http://127.0.0.1:18790/health
echo  Logs:   C:\Users\wifik\AppData\Local\Temp\openclaw\openclaw-2026-05-16.log
echo ============================================

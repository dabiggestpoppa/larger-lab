@echo off
REM OC2 Doctor — Full Diagnostic
REM Usage: tools\oc2-doctor.cmd

echo ============================================
echo  OC2 Doctor — Full Diagnostic
echo ============================================
echo.

set "OPENCLAW_HOME=C:\Users\wifik\Desktop\projects\larger-lab\.openclaw-2"

REM 1. Process check
echo [1] Process Check:
powershell -Command "Get-Process -Name node -ErrorAction SilentlyContinue | Where-Object { $_.CommandLine -like '*18790*' } | ForEach-Object { Write-Host ('  PID: ' + $_.Id + ' | Memory: ' + [math]::Round($_.WorkingSet64/1MB,1) + 'MB') }"
echo.

REM 2. Port check
echo [2] Port Check:
powershell -Command "try { $r = Invoke-RestMethod -Uri 'http://127.0.0.1:18790/health' -TimeoutSec 5; Write-Host ('  Gateway: ' + $r.status) } catch { Write-Host '  Gateway: DOWN - ' $_.Exception.Message }"
echo.

REM 3. Config check
echo [3] Config Check:
if exist "%OPENCLAW_HOME%\.openclaw\openclaw.json" (
    echo   Config file: OK
    python -c "
import json
with open(r'%OPENCLAW_HOME%\.openclaw\openclaw.json') as f:
    config = json.load(f)
model = config.get('agents',{}).get('defaults',{}).get('model','NOT SET')
print('  Model: ' + model)
# Check for invalid keys
bad = []
for k in ['contextLimit']:
    if k in config.get('agents',{}).get('defaults',{}):
        bad.append(k)
if bad:
    print('  WARNING: Invalid keys found: ' + ', '.join(bad))
else:
    print('  Config keys: OK')
" 2>nul
) else (
    echo   Config file: MISSING
)
echo.

REM 4. Agent models.json check
echo [4] Agent Models Check:
python -c "
import json
models_file = r'C:\Users\wifik\.openclaw\agents\main\agent\models.json'
try:
    with open(models_file) as f:
        config = json.load(f)
    or_config = config.get('providers',{}).get('openrouter',{})
    api_key = or_config.get('apiKey','')
    if api_key == 'OPENROUTER_API_KEY':
        print('  ERROR: API key is literal string OPENROUTER_API_KEY')
        print('  Fix: Replace with actual API key')
    elif not api_key:
        print('  ERROR: No API key found')
    else:
        print('  API key: OK (' + api_key[:10] + '...)')
    models = or_config.get('models',[])
    print('  Models: ' + str(len(models)) + ' configured')
    for m in models:
        print('    - ' + m.get('id','?'))
except Exception as e:
    print('  ERROR: ' + str(e))
" 2>nul
echo.

REM 5. Session check
echo [5] Session Check:
python -c "
import json
sessions_file = r'%OPENCLAW_HOME%\.openclaw\agents\main\sessions\sessions.json'
try:
    with open(sessions_file, encoding='utf-8') as f:
        data = json.load(f)
    tg_sessions = {k:v for k,v in data.items() if 'telegram' in k.lower()}
    if not tg_sessions:
        print('  No telegram sessions found (fresh start)')
    for k,v in tg_sessions.items():
        status = v.get('status','?')
        tokens = v.get('contextTokens',0)
        model = v.get('model','?')
        print('  Session: ' + k[-30:])
        print('    Status: ' + status)
        print('    Model: ' + model)
        print('    Context: ' + str(tokens) + ' tokens')
        if tokens > 600000:
            print('    WARNING: Context very high! Consider /new session')
        if status == 'running':
            print('    WARNING: Session stuck in running state!')
except Exception as e:
    print('  ERROR: ' + str(e))
" 2>nul
echo.

REM 6. Log check
echo [6] Recent Log Errors:
powershell -Command "Get-Content 'C:\Users\wifik\AppData\Local\Temp\openclaw\openclaw-2026-05-16.log' -Tail 20 | Where-Object { $_ -match 'error|Error|ERROR|fail|FAIL|failed' } | ForEach-Object { Write-Host ('  ' + $_) }"
echo.

echo ============================================
echo  Doctor Complete
echo ============================================

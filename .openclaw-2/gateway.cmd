@echo off
cd /d C:\Users\wifik\Desktop\projects\larger-lab

:: Clear stale sessions to prevent context overflow on restart
del /q "%USERPROFILE%\.openclaw-2\.openclaw\agents\main\sessions\*.jsonl" 2>nul
del /q "%USERPROFILE%\.openclaw-2\.openclaw\agents\main\sessions\*.reset.*" 2>nul
del /q "%USERPROFILE%\.openclaw-2\.openclaw\agents\main\sessions\*.trajectory*" 2>nul
del /q "%USERPROFILE%\.openclaw-2\.openclaw\agents\main\sessions\*.checkpoint*" 2>nul

node "C:\Users\wifik\AppData\Roaming\npm\node_modules\openclaw\openclaw.mjs" gateway run --port 18790

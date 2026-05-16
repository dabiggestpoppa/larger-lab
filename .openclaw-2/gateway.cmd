@echo off
rem OpenClaw 2 Gateway (v2026.5.7) - Port 18790
set "TMPDIR=C:\Users\wifik\AppData\Local\Temp"
set "OPENCLAW_HOME=C:\Users\wifik\Desktop\projects\larger-lab\.openclaw-2"
set "OPENCLAW_GATEWAY_PORT=18790"
set "OPENCLAW_SYSTEMD_UNIT=openclaw-2-gateway.service"
set "OPENCLAW_WINDOWS_TASK_NAME=OpenClaw 2 Gateway"
set "OPENCLAW_SERVICE_MARKER=openclaw-2"
set "OPENCLAW_SERVICE_KIND=gateway"
set "OPENCLAW_SERVICE_VERSION=2026.5.7"
"C:\Program Files\nodejs\node.exe" C:\Users\wifik\AppData\Roaming\npm\node_modules\openclaw\dist\index.js gateway --port 18790

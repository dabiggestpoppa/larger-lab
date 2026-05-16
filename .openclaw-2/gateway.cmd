@echo off
set "OPENCLAW_HOME=C:\Users\wifik\Desktop\projects\larger-lab\.openclaw-2"
set "TMPDIR=C:\Users\wifik\AppData\Local\Temp"
cd /d "C:\Users\wifik\Desktop\projects\larger-lab"
"C:\Program Files\nodejs\node.exe" "C:\Users\wifik\AppData\Roaming\npm\node_modules\openclaw\dist\index.js" gateway run --port 18790 --allow-unconfigured

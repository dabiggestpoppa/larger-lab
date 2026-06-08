@echo off
echo Starting all Larger-Lab services...
start "OCE Frontend" cmd /c "cd /d C:\Users\wifik\Desktop\projects\larger-lab\oce\frontend && npm run dev"
start "SRRA-OPH Frontend" cmd /c "cd /d C:\Users\wifik\Desktop\projects\larger-lab\srrs_opc\frontend && npm run dev"
start "API Server" cmd /c "cd /d C:\Users\wifik\Desktop\projects\larger-lab && python srrs_opc/frontend/api_server.py"
start "PO Bot" cmd /c "cd /d C:\Users\wifik\Desktop\projects\larger-lab && python scripts/telegram_gateway.py"
echo All services started.
@echo off
echo === KILLING ALL DUPLICATES ===

:: Kill ALL python processes running our scripts
wmic process where "name='python.exe' and (commandline like '%%cerebus_live_bridge%%' or commandline like '%%signal_bot%%' or commandline like '%%telegram_gateway%%' or commandline like '%%twin_bridge%%')" delete 2>nul

:: Also kill UV python instances
wmic process where "name='python.exe' and commandline like '%%uv%%python%%' and (commandline like '%%cerebus%%' or commandline like '%%signal%%' or commandline like '%%telegram%%')" delete 2>nul

timeout /t 3 /nobreak >nul

echo === STARTING FRESH ===

cd /d C:\Users\wifik\Desktop\projects\larger-lab

:: Start bridge (venv python only)
start /B C:\Users\wifik\Desktop\projects\larger-lab\.venv\Scripts\python.exe quant-lab\mt5\cerebus_live_bridge.py --symbols EURJPY.PRO,EURNZD.PRO,GBPNZD.PRO,EURAUD.PRO,GBPAUD.PRO,GBPCAD.PRO,FR40.PRO --lot-size 0.01

timeout /t 5 /nobreak >nul

:: Start signal bot
start /B C:\Users\wifik\Desktop\projects\larger-lab\.venv\Scripts\python.exe scripts\signal_bot.py

timeout /t 3 /nobreak >nul

:: Start telegram gateway
start /B C:\Users\wifik\Desktop\projects\larger-lab\.venv\Scripts\python.exe scripts\telegram_gateway.py

timeout /t 5 /nobreak >nul

echo === STATUS ===
wmic process where "name='python.exe' and (commandline like '%%cerebus_live_bridge%%' or commandline like '%%signal_bot%%' or commandline like '%%telegram_gateway%%')" get ProcessId,CommandLine /format:list

echo === DONE ===

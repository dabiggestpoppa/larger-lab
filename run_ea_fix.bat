@echo off
REM CEREBUS EA Auto-Fix Script
REM This will compile and test the EA continuously

:loop
echo [%date% %time%] Starting EA check...

REM Try to compile with MetaEditor
echo Compiling EA...
"C:\Program Files\MetaTrader 5\metaeditor64.exe" /compile:"C:\Users\wifik\AppData\Roaming\MetaQuotes\Terminal\A9831A95D2ED3390882422E0C995D278\MQL5\Experts\Cerebus_Symmetry_OptionB.mq5" 2>nul

if %errorlevel% equ 0 (
    echo EA compiled successfully
) else (
    echo Compilation may have issues - check manually
)

REM Wait 5 minutes
timeout /t 300 /nobreak >nul

goto loop
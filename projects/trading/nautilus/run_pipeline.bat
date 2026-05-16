@echo off
cd /d C:\Users\wifik\Desktop\projects\larger-lab
call .venv\Scripts\activate.bat

echo === STEP 1: DATA PREP ===
python nautilus\step1_prep_data.py
echo STEP1 EXIT CODE: %ERRORLEVEL%

echo.
echo === STEP 2: BACKTEST ===
python nautilus\step2_backtest.py
echo STEP2 EXIT CODE: %ERRORLEVEL%

echo.
echo === DONE ===
pause

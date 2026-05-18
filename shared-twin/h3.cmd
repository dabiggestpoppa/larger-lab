@echo off
REM H3 Hermes Support Instance Launcher
REM Runs H3 as a persistent background process
:loop
python C:\Users\wifik\Desktop\projects\larger-lab\shared-twin\h3_hermes.py
timeout /t 5 /nobreak >nul
goto loop

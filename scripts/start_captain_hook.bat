@echo off
REM Captain Hook Discord Bot - Startup Script
REM Runs the bot in background, logs to file

cd /d C:\Users\wifik\Desktop\projects\larger-lab
python scripts\captain_hook_discord.py >> logs\captain_hook.log 2>&1
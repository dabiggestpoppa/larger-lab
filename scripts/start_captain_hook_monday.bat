@echo off
REM ============================================================
REM CAPTAIN HOOK DISCORD BOT - Monday Startup
REM ============================================================
REM Simple workflow:
REM 1. Wait for DMR signals from dmr_signals.jsonl
REM 2. One signal = one Discord message = one log entry (no spam)
REM 3. 5 PM EST daily: EOD report (signals sent, trades triggered)
REM ============================================================

cd /d C:\Users\wifik\Desktop\projects\larger-lab

echo Starting Captain Hook Discord Bot...
echo Webhook: CONFIGURED
echo Watching: quant-lab/mt5/live_logs/dmr_signals.jsonl
echo EOD Report: 5 PM EST daily
echo.
echo Press Ctrl+C to stop
echo.

python scripts\captain_hook_discord.py

pause
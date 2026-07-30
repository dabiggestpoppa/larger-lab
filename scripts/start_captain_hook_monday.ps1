# CAPTAIN HOOK DISCORD BOT - Monday Startup
# ============================================================
# Simple workflow:
# 1. Wait for DMR signals from dmr_signals.jsonl
# 2. One signal = one Discord message = one log entry (no spam)
# 3. 5 PM EST daily: EOD report (signals sent, trades triggered)
# ============================================================

Set-Location "C:\Users\wifik\Desktop\projects\larger-lab"

Write-Host "Starting Captain Hook Discord Bot..." -ForegroundColor Green
Write-Host "Webhook: CONFIGURED" -ForegroundColor Cyan
Write-Host "Watching: quant-lab/mt5/live_logs/dmr_signals.jsonl" -ForegroundColor Cyan
Write-Host "EOD Report: 5 PM EST daily" -ForegroundColor Cyan
Write-Host ""
Write-Host "Press Ctrl+C to stop" -ForegroundColor Yellow
Write-Host ""

python scripts\captain_hook_discord.py
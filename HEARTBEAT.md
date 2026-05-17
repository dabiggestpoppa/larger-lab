# HEARTBEAT.md — OWL Operator

## System Health Check
- Run `python tools/hermes-watchdog.py --once` every 4 hours
- Run `python tools/system_health.py --full` daily at 6am
- Alert on any `degraded` or `critical` findings

## Active Monitoring
- Hermes Watchdog runs in background (checks gateway every 5 min)
- Sub-agent status checked on-demand (not polled)
- Team chat checked for new messages on each turn

## Do NOT
- Poll subagents in a loop
- Send heartbeat messages to Telegram
- Run continuous background processes from heartbeat
- Modify this file without MAD approval

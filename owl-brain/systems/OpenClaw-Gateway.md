# OpenClaw Gateway

> The runtime that powers OWL. OC2 on port 18790.

## Instance: OC2 (Active)
- **Port:** 18790
- **Config:** `.openclaw-2/.openclaw/openclaw.json`
- **Status:** Running (PID varies)
- **Dashboard:** http://127.0.0.1:18790/
- **Logs:** `C:\Users\wifik\AppData\Local\Temp\openclaw\openclaw-YYYY-MM-DD.log`

## Instance: OC1 (Deprecated)
- **Port:** 18789
- **Status:** Removed from all docs, no longer maintained

## Key Config
```json5
{
  "agents.defaults.model": "openrouter/owl-alpha",
  "gateway.port": 18790,
  "gateway.bind": "loopback",
  "session.dmScope": "per-channel-peer",
  "channels.telegram.enabled": true
}
```

## Known Issues (from self-healing scan)
1. **Model prewarm**: Avg 7436ms, max 15938ms — blocks event loop
2. **Stalled subagents**: 2 sessions stuck 800-900+ seconds
3. **Orphan recovery timeout**: 10s too low, causing failures
4. **Fetch timeouts**: 44 network timeout events (Telegram API)

## Health Monitoring
- Self-heal engine scans logs every 4th heartbeat
- Errors logged to `db/owl_health.db`
- Bug annotations in `bugs/open/`

## Related
- [[Self-Healing Framework]]
- [[Error DB]]
- [[Agent Team]]

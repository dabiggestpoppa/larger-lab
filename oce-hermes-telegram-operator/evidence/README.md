# Evidence Directory

This directory contains:

- `audit.jsonl` — Structured audit log of all MCP interactions
- `startup.json` — Last startup state
- `validation-report.md` — Acceptance gate validation results

## Audit Log Format

Each line is a JSON object:

```json
{
  "timestamp": "2026-08-23T12:00:00Z",
  "request_id": "uuid-v4",
  "actor_id": "telegram-user-id",
  "chat_id": "telegram-chat-id",
  "tool_name": "oce_health",
  "decision": "ALLOW",
  "latency_ms": 42.5,
  "outcome": {"state": "PASS"},
  "error": null,
  "metadata": {}
}
```

## Decisions

- `ALLOW` — Request was permitted and executed
- `DENY` — Request was denied (auth failure, policy violation)
- `ERROR` — Request failed due to system error
- `RATE_LIMITED` — Request was blocked by rate limiter

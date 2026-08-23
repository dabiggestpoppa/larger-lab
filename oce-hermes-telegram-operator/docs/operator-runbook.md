# Operator Runbook — OCE Hermes Telegram Operator

> Version: 0.1.0  
> Date: 2026-08-23

## Quick Reference

| Action | Command |
|--------|---------|
| Setup | `./scripts/setup.sh` |
| Start | `./scripts/start.sh` |
| Stop | `./scripts/stop.sh` |
| Status | `./scripts/status.sh` |
| Doctor | `python3 scripts/doctor.py` |
| Tests | `python3 -m pytest tests/ -v` |

## First-Time Setup

1. Clone the repository
2. Run `./scripts/setup.sh`
3. Edit `.env` with your secrets:
   - `TELEGRAM_BOT_TOKEN` — from @BotFather
   - `TELEGRAM_ALLOWED_USERS` — your numeric Telegram user ID
4. Run `./scripts/doctor.py` to validate
5. Run `./scripts/start.sh` to start
6. Send `/start` to your bot on Telegram

## Daily Operations

### Checking System Health
```bash
./scripts/status.sh
```

### Viewing Logs
```bash
# Facade logs
tail -f logs/facade.log

# Hermes logs
tail -f logs/hermes.log

# Audit trail
tail -f evidence/audit.jsonl | python3 -m json.tool
```

### Restarting Services
```bash
./scripts/stop.sh
./scripts/start.sh
```

## Telegram Commands

| Command | Description |
|---------|-------------|
| `/start` | Welcome and identity |
| `/help` | List commands |
| `/health` | Backend health check |
| `/status` | Full system status |
| `/components` | Component health |
| `/jobs` | List jobs |
| `/job <id>` | Job details |
| `/events` | Recent events |
| `/evidence` | Evidence status |
| `/cost` | Cost analytics |
| `/capabilities` | System capabilities |
| `/privacy` | Privacy policy |
| `/audit <id>` | Audit trail |

## Troubleshooting

### Bot not responding
1. Check `./scripts/status.sh` — is Hermes running?
2. Check `logs/hermes.log` for errors
3. Verify `TELEGRAM_BOT_TOKEN` is correct
4. Verify `TELEGRAM_ALLOWED_USERS` contains your user ID

### OCE offline
1. Check if OCE backend is running: `curl http://localhost:8000/health`
2. If OCE is down, facade returns OFFLINE (correct behavior)
3. Facade uses mock data when no `OCE_SERVICE_TOKEN` is set

### Rate limiting
1. Check `evidence/audit.jsonl` for RATE_LIMITED entries
2. Default limit: 60 requests/minute
3. Increase `RATE_LIMIT_PER_MINUTE` in `.env` if needed

### Permission denied
1. Verify your Telegram user ID is in `TELEGRAM_ALLOWED_USERS`
2. Use @userinfobot to get your numeric ID
3. Ensure `TELEGRAM_ALLOW_ALL_USERS=false`

## Security Checklist

- [ ] `.env` is not committed to git
- [ ] `TELEGRAM_ALLOW_ALL_USERS=false`
- [ ] `TELEGRAM_ALLOWED_USERS` contains only authorized IDs
- [ ] No bot tokens in logs or evidence
- [ ] Facade binds to 127.0.0.1 only
- [ ] No public ports are open
- [ ] Audit logging is enabled

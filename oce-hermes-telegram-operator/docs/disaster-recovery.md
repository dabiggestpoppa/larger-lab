# Disaster Recovery Runbook — OCE Hermes Telegram Operator

> Version: 0.1.0  
> Date: 2026-08-23

## Recovery Scenarios

### Scenario 1: Bot Token Compromised

**Impact:** An attacker can control the bot and read messages.

**Recovery:**
1. Immediately revoke the token via @BotFather: `/revoke`
2. Generate a new token
3. Update `TELEGRAM_BOT_TOKEN` in `.env`
4. Restart: `./scripts/stop.sh && ./scripts/start.sh`
5. Verify bot responds to authorized users only
6. Review `evidence/audit.jsonl` for unauthorized access

### Scenario 2: OCE Service Token Compromised

**Impact:** An attacker can read OCE data through the facade.

**Recovery:**
1. Rotate the OCE service token
2. Update `OCE_SERVICE_TOKEN` in `.env`
3. Restart facade
4. Verify old token is rejected
5. Review audit logs for suspicious queries

### Scenario 3: Unauthorized User Access

**Impact:** An unauthorized user accessed the bot.

**Recovery:**
1. Check `evidence/audit.jsonl` for the unauthorized actor ID
2. Remove the user from `TELEGRAM_ALLOWED_USERS`
3. Verify `TELEGRAM_ALLOW_ALL_USERS=false`
4. Restart: `./scripts/stop.sh && ./scripts/start.sh`
5. Consider revoking and rotating the bot token

### Scenario 4: Hermes Agent Crash

**Impact:** Telegram bot stops responding.

**Recovery:**
1. Check `logs/hermes.log` for crash details
2. Restart: `./scripts/start.sh`
3. If persistent, check Hermes Agent version compatibility
4. Verify OCE MCP facade is still running

### Scenario 5: OCE Backend Unreachable

**Impact:** Facade returns OFFLINE for all queries.

**Recovery:**
1. Check OCE backend: `curl http://localhost:8000/health`
2. If OCE is down, this is expected behavior — facade correctly reports OFFLINE
3. Restart OCE backend if needed
4. Facade will automatically reconnect

### Scenario 6: Data Loss

**Impact:** Audit logs or evidence lost.

**Recovery:**
1. Check if backup exists in `evidence/` directory
2. Audit logs are append-only — partial loss may occur
3. Restart with fresh logs if needed
4. Document the incident

## Backup Strategy

### What to Back Up
- `.env` (securely, with encryption)
- `evidence/audit.jsonl`
- `evidence/startup.json`
- `config/hermes-config.yaml`

### Backup Commands
```bash
# Create encrypted backup
tar czf - evidence/ config/ .env | gpg -c -o backup-$(date +%Y%m%d).tar.gz.gpg

# Restore from backup
gpg -d backup-YYYYMMDD.tar.gz.gpg | tar xzf -
```

## Communication Template

### Incident Notification
```
Subject: OCE Telegram Operator Incident

What happened: [Brief description]
Impact: [Who/what was affected]
Current status: [Recovery in progress / Resolved]
Actions taken: [List of steps]
Next steps: [What will happen next]
```

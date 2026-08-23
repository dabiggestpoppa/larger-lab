# Secret Rotation Runbook — OCE Hermes Telegram Operator

> Version: 0.1.0  
> Date: 2026-08-23

## Secrets Inventory

| Secret | Location | Rotation Frequency |
|--------|----------|-------------------|
| Telegram Bot Token | `TELEGRAM_BOT_TOKEN` in `.env` | On compromise / quarterly |
| OCE Service Token | `OCE_SERVICE_TOKEN` in `.env` | On compromise / quarterly |
| LLM Provider Key | `OPENROUTER_API_KEY` in `.env` | Per provider policy |

## Rotation Procedures

### Telegram Bot Token

1. Open Telegram → @BotFather
2. Send `/mybots` → Select your bot
3. Send `/revoke` → Select your bot
4. Confirm revocation
5. Generate new token: `/newbot` or use existing bot
6. Update `TELEGRAM_BOT_TOKEN` in `.env`
7. Restart: `./scripts/stop.sh && ./scripts/start.sh`
8. Verify bot responds on Telegram

**Warning:** Revoking the token immediately invalidates the old one.

### OCE Service Token

1. Generate new token: `python3 -c "import secrets; print('oce-read-' + secrets.token_hex(16))"`
2. Update OCE backend with new token (if applicable)
3. Update `OCE_SERVICE_TOKEN` in `.env`
4. Restart: `./scripts/stop.sh && ./scripts/start.sh`
5. Verify facade connects to OCE

### LLM Provider Key

1. Log in to your LLM provider (OpenRouter, Anthropic, etc.)
2. Generate new API key
3. Update the corresponding env var in `.env`
4. Restart Hermes Agent

## Security Notes

- Never commit `.env` to git
- Never log, display, or commit actual token values
- Use `mask_for_display()` for safe output
- Audit logs always redact tokens
- Rotate immediately if compromise is suspected

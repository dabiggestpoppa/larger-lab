---
name: claude-hermes-mcp
description: MCP bridge that lets Claude Desktop/mobile delegate tasks to a local Hermes Agent running on your hardware.
---

# Claude Hermes MCP Skill

An MCP server that bridges Claude Desktop and Claude mobile apps to a local Hermes Agent.

## Architecture

```
Claude Desktop/Mobile → HTTPS (Custom Connector + OAuth 2.1) → cloudflared tunnel → hermes-mcp (port 8765) → Hermes gateway (port 8642)
```

## Prerequisites

- Hermes Agent installed and running on a Linux/WSL machine
- Hermes gateway listening on `127.0.0.1:8642`
- `API_SERVER_KEY` from `~/.hermes/.env`

## Installation

```bash
# 1. Install
pipx install hermes-mcp

# 2. Mint OAuth client credentials
hermes-mcp mint-client

# 3. Start tunnel (testing)
cloudflared tunnel --url http://127.0.0.1:8765

# 4. Export env vars
export OAUTH_CLIENT_ID=<from step 2>
export OAUTH_CLIENT_SECRET=<from step 2>
export OAUTH_ISSUER_URL=https://<tunnel-url>
export HERMES_API_KEY=<from ~/.hermes/.env>

# 5. Verify
hermes-mcp doctor

# 6. Run
hermes-mcp serve
```

## Configuration

| Variable | Required | Purpose |
|----------|----------|---------|
| `OAUTH_CLIENT_ID` | yes | OAuth 2.1 client ID |
| `OAUTH_CLIENT_SECRET` | yes | OAuth 2.1 client secret |
| `OAUTH_ISSUER_URL` | yes | Public HTTPS tunnel URL |
| `HERMES_API_KEY` | yes | Bearer token for Hermes gateway |
| `HERMES_API_URL` | no | Hermes gateway URL (default: `http://127.0.0.1:8642`) |
| `MCP_ALLOWED_HOSTS` | no | Additional allowed hostnames |

## Tool: `hermes_ask(prompt, session_id?, toolsets?)`

Delegates tasks to Hermes for:
- Scheduling cron jobs / recurring tasks
- Browser-driven web search and scraping
- Sending email
- Creating/editing local documents
- Persistent memory and skills
- WhatsApp/Slack messaging

## Source

https://github.com/mlennie/claude-hermes-mcp
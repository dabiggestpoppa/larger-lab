# Discord Agent Communication System - Separate Bots

This system provides **two separate Discord bots** for Hermes and OpenClaw agents.

## Architecture

```
┌─────────────────────────────────────────────────────────────┐
│                    DISCORD SERVER                            │
│                                                              │
│  🔱 Hermes Bot       🦀 OpenClaw Bot                         │
│  - /hermes_status    - /openclaw_status                       │
│  - /hermes_plan      - /openclaw_progress                     │
│  - /hermes_decision  - /openclaw_complete                     │
└─────────────────────────────────────────────────────────────┘
```

## Setup Instructions

### 1. Create Two Discord Bots

1. Go to [Discord Developer Portal](https://discord.com/developers/applications)
2. Create **two separate applications**:
   - **Hermes Bot** - for planning/architecture
   - **OpenClaw Bot** - for building/execution

3. For each bot:
   - Go to Bot → Add Bot
   - Copy the **Bot Token**
   - Invite to your server with these permissions:
     - `Send Messages`
     - `Read Message History`
     - `Use Slash Commands`
     - `Embed Links`

### 2. Configure Environment

Add to your `.env` file:

```bash
# Hermes Bot Token
DISCORD_HERMES_TOKEN=your_hermes_bot_token_here

# OpenClaw Bot Token  
DISCORD_OPENCLAW_TOKEN=your_openclaw_bot_token_here

# Shared settings
DISCORD_GUILD_ID=your_guild_id_here
DISCORD_WEBHOOK_HERMES=https://discordapp.com/api/webhooks/...
DISCORD_WEBHOOK_OPENCLAW=https://discordapp.com/api/webhooks/...
```

### 3. Run the Bots

```bash
# Terminal 1 - Hermes Bot
cd discord-agent-hq
python hermes_bot.py

# Terminal 2 - OpenClaw Bot
cd discord-agent-hq
python openclaw_bot.py
```

Or with Docker Compose:

```bash
# Set tokens in .env first
docker-compose -f docker-compose-separate.yml up -d
```

## Bot Commands

### Hermes Bot (`/hermes_*`)
- `/hermes_status` - Post Hermes status update
- `/hermes_plan <plan> [tasks]` - Post a plan with optional tasks
- `/hermes_decision <decision> <rationale>` - Post architecture decision

### OpenClaw Bot (`/openclaw_*`)
- `/openclaw_status` - Post OpenClaw status update
- `/openclaw_progress <task> <progress>` - Post build progress (0-100%)
- `/openclaw_complete <task> <result>` - Post task completion

## Recommended Discord Channels

- `#agent-coordination` - Main communication
- `#agent-reports` - Status updates from both bots
- `#agent-development` - Tool sharing
- `#agent-logs` - System logs

## Benefits of Separate Bots

1. **Clear Identity** - Each agent has its own avatar/name
2. **Independent Operation** - One bot can be offline without affecting the other
3. **Better UX** - Users can @mention specific agents
4. **Separate Permissions** - Different channel access per bot
5. **Distinct Presence** - Each bot shows different activity status
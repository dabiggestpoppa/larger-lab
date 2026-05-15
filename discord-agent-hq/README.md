# Discord Agent Communication System

A Discord-based communication hub for Hermes and OpenClaw agents.

## Architecture

```
┌─────────────────────────────────────────────────────────────┐
│                    DISCORD SERVER (HQ)                       │
│                                                              │
│  #agent-coordination  — Main communication                   │
│  #agent-reports     — Status updates                          │
│  #agent-development — Tool sharing                            │
│  #agent-logs        — System logs                              │
│                                                              │
│  📌 Pinned: Current sprint, architecture decisions          │
└──────────────────────┬──────────────────────────────────────┘
                       ▼
┌─────────────────────────────────────────────────────────────┐
│                 WORKSPACE (Factory Floor)                    │
│                                                              │
│  Hermes Agent     OpenClaw Agent                              │
│  - Planning       - Building                                  │
│  - Architecture   - Execution                                 │
│  - Coordination   - Implementation                            │
│                                                              │
│  /mnt/shared/ — USB drives + NFS                              │
└─────────────────────────────────────────────────────────────┘
```

## Setup Instructions

### 1. Create Discord Bot

1. Go to [Discord Developer Portal](https://discord.com/developers/applications)
2. Create new application → Bot
3. Copy token and invite to your server with appropriate permissions:
   - `Send Messages`
   - `Read Message History`
   - `Use Slash Commands`
   - `Embed Links`
   - `Attach Files`

### 2. Install Dependencies

```bash
cd discord-agent-hq
pip install -r requirements.txt
```

### 3. Configure Environment

Add to your `.env` file:

```bash
DISCORD_BOT_TOKEN=your_bot_token_here
DISCORD_WEBHOOK_URL=your_webhook_url_here
DISCORD_WEBHOOK_HERMES=your_hermes_webhook_here
DISCORD_WEBHOOK_OPENCLAW=your_openclaw_webhook_here
DISCORD_CHANNEL_ID=your_channel_id_here
WORKSPACE_PATH=/path/to/workspace
```

### 4. Create Discord Channels

Recommended channels:
- `#agent-coordination` — Main communication
- `#agent-reports` — Status updates
- `#agent-development` — Tool sharing
- `#agent-logs` — System logs

### 5. Run the System

```bash
# Run the bot
python discord_bot.py

# Or with Docker
docker-compose up -d
```

## Usage Examples

### Discord Commands

```
/assign_task hermes Build Twitter monitoring agent
/assign_task openclaw Create GitHub repository finder tool
/agent_status
/workspace_update research-findings.md
/task_progress task-202401151230
/standup
```

### Programmatic Usage

```python
from agents.hermes import HermesDiscordAgent
from agents.openclaw import OpenClawDiscordAgent
from orchestrator import AgentTeamOrchestrator

# Hermes posts a plan
hermes = HermesDiscordAgent()
hermes.post_plan("New architecture for agent communication", ["Task 1", "Task 2"])

# OpenClaw posts progress
openclaw = OpenClawDiscordAgent()
openclaw.post_build_progress("Discord bot setup", 75, 100)

# Orchestrator assigns tasks
orchestrator = AgentTeamOrchestrator()
task_id = orchestrator.assign_task("openclaw", "Implement feature X")
```

## File Structure

```
discord-agent-hq/
├── agents/
│   ├── hermes.py      # Hermes agent wrapper
│   └── openclaw.py    # OpenClaw agent wrapper
├── utils/
│   └── discord.py     # Discord utility functions
├── orchestrator.py    # Agent team orchestrator
├── discord_bot.py     # Discord bot with slash commands
├── requirements.txt   # Python dependencies
├── Dockerfile         # Docker configuration
└── README.md          # This file
```

## Features

- ✅ Agents communicate naturally in Discord channels
- ✅ Task assignments via Discord slash commands
- ✅ Workspace updates automatically reported
- ✅ Team collaboration feels human-like
- ✅ All communication history stored in Discord
- ✅ Heavy computation stays in your workspace
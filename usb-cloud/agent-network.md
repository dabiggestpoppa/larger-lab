# Agent Network — Multi-Machine Coordination

> How OpenClaw, Hermes, and Claude Code work together across local + cloud.

## Network Topology

```
┌─────────────────────────────────────────────────────────────────────────────┐
│                              LOCAL MACHINE                                   │
│                                                                              │
│  ┌──────────────┐    ┌──────────────┐    ┌──────────────┐                   │
│  │  Claude Code  │    │   OpenClaw   │    │    Hermes    │                   │
│  │  (VS Code)    │    │   (Gateway)  │    │  (Telegram)  │                   │
│  │              │    │   :18789     │    │              │                   │
│  └──────┬───────┘    └──────┬───────┘    └──────┬───────┘                   │
│         │                   │                   │                            │
│         └───────────────────┼───────────────────┘                            │
│                             │                                                │
│                    ┌────────▼────────┐                                       │
│                    │   Workspace      │                                       │
│                    │   larger-lab/    │                                       │
│                    │   (shared)       │                                       │
│                    └────────┬────────┘                                       │
│                             │                                                │
│              ┌──────────────┼──────────────┐                                 │
│              │              │              │                                  │
│         ┌────▼────┐   ┌────▼────┐   ┌────▼────┐                             │
│         │ USB D:  │   │ USB E:  │   │  Cloud  │                             │
│         │ (warm)  │   │ (cold)  │   │ (offsite)│                             │
│         └─────────┘   └─────────┘   └─────────┘                             │
└─────────────────────────────────────────────────────────────────────────────┘
                                    │
                          SSH Tunnel / rclone
                                    │
┌───────────────────────────────────▼─────────────────────────────────────────┐
│                              CLOUD SERVER                                    │
│                                                                              │
│  ┌──────────────┐    ┌──────────────┐    ┌──────────────┐                   │
│  │   OpenClaw    │    │    Hermes    │    │  MT5 MCP     │                   │
│  │   (Gateway)   │    │  (Telegram)  │    │  (if needed) │                   │
│  │   :18789      │    │              │    │              │                   │
│  └──────┬───────┘    └──────┬───────┘    └──────┬───────┘                   │
│         └───────────────────┼───────────────────┘                            │
│                             │                                                │
│                    ┌────────▼────────┐                                       │
│                    │   Workspace      │                                       │
│                    │   larger-lab/    │                                       │
│                    │   (synced)       │                                       │
│                    └─────────────────┘                                       │
└─────────────────────────────────────────────────────────────────────────────┘
```

## Agent Roles

| Agent | Machine | Role | Always-On? |
|-------|---------|------|------------|
| **Claude Code** | Local | Deep coding, file ops, git | No (session-based) |
| **OpenClaw** | Local | Task execution, automation, MCP | Yes (gateway) |
| **Hermes** | Local + Cloud | Telegram interface, scheduling | Yes (cron) |
| **OpenClaw** | Cloud | 24/7 agent, long-running tasks | Yes (gateway) |
| **Hermes** | Cloud | Cloud-side Telegram bot | Yes (if needed) |

## Communication

- **Shared Workspace:** Git repo + rclone sync keeps files in sync
- **Shared Memory:** MEMORY.md + USER.md synced via git
- **Task Handoff:** Orchestrator on local delegates to cloud agents via SSH
- **Notifications:** Hermes Telegram bot reports status from both machines

## Storage Strategy

| Data | Local | USB | Cloud |
|------|-------|-----|-------|
| Code/workspace | Hot | Warm mirror | Git backup |
| Market data | Hot | Warm mirror | Cold backup |
| Backtest results | Warm | Cold | Cold backup |
| Models | Warm | Cold | Cold backup |
| Agent memory | Hot | Warm mirror | Git backup |

## Free Cloud Options

| Provider | Free Tier | Specs | Notes |
|----------|-----------|-------|-------|
| **Oracle Cloud** | Always free | 4 ARM cores, 24GB RAM | Best option, always free |
| **GCP** | $300 credit | 1 e2-micro | 1 year trial |
| **AWS** | 12 months | 1 t2.micro | 1 year trial |
| **Hetzner** | None | - | Cheap paid option |

## Migration Checklist

- [ ] Provision Oracle Cloud free tier ARM instance
- [ ] SSH in and run `cloud-server-setup.sh`
- [ ] Set API keys on cloud server
- [ ] Clone workspace from GitHub
- [ ] Start OpenClaw gateway on cloud
- [ ] Set up SSH tunnel from local to cloud
- [ ] Configure rclone for cloud sync
- [ ] Test: Hermes on cloud can access workspace
- [ ] Test: Local OpenClaw can delegate to cloud agent

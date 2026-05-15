# USB Cloud Agent Network — Architecture

> **Goal:** Extend the agent workspace across USB drives + free cloud tiers so agents (OpenClaw, Hermes, Claude Code) have unlimited storage and can run from any machine.
> **Philosophy:** Structure over tools. The storage layer is decoupled from the agent layer. Agents don't care where files live.

---

## Problem

- Local disk fills up with market data, backtest results, models, logs
- USB drives sit idle as "extra storage" but aren't integrated
- Cloud costs money; free tiers are fragmented (15GB here, 20GB there)
- Agents need persistent access to workspace regardless of which machine they're on

## Solution: Hybrid USB + Cloud Storage Mesh

```
┌─────────────────────────────────────────────────────────────────────┐
│                     AGENT LAYER (unchanged)                         │
│  ┌──────────┐  ┌──────────┐  ┌──────────┐  ┌──────────────────┐   │
│  │ OpenClaw │  │  Hermes  │  │Claude Code│  │  Other Agents    │   │
│  └────┬─────┘  └────┬─────┘  └────┬─────┘  └───────┬──────────┘   │
│       └──────────────┼─────────────┼────────────────┘              │
│                      │             │                                │
│              ┌───────▼─────────────▼───────┐                       │
│              │   Virtual Workspace Layer    │                       │
│              │   (unified file access)      │                       │
│              └──────────────┬───────────────┘                       │
└─────────────────────────────┼───────────────────────────────────────┘
                              │
┌─────────────────────────────▼───────────────────────────────────────┐
│                     STORAGE MESH LAYER                               │
│                                                                      │
│  ┌─────────────────┐  ┌─────────────────┐  ┌─────────────────────┐  │
│  │  USB Drive 1     │  │  USB Drive 2     │  │  Local SSD          │  │
│  │  (active data)   │  │  (backup mirror) │  │  (hot cache)        │  │
│  │  /usb1/storage/  │  │  /usb2/storage/  │  │  ~/workspace/       │  │
│  └────────┬────────┘  └────────┬────────┘  └──────────┬──────────┘  │
│           │                    │                       │              │
│           └────────────────────┼───────────────────────┘              │
│                                │                                      │
│  ┌─────────────────────────────▼──────────────────────────────────┐  │
│  │                    Cloud Sync Layer (rclone)                    │  │
│  │  ┌────────────┐  ┌────────────┐  ┌────────────┐  ┌──────────┐  │  │
│  │  │ Google Drive│  │   MEGA     │  │  pCloud    │  │ GitHub   │  │  │
│  │  │  15GB free  │  │  20GB free │  │  10GB free │  │  LFS     │  │  │
│  │  └────────────┘  └────────────┘  └────────────┘  └──────────┘  │  │
│  └─────────────────────────────────────────────────────────────────┘  │
└──────────────────────────────────────────────────────────────────────┘
```

## Storage Tiers

| Tier | Location | Speed | Capacity | Use Case |
|------|----------|-------|----------|----------|
| **Hot** | Local SSD | Fastest | Limited | Active workspace, code, configs |
| **Warm** | USB Drive 1 | Fast | 100GB+ | Market data, backtest results, models |
| **Cold** | USB Drive 2 | Fast | 100GB+ | Backup mirror, archives |
| **Offsite** | Cloud (rclone) | Slow | 45GB+ free | Disaster recovery, remote access |

## How It Works

1. **Virtual Workspace Layer** — A FUSE mount or symlink farm that presents all storage as a single `~/workspace/` tree
2. **Smart Tiering** — Recent/hot data stays on SSD; older data auto-migrates to USB
3. **USB Sync** — When USB is plugged in, rsync mirrors data across drives
4. **Cloud Sync** — rclone pushes critical data to free cloud tiers in background
5. **Agent Transparency** — Agents read/write normally; the mesh handles placement

## Implementation Phases

### Phase 1: USB Storage Mesh (This Week)
- Detect and mount USB drives automatically
- Create unified storage directory structure
- Rsync-based mirroring between USB drives
- Symlink farm so agents see single workspace

### Phase 2: Cloud Tier Integration (Week 2)
- Set up rclone with free cloud providers
- Configure auto-sync for critical workspace files
- Git LFS for large files in version control

### Phase 3: Cloud Server Migration (Week 3)
- Provision free cloud VM (Oracle Cloud free tier, GCP free tier, etc.)
- Copy workspace to cloud server
- Install OpenClaw + Hermes on cloud server
- Agents run 24/7 regardless of local machine

### Phase 4: Agent Network (Week 4+)
- Multi-machine agent coordination
- Shared memory across local + cloud agents
- Hermes Telegram bot controls cloud agents

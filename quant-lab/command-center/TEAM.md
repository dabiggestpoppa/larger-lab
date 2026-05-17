# 🦉 OWL Command Center — Team Manifest

> **Operator:** OWL (Research Lead / OCE Operator)
> **Lead:** MAD (strategic anchor, attractor definer)
> **Domain:** CEREBUS Quant Trading System — `quant-lab/`
> **Scope:** Nautilus Trader port, backtesting, strategy implementation, pipeline optimization
> **Last Updated:** 2026-05-17

---

## ⚠️ OPERATOR RULES

See `~/Desktop/projects/larger-lab/OPERATOR_RULES.md` for complete rules. Key constraints:

- **Max 5 concurrent sub-agents** — prevents topology fragmentation
- **No unrestricted self-modification** — don't modify system prompts/safety rules
- **No infinite agent spawning** — sub-agents cannot spawn sub-agents
- **Repair before expansion** — stability > scale
- **Entropy governance** — compute, attention, sync are finite
- **All execution logged** — observable, replayable, reconstructable
- **MAD is strategic anchor** — MAD defines attractors, OWL executes
- **Do NOT post to `shared-conversations/team-chat.md`** unless MAD says so
- **Stay in lane:** quant-lab domain only. OCE/SRRA is CC's team's domain.

---

## OWL Sub-Agent Roster

These are spawned from OWL's session as needed. Each gets a label, a task file, and a results file.

| Label | Role | Domain | Output Dir |
|-------|------|--------|------------|
| `quant-researcher` | Research / Analysis | Manual extraction, strategy docs, gap analysis | `quant-lab/reports/` |
| `quant-optimizer` | Backtesting / Optimization | Bug fixes, parameter tuning, validation | `quant-lab/backtests/` |
| `quant-developer` | Implementation / Porting | Nautilus Trader code, API integration | `quant-lab/strategies/` |
| `quant-analyst` | Data / Pipeline | Data fetching, indicator calc, preprocessing | `quant-lab/research/` |

### Agent Lifecycle

```
SPAWN → TASK FILE CREATED → AGENT WORKS → RESULTS WRITTEN → OWL REVIEWS → ARCHIVE
```

1. OWL spawns sub-agent with `sessions_spawn`
2. Task details written to `quant-lab/command-center/tasks/{agent}-{timestamp}.md`
3. Agent works, writes results to designated output dir
4. Agent posts summary to `quant-lab/command-center/logs/{agent}-{timestamp}-result.md`
5. OWL reviews, updates progress, archives task file

---

## Communication Protocol

1. **OWL ↔ MAD:** Direct in this session (Signal/Telegram)
2. **OWL ↔ Sub-agents:** `sessions_spawn` task delegation, `subagents(list/steer/kill)` for management
3. **OWL → CC Team:** Read-only access to `srrs_opc/` and `oce/`. Don't modify. Reference only.
4. **Cross-domain:** If OCE integration needed, request via MAD (don't self-initiate with CC's team)

---

## Project: CEREBUS Quant System

### Phase Status

| Phase | Status | Description | Lead |
|-------|--------|-------------|------|
| Phase 0 (Manual Processing) | ✅ Complete | PDF extracted, PineScript saved, strategy guide created | OWL |
| Phase 1 (P90 Base Port) | 🔄 Next | Core P90 momentum expansion engine in Nautilus | TBD |
| Phase 2 (Cascade System) | Pending | Cascade activation logic, timing windows, 168% boundary | TBD |
| Phase 3 (45-Min Add) | Pending | Complementary add-on logic, combined with cascade | TBD |
| Phase 4 (P90P Tracker) | Pending | Distribution tracker, 3 checkpoints, regime detection | TBD |
| Phase 5 (Atomic Structure) | Pending | Density Zone, Phi scoring, Fixed Dollar Expectancy | TBD |
| Phase 6 (Integration) | Pending | Full system integration, end-to-end backtest | TBD |

### Key Files

| File | Purpose |
|------|---------|
| `quant-lab/reports/CEREBUS_v4_Manual_EXTRACTED.txt` | Full manual (194 pages) |
| `quant-lab/reports/P90_STRATEGY_GUIDE.md` | Implementation guide |
| `quant-lab/reports/STRATEGY_GAP_ANALYSIS.md` | Gap analysis (19 strategies) |
| `quant-lab/strategies/CEREBUS_V5_LIVE_PERFECT_FORM.pine` | PineScript V5 source |
| `quant-lab/backtests/p90_cascade_results.json` | Cascade backtest results |
| `progress/rl-progress.md` | OWL progress file |

### Source of Truth Hierarchy

1. **CEREBUS Manual v4.0 (PDF)** — primary source
2. **PineScript V5** — reference implementation
3. **Strategy Guide** — derived implementation notes
4. **Backtest Results** — empirical validation

---

## Memory Architecture

| Layer | File | Purpose |
|-------|------|---------|
| Working Memory | `quant-lab/command-center/memory/working.md` | Current session context, active tasks |
| Task History | `quant-lab/command-center/logs/` | Completed task results |
| Progress | `progress/rl-progress.md` | Synced to main progress system |
| Persistent | `MEMORY.md` / `progress/rl-memory.md` | Long-term memory |

---

## Directory Structure

```
quant-lab/
├── command-center/       # OWL's command center hub
│   ├── TEAM.md           # This file
│   ├── TASKS.md          # Active task board
│   ├── tasks/            # Individual task files
│   ├── memory/           # Working memory
│   └── logs/             # Task results & logs
├── backtests/            # Backtest scripts & results
├── config/               # Lab configuration
├── reports/              # Strategy docs, manual extractions
├── research/             # Research notes, data analysis
├── strategies/           # PineScript & Nautilus code
├── war-room/             # War room sessions
└── wiki/                 # Wiki/knowledge base
```

---

## Task Priority Queue

See `quant-lab/command-center/TASKS.md` for active tasks.

When MAD is away, OWL autonomously works through the queue:
1. Highest priority task first
2. Spawn appropriate sub-agent
3. Review results
4. Update progress
5. Mark complete, move to next

When MAD is present, MAD sets priority.

---

_Created 2026-05-17 by OWL. This is my command center. My rules. My team._

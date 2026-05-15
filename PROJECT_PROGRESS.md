# Project Progress & Context

> **Last Updated:** May 15, 2026
> **Maintain this file:** Update after every significant work session. This is the single source of truth for project state across long-horizon tasks.

---

## Architecture Update (May 15, 2026)

**MT5 is FULLY DEPRECATED for backtesting.** MetaEditor can't compile headlessly and Strategy Tester can't be automated. All strategy development and backtesting now runs through **NautilusTrader** (Python-based).

**Agent Network Architecture** replaces direct tool usage. Hermes and OpenClaw operate autonomously using workspace files as communication channels. The human sets direction; agents execute.

**Data pipeline:** `Downloads/*.csv` → `nautilus/data/*.parquet` → Nautilus backtest engine → `nautilus/reports/`
**Verification:** Oanda API data → same Nautilus strategy → cross-validate
**MT5 MCP server:** FULLY REMOVED. No MT5 dependencies remain in OpenClaw config. All backtesting is Nautilus-only.

**Core Architecture Principles:**
- **Structure over tools.** The storage layer is decoupled from the agent layer.
- **Thin harness, thick model** — Let agents internalize capabilities; explicit harness only for safety-critical paths
- **Decoupled layers** — Human Interface ↔ MCP Protocol ↔ Nautilus Engine ↔ Agent Orchestration
- **Independent tools** — Each tool does one thing. Adding tools doesn't affect existing ones
- **Verification at every step** — Each agent runs verification loops before passing to next step
- **3-tier memory** — Tier 1 (MEMORY.md/USER.md), Tier 2 (SQLite FTS5), Tier 3 (vector store)
- **Self-evolving skills** — Repeated patterns become SKILL.md files; Curator prunes stale ones
- **Hybrid storage** — Local SSD (hot) → USB drives (warm/cold) → Cloud (offsite). Agents don't care where files live.
- **Errors are data** — Every failure is a signal that the system's model of reality is wrong. The repair mechanism captures, classifies, fixes, validates, and learns.

---

## Active Cloud Infrastructure

### Hetzner Cloud (Primary Cloud Server)
- **Account:** dabiggestpoppa@gmail.com / Client K0223247625
- **Server:** larger-lab-cloud (CPX31: 4 vCPU, 8GB RAM, 160GB NVMe)
- **Location:** fsn1 (Falkenstein, Germany)
- **Cost:** ~€8.50/month
- **Status:** Setup script ready, awaiting API token
- **Credentials:** ~/.larger-lab/hetzner-credentials.env (NOT in repo)

### Gmail Connector
- **Account:** kemettrucking@gmail.com
- **Purpose:** OpenClaw email access, trading notifications
- **Setup:** `GMAIL_CONNECTOR.md` has 3 options (Gmail MCP, rclone, Python API)
- **Status:** Pending OAuth setup

### Hetzner CLI
- **Version:** 1.64.1 installed
- **Command:** hcloud
- **Setup script:** `usb-cloud/hetzner-setup.sh`
- **Tunnel script:** `usb-cloud/tunnel-to-cloud.ps1`

---

## Agent Runtime: Hermes + OpenClaw + Claude Code

| Agent | Role | Interface | Status |
|-------|------|-----------|--------|
| **Hermes** | On-the-go agent | Telegram | Configured (.hermes/) |
| **OpenClaw** | Messaging-first agent | CLI + Gateway | Installed & Running |
| **Claude Code** | Desk-based coding | VS Code | Active (this session) |

### OpenClaw Config
- **Version:** 2026.5.7
- **Workspace:** `C:\Users\wifik\Desktop\projects\larger-lab`
- **Gateway:** `ws://127.0.0.1:18789`
- **Model:** anthropic/claude-sonnet-4-20250514
- **Config:** `~/.openclaw/openclaw.json`
- **MCP:** Nautilus tools configured
- **Skills:** `.hermes/skills/` + `nautilus/` loaded

---

## Completed

### Workspace Infrastructure
- [x] CLAUDE.md — 12-rule behavioral contract
- [x] SOUL.md — Agent identity layer
- [x] AGENTS.md — Team manifest with harness architecture
- [x] All 8 agent specs updated (orchestrator, architect, debugger, memory-engineer, qa, devops, research, code-reviewer)
- [x] .hermes/ directory (MEMORY.md, USER.md, SOUL.md, skills)
- [x] 3 Hermes skills (goal-mode, hermes-maintenance, github-backup)
- [x] .cursor/rules/karpathy-guidelines.mdc
- [x] WORKFLOW.md updated with harness-aware phases

### Agent Network Architecture (May 15, 2026)
- [x] `SYSTEM_ARCHITECTURE.md` — System constitution, agent roles, data flow, error handling, continuous improvement
- [x] `WORKFLOW_PROTOCOL.md` — Task lifecycle, handoff rules, reporting standards, error protocol
- [x] `TASK_BRIEF_TEMPLATE.json` — Standardized task definition format
- [x] `ERROR_CLASSIFICATION.md` — Error severity levels and auto-repair rules
- [x] `error_log.json` — Centralized error tracking
- [x] `agent-lab/agents/hermes/hermes_workspace/agent_prompt.md` — Hermes mission instructions (Nautilus, no MT5)
- [x] `.openclaw/openclaw_prompt.md` — OpenClaw mission instructions (coordinate with Hermes, archive MT5)
- [x] `agent-lab/agents/hermes/hermes_progress_summary.json` — Hermes execution log
- [x] `.openclaw/openclaw_progress_summary.json` — OpenClaw planning log

### MT5 MCP Server (FULLY ARCHIVED — May 15 2026)
- [x] `mt5_mcp_server.py` — 13 tools [FULLY ARCHIVED — removed from openclaw.json MCP servers]
- [x] `controller_ea.mq5` — Helper EA [ARCHIVED]
- [x] `ARCHITECTURE.md` — Full architecture doc [ARCHIVED]
- [x] `skills/mt5-strategy-builder.md` — Agent skill [ARCHIVED]
- [x] `mcp-config-stdio.json` + `mcp-config-sse.json` [ARCHIVED]
- [x] TOOLS.md — OpenClaw tools reference [ARCHIVED]
- [x] `mt5-mcp/skills/` removed from OpenClaw skills load path
- [x] MCP servers section in openclaw.json cleared (was: mt5, now: {})

### OpenClaw Setup
- [x] Node.js 24 confirmed installed
- [x] OpenClaw 2026.5.7 installed globally
- [x] `openclaw onboard` completed with workspace pointing to larger-lab
- [x] Nautilus tools configured in `~/.openclaw/openclaw.json`
- [x] Skills directories registered (`.hermes/skills/`)
- [x] **Model routing configured** (May 15 2026):
  - Default/Orchestrator: `nvidia/nemotron-3-nano-omni-30b-a3b-reasoning:free` (Nvidia Nemo Nano Omni 3)
  - Orchestration fallback (1 rate limit): `inclusionai/ring-2.6-1t:free` (Inclusion AI)
  - Orchestration fallback (2 consecutive rate limits): `openrouter/owl-alpha` (Owl Alpha)
  - Planning/Error Handling: `deepseek/deepseek-v4-flash:free` (DeepSeek V4 Flash) → `openrouter/owl-alpha` fallback
  - Coding/Working: `poolside/laguna-m.1:free` (Laguna M.1) → `openrouter/owl-alpha` fallback
  - Code Review: `inclusionai/ring-2.6-1t:free` (Inclusion AI) → `arcee-ai/trinity-large-thinking:free` (Trinity Large Thinking) backup
  - **2-attempt rate limit switch enforced** — agents never stall mid-build
- [x] Gateway running on port 18789

### USB Cloud Storage Mesh
- [x] `usb-cloud/ARCHITECTURE.md` — Hybrid storage architecture
- [x] `usb-cloud/usb-mesh.ps1` — USB detection, sync, cloud sync script
- [x] `usb-cloud/cloud-server-setup.sh` — Cloud server provisioning script
- [x] `usb-cloud/agent-network.md` — Multi-machine agent coordination
- [x] USB drives detected: D:\ (backup, 57.3GB) and E:\ (57.3GB)
- [x] Storage directories initialized on both USB drives
- [ ] Initial workspace → USB sync (run `usb-mesh.ps1 sync`)
- [ ] Cloud tier setup (rclone config for Google Drive, MEGA, pCloud)
- [ ] Cloud server provisioning (Oracle Cloud free tier)

---

## Immediate Priority: Nautilus Backtest Pipeline

### Phase 1: Data Prep
- [x] CSV data files identified in Downloads (29 files, all major pairs, M1/M5, 2022-2026)
- [x] Data prep script created (`nautilus/step1_prep_data.py`)
- [ ] **Agent task:** OpenClaw verifies CSV inventory → Hermes runs `step1_prep_data.py` → verify parquet output

### Phase 2: Strategy Implementation
- [x] Symmetry Trap strategy already implemented (`nautilus/strategies/symmetry_trap.py`)
- [x] EMA Cross strategy already implemented (`nautilus/strategies/ema_cross.py`)
- [ ] **Agent task:** OpenClaw extracts Option B rules from manual → Hermes implements as Nautilus Python strategy
- [ ] **Agent task:** OpenClaw extracts Option A rules from manual → Hermes implements as Nautilus Python strategy
- [ ] **Agent task:** Hermes builds parameter optimization loop (grid/random search over Nautilus backtests)

### Phase 3: Backtest + Optimize
- [ ] **Agent task:** Hermes runs `run_all_backtests.py` across all prepared pairs (EURUSD, GBPUSD, USDJPY, AUDUSD)
- [ ] **Agent task:** Hermes executes parameter sweeps per strategy per pair
- [ ] **Agent task:** OpenClaw collects and ranks results → produces recommendation brief

### Phase 4: Oanda Verification
- [ ] **Agent task:** Hermes fetches Oanda data via `oanda_adapter.py` → runs identical strategies → compares with CSV-based results

---

## Mid-Term: Cloud Server + USB Sync

### Phase 1: USB Sync (This Week)
- [ ] **Agent task:** OpenClaw executes `usb-mesh.ps1 sync` → verifies bidirectional sync → reports

### Phase 2: Cloud Accounts (Week 2)
- [ ] **Agent task:** OpenClaw researches cloud providers → overseer approves → proceeds
- [ ] Sign up Oracle Cloud free tier (24GB RAM ARM) — PRIORITY
- [ ] Sign up GCP free trial ($300, 90 days, 16GB RAM)
- [ ] Sign up AWS free tier (1GB RAM, 12 months)
- [ ] Create ProtonMail emails for each provider

### Phase 3: Cloud Deployment (Week 3)
- [ ] **Agent task:** OpenClaw provisions Oracle Cloud → runs `cloud-server-setup.sh` → deploys workspace → installs agent runtimes → tests SSH tunnel

### Phase 4: Agent Distribution (Week 4)
- [ ] **Agent task:** OpenClaw distributes agent runtimes across cloud instances → configures cron jobs → verifies all nodes report healthy
- Oracle ARM (24GB): Main agent rig — OpenClaw + Hermes + Nautilus
- Oracle Micro x2 (1GB each): Monitoring, cron jobs, backups
- GCP (16GB): Burst workloads, heavy backtests
- AWS (1GB): Hermes Telegram bot, notifications
- Local: Claude Code + OpenClaw for development

---

## Continuous Improvement Framework

### How the System Improves Itself
1. **Every backtest result is stored** with full parameters → enables optimization over time
2. **Failed strategies are analyzed** for patterns → inform future strategy design
3. **Agent prompts are versioned** → improvements tracked, rollback possible
4. **Error log drives fixes** → recurring errors trigger structural improvements
5. **Weekly review cycle** — agents flag issues, overseer approves architectural changes

### Error Repair Loop
```
ERROR DETECTED → ROOT CAUSE ANALYSIS → CLASSIFY:
  ├── ONE-OFF → Retry, log, move on
  ├── RECURRING (3+) → SYSTEM FIX: agent proposes + implements structural change
  │       └── VALIDATE: re-run same task → DOCUMENT fix
  └── STRUCTURAL (design flaw) → Escalate to overseer → Redesign component
```

See `SYSTEM_ARCHITECTURE.md` Section 5 for full error classification and repair protocol.

---

## Mid-Term: Twitter AI Research Bot

### Objective
Autonomous Twitter bot that scrapes for latest AI advancements and best practices, feeding findings back into the agent system.

### Architecture
```
┌──────────────────────────────────────────────────┐
│           Twitter AI Research Bot                 │
├──────────────────────────────────────────────────┤
│  ┌──────────────┐  ┌──────────────┐  ┌─────────┐ │
│  │ Twitter       │  │ AI Content   │  │ Memory  │ │
│  │ Scraper       │  │ Ranker       │  │ Writer  │ │
│  │ (tweepy/API)  │  │ (LLM filter) │  │         │ │
│  └──────┬───────┘  └──────┬───────┘  └────┬────┘ │
│         │                │               │        │
│         └────────────────┼───────────────┘        │
│                          │                        │
│  ┌───────────────────────▼──────────────────────┐ │
│  │  Hermes / OpenClaw Agent                      │ │
│  │  - Receives ranked AI content                │ │
│  │  - Extracts patterns → SKILL.md              │ │
│  │  - Updates MEMORY.md with findings           │ │
│  └──────────────────────────────────────────────┘ │
└──────────────────────────────────────────────────┘
```

### Implementation Plan
1. Create Twitter scraper skill using tweepy
2. Add AI content ranking/filtering logic
3. Integrate with Hermes memory system
4. Deploy as scheduled cron job (Hermes cron or OpenClaw cron)

### Expected Benefits
- Continuous AI best practices ingestion
- Automatic skill generation from discovered patterns
- Reduced manual research overhead
- Performance boost from staying current

---

## Key Reference Files

| File | Purpose |
|------|---------|
| `CLAUDE.md` | 12-rule behavioral contract |
| `SOUL.md` | Agent identity layer |
| `AGENTS.md` | Team manifest |
| `SYSTEM_ARCHITECTURE.md` | System constitution — start here |
| `WORKFLOW_PROTOCOL.md` | Task lifecycle and handoff rules |
| `ERROR_CLASSIFICATION.md` | Error severity and repair rules |
| `TASK_BRIEF_TEMPLATE.json` | Task definition template |
| `TOOLS.md` | OpenClaw tools reference |
| `PROJECT_PROGRESS.md` | This file — project state |
| `.agents/AGENTS.md` | Full agent team spec |
| `.hermes/MEMORY.md` | Hermes persistent memory |
| `.hermes/SOUL.md` | Hermes identity |
| `nautilus/` | Nautilus strategies, data, reports |
| `usb-cloud/ARCHITECTURE.md` | USB cloud storage architecture |
| `usb-cloud/usb-mesh.ps1` | USB sync script |
| `usb-cloud/cloud-server-setup.sh` | Cloud server provisioning |
| `usb-cloud/agent-network.md` | Multi-machine agent coordination |
| `~/.openclaw/openclaw.json` | OpenClaw config |

---

## Agent Runtime: Hermes + OpenClaw + Claude Code

| Agent | Role | Interface | Status |
|-------|------|-----------|--------|
| **Hermes** | Execution agent — implements strategies, runs backtests, reports results | Telegram + workspace files | Configured |
| **OpenClaw** | Analysis agent — parses manuals, plans tasks, prepares data, reviews results | CLI + Gateway (port 18789) | Running |
| **Claude Code** | Overseer/CEO — architecture decisions, quality gates, task delegation | VS Code | Active (this session) |

### OpenClaw Config
- **Version:** 2026.5.7
- **Workspace:** `C:\Users\wifik\Desktop\projects\larger-lab`
- **Gateway:** `ws://127.0.0.1:18789`
- **Model:** anthropic/claude-sonnet-4-20250514
- **Config:** `~/.openclaw/openclaw.json`
- **MCP:** Nautilus tools configured
- **Skills:** `.hermes/skills/` + `nautilus/` loaded

---

## P90 Manual Strategies Results (2026-05-15)
- P90_CFD_Expansion: 0.0% return, 165 trades
- Symmetry_Trap: 0.0% return, 0 trades


## P90 Manual Strategies Results (2026-05-15 03:51:58)
- P90_CFD_Expansion: 0.0% return, 165 trades
- Symmetry_Trap: 0.0% return, 0 trades


## P90 Manual Strategies Results (2026-05-15 03:55:14)
- P90_CFD_Expansion: -0.0% return, 268 trades
- Symmetry_Trap: -0.0% return, 236 trades


## P90 Manual Strategies Results (2026-05-15 03:55:49)
- P90_CFD_Expansion: -0.0% return, 268 trades
- Symmetry_Trap: -0.0% return, 236 trades


## Hermes Autopilot v2 Update (2026-05-15 04:18:45.866009)
- Iteration: 1
- Profitable strategies found: 2/5
  - P90_CFD_Expansion (USDJPY): 0.01% (232 trades, 6.98 pips PnL)
  - RSI_Reversion (USDJPY): 0.01% (352 trades, 5.18 pips PnL)

## Strategy Logic Fixes (2026-05-15)
- ✅ Fixed P90 exit logic: now exits at -25% pullback (mean reversion) instead of +25% extension
- ✅ Fixed position sizing: 10 micro lots (0.1 standard lots) with proper pip value calculation
- ✅ Fixed Symmetry Trap exit: same -25% pullback logic
- ✅ Updated hermes_autopilot_v3.py with corrected logic

### Status
- ✅ Hermes autopilot v2 created and executed
- ✅ Found 2 profitable strategies on USDJPY
- ✅ Position sizing fixed (10 micro lots per trade)
- ✅ Strategy exit logic corrected (mean reversion at -25% Asian Range)
- ⏳ Need to run again to find 3 more profitable strategies

### Next Steps
- Run autopilot v3 to find 3 more profitable strategies
- Verify EUR/USD data availability for P90 backtest

---

## XHAAK / Kulu → Current Implementation Bridge (May 15, 2026)

### Context
Full archival review of USB drive contents (E:\) and legacy desktop folder (`KULU XHAAK AGENTS OLD IDEAS`) completed. ~40+ files catalogued across four systems: **Kulu** (sovereign AI swarm), **XHAAK Phase 3** (Genesis Rebirth protocols), **Cerebus FX** (trading strategy system), and **supporting infrastructure** docs.

### What Already Exists (60–70% of old vision realized)
| Old Concept | Current Equivalent | Status |
|---|---|---|
| GSP (Genesis Swarm Protocol) | OpenClaw + Hermes agent network | ✅ Partially realized |
| Cerebus Dialectic Brain Mode | Parallel Thought Synthesis (OpenRouter) | ✅ Operational |
| LocalAGI Foundation | OpenClaw gateway on :18789 | ✅ Operational |
| Multi-tier Cloud Nodes | Hetzner CX31 ready, Oracle planned | ✅ Infrastructure ready |
| Stigmergic Memory | MEMORY.md + SQLite FTS5 + vector store | ✅ Partially realized |
| xhaakctl CLI | OpenClaw CLI + PowerShell scripts | ✅ Partially realized |
| Cerebus FX Strategies | Nautilus Trader (8 strategies) | ✅ Implemented |
| USB Cloud Storage Mesh | usb-cloud/ scripts + sync | ✅ Operational |
| Agent specs & roles | agent-lab/ (8 agents defined) | ✅ Scaffolded |

### What Still Needs Building (Gap Analysis)
| Missing Component | Priority | Implementation Path |
|---|---|---|
| **FMP Protocol** (Clarity-Outcome Delta tracking) | 🔴 HIGH | Encode as system prompt + MEMORY.md audit pattern |
| **SCOPE Protocol** (Breathfold Recursion) | 🟡 MEDIUM | LangGraph chain in OpenClaw skill |
| **GSP Full Swarm Behavior** | 🟡 MEDIUM | Structured JSON glyph messages between agents |
| **Browser Ritual Agent** | 🟡 MEDIUM | Playwright skill triggered via Hermes Telegram |
| **Glyph Communication** | 🟢 LOW | JSON envelope schema for agent-to-agent messages |
| **ZeroConf Agent Discovery** | 🟢 LOW | Defer — OpenClaw gateway handles routing |
| **Kulu Containerized Orchestration** | ⚪ DEFERRED | Overkill at current scale |
| **Tailscale Mesh Networking** | ⚪ DEFERRED | Single cloud instance sufficient for now |
| **DSPy Optimization Loop** | 🟡 MEDIUM | Post-backtest validation phase |
| **Nightly LoRA Training** | ⚪ DEFERRED | Requires GPU burst infrastructure |

### Recommended Implementation Phases
**Phase 1 (Now):** Consolidate — wire Hermes to trigger Nautilus backtests, collect results, iterate
**Phase 2 (Week 2–3):** Cerebus Dialectic Brain — dual-model reasoning loop via OpenClaw prompts
**Phase 3 (Week 3–4):** FMP Protocol — system prompt + memory audit pattern
**Phase 4 (Week 4–6):** GSP-Lite — structured agent communication + task routing skill
**Phase 5 (Week 6–8):** Browser Ritual Agent — Playwright web automation skill

### Key Insight
The old XHAAK/Kulu vision was designed for a world without OpenClaw or Hermes. Today, these platforms provide 60–70% of the desired capability natively. The remaining gaps (FMP, SCOPE, GSP core) can be implemented as **agent prompt patterns and skills** rather than standalone microservices — dramatically reducing complexity while preserving the philosophical architecture.

### Reference
- Full USB file inventory: `usb-cloud/xhaak-kulu-inventory.md`
- Old architecture docs preserved in: `usb-cloud/` (40+ files)
- Synthesis roadmap: `xhaak-kulu-bridge-progress.md` (this work stream's tracker)

---

## XHAAK/Kulu Bridge Phase 1 Update (2026-05-15 14:00:00Z)
- **Status:** ⏳ In Progress
- **Task:** FMP Protocol implementation (XKB-001)
- **Actions:**
  - Created `tasks/xhaak-kulu-bridge-phase1-fmp.json` task brief
  - Updated OpenClaw prompt with FMP/SCOPE/GSP-Lite directives
  - Updated Hermes prompt with bridge-building responsibilities
  - Updated both progress summaries with Phase 1 entry
- **Next:** OpenClaw implements CØD logging pattern in MEMORY.md and creates `fmp_audit.py`

---


## Hermes Autopilot v2 Update (2026-05-15 04:37:25.170833)
- Iteration: 2
- Profitable strategies found: 2/5
  - P90_CFD_Expansion (USDJPY): 0.01%
  - RSI_Reversion (USDJPY): 0.01%


## Hermes Autopilot v2 Update (2026-05-15 04:56:04.027615)
- Iteration: 3
- Profitable strategies found: 2/5
  - P90_CFD_Expansion (USDJPY): 0.01%
  - RSI_Reversion (USDJPY): 0.01%


## Strategy Logic Fixes Completed (2026-05-15)
### P90 CFD Expansion & Symmetry Trap - Exit Logic Corrected
**Problem:** Strategies were exiting at +25% Asian Range extension instead of -25% pullback (mean reversion)

**Fix Applied:**
- `nautilus/p90_backtest.py` - Line 117: Changed `target = entry_price + direction * range * 0.25` to `target = entry_price - direction * range * 0.25`
- `nautilus/hermes_autopilot_v3.py` - Same fix applied to both P90 and Symmetry Trap
- `nautilus/hermes_simple.py` - Same fix applied

**Position Sizing Fixed:**
- All strategies now use 10 micro lots (0.1 standard lots)
- PnL calculation: `(price_diff * 0.1 * 10000)` for proper pip value

### Data Status
- CSV files were present in Downloads during earlier runs (27 files found)
- Data prep script (`step1_prep_data.py`) found files but parsing failed
- Need to verify CSV format and re-run data prep


## Hermes Autopilot v2 Update (2026-05-15 06:32:29.418966)
- Iteration: 4
- Profitable strategies found: 2/5
  - P90_CFD_Expansion (USDJPY): 0.01%
  - RSI_Reversion (USDJPY): 0.01%


## Hermes Autopilot v2 Update (2026-05-15 06:53:34.559359)
- Iteration: 5
- Profitable strategies found: 2/5
  - P90_CFD_Expansion (USDJPY): 0.01%
  - RSI_Reversion (USDJPY): 0.01%


## Hermes Autopilot v2 Update (2026-05-15 07:11:51.505048)
- Iteration: 6
- Profitable strategies found: 2/5
  - P90_CFD_Expansion (USDJPY): 0.01%
  - RSI_Reversion (USDJPY): 0.01%


## Hermes Autopilot v2 Update (2026-05-15 07:30:09.371865)
- Iteration: 7
- Profitable strategies found: 2/5
  - P90_CFD_Expansion (USDJPY): 0.01%
  - RSI_Reversion (USDJPY): 0.01%


## Hermes Autopilot v2 Update (2026-05-15 07:48:55.221183)
- Iteration: 8
- Profitable strategies found: 2/5
  - P90_CFD_Expansion (USDJPY): 0.01%
  - RSI_Reversion (USDJPY): 0.01%


## P90 Manual Strategies Results (2026-05-15 07:49:47.807281)
- P90_CFD_Expansion: 0.09% return, 263 trades
- Symmetry_Trap: -1.77% return, 236 trades


## Hermes Autopilot v2 Update (2026-05-15 08:04:40.315539)
- Iteration: 9
- Profitable strategies found: 2/5
  - P90_CFD_Expansion (USDJPY): 0.01%
  - RSI_Reversion (USDJPY): 0.01%


## Hermes Autopilot v2 Update (2026-05-15 08:20:29.554523)
- Iteration: 10
- Profitable strategies found: 2/5
  - P90_CFD_Expansion (USDJPY): 0.01%
  - RSI_Reversion (USDJPY): 0.01%


## Hermes Autopilot v2 Update (2026-05-15 08:38:03.582883)
- Iteration: 11
- Profitable strategies found: 2/5
  - P90_CFD_Expansion (USDJPY): 0.01%
  - RSI_Reversion (USDJPY): 0.01%


## Backup & Portability Pipeline (2026-05-15)
- ✅ Created `backup-workspace.ps1` - Complete backup to USB + Git + Cloud
- ✅ Created `backup.bat` - Wrapper to bypass PowerShell execution policy
- ✅ Created `restore-workspace.ps1` - Restore on new computer from USB/Git
- ✅ Created `restore.bat` - Wrapper for restore
- ✅ Created `quick-setup.ps1` - One-command fresh setup on new machine
- ✅ Created `BACKUP_README.md` - Documentation
- ✅ Tested backup: Successfully pushed to GitHub + synced to USB drives (D: and E:)
- ✅ USB sync working: data/, models/, backtests/, strategies/, notebooks/, nautilus/data/

### Usage
```powershell
# Backup everything
.\backup.bat -FullBackup

# Restore on new computer
.\restore.bat -Source Both

# One-command fresh setup
curl -fsSL https://raw.githubusercontent.com/dabiggestpoppa/larger-lab/main/quick-setup.ps1 | pwsh -File -
```

## Pine Strategy Conversion (2026-05-15)
- ✅ Received P90 base strategy (CEREBUS V5) - 649 lines of Pine Script
- ✅ Strategy includes: Asian Range P90 system, tier-based thresholds, position sizing, mean reversion exits
- ✅ Key functions identified for Nautilus conversion:
  - Asian Range calculation (19:00-03:00 EST)
  - P90 bull/bear signal detection (2-11 AM EST)
  - Tier-based target calculation (T1/T2/T3)
  - Position 1/2/3 entry logic with 45-min add
  - Mean reversion exits at -25% pullback
  - 132% violation stop-out
  - Daily drawdown protection
- ⏳ Next: Extract core logic into Nautilus Python strategy


## Hermes Autopilot v2 Update (2026-05-15 08:57:15.936543)
- Iteration: 12
- Profitable strategies found: 2/5
  - P90_CFD_Expansion (USDJPY): 0.01%
  - RSI_Reversion (USDJPY): 0.01%


## Hermes Autopilot v2 Update (2026-05-15 09:16:34.863114)
- Iteration: 13
- Profitable strategies found: 2/5
  - P90_CFD_Expansion (USDJPY): 0.01%
  - RSI_Reversion (USDJPY): 0.01%


## Hermes Autopilot v2 Update (2026-05-15 09:33:04.377789)
- Iteration: 14
- Profitable strategies found: 2/5
  - P90_CFD_Expansion (USDJPY): 0.01%
  - RSI_Reversion (USDJPY): 0.01%


## 🔥 LARGER BUILD PLAN - PHASE 1 INITIATED (2026-05-15)

### Objective
Build the complete agentic trading system with P90 strategy converted to Nautilus, full backup pipeline, and cloud deployment ready.

### Phase 1: Pine → Nautilus Conversion (IN PROGRESS)
- [ ] Extract P90 core logic from Pine Script (649 lines)
- [ ] Create `nautilus/strategies/p90_cerebus_v5.py`
- [ ] Implement Asian Range calculation (19:00-03:00 EST)
- [ ] Implement P90 signal detection (2-11 AM EST)
- [ ] Implement tier-based targets (T1/T2/T3)
- [ ] Implement position 1/2/3 logic with 45-min add
- [ ] Implement mean reversion exits (-25% pullback)
- [ ] Implement 132% violation stop-out
- [ ] Test with `hermes_autopilot_v3.py`

### Phase 2: Data Pipeline (READY)
- [ ] Verify CSV data in Downloads (29 files)
- [ ] Run `nautilus/step1_prep_data.py`
- [ ] Convert to parquet format
- [ ] Verify data integrity

### Phase 3: Backtest & Optimize
- [ ] Run P90 strategy on EURUSD, GBPUSD, USDJPY
- [ ] Parameter sweep for optimal thresholds
- [ ] Generate performance reports

### Phase 4: Cloud Deployment
- [ ] Provision Oracle Cloud ARM (24GB RAM)
- [ ] Deploy workspace via `agent-setup.sh`
- [ ] Configure SSH tunnel
- [ ] Test agent connectivity

### Phase 5: Full System Integration
- [ ] Connect Hermes Telegram bot
- [ ] Set up cron jobs for daily backtests
- [ ] Configure alerts for profitable signals
- [ ] Document full workflow

### Success Criteria
- P90 strategy running in Nautilus with positive expectancy
- Backup/restore working on any computer
- Cloud instance accessible from anywhere
- Agents can run autonomously 24/7

---

## 🗺️ CODE MAP & ARCHITECTURE DIAGRAMS

### System Architecture Overview

```mermaid
graph TB
    subgraph "Human Interface Layer"
        A[Claude Code<br/>VS Code] --> B[OpenClaw<br/>CLI Gateway :18789]
        C[Hermes<br/>Telegram Bot] --> B
    end

    subgraph "Agent Orchestration Layer"
        B --> D[Orchestrator Agent]
        D --> E[Hermes Agent<br/>Execution]
        D --> F[OpenClaw Agent<br/>Analysis]
        D --> G[Memory Engineer<br/>Persistence]
        D --> H[Code Reviewer<br/>Quality Gate]
    end

    subgraph "Data & Strategy Layer"
        I[Downloads/*.csv<br/>29 data files] --> J[nautilus/step1_prep_data.py]
        J --> K[nautilus/data/*.parquet]
        K --> L[Nautilus Trader<br/>Backtest Engine]
        L --> M[nautilus/reports/]
    end

    subgraph "Storage Layer"
        N[Local SSD<br/>Hot Data] --> O[USB Drives<br/>D: & E: 57GB each]
        O --> P[GitHub<br/>Source Control]
        P --> Q[Cloud Storage<br/>Google Drive/MEGA/pCloud]
    end

    subgraph "External Services"
        R[Oanda API<br/>Verification Data] --> L
        S[Hetzner Cloud<br/>Primary Server] --> T[Oracle Cloud<br/>ARM 24GB]
        U[Gmail<br/>Notifications] --> C
    end

    B <--> K
    E <--> L
    F <--> J
    G <--> M
    H <--> M
```

### Agent Network Communication Flow

```mermaid
sequenceDiagram
    participant H as Human
    participant CC as Claude Code
    participant OC as OpenClaw
    participant HM as Hermes
    participant NT as Nautilus Trader
    participant MEM as Memory Engineer

    H->>CC: Set Direction / Review
    CC->>OC: Task Brief (JSON)
    OC->>HM: Execute Strategy
    HM->>NT: Run Backtest
    NT->>MEM: Store Results
    MEM->>OC: Analysis Report
    OC->>CC: Progress Update
    CC->>H: Status Report
```

### Data Pipeline Flow

```mermaid
flowchart LR
    subgraph "Input"
        A[Downloads/*.csv<br/>29 files<br/>M1/M5 2022-2026]
    end

    subgraph "Processing"
        B[nautilus/step1_prep_data.py<br/>CSV → Parquet]
        C[Data Validation<br/>Schema Check]
        D[Feature Engineering<br/>Asian Range, P90 Signals]
    end

    subgraph "Execution"
        E[Nautilus Trader<br/>Backtest Engine]
        F[Parameter Sweep<br/>Grid/Random Search]
    end

    subgraph "Output"
        G[nautilus/reports/<br/>Performance Metrics]
        H[MEMORY.md<br/>Strategy Results]
        I[GitHub<br/>Version Control]
    end

    A --> B --> C --> D --> E --> F --> G
    G --> H
    H --> I
```

### Backup & Restore Architecture

```mermaid
graph LR
    subgraph "Backup Sources"
        A[larger-lab workspace]
        B[nautilus/data/]
        C[nautilus/reports/]
        D[models/]
        E[backtests/]
    end

    subgraph "Backup Targets"
        F[USB Drive D:<br/>57.3GB]
        G[USB Drive E:<br/>57.3GB]
        H[GitHub<br/>master branch]
        I[Cloud Storage<br/>rclone sync]
    end

    subgraph "Scripts"
        J[backup-workspace.ps1]
        K[restore-workspace.ps1]
        L[quick-setup.ps1]
    end

    A --> J
    B --> J
    C --> J
    D --> J
    E --> J

    J --> F
    J --> G
    J --> H
    J --> I

    K --> A
    L --> A
```

### P90 Strategy Logic Flow

```mermaid
flowchart TD
    A[Market Opens<br/>19:00 EST] --> B[Calculate Asian Range<br/>19:00-03:00 EST]
    B --> C[Range = High - Low]
    C --> D[Set Thresholds<br/>T1=90%, T2=110%, T3=132%]

    D --> E[Signal Window<br/>02:00-11:00 EST]
    E --> F{Price Action}
    F -->|Breaks T1| G[Bull Signal]
    F -->|Breaks -T1| H[Bear Signal]

    G --> I[Position 1 Entry]
    H --> I

    I --> J[45-min Timer]
    J --> K{Price Action}
    K -->|Breaks T2| L[Position 2 Add]
    K -->|Breaks T3| M[Position 3 Add]
    K -->|Pullback -25%| N[Mean Reversion Exit]
    K -->|Time Expiry| O[Close All]

    L --> K
    M --> K
```

### XHAAK/Kulu Bridge Architecture

```mermaid
graph TB
    subgraph "Legacy Concepts"
        A[GSP - Genesis Swarm Protocol]
        B[FMP - Clarity-Outcome Delta]
        C[SCOPE - Breathfold Recursion]
        D[Kulu Containerized Orchestration]
    end

    subgraph "Current Implementation"
        E[OpenClaw + Hermes<br/>Agent Network]
        F[MEMORY.md + SQLite FTS5<br/>Stigmergic Memory]
        G[OpenRouter Parallel<br/>Dialectic Brain]
        H[USB Cloud Mesh<br/>Multi-node Storage]
    end

    subgraph "Bridge Status"
        I[60-70% Realized]
        J[FMP Protocol<br/>Prompt Pattern]
        K[SCOPE Protocol<br/>LangGraph Chain]
        L[GSP-Lite<br/>JSON Glyph Messages]
    end

    A -.-> E
    B -.-> J
    C -.-> K
    D -.-> H

    E --> I
    F --> I
    G --> I
    H --> I

    I --> J
    I --> K
    I --> L
```

### File Structure Map

```mermaid
graph TD
    A[larger-lab/] --> B[nautilus/]
    A --> C[usb-cloud/]
    A --> D[agent-lab/]
    A --> E[.hermes/]
    A --> F[models/]
    A --> G[backtests/]
    A --> H[data/]

    B --> B1[strategies/]
    B --> B2[data/]
    B --> B3[reports/]
    B1 --> B1a[symmetry_trap.py]
    B1 --> B1b[ema_cross.py]
    B1 --> B1c[p90_cerebus_v5.py]

    C --> C1[usb-mesh.ps1]
    C --> C2[cloud-server-setup.sh]
    C --> C3[agent-network.md]

    D --> D1[agents/]
    D1 --> D1a[hermes/]
    D1 --> D1b[openclaw/]

    E --> E1[MEMORY.md]
    E --> E2[SOUL.md]
    E --> E3[skills/]

    F --> F1[*.pkl]
    F --> F2[*.onnx]

    G --> G1[*.json]
    G --> G2[*.csv]
```

### Workflow Protocol State Machine

```mermaid
stateDiagram-v2
    [*] --> TaskReceived
    TaskReceived --> Planning: OpenClaw
    Planning --> Implementation: Hermes
    Implementation --> Verification: Nautilus
    Verification --> Review: Code Reviewer
    Review --> Approved: Quality Gate
    Review --> Rejected: Fix Required
    Rejected --> Implementation
    Approved --> Memory: Memory Engineer
    Memory --> [*]

    state Planning {
        [*] --> ParseBrief
        ParseBrief --> CreatePlan
        CreatePlan --> EstimateEffort
    }

    state Implementation {
        [*] --> ExecuteCode
        ExecuteCode --> RunTests
        RunTests --> CollectResults
    }

    state Verification {
        [*] --> ValidateOutput
        ValidateOutput --> CrossCheck
        CrossCheck --> GenerateReport
    }
```

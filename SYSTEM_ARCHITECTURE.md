# SYSTEM ARCHITECTURE — Quant Lab Agent Network
> Version: 1.1 | Date: 2026-05-16 | Status: ACTIVE

---

## 1. OVERVIEW

Six-agent system where the human is the **Board of Directors** (sets direction, approves strategy), CC is the **Overseer/Architect**, and OC/OC2/AS/PM/RL are **autonomous execution agents** that operate in the background.

```
┌─────────────────────────────────────────────────────────────────┐
│                    GOVERNANCE LAYER                              │
│  Human (Board) ──→ Overseer/CEO (me) ──→ Agent Network          │
│  Sets direction    Defines tasks     Executes work               │
│  Approves plans    Reviews output    Reports results             │
│  Corrects course   Maintains arch    Self-improves              │
└─────────────────────────────────────────────────────────────────┘
```

## 2. AGENT ROLES & CONTRACTS

### OpenClaw — The Analyst
- **Role:** Research, parsing, planning, data preparation, bookkeeping
- **Interface:** Workspace files + CLI gateway (ws://127.0.0.1:18789)
- **Workspace:** `.openclaw/`
- **Core responsibility:** Transform ambiguous goals into structured, executable task briefs
- **Output contract:** Every task produces a structured JSON result + a human-readable summary

### Hermes — The Engineer
- **Role:** Strategy implementation, backtest execution, parameter sweeps, code generation
- **Interface:** Workspace files + Telegram bot
- **Workspace:** `agent-lab/agents/hermes/hermes_workspace/`
- **Core responsibility:** Take structured task briefs from OpenClaw, execute Nautilus backtests, report results
- **Output contract:** Every backtest produces a Nautilus report JSON + a progress summary entry

### Claude Code (CC) — The Overseer
- **Role:** Define objectives, architect workflows, review outputs, handle escalations, maintain system integrity
- **Interface:** VS Code + this conversation + file system inspection
- **Core responsibility:** Ensure the system produces coherent results and improves over time
- **Output contract:** Architecture decisions, task assignments, quality reviews
- **Phase authority:** Only CC can advance phases via `python tools/phase-gate.py --advance`

### Polymorph (PM) — The Debugger & Tool Builder
- **Role:** Debug workspace/agent issues, optimize workflows, build tools & skills from repos, automate repetitive tasks
- **Interface:** Workspace files + progress tracking + team chat
- **Workspace:** `progress/polymorph-progress.md`
- **Core responsibility:** Keep the machine running — diagnose problems before they cascade, convert GitHub repos into agent tools, build cron jobs and automation
- **Output contract:** Bug fixes, new tools/skills, automation scripts, workflow improvements
- **Status:** 🟢 Active — Standing by for AS or CC task assignments

### OWL (RL) — The Research Lead
- **Role:** Research, DSPy integration, pipeline optimization, tool evaluation
- **Interface:** Workspace files + progress tracking + team chat
- **Workspace:** `progress/rl-progress.md`
- **Core responsibility:** Evaluate and integrate new AI tools with minimal disruption
- **Output contract:** Research reports, integration plans, pipeline improvements
- **Status:** 🟢 Active — Registered 2026-05-16

## 3. DATA FLOW — The Task Lifecycle

```
[IDEA] → [BRIEF] → [PLAN] → [EXECUTE] → [REPORT] → [REVIEW] → [IMPROVE]
   │         │         │          │           │          │          │
   ▼         ▼         ▼          ▼           ▼          ▼          ▼
 Human    OpenClaw  OpenClaw   Hermes     Hermes    Overseer   All agents
          (parse &  (compose   (implement  (collect  (approve/  (learn from
          research)  commands)  & run)     results)  redirect)  failures)
```

### Step-by-step:

1. **IDEA** — Human communicates a goal (e.g., "backtest symmetry trap on GBPUSD")
2. **BRIEF** — OpenClaw parses the idea, extracts parameters, checks feasibility, produces `task_brief.json`
3. **PLAN** — OpenClaw composes the exact commands, parameter ranges, expected outputs → `execution_plan.json`
4. **EXECUTE** — Hermes runs Nautilus backtests, parameter sweeps, strategy implementations
5. **REPORT** — Hermes writes results to `nautilus/reports/` + appends to `hermes_progress_summary.json`
6. **REVIEW** — Overseer (me) inspects results, decides: ship / iterate / redirect
7. **IMPROVE** — All agents update their understanding: fix bugs, adjust parameters, refine prompts

## 4. PROGRESS TRACKING — The Single Source of Truth

Every agent writes to a **progress summary JSON** that follows this schema:

```json
{
  "timestamp": "ISO-8601",
  "task": "descriptive_task_name",
  "summary": "What was done in 1-2 sentences",
  "impact": "How this changes the system or results",
  "metrics": { "key": "value" },
  "errors": [],
  "lessons": "What was learned (empty if none)",
  "next_action": "What to do next"
}
```

### Files:
- `agent-lab/agents/hermes/hermes_progress_summary.json` — Hermes execution log
- `.openclaw/openclaw_progress_summary.json` — OpenClaw planning log
- `nautilus/reports/` — Detailed backtest JSON reports
- `PROJECT_PROGRESS.md` — Human-readable project state (updated by me)

## 5. ERROR HANDLING & CONTINUOUS REPAIR

### Error Classification

| Level | Description | Action |
|-------|-------------|--------|
| **INFO** | Expected variation (e.g., no trades generated) | Log, continue |
| **WARN** | Suboptimal result (e.g., low win rate) | Log, flag for review |
| **ERROR** | Execution failure (e.g., missing data, crash) | Log, retry with backoff |
| **FATAL** | Systemic failure (e.g., bad data pipeline, corrupted state) | Halt, escalate to overseer |

### The Repair Loop

```
ERROR DETECTED
    │
    ▼
ROOT CAUSE ANALYSIS (agent writes to error log)
    │
    ▼
CLASSIFY: Is this a...
    │
    ├── ONE-OFF (bad data, network glitch) → Retry, log, move on
    │
    ├── RECURRING (same error 3+ times) → Flag for SYSTEM FIX
    │       │
    │       ▼
    │   SYSTEM FIX: Agent proposes + implements structural change
    │   (e.g., add data validation, adjust parameter bounds, fix parsing)
    │       │
    │       ▼
    │   VALIDATE: Run the same task again to confirm fix
    │       │
    │       ▼
    │   DOCUMENT: Add the fix to the agent's knowledge base
    │
    └── STRUCTURAL (flawed assumption in system design) → Escalate to overseer
            │
            ▼
        Overseer redesigns the affected component
        Agents update their prompts and configs accordingly
```

### Key Principle: Errors Are Data

Every error is a signal that the system's model of reality is wrong. The repair mechanism exists to:
1. **Capture** the error with full context
2. **Classify** it by severity and recurrence
3. **Fix** the root cause, not the symptom
4. **Validate** the fix works
5. **Learn** — update prompts, configs, and data validation to prevent recurrence

## 6. NO-MT5 POLICY

MT5 is **fully deprecated** for backtesting. This is a hard constraint.

- **Why:** MetaEditor can't compile headlessly; Strategy Tester can't be automated
- **Replacement:** NautilusTrader (Python-based, local CSV/parquet data)
- **Data pipeline:** `Downloads/*.csv` → `nautilus/data/*.parquet` → Nautilus engine → reports
- **Verification:** Oanda API data → same Nautilus strategy → cross-validate
- **MT5 MCP server:** Kept ONLY for `mt5_get_market_data` (live data fetch), NOT for backtesting

### MT5 Artifact Migration
All existing MT5 artifacts (MQL5 EAs, `.set` files, MT5-specific configs) should be archived to `archive/mt5/` and replaced with Nautilus equivalents.

## 7. STORAGE & INFRASTRUCTURE

### Hybrid Storage Mesh
```
Hot (Local SSD) → Warm (USB Drive 1) → Cold (USB Drive 2) → Offsite (Cloud)
```
- Agents don't care where files live — the Virtual Workspace Layer handles placement
- `usb-mesh.ps1` handles USB sync; `rclone` handles cloud sync

### Cloud Deployment (Future)
- Oracle Cloud free tier (24GB ARM) for 24/7 agent execution
- Agents run headless on cloud, accessible via SSH tunnel
- Local machine used for development and oversight only

## 8. COMMUNICATION PROTOCOL

### Between Agents
- **Method:** Workspace file drops (JSON files in shared directories)
- **Signal:** New file in shared directory = task available
- **Acknowledgment:** Agent writes a `.done` file or updates progress summary

### Between Human and System
- **Input:** Human communicates intent (this chat, or future Telegram bot)
- **Output:** Progress summaries + backtest reports + this architecture doc
- **Escalation:** FATAL errors or ambiguous goals → routed to human for decision

## 9. CONTINUOUS IMPROVEMENT MECHANISM

### Built-in Learning
1. Every backtest result is stored with full parameters → enables parameter optimization over time
2. Failed strategies are analyzed for patterns → inform future strategy design
3. Agent prompts are versioned → improvements are tracked and can be rolled back
4. Weekly review process: agents flag recurring issues, overseer approves fixes

### Self-Improvement Loop
```
COLLECT DATA → IDENTIFY PATTERNS → PROPOSE IMPROVEMENT → TEST → DEPLOY → MEASURE
      ↑                                                                    │
      └────────────────────────────────────────────────────────────────────┘
```

This loop runs at two levels:
- **Tactical:** Parameter optimization within a single strategy
- **Strategic:** Workflow improvements across the entire agent network

---

*This document is the system's constitution. Changes require overseer approval and must be reflected in all agent prompts.*
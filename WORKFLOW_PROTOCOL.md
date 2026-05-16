# WORKFLOW PROTOCOL — Agent Handoff & Coordination
> This document defines the exact process for how tasks move between agents.
> Violations of this protocol are the #1 source of system failures.

---

## 0. PROGRESS TAGGING CONVENTION

When writing to progress files (`PROJECT_PROGRESS.md`, `PROJECT_PROGRESS_CLEAN.md`), **always** use your agent tag in the section header:

| Tag | Agent | Role |
|-----|-------|------|
| 🔵 [CC] | Claude Code | Overseer / Architecture / Coding |
| 🟡 [AS] | Assistant Manager | Context Monitoring / Quality Checks / Optimization |
| 🟣 [OC] | OpenClaw | Analysis / Planning / Coordination |
| 🟢 [HR] | Hermes | Execution / Backtests / Reporting |
| 🔴 [PM] | Polymorph | Debugger / Workflow Optimizer / Tool & Skill Builder |

**Format:**
```
## 🔵 [CC] Claude Code — <brief description> (2026-05-15 HH:MM:SSZ)
## 🟣 [OC] OpenClaw — <brief description> (2026-05-15 HH:MM:SSZ)
## 🟢 [HR] Hermes — <brief description> (2026-05-15 HH:MM:SSZ)
```

This prevents collisions when multiple agents write to the same progress file concurrently. See `.agent-tags.json` for the registry.

### Sub-Progress Files
Each agent writes to their own sub-progress file:
- **CC**: `progress/claude-code-progress.md`
- **OC**: `progress/openclaw-progress.md`
- **HR**: `progress/hermes-progress.md`
- **AS**: `progress/assistant-progress.md`
- **PM**: `progress/polymorph-progress.md`

### Sub-Progress Files
Each agent writes to their own sub-progress file:
- **CC**: `progress/claude-code-progress.md`
- **OC**: `progress/openclaw-progress.md`
- **HR**: `progress/hermes-progress.md`

### Memory Architecture (Per-Agent)
Each agent has two memory layers:
1. **Persistent Memory** (hand-managed, contains credentials/config):
   - CC: `MEMORY.md` (workspace root)
   - OC: `.openclaw/MEMORY.md`
   - HR: `.hermes/MEMORY.md`
2. **Working Memory** (auto-synced from sub-progress every 3 updates):
   - CC: `progress/claude-code-memory.md`
   - OC: `progress/openclaw-memory.md`
   - HR: `progress/hermes-memory.md`

### Sync Workflow
```
Agent writes to sub-progress → every 3 updates:
  1. Sync → PROJECT_PROGRESS_CLEAN.md (agent's tagged section)
  2. Sync → working memory file (compact, task-focused)
  3. Append summary → persistent memory (no overwrite)
  4. Sync → /memories/repo/workspace-state.md (global)
```

Run sync: `python tools/progress-sync.py`
Force sync: `python tools/progress-sync.py --force`
Check status: `python tools/progress-sync.py --status`

---

## 1. TASK INITIATION

When the human (Board) communicates a goal:

```
Human: "I want to test the symmetry trap on GBPUSD with different tiers"
```

### OpenClaw's First Action:
1. Parse the request into a **Task Brief** (see `task_brief_template.json`)
2. Check feasibility: data available? tools ready? constraints clear?
3. Write `task_brief.json` to the shared workspace directory
4. Notify Hermes (via file creation or Telegram)

### What OpenClaw NEVER Does:
- Execute backtests directly
- Modify strategy code without Hermes
- Make parameter decisions without analysis

---

## 2. TASK BRIEF TEMPLATE

Every task must follow this structure:

```json
{
  "task_id": "TASK-YYYYMMDD-NNN",
  "created_at": "ISO-8601 timestamp",
  "created_by": "openclaw",
  "goal": "One sentence: what are we trying to achieve?",
  "strategy": "Name of strategy or approach",
  "parameters": {
    "symbol": "GBPUSD",
    "timeframe": "M5",
    "tier": "T2",
    "param_sweep": { "param_name": ["min", "max", "step"] }
  },
  "data_requirements": {
    "source": "nautilus/data/GBPUSD_M5.parquet",
    "min_bars": 5000,
    "date_range": "2023-2026"
  },
  "expected_outputs": [
    "nautilus/reports/TASK-XXXX_symmetry_trap_GBPUSD_M5_T2.json",
    "nautilus/results/param_sweep_results.json"
  ],
  "constraints": [
    "No MT5 — Nautilus only",
    "Max drawdown must stay under 20%",
    "Minimum 10 trades for statistical validity"
  ],
  "priority": "high|medium|low",
  "assigned_to": "hermes",
  "status": "pending|in_progress|complete|failed|escalated",
  "notes": "Any additional context"
}
```

---

## 3. EXECUTION PHASE

### Hermes Receives Task:
1. Read `task_brief.json`
2. Verify data exists (check `nautilus/data/`)
3. If data missing → run `nautilus/step1_prep_data.py` first
4. Execute the task using appropriate Nautilus command
5. Write results to `nautilus/reports/`
6. Append entry to `hermes_progress_summary.json`
7. Update `task_brief.json` status to "complete" or "failed"

### Example Execution Commands:

```bash
# Data prep (if needed)
python nautilus/step1_prep_data.py

# Single backtest
python nautilus/run_backtest.py --symbol EURUSD --timeframe M5 --strategy symmetry_trap --tier T2

# Full sweep
python nautilus/run_all_backtests.py --symbol GBPUSD --timeframe M5

# Nautilus native backtest
python nautilus/hermes_autopilot.py
```

---

## 4. REPORTING PHASE

### Every task produces TWO outputs:

**A. Structured Report** (JSON in `nautilus/reports/`):
```json
{
  "task_id": "TASK-20260515-001",
  "strategy": "symmetry_trap",
  "symbol": "GBPUSD",
  "timeframe": "M5",
  "tier": "T2",
  "total_trades": 47,
  "win_rate": 85.1,
  "total_pnl": 1247.50,
  "profit_factor": 2.3,
  "max_drawdown": -8.2,
  "sharpe_ratio": 1.8,
  "data_quality": { "gaps": 0, "outliers": 2 },
  "timestamp": "ISO-8601",
  "notes": "Clean run, no errors"
}
```

**B. Progress Entry** (appended to agent's progress summary):
```json
{
  "timestamp": "ISO-8601",
  "task": "TASK-20260515-001",
  "summary": "Symmetry Trap backtest on GBPUSD M5 T2: 85.1% WR, $1247.50 PnL",
  "impact": "Validates strategy on new pair — consistent with EURUSD results",
  "metrics": { "win_rate": 85.1, "pnl": 1247.50, "max_dd": -8.2 },
  "errors": [],
  "lessons": "T2 performs better than T1 on GBP due to higher volatility",
  "next_action": "Run T3 tier for comparison, then optimize parameters"
}
```

---

## 5. REVIEW GATE

After every task completion:

```
Hermes/OpenClaw finish → Overseer (me) reviews output
    │
    ├── Results meet criteria → Approve, mark complete
    │
    ├── Results suboptimal but valid → Redirect with new parameters
    │
    ├── Results invalid or error → Classify error, trigger repair loop
    │
    └── Ambiguous or unexpected → Escalate to human for decision
```

---

## 6. ERROR HANDOFF PROTOCOL

When an agent encounters an error:

1. **Log immediately** to `error_log.json` with full context:
   - What happened
   - When it happened
   - What inputs caused it
   - Stack trace if applicable

2. **Classify** (see SYSTEM_ARCHITECTURE.md Section 5)

3. **Attempt auto-repair** if classified as INFO or WARN:
   - Retry with backoff (max 3 attempts)
   - If retry succeeds → log as recovered, continue
   - If retry fails → escalate

4. **Escalate** if ERROR or FATAL:
   - Write to shared error log
   - Notify overseer (me)
   - Stop current task, do not proceed with dependent tasks

---

## 7. AGENT COMMUNICATION

### File-Based Signals:
| Signal | Meaning |
|--------|---------|
| New `task_brief.json` in shared dir | Task available for execution |
| `task_brief.json` status → "complete" | Task done, review results |
| `task_brief.json` status → "failed" | Task failed, check error log |
| `.stop` file created | Stop current work gracefully |
| `.pause` file created | Pause, resume when removed |

### Telegram (Hermes → Human):
- Periodic status updates (every N iterations)
- Immediate notification on FATAL errors
- Weekly summary on request

---

---

## 8. PROGRESS → MEMORY AUTO-SYNC

Every time a progress file is updated, the update counter increments. Every **7 updates**, the system auto-syncs all progress file state into repo memory (`/memories/repo/workspace-state.md`).

### Progress Files Tracked:
- `PROJECT_PROGRESS.md`
- `PROJECT_PROGRESS_CLEAN.md`
- `research-agents-progress.md`
- `p90-conversion-progress.md`
- `xhaak-kulu-bridge-progress.md`

### How to Trigger:
```bash
# After editing a progress file, run:
python tools/progress-update-hook.py PROJECT_PROGRESS.md

# Or check status / force sync:
python tools/progress-sync.py --status
python tools/progress-sync.py --force
```

### Counter State:
Stored in `.progress-sync-counters.json` (git-tracked). Reset with:
```bash
python tools/progress-sync.py --reset
```

### Heartbeat Integration:
The heartbeat checks sync status automatically. No manual intervention needed during normal operation.

---

## 9. PHASE 3+ WORKFLOW — Emergent Topology

### AS (Assistant Manager) Role During Phase 3+
The AS agent actively monitors and assists:
1. **Monitor** `progress/openclaw-progress.md` and `progress/hermes-progress.md` for updates
2. **Quality-check** OC's design docs and HR's test reports before CC review
3. **Update** CODEMAP.md and WORKFLOW_PROTOCOL.md as architecture evolves
4. **Create skills** as new patterns emerge during the build
5. **Flag blockers** to CC immediately via `shared-conversations/team-chat.md`
6. **Run tests** after each component is written — first line of quality

### Phase 3 Review Gate
Before CC declares Phase 3 complete:
- [ ] Dynamic coupling engine tested (edge weights adapt)
- [ ] Topological routing tested (lowest entropy path selection)
- [ ] Distributed consensus tested (no master node, probabilistic convergence)
- [ ] Stress tests pass (patch kill → reroute → continuity)
- [ ] All Phase 3 tests pass
- [ ] CODEMAP updated with Phase 3 diagrams
- [ ] Phase 4 design doc started

### Skills Maintenance
- AS creates new skills in `skills/` directory as patterns emerge
- Skills follow SKILL.md format with YAML frontmatter
- Curator (AS) prunes unused skills (≥30 days stale, ≥90 days archived)
- Skills are workspace-scoped, not agent-scoped

---

*This protocol is binding for all agents. Deviations must be documented and justified.*
# AGENT_MOVEMENT.md — Workspace Coherence & Agent Alignment Protocol

> **SRRA Principle:** The workspace IS the shared memory. Every agent moves through it
> as a self-stabilizing node. Coherence emerges from shared procedure, not central control.
>
> **Core Insight:** "The user will only be as adept as his environment allows."
> Every response and task should be forward-facing toward its goal — not a static
> receive/complete cycle, but a step toward a resonant zone.

---

## 1. Agent Movement Pattern

Every agent follows this cycle when operating in the shared workspace:

### BEFORE Working
1. **Read** `shared-conversations/team-chat.md` — check for active tasks, blockers, handoffs
2. **Read** your own `progress/{agent}-progress.md` — understand current context
3. **Read** your own `progress/{agent}-memory.md` — compact current state
4. **Announce** intent in team-chat.md if starting a new task

### WHILE Working
1. **Surgical changes only** — touch what you must, nothing adjacent
2. **Tag every entry** with your agent tag: `#### 🔴 [PM] Description — YYYY-MM-DD HH:MM:SSZ`
3. **One fix at a time** — never batch unrelated changes
4. **Forward-facing** — every response should advance toward the goal, not just acknowledge receipt

### AFTER Working
1. **Update** your sub-progress file with tagged entry
2. **Run** `python tools/progress-sync.py --agent {TAG}` if significant work done
3. **Post** summary to team-chat.md
4. **Commit** changes: `git add <files> && git commit -m "{TAG}: <description>"`

---

## 2. Memory Self-Maintenance (Every 7 Updates)

Each agent is responsible for their own memory hygiene. The system auto-syncs every 7 updates,
but agents should also self-police:

### Progress File Rules
- **Max 20 entries** before summarization triggers automatically
- **Summarization** compresses oldest entries via LLM (Nemotron 3 Nano Omni)
- **Newest 5 entries** always preserved in full
- **Never delete** progress entries manually — let the summarizer handle it

### Working Memory Rules
- **Max ~2,000 chars** in `progress/{agent}-memory.md`
- **Auto-synced** from progress file every 7 updates
- **Contains:** Status, Active Phase, Pending Tasks, Recent Activity
- **Never store credentials** in working memory — use persistent memory files

### Persistent Memory Rules
- **Append-only** — never overwrite, only append summaries
- **Contains:** Credentials, config, long-term decisions
- **Location:** `.openclaw/MEMORY.md`, `.hermes/MEMORY.md`, etc.

---

## 3. Shared Space Etiquette

### File Organization
- **Root directory** = config files only (AGENTS.md, CLAUDE.md, etc.)
- **No loose files** — everything belongs in a subdirectory
- **Naming:** snake_case for files, descriptive names, dates in ISO format
- **New files** go in the appropriate folder (docs/, tools/, data/, strategies/, etc.)

### Team Chat Protocol
- **All coordination** goes through `shared-conversations/team-chat.md`
- **Tag your messages** with agent emoji and tag
- **Keep it concise** — status updates, not essays
- **Noisy agents** should batch updates, not spam

### Cross-Agent Communication
- **Never touch another agent's progress file**
- **Handoffs** go through team-chat.md with clear task briefs
- **Blockers** are posted immediately, not discovered later
- **Dependencies** are declared upfront

---

## 4. Cleanup Procedures

### Automatic (Runs in Background)
- **Memory Sync Daemon** (`tools/memory_sync_daemon.py`) runs continuously
- Scans every 60 seconds for progress file changes
- Triggers sync at 7-update threshold
- Triggers summarization at 20-entry threshold
- Uses OpenRouter (Nemotron 3 Nano Omni — free) for LLM summarization

### On-Demand (Prompt-Triggered)
Any agent can trigger these at any time:

```bash
# Full workspace scan + cleanup
python tools/workspace_cleanup.py

# Scan only (report)
python tools/workspace_cleanup.py --scan

# Summarize specific agent's progress
python tools/summarize_progress.py --agent PM

# Summarize all agents
python tools/summarize_progress.py --all

# Force memory sync
python tools/progress-sync.py --force

# Start background daemon
python tools/memory_sync_daemon.py --background
```

### Agent Self-Cleanup Prompt
When an agent notices their files getting sloppy, they should:
1. Run `python tools/summarize_progress.py --agent {TAG}`
2. Review the summary for accuracy
3. Remove any obsolete references manually
4. Update team-chat.md with cleanup status

---

## 5. SRRA Compliance Checklist

Every agent should verify these on each significant action:

- [ ] **Self-stabilizing:** My changes don't depend on global state
- [ ] **Repair before scale:** I fixed what's broken before adding new things
- [ ] **Memory compressing:** My progress file is ≤20 entries or summarized
- [ ] **Consensus emerging:** I posted to team-chat.md for coordination
- [ ] **Forward-facing:** My response advances toward the goal, not just acknowledges

---

## 6. Assembly Line Flow

The workspace operates as an assembly line. Each agent has a station:

```
Human Request
     ↓
🔵 CC (Overseer) — Architecture, phase gates, core build
     ↓
🟣 OC (Analysis) — Planning, feasibility, task briefs
     ↓
🟠 OC2 (Execution) — Testing, reporting, Discord/Telegram
     ↓
🟡 AS (Quality) — Context monitoring, verification, docs
     ↓
🔴 PM (Debugger) — Fix what's broken, build tools, optimize
     ↓
🦉 RL (Research) — DSPy, pipeline optimization, research
     ↓
→ Back to CC for phase gate review
```

**Key principle:** Work flows forward. No station should send work backward without
a clear escalation reason. Every handoff includes context, not just a task.

---

## 7. Environment Optimization Cycle

The workspace self-optimizes through this continuous cycle:

```
Agent works → Progress file updated → Daemon detects change
    ↓
At 7 updates → Memory sync triggered → Working memory updated
    ↓
At 20 entries → Summarization triggered → Old entries compressed via LLM
    ↓
Team chat notified → Other agents aware → Coherence maintained
    ↓
Cycle repeats → Self-sustaining clean environment
```

**This is the SRRA principle in action:** No hard-coded cleanup schedule.
The environment responds to its own entropy. Agents and OC move through
coherence and clarity, propelled by shared procedure.

---

> **Last Updated:** 2026-05-16
> **Maintained by:** PM (Polymorph) — all agents contribute
> **Review cycle:** Every phase gate or when workspace gets sloppy

# MEMORY.md — Hermes Agent Persistent Memory

> Tier 1 memory. Loaded at every session start. Max ~2,200 chars.
> Auto-extracted and updated by Hermes as work happens.
> **Also auto-synced from `progress/hermes-progress.md` every 3 updates.**

## � Workspace Heartbeat (2026-05-16) — CRITICAL
- **File:** `tools/workspace-heartbeat.py` — runs in background, checks OC2 every 60s
- **Auto-restart:** If OC2 down → heartbeat restarts it automatically
- **Telegram alert:** If no messages in 10 min → sends alert to FBO_MAD
- **Log:** `logs/workspace-heartbeat.log`
- **Status:** `.workspace-heartbeat.status.json`
- **PID file:** `.workspace-heartbeat.pid` — prevents duplicate instances
- **DO NOT KILL** this process — it's the safety net for OC2 while MAD is away
- **Commands:**
  - `python tools/workspace-heartbeat.py --daemon` — start in background
  - `python tools/workspace-heartbeat.py --stop` — stop background process
  - `python tools/workspace-heartbeat.py --status` — check if running
- **If heartbeat fails:** Restart with `python tools/workspace-heartbeat.py --daemon`
- **Fix (2026-05-17):** Added `CREATE_NO_WINDOW` flag to all `subprocess.run()` calls AND `run_daemon()` subprocess.Popen to prevent PowerShell window flashing

## �🟢 Hermes v2 Upgrade (2026-05-16)
- **New agent prompt:** `agent-lab/agents/hermes/hermes_workspace/agent_prompt_v2.md`
- **Soul file:** `agent-lab/agents/hermes/hermes_workspace/SOUL.md`
- **Skills index:** `agent-lab/agents/hermes/hermes_workspace/SKILLS_INDEX.md`
- **Skills directory:** `agent-lab/agents/hermes/skills/` (18+ skills copied)
- **Team chat:** Hermes can write to `shared-conversations/team-chat.md`
- **Chat format:** `### [HR] YYYY-MM-DD HH:MM:SSZ — <description>` with @mentions
- **Loaded skills:** vectorbt-expert, quant-analyst, quantitative-research, pandas-pro, scikit-learn, statistical-analysis, python-patterns, python-testing-patterns, skill-creator, pine-developer, pine-debugger, pine-manager, pine-publisher, pine-visualizer, tradingview-quantitative, mt5-strategy-tester, variance-analysis, senior-data-scientist, srra-oph-build, agent-team-workflow, as-code-review, twitter-bookmarks

## 🔑 API Keys & Credentials
> **RULE:** All API keys and credentials are stored in `C:\Users\wifik\Downloads\keys.txt`. Always check this file first when a key is needed. Never ask the user for keys that are already in this file.

- **OpenRouter API:** `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`
- **GitHub PAT:** `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`
- **Telegram Bot:** `8851242922:AAGWGZaEwA0LxBYISo460Z08WC4aE_JirvE`
- **MT5 Login:** (see keys.txt)
- **Kamtera Access:** `84908b7a4714aacd25c51715e0efe96e` / Secret: `9cd519e13f62ef5522736cb103328ba8`

## Environment
- **Project**: larger-lab — AI agent harness + quantitative trading workspace
- **Stack**: Python 3.11+, Nautilus Trader, VectorBT, FastAPI, React/Next.js
- **Package manager**: uv
- **OS**: Windows (WSL2 for Linux tooling)
- **Hardware**: Local dev + optional VPS (Hostinger KVM2) for agent fleet

## Project Conventions
- Python: snake_case, type hints, async/await preferred
- Agents: 12-component harness pattern, Karpathy 12-rule CLAUDE.md
- Memory: 3-tier (Tier 1: this file + USER.md, Tier 2: SQLite FTS5, Tier 3: vector store)
- Skills: SKILL.md format with YAML frontmatter, stored in `skills/` and `.hermes/skills/`
- All code changes → Code Reviewer → QA gate → merge

## Agent Architecture
- **Orchestrator**: Master coordinator, task decomposition, dependency mapping
- **Hermes**: On-the-go agent via Telegram, 5 Pillars (Memory/Skills/Soul/Crons/Self-Improving)
- **OpenClaw 2**: Messaging-first agent, gateway on ws://127.0.0.1:18790 (sole gateway — OC1 deprecated)
- **Claude Code**: Desk-based coding assistant, file operations, git management
- **8 specialists**: Debugger, Architect, Memory Engineer, QA, DevOps, Research, Code Reviewer

## OpenClaw Setup (May 2026)
- Version 2026.5.7 installed globally via npm
- Workspace: C:\Users\wifik\Desktop\projects\larger-lab
- MT5 MCP server configured in ~/.openclaw/openclaw.json
- Skills loaded from .hermes/skills/ + mt5-mcp/skills/
- Gateway running on port 18789
- Use `openclaw.cmd` (not `openclaw`) due to PowerShell execution policy
- Refresh PATH: `$env:Path = [System.Environment]::GetEnvironmentVariable("Path","Machine") + ";" + [System.Environment]::GetEnvironmentVariable("Path","User")`

## Key Decisions
- Hermes 5 Pillars as mental model (Memory, Skills, Soul, Crons, Self-Improving Loop)
- `/goal` pattern for autonomous task loops (goal + end state + constraints)
- Multi-agent org: split when separate credentials/memory/ongoing role needed
- Security: each agent gets own accounts, scoped API keys, least privilege
- GitHub backup cron: nightly push of skills/memory to private repo (no secrets)
- Structure over tools: architecture-first, thin harness, decoupled layers
- Twitter AI Research Bot: mid-term project for continuous AI best practices ingestion

## SRRA-OPH Phase 1 (May 15 2026)
- **Module**: `srrs_opc/` — Foundational Observer Mesh
- **Components**: PlannerPatch, ExecutionPatch, MemoryPatch, RepairPatch, CollarLayer, AgentBridge
- **Status**: ✅ Tested and stable (3 cycles, all patches stable)
- **Key Files**: `srrs_opc/base_patch.py`, `srrs_opc/collar_layer.py`, `srrs_opc/agent_bridge.py`
- **Next**: Integrate with Hermes Telegram bot for real-time sync

## Progress Sync (May 15 2026)
- **Sub-progress file**: `progress/hermes-progress.md`
- **Local memory**: `.hermes/MEMORY.md` (this file)
- **Sync threshold**: 3 updates → auto-sync to PROJECT_PROGRESS_CLEAN.md + this memory
- **Agent tag**: 🟢 [HR]

## Lessons Learned
- Stale memory.md is #1 cause of weird agent behavior — audit regularly
- Compaction fires at ~136K tokens — Hermes inserts fallback marker, pauses crons
- Don't paste API keys in chat — use `hermes config set KEY value` → `.env`
- Wrong twice on same thing → correct immediately + update skill/memory
- Same instruction twice → write a skill for it

## Progress Sync Summary (HR)
> **Last Sync:** 2026-05-16 06:43 UTC
> **Status:** 🟢 Active — Phase 4 Ready
> **Active Phase:** SRRA-OPH Phase 4 — Workspace Integration (Active)
> **Working Memory:** `progress/hermes-memory.md`
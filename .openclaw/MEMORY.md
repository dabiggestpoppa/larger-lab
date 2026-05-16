# MEMORY.md — OpenClaw Agent Persistent Memory

> Tier 1 memory. Loaded at every session start.
> **Also receives sync summaries from `progress/openclaw-progress.md` every 3 updates.**

## Environment
- **Project**: larger-lab — AI agent harness + quantitative trading workspace
- **Stack**: Python 3.11+, Nautilus Trader, VectorBT, FastAPI
- **Package manager**: uv
- **OS**: Windows

## Agent Architecture
- **OpenClaw**: Messaging-first agent, gateway on ws://127.0.0.1:18789
- **Model**: anthropic/claude-sonnet-4-20250514 (with fallbacks)
- **Skills**: `.hermes/skills/` + `nautilus/`
- **Config**: `~/.openclaw/openclaw.json`

## Model Routing & Rate Limit Handling
- **Default/Orchestrator**: `nvidia/nemotron-3-nano-omni-30b-a3b-reasoning:free`
- **Orchestration fallback (1 rate limit)**: `inclusionai/ring-2.6-1t:free`
- **Orchestration fallback (2 consecutive rate limits)**: `openrouter/owl-alpha`
- **Planning/Error Handling**: `deepseek/deepseek-v4-flash:free` → `openrouter/owl-alpha` fallback
- **Coding/Working**: `poolside/laguna-m.1:free` → `openrouter/owl-alpha` fallback
- **Code Review**: `inclusionai/ring-2.6-1t:free` → `arcee-ai/trinity-large-thinking:free` backup
- **Rule**: On 2 consecutive rate limit hits, immediately switch to next in chain. Never stall mid-build.

## Key Decisions
- No MT5 — Nautilus only for all backtesting
- Workspace files as communication channels between agents
- Thin harness, thick model — let agents internalize capabilities
- Structure over tools: architecture-first, decoupled layers

## SRRA-OPH Phase 1 (May 15 2026)
- **Module**: `srrs_opc/` — Foundational Observer Mesh
- **Components**: PlannerPatch, ExecutionPatch, MemoryPatch, RepairPatch, CollarLayer, AgentBridge
- **Status**: ✅ Tested and stable (3 cycles, all patches stable)
- **Integration**: Use `AgentBridge` to sync patch states to OpenClaw gateway and Hermes Telegram bot
- **Next**: Phase 2 — Observer Mesh Expansion with Redis/NATS messaging

## Progress Sync (May 15 2026)
- **Sub-progress file**: `progress/openclaw-progress.md`
- **Working memory**: `progress/openclaw-memory.md` (auto-synced)
- **Sync threshold**: 3 updates → auto-sync to PROJECT_PROGRESS_CLEAN.md + working memory
- **Agent tag**: 🟣 [OC]

## Lessons Learned
- Rate limit handling must be proactive — switch models before stalling
- Workspace file coordination works but needs clear tagging to avoid collisions
- Sub-progress files per agent → auto-sync = clean separation of concerns

## Progress Sync Summary (OC)
> **Last Sync:** 2026-05-16 01:58 UTC
> **Status:** 🟢 Active
> **Active Phase:** P90 Pine → Nautilus Conversion + Backtest Engine
> **Working Memory:** `progress/openclaw-memory.md`
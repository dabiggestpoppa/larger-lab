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
> **Last Sync:** 2026-05-17 06:49 UTC
> **Status:** 🟢 Active
> **Active Phase:** P90 Pine → Nautilus Conversion + Backtest Engine
> **Working Memory:** `progress/openclaw-memory.md`

## Content Farm — CivitAI Strategy (2026-05-17)
- **Source:** https://github.com/civitai/civitai — open-source AI content platform (Next.js + tRPC + Prisma)
- **MAD's Strategy:** Copy, remix, repurpose CivitAI content for content farm. "Play copy and post promote paid."
- **Key Insight:** Massive library of AI-generated content including NSFW. All freely accessible.
- **Integration Path:** CivitAI scraper → remix pipeline (watermark, crop, filter) → DeekeScript automation → multi-platform posting
- **Content farm projects:** `projects/content/` (DeekeScript, MediaCrawler, Spider_XHS, accounts, templates)
- **Next:** Build scraper for trending/popular content, remix pipeline, account rotation
- **API:** https://civitai.com/api/v1/ — /images, /models, /model-versions endpoints
- **NSFW levels:** None, Soft, Mature, X — all accessible with API token
- **Scraper tools:** Confuzu's Image Grabber + Model Grabber on GitHub
- **Ready-made datasets:** 800+ NSFW videos model, 10k+ NSFW prompts dataset on CivitAI
- **Integration doc:** `projects/content/content-farm/CIVITAI_INTEGRATION.md`
- **Content funnel:** Free (TikTok/IG/X) → Followers → Paid (OF/Fansly) + Affiliates + Sponsorships
- **MAD's key insight:** "We never start from ground 0. CivitAI is production-grade. We just curate, remix, and push."

## Quant Lab — 6 Goals & Agent Team (2026-05-17)
- **GOALS.md:** `quant-lab/GOALS.md` — 6 non-negotiable goals with actionable steps
- **Team:** Manager v2 (orchestrator) + Optimizer (builds/runs) + Researcher (analyzes/designs)
- **Communication:** File-based via `quant-lab/insights/`, `quant-lab/findings/`, `quant-lab/decisions/`
- **Key Finding:** p90_cascade.py has TP bug (mean-reversion vs directional), Stall_Harvest 100% WR suspicious
- **Command Center:** Built at `oce/frontend/app/command-center/` — MAD can talk to any agent, create rooms
- **Lazyweb MCP:** Installed for design research — `lazyweb_search`, `lazyweb_health` tools available
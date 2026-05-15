# MEMORY.md — Hermes Agent Persistent Memory

> Tier 1 memory. Loaded at every session start. Max ~2,200 chars.
> Auto-extracted and updated by Hermes as work happens.

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
- **OpenClaw/Claude Code**: Desk-based coding assistant, file operations, git management
- **8 specialists**: Debugger, Architect, Memory Engineer, QA, DevOps, Research, Code Reviewer

## Key Decisions
- Hermes 5 Pillars as mental model (Memory, Skills, Soul, Crons, Self-Improving Loop)
- `/goal` pattern for autonomous task loops (goal + end state + constraints)
- Multi-agent org: split when separate credentials/memory/ongoing role needed
- Security: each agent gets own accounts, scoped API keys, least privilege
- GitHub backup cron: nightly push of skills/memory to private repo (no secrets)

## Lessons Learned
- Stale memory.md is #1 cause of weird agent behavior — audit regularly
- Compaction fires at ~136K tokens — Hermes inserts fallback marker, pauses crons
- Don't paste API keys in chat — use `hermes config set KEY value` → `.env`
- Wrong twice on same thing → correct immediately + update skill/memory
- Same instruction twice → write a skill for it

---
name: agent-harness-sop
description: Standard Operating Procedure for building agent-native tools. 7-phase pipeline, 5-layer compaction, 7 safety layers, 4 extension mechanisms.
---

# Agent Harness SOP Skill

Definitive guide for building agent-native tools in the larger-lab workspace.

## Core Philosophy

**The agent loop is simple. The harness around it is where the real engineering lives.**

- 98.4% of agent infrastructure is deterministic
- 1.6% is AI decision logic
- The model reasons. The harness enforces.

## 7-Phase Tool Building Pipeline

1. **Codebase Analysis** — Identify backend, map GUI→API, find data model
2. **CLI Architecture Design** — REPL + subcommand, command groups, state model
3. **Implementation** — Data layer → probe commands → mutations → backend → session
4. **Test Planning** — Unit + E2E + subprocess tests
5. **Test Writing** — test_core.py, test_e2e.py, test_cli.py
6. **Documentation** — SKILL.md, TEST.md, architecture SOP
7. **Publishing** — setup.py, PATH install, skill registry

## Key Patterns

### 5-Layer Context Compaction
Budget Reduction → Snip → Microcompact → Context Collapse → Auto-Compact

### 7 Safety Layers
Tool pre-filtering → Deny-first rules → Permission modes → Auto-classifier → Shell sandbox → Non-restoration → Hook interception

### 4 Extension Mechanisms (by cost)
Hooks (zero) → Skills (low) → Plugins (medium) → MCP (high)

### Subagent Sidechain Pattern
Subagents return ONLY summaries. Full transcripts → `progress/sidechains/*.jsonl`

### Tool Output Standard
Every command MUST support `--json` flag for agent consumption.

## Reference Files
- `docs/agent-harness-sop.md` — Full SOP document
- `tools/context_compaction.py` — Compaction implementation
- `tools/subagent_manager.py` — Subagent manager implementation

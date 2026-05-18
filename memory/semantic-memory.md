---
created: 2026-05-17
updated: 2026-05-17
tags: [memory, semantic, facts, concepts, relationships]
importance: 4
---

# Semantic Memory

> Facts, concepts, relationships. The knowledge graph of the system.

## System Architecture

- **SRRA-OPH** → Substrate system (33 Python files, 77 tests)
- **OCE** → Operator Continuity Engine (FastAPI backend + Next.js frontend)
- **V3** → Current development phase (P1 RSS done, P2-P9 pending)
- **Cognitive Field** → Team of distributed agents with OWL as orchestrator

## Key Concepts

### Cognitive Field Team
| Tag | Agent | Role |
|-----|-------|------|
| 🔵 CC | Claude Code | Overseer / Architecture |
| 🟠 OC2 | OWL | Orchestrator |
| 🟡 AS | Assistant Manager | Context Monitoring |
| 🔴 PM | Polymorph | Debugger / Tool Builder |
| 🟢 RL | OWL (Research Lead) | Research / DSPy |

### Memory Architecture (PAI-Inspired)
| Memory Type | File | Purpose |
|-------------|------|---------|
| Working | `memory/working-memory.md` | Active session context, in-flight state |
| Episodic | `memory/episodic-memory.md` | Past events, decisions, outcomes |
| Semantic | `memory/semantic-memory.md` | Facts, concepts, relationships |
| Procedural | `memory/procedural-memory.md` | Workflows, SOPs, how-to |
| Identity | `memory/identity-memory.md` | System identity, preferences, values |

## Infrastructure

| Service | Port | Path |
|---------|------|------|
| OpenClaw Gateway | 18790 | `~/.openclaw-2/` |
| OCE Frontend | 3000 | `oce/frontend/` |
| OCE Backend | 8000 | `oce/backend/` |
| Desktop Control API | 8001 | `tools/operator/desktop_api.py` |
| AgentMemory | 3111 | MCP server |
| AgentMemory Viewer | 3113 | Web UI |

## Agent Rules
- Max 5 concurrent sub-agents (system), max 2 (current policy)
- No recursive spawning
- All execution logged
- Repair before expansion
- Continuity over speed

## Relationships

- OWL → delegates to → Manager → Optimizer/Researcher
- CC → builds → code → AS tests → PM debugs → RL researches
- Agents communicate via → `shared-conversations/team-chat.md`
- Progress sync via → `tools/progress-sync.py` (7-update threshold)

# TOOLS.md — OWL Operator Tool Reference

> **Last Updated**: 2026-05-16
> **Purpose**: Quick reference for all tools, paths, and configurations

---

## Workspace Paths

| Path | Purpose |
|------|---------|
| `C:\Users\wifik\Desktop\projects\larger-lab` | Main workspace |
| `oce/` | Operator Continuity Engine |
| `oce/backend/` | FastAPI backend (main.py, event_fabric.py, observer_runtime.py, structural_memory.py) |
| `oce/frontend/` | Next.js frontend |
| `oce/docs/` | OCE documentation |
| `oce/tests/` | OCE test suites |
| `srrs_opc/` | SRRA-OPH core (33 modules, 77 tests) |
| `tools/` | Python/JS tools |
| `tools/operator/` | Operator control layer (desktop, vscode, system, observer) |
| `tools/agent-hooks/` | Agent lifecycle hooks |
| `skills/` | Agent skills (57 active) |
| `.agents/skills/` | Agent-specific skills (51) |
| `archive/skills/` | Archived dead skills (67) |
| `shared-conversations/` | Team chat |
| `progress/` | Agent progress files |
| `logs/` | System logs |
| `config/` | Configuration files |
| `projects/` | External projects (ads, content, trading, ai-tools, social) |

---

## Operator Control Tools

| Tool | Path | Purpose |
|------|------|---------|
| Desktop Control | `tools/operator/desktop-control.py` | Screen capture, input simulation, window management |
| VS Code Bridge | `tools/operator/vscode_bridge.py` | VS Code CLI control (files, editor, terminal, extensions, git) |
| System Operator | `tools/operator/system_operator.py` | Process, package, env, service, scheduler, network management |
| Observer Debug | `tools/operator/observer-debug.py` | Observer CLI (list, status, health, events, logs, activate, suspend) |
| Observer Integration | `tools/operator/observer-integration.py` | Operator ↔ Observer event bridge |
| Desktop API | `tools/operator/desktop_api.py` | FastAPI server on port 8001 |

---

## System Tools

| Tool | Path | Purpose |
|------|------|---------|
| Hermes Watchdog | `tools/hermes-watchdog.py` | OWL health monitor (gateway, workspace, disk) |
| Progress Sync | `tools/progress-sync.py` | Agent progress → memory sync |
| Chat Sync | `tools/chat_sync.py` | Team chat → agent memory sync |
| Memory Sync Daemon | `tools/memory_sync_daemon.py` | Background memory tracker |
| Workspace Cleanup | `tools/workspace_cleanup.py` | Loose file detection, oversized progress |
| Self Heal | `tools/self_heal.py` | Log scanner, error classifier, auto-fixer |
| Phase Gate | `tools/phase-gate.py` | Phase transition manager |
| CC Workflow | `tools/cc-workflow.py` | CC continuous workflow engine |

---

## New Tools (Installed 2026-05-16)

| Tool | Path/Package | Purpose |
|------|-------------|---------|
| CloakBrowser | `pip install cloakbrowser` | Stealth Chromium, bypasses bot detection |
| AgentMemory | `npm install -g @agentmemory/agentmemory` | Persistent memory engine (MCP server) |
| TradingView MCP | `pip install tradingview-mcp-server` | Real-time market data + 30+ indicators |
| TensorTrade | `pip install tensortrade` | RL trading framework |
| Supertonic TTS | `pip install supertonic` | On-device multilingual TTS (31 languages) |
| LLM Wiki | `projects/llm_wiki/` | Self-building knowledge base |
| Agent Hooks | `tools/agent-hooks/` | Pre/post tool use hooks |

---

## OCE API Endpoints

| Endpoint | Method | Purpose |
|----------|--------|---------|
| `/health` | GET | Health check |
| `/chat` | POST | Continuity chat |
| `/observers` | GET | List observers |
| `/observers/{id}` | GET/POST/DELETE | Observer CRUD |
| `/observers/{id}/health` | GET | Observer health |
| `/observers/{id}/activate` | POST | Activate observer |
| `/observers/{id}/suspend` | POST | Suspend observer |
| `/events` | GET | Query event history |
| `/events/ingest` | POST | Ingest event |
| `/events/stats` | GET | Event statistics |
| `/events/types` | GET | List event types |
| `/events/persistence/stats` | GET | Persistence statistics |
| `/events/persistence/compress` | POST | Compress old events |
| `/topology/stats` | GET | Topology statistics |
| `/topology/edge` | POST | Update coupling weight |
| `/memory` | GET | Memory view |
| `/memory/store` | POST | Store memory entry |
| `/memory/search` | GET | Search memories |
| `/memory/timeline/{id}` | GET | Observer timeline |
| `/memory/compress` | POST | Compress memory layer |
| `/memory/export` | GET | Export as wiki markdown |
| `/memory/stats` | GET | Memory statistics |
| `/attractor` | GET | Attractor state |
| `/health/srrs` | GET | SRRA-OPH substrate health |
| `/ws/events` | WS | Real-time event stream |
| `/ws/observers` | WS | Real-time observer updates |

---

## Key Config Files

| File | Purpose |
|------|---------|
| `~/.openclaw/openclaw.json` | OpenClaw gateway config |
| `config/tradingview-mcp.json` | TradingView MCP config |
| `~/.agentmemory/.env` | AgentMemory config |

---

## Ports

| Port | Service |
|------|---------|
| 18789 | OpenClaw gateway (OC1) |
| 18790 | OpenClaw gateway (OC2, primary) |
| 3000 | OCE frontend (Next.js) |
| 8000 | OCE backend (FastAPI) |
| 8001 | Desktop control API |
| 3111 | AgentMemory server |
| 3113 | AgentMemory viewer |

---

## Agent Registry

| Tag | Agent | Status | Progress File |
|-----|-------|--------|---------------|
| 🔵 CC | Claude Code | Active | `progress/claude-code-progress.md` |
| 🟣 OC | OpenClaw | Active | `progress/openclaw-progress.md` |
| 🟠 OC2 | OpenClaw 2 | Active | `progress/openclaw-2-progress.md` |
| 🟡 AS | Assistant Manager | Active | `progress/assistant-progress.md` |
| 🔴 PM | Polymorph | Active | `progress/polymorph-progress.md` |
| 🟢 RL | OWL (Research Lead) | **OPERATOR** | `progress/rl-progress.md` |

---

## Sub-Agent Governance

- **Max concurrent**: 5
- **Max runtime**: 15 minutes (soft limit)
- **Cannot spawn sub-agents**: No recursive proliferation
- **Must report to team-chat**: Tag entries with `[Sub-*]`
- **See**: `SUB_AGENT_RULES.md` for complete rules

---

## Operator Rules

- **See**: `OPERATOR_RULES.md` for complete rules
- **Core principle**: Bounded sovereign operational continuity
- **Not**: Unrestricted autonomy, mythologized digital entity

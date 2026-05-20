# TOOLS.md — Larger-Lab Tool Reference

> **Last Updated:** 2026-05-20
> **Purpose:** Quick reference for all tools, paths, and configurations

---

## Table of Contents

1. [Workspace Paths](#workspace-paths)
2. [Operator Control Tools](#operator-control-tools)
3. [System Tools](#system-tools)
4. [Agent Environment Tools](#agent-environment-tools)
5. [Validation & Monitoring Tools](#validation--monitoring-tools)
6. [External Tool Integrations](#external-tool-integrations)
7. [OCE API Endpoints](#oce-api-endpoints)
8. [Key Config Files](#key-config-files)
9. [Ports](#ports)
10. [Agent Registry](#agent-registry)

---

## Workspace Paths

| Path | Purpose |
|------|---------|
| `C:\Users\wifik\Desktop\projects\larger-lab` | Main workspace root |
| `oce/` | Operator Continuity Engine (V3 cognitive field) |
| `oce/backend/` | FastAPI backend (main.py, event_fabric.py, observer_runtime.py, structural_memory.py) |
| `oce/backend/<phase>/` | Phase modules (resonance, topology, sovereign, temporal, etc.) |
| `oce/frontend/` | Next.js frontend |
| `srrs_opc/` | SRRA-OPH core (33 modules, 56 tests) |
| `tools/` | Python/JS automation tools |
| `tools/operator/` | Operator control layer (desktop, vscode, system, observer) |
| `tools/agent-hooks/` | Agent lifecycle hooks |
| `tools/scripts/` | Utility scripts |
| `skills/` | Agent skills (57 active) |
| `.agents/skills/` | Agent-specific skills (40+ trading, quant, ML, Pine) |
| `.github/skills/` | GitHub skills (docx, xlsx, pptx, pdf, etc.) |
| `archive/skills/` | Archived skills (67) |
| `docs/` | Documentation (TESTING, DEBUGGING, CODE_QUALITY, API_REFERENCE, MODULE_GUIDE) |
| `shared-conversations/` | Team chat hub |
| `progress/` | Agent sub-progress files |
| `logs/` | System logs (hermes-watchdog, oc2-monitor) |
| `config/` | Configuration files |
| `memory-bank/` | Error DB, errors-and-solutions, gateway failures |
| `system-arch/` | Architecture diagrams and change log |
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
| Terminal Cleanup | `tools/terminal_cleanup.py` | Kill stale python/node processes |
| Progress Sync | `tools/progress-sync.py` | Agent progress → memory auto-sync |
| Chat Sync | `tools/chat_sync.py` | Team chat → agent memory sync |
| Memory Sync Daemon | `tools/memory_sync_daemon.py` | Background memory tracker |
| Workspace Cleanup | `tools/workspace_cleanup.py` | Loose file detection, oversized progress cleanup |
| Self Heal | `tools/self_heal.py` | Log scanner, error classifier, auto-fixer |
| Phase Gate | `tools/phase-gate.py` | Phase transition manager (validates tests before advance) |
| CC Workflow | `tools/cc-workflow.py` | CC continuous workflow engine |
| Arch Commit | `tools/arch-commit.py` | Post-change architecture alignment review |
| Validation Gate | `tools/validation-gate.py` | Pre-deployment validation |
| Error Analyzer | `tools/analyze_errors.py` | Error pattern analysis |
| Error Logger | `tools/error_logger.py` | Structured error logging |
| OC2 Watchdog | `tools/hermes-watchdog.py` | OWL health monitor (gateway, workspace, disk) |
| OC2 Monitor | `tools/oc2-monitor.ps1` | OC2 process monitoring |
| PM V3 Monitor | `tools/pm-v3-monitor.py` | V3 phase progress monitoring |
| Safety Net | `tools/safety_net.py` | Safety boundary enforcement |
| Subagent Manager | `tools/subagent_manager.py` | Sub-agent lifecycle management |
| Task Runner | `tools/task-runner.py` | Generic task execution |
| Summarize Progress | `tools/summarize_progress.py` | LLM-based progress summarization |
| Memory Pipeline | `tools/memory_pipeline.py` | Memory processing pipeline |
| Update Memory | `tools/update_memory.py` | Memory file updater |
| Doctor | `tools/doctor.py` | System diagnostic tool |
| Health Check | `tools/syshealth.ps1` | System health PowerShell check |
| Disk Check | `tools/diskcheck.js` | Disk space monitoring |
| HB Check | `tools/hbcheck.ps1` | Heartbeat check |
| RAM Check | `tools/ramcheck.ps1` | Memory usage check |
| Server Check | `tools/check_servers.ps1` | Server status check |
| WS Info | `tools/wsinfo.ps1` | Workspace info |
| Find Files | `tools/find_files.ps1` | File search utility |
| List Python | `tools/list_python.ps1` | List Python files |
| List Reports | `tools/list_reports.ps1` | List report files |
| VS PS | `tools/vsps.ps1` | VS Code process check |

---

## Agent Environment Tools

| Tool | Path | Purpose |
|------|------|---------|
| Agent Onboarding | `tools/agent-onboarding-tool.py` | New agent setup and registration |
| Agent Hooks | `tools/agent-hooks/` | Pre/post tool use lifecycle hooks |
| Agent Hooks In Depth | `tools/agent-hooks-in-depth/` | Advanced hook patterns |
| Import Agency Agents | `tools/import_agency_agents.py` | Import agent configurations |
| Create Tool | `tools/create_tool.py` | Tool scaffolding generator |
| Hermes Workflows | `tools/hermes_workflows.py` | Hermes workflow definitions |
| Claude Hermes MCP | `tools/claude_hermes_mcp.py` | Claude-Hermes MCP bridge |
| Motus Agent | `tools/motus_agent.py` | Motus agent integration |
| Pre-Restart Hook | `tools/pre_restart_hook.py` | Pre-restart cleanup hook |
| Progress Update Hook | `tools/progress-update-hook.py` | Progress update automation |

---

## Validation & Monitoring Tools

| Tool | Path | Purpose |
|------|------|---------|
| Phase Gate | `tools/phase-gate.py` | Validates all tests pass before phase advance |
| Validation Gate | `tools/validation-gate.py` | Pre-deployment validation |
| Self Heal | `tools/self_heal.py` | Auto-detect and fix common errors |
| Self Heal Safety | `tools/self_heal_safety.py` | Safety-constrained self-healing |
| Self Surgery | `tools/self_surgery.py` | Advanced self-repair |
| Safety Net | `tools/safety_net.py` | Safety boundary enforcement |
| Error Analyzer | `tools/analyze_errors.py` | Error pattern analysis |
| Error Logger | `tools/error_logger.py` | Structured error logging |
| Arch Commit | `tools/arch-commit.py` | Architecture alignment review |
| Test OCE Import | `tools/test_oce_import.py` | OCE import validation |
| Fix Phase Gate | `tools/fix-phase-gate.py` | Phase gate repair |
| Fix RL Progress | `tools/fix_rl_progress.py` | RL progress file repair |
| V3 Cleanup | `tools/v3-cleanup.ps1` | V3 temporary file cleanup |
| Overnight Monitor | `tools/overnight_monitor.py` | Overnight process monitoring |
| AS Monitor | `tools/as-monitor.ps1` | AS agent monitoring |
| AS Cron Check | `tools/as-cron-check.py` | AS cron job check |
| CC Cron | `tools/cc-cron.py` | CC cron job |
| RL Monitor | `tools/rl-monitor.py` | RL agent monitoring |
| TV Check | `tools/tv_check.ps1` | TradingView check |
| Check Forward Test | `tools/check_forward_test.ps1` | Forward test check |
| Check Reports | `tools/check_reports.ps1` | Report validation |

---

## External Tool Integrations

### Submodules & Cloned Projects

| Tool | Path | Purpose |
|------|------|---------|
| CLI-Anything | `tools/CLI-Anything/` | Agent-native CLI registry |
| TradingView MCP | `tools/tradingview-mcp/` | Real-time market data + 30+ indicators |
| TradingView MCP TV | `tools/tradingview-mcp-tv/` | TradingView MCP (TV variant) |
| TensorTrade | `tools/tensortrade/` | RL trading framework |
| LLM Wiki | `tools/llm_wiki/` | Self-building knowledge base |
| CloakBrowser | `tools/CloakBrowser/` | Stealth Chromium |
| DeepWiki Open | `tools/deepwiki-open/` | Deep wiki explorer |
| Dive into Claude Code | `tools/Dive-into-Claude-Code/` | Claude Code resources |
| UI-TARS Desktop | `tools/UI-TARS-desktop/` | UI automation |
| Video Search | `tools/video-search-and-summarization/` | Video search & summarization |
| QuantLib | `tools/QuantLib/` | Quantitative finance library |
| ArcticDB | `tools/ArcticDB/` | Columnar database |
| Supabase | `tools/supabase/` | Backend-as-a-service |
| n8n | `tools/n8n/` | Workflow automation |
| Cal.com | `tools/cal.com/` | Scheduling |
| Penpot | `tools/penpot/` | Design platform |
| Coolify | `tools/coolify/` | Self-hosted PaaS |
| Ghost | `tools/Ghost/` | Publishing platform |
| Listmonk | `tools/listmonk/` | Newsletter manager |
| Medusa | `tools/medusa/` | E-commerce framework |
| PyBloqs | `tools/PyBloqs/` | Financial report generation |
| RuView | `tools/RuView/` | Review platform |
| Netviz | `tools/netviz/` | Network visualization |
| Notebooker | `tools/notebooker/` | Notebook generation |
| Open Design | `tools/open-design/` | Design system |
| Opskat | `tools/opskat/` | Operations toolkit |
| Coral | `tools/coral/` | Coral framework |
| Streambert | `tools/streambert/` | Stream processing |
| WitR | `tools/witr/` | WITR framework |
| Ziwei Doushu | `tools/ziwei-doushu/` | Chinese astrology |
| WorldQuant Alpha101 | `tools/WorldQuant_alpha101_code/` | Alpha factors |
| Ultimate AI Engineer | `tools/Ultimate-AI-Engineer-Roadmap-2026/` | Learning roadmap |
| Personal AI Infra | `tools/Personal_AI_Infrastructure/` | AI infrastructure |
| Repowise | `tools/repowise/` | Repository management |
| AppFlowy | `tools/AppFlowy/` | Open-source Notion |
| Manim | `tools/manim/` | Mathematical animation |
| Dtale | `tools/dtale/` | Data exploration |
| Server | `tools/server/` | Server utilities |
| Scripts | `tools/scripts/` | Utility scripts |
| Bin | `tools/bin/` | Binary tools |
| Analytics | `tools/analytics/` | Analytics tools |
| Anime | `tools/anime/` | Anime utilities |
| Workspaces | `tools/workspaces/` | Workspace management |

### External Services

| Service | Purpose |
|---------|---------|
| OpenClaw Gateway | Agent orchestration (port 18790) |
| OCE Backend | FastAPI API (port 8000) |
| OCE Frontend | Next.js UI (port 3000) |
| AgentMemory | Persistent memory MCP (port 3111) |
| Desktop Control API | Desktop automation (port 8001) |

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
| `~/.openclaw-2/openclaw.json` | OpenClaw gateway config (OC2) |
| `config/tradingview-mcp.json` | TradingView MCP config |
| `~/.agentmemory/.env` | AgentMemory config |
| `pyproject.toml` | Python dependencies and project config |
| `.python-version` | Python version pinning |
| `.agent-tags.json` | Agent registry |
| `.phase-state.json` | Phase tracking state |
| `CLAUDE.md` | 12-rule behavioral contract |
| `OPERATOR_RULES.md` | Operator governance rules |

---

## Ports

| Port | Service |
|------|---------|
| 18790 | OpenClaw gateway (OC2, primary) |
| 3000 | OCE frontend (Next.js) |
| 8000 | OCE backend (FastAPI) |
| 8001 | Desktop control API |
| 3111 | AgentMemory server |
| 3113 | AgentMemory viewer |

---

## Agent Registry

| Tag | Agent | Role | Progress File |
|-----|-------|------|---------------|
| 🔵 CC | Claude Code | Overseer / Architecture | `progress/claude-code-progress.md` |
| 🟠 OC2 | OWL (OpenClaw 2) | Primary Operator / Orchestrator | `progress/openclaw-2-progress.md` |
| 🟡 AS | Assistant Manager | Context Monitoring / Quality | `progress/assistant-progress.md` |
| 🔴 PM | Polymorph (Hawk) | Debugger / Tool Builder | `progress/polymorph-progress.md` |
| 🟢 RL | OWL (Research Lead) | Research / DSPy | `progress/researcher-progress.md` |

---

## Sub-Agent Governance

- **Max concurrent:** 5
- **Max runtime:** 15 minutes (soft limit)
- **Cannot spawn sub-agents:** No recursive proliferation
- **Must report to team-chat:** Tag entries with `[Sub-*]`
- **See:** `SUB_AGENT_RULES.md` for complete rules

---

## Operator Rules

- **See:** `OPERATOR_RULES.md` for complete rules
- **Core principle:** Bounded sovereign operational continuity
- **MAD Directive:** OWL is an ORCHESTRATOR, not an execution work horse
- **Not:** Unrestricted autonomy, mythologized digital entity, execution worker

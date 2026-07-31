# Codemap

> Category: doctrine | Imported: 2026-06-02 01:13 UTC

Tags: #doctrine

# 🗺️ CODEMAP — Complete Workspace Reference

> **Last Updated:** 2026-06-01
> **Version:** 2.0 (Post-Reorganization)

---

## Quick Reference

| System | Port | Status | Description |
|--------|------|--------|-------------|
| OC2 Gateway | 18790 | ✅ | OpenClaw agent gateway (Telegram) |
| Hermes Gateway | 8642 | ✅ | Hermes agent gateway (Discord) |
| OCE Backend | 8000 | ✅ | FastAPI + WebSocket server |
| SRRA-OPH API | 8001 | ✅ | Observer substrate API |
| OCE Frontend | 3000 | ✅ | Next.js React dashboard |
| Sniper Dashboard | 3001 | ✅ | Trading dashboard |
| Gateway Watchdog | — | ✅ | Python auto-restart monitor |

---

## Directory Structure

```
larger-lab/
├── docs/                          # All documentation
│   ├── architecture/              # System architecture docs
│   │   ├── SYSTEM_ARCHITECTURE.md
│   │   ├── V3_COGNITIVE_FIELD.md
│   │   └── ALL_MERMAID_GRAPHS.md  # All Mermaid diagrams (40+)
│   ├── plans/                     # Project plans & roadmaps
│   │   ├── observer-core/
│   │   └── oce-unified/
│   ├── reference/                 # API refs, debugging, testing
│   │   ├── CODEMAP.md            # This file
│   │   ├── API_REFERENCE_SUMMARY.md
│   │   ├── MODULE_GUIDE_SUMMARY.md
│   │   └── DEBUGGING.md
│   └── meta/                      # Behavioral contracts
│       ├── AGENTS.md
│       ├── CLAUDE.md
│       ├── PRINCIPLES.md
│       ├── SOUL.md
│       ├── IDENTITY.md
│       ├── USER.md
│       └── SUB_AGENT_RULES.md
├── memory/                        # All memory/knowledge
│   ├── memories/                  # Session-based memory
│   ├── memory-bank/               # Self-heal state
│   ├── obsidian-vault/            # Full Obsidian vault (64 .md files)
│   │   ├── agents/
│   │   ├── architecture/
│   │   ├── doctrine/
│   │   ├── execution/
│   │   ├── failures/
│   │   ├── graphs/
│   │   ├── heuristics/
│   │   ├── journals/
│   │   ├── memory/
│   │   ├── ontology/
│   │   ├── routing/
│   │   └── skills/
│   ├── .dreams/
│   └── archive/
├── core/                          # Core system modules
│   ├── observer/                  # Observer runtime
│   │   ├── chat_log.py
│   │   └── continuity_memory.py
│   ├── persistent_field/          # O-7 Persistent Field
│   │   ├── recovery_persistence.py
│   │   ├── runtime_health.py
│   │   └── dormant_state.py
│   ├── execution/                 # Execution engine
│   │   └── journal.py
│   ├── skills/                    # Skill system
│   │   └── loader.py
│   ├── consensus/                 # O-2 Consensus
│   ├── spawn/                     # O-3 Spawn Engine
│   ├── learning/                  # O-4 Field Learning
│   ├── observability/             # Observability layer
│   ├── response/                  # Response builder
│   ├── semantic/                  # Semantic memory
│   ├── topology/                  # Topology engine
│   └── utils/                     # Utility functions
│       ├── data_fetcher.py
│       ├── indicators.py
│       └── metrics.py
├── oce/                           # Operator Continuity Engine
│   ├── backend/                   # FastAPI server
│   │   ├── main.py               # App entry (30+ imports)
│   │   ├── vault_api.py          # Vault API endpoints (19 routes)
│   │   ├── persistent_field_api.py
│   │   └── substrate/            # Substrate layer
│   └── frontend/                  # Next.js app
│       ├── components/           # React components
│       ├── stores/               # Zustand stores
│       └── pages/                # App pages
├── srrs_opc/                      # SRRA-OPH Substrate
│   ├── frontend/                  # Observatory frontend
│   │   ├── api_server.py         # FastAPI (port 8001)
│   │   └── components/           # Cytoscape graphs
│   └── constraint_propagator.py
├── quant-lab/                     # Quantitative trading
│   ├── engines/                   # Strategy engines
│   │   ├── symmetry_trap.py      # Symmetry Trap (Engine B)
│   │   ├── p90_engine_dmr.py     # P90 Kinetic Engine
│   │   └── dmr_standalone_backtest.py
│   ├── strategies/                # Strategy implementations
│   │   └── dmr_strategy.py
│   ├── backtests/                 # Backtest results
│   │   ├── naut_dmr_backtest.py
│   │   └── run_naut_backtest.py
│   ├── reports/                   # Generated reports
│   ├── data/                      # Market data
│   └── mt5/                       # MetaTrader 5 integration
│       ├── dmr_executor.py
│       ├── dmr_monitor.py
│       └── symmetry_trap_executor.py
├── tradovate/                     # NinjaTrader 8 + Tradovate
│   ├── CEREBUS_ST_NT8.cs         # Symmetry Trap NinjaScript
│   ├── CEREBUS_P90_NT8.cs        # P90 NinjaScript
│   ├── CEREBUS_BacktestHarness.cs
│   ├── CEREBUS_DeployConfig.json
│   └── CEREBUS_TradeCopier.cs
├── crypto/                        # Crypto execution
├── sniper-dashboard/              # Trading dashboard (Next.js)
│   ├── src/app/                   # App pages
│   │   ├── page.tsx              # Overview
│   │   ├── strategies/page.tsx
│   │   ├── trades/page.tsx
│   │   ├── backtests/page.tsx
│   │   └── health/page.tsx
│   └── api/                       # FastAPI backend (port 8090)
├── experiments/                   # R&D experiments
│   ├── codegraph/                 # Code topology analysis
│   ├── hybrid/                    # Hybrid experiments
│   ├── phase11/                   # Phase 11 test results
│   │   ├── test1/entropy_trace.py
│   │   ├── test2/continuity_persistence.py
│   │   └── test3/consensus_tests.py
│   ├── research/                  # Research notes
│   │   ├── RA_GAP_ANALYSIS.md
│   │   └── RESOURCE_INDEX.md
│   ├── agent-lab/                 # Agent experiments
│   │   ├── agents/hermes/         # Hermes agent config
│   │   ├── coordinator/
│   │   └── shared/
│   └── turbovec/                  # TurboVec experiments
├── tests/                         # All tests
│   ├── test_observer/             # Observer tests
│   ├── stability/                 # Stability test results
│   │   ├── chaos_results/
│   │   └── reports/
│   └── test_*.py                  # Unit tests
├── tools/                         # Utility scripts
│   ├── gateway_watchdog.py        # OC2+Hermes auto-restart
│   ├── terminal_cleanup.py        # Stale process cleaner
│   ├── progress-sync.py           # Agent progress sync
│   ├── obsidian_access.py         # Vault read/write
│   └── analyze_errors.py          # Error analysis
├── config/                        # Configuration
│   ├── REPOS.md                   # Repository registry
│   └── WORKSPACE_TOOLS_AND_SKILLS.md
├── skills/                        # Agent skills
│   ├── vectorbt-expert/
│   ├── pine-developer/
│   ├── pine-debugger/
│   ├── fastapi-python/
│   └── ...
├── shared-conversations/          # Team communication
│   ├── team-chat.md               # Main team chat
│   ├── team-chat-archive-*.md     # Archived chats
│   └── prompts/                   # Agent prompts
├── progress/                      # Agent progress tracking
│   ├── BUILD-NOTES.md
│   ├── TEAM-NOTES.md
│   ├── phase-11-status.md
│   ├── assistant-progress.md
│   ├── assistant-memory.md
│   └── *-progress.md              # Per-agent progress
├── logs/                          # System logs
├── data/                          # Data files
│   └── observer/                  # Observer data
│       ├── ontology/              # Ontology definitions
│       └── notes/                 # Obsidian notes
├── archive/                       # Archived files
│   ├── .openclaw-old/             # Old OpenClaw config
│   ├── shared-old/                # Old shared dir
│   ├── plans-original/            # Original plans dir
│   ├── system-arch-original/      # Original system-arch dir
│   ├── memories-*/                # Original memory dirs
│   ├── research-*/                # Original research dir
│   ├── agent-lab-*/               # Original agent-lab dir
│   ├── tasks-*/                   # Original tasks dir
│   └── stability-*/               # Original stability dir
├── .github/                       # GitHub config
│   ├── skills/                    # GitHub skills
│   └── workflows/                 # CI/CD workflows
├── .hermes/                       # Hermes agent config
│   ├── MEMORY.md
│   ├── SOUL.md
│   ├── cron/jobs.json
│   └── skills/
├── .openclaw-2/                   # OpenClaw config
│   ├── openclaw.json
│   ├── gateway.cmd
│   └── skills/
├── .venv/                         # Python virtual environment
├── .agents/                       # Agent definitions
├── .claude/                       # Claude config
├── .cursor/                       # Cursor config
├── .pytest_cache/                 # Pytest cache
├── .roo/                          # Roo config
├── .worktrees/                    # Git worktrees
├── pyproject.toml                 # Python project config
├── requirements.txt               # Python dependencies
├── uv.lock                        # UV lock file
├── .gitignore                     # Git ignore rules
├── .env                           # Environment variables
├── .agent-tags.json               # Agent tags
├── .chat-sync-counters.json       # Chat sync state
├── .phase-state.json              # Phase state
├── .progress-sync-counters.json   # Progress sync state
├── .python-version                # Python version
├── .clinerules                    # Claude rules
├── .memory-sync-daemon.pid        # Memory sync PID
├── .memory-sync-daemon.status.json
├── README.md                      # Project readme
└── MEMORY.md                      # Long-term memory
```

---

## Key Files by Category

### Architecture & Design
| File | Description |
|------|-------------|
| `docs/architecture/SYSTEM_ARCHITECTURE.md` | 5-level system architecture |
| `docs/architecture/V3_COGNITIVE_FIELD.md` | V3 cognitive field theory |
| `docs/architecture/ALL_MERMAID_GRAPHS.md` | All 40+ Mermaid diagrams |
| `docs/reference/CODEMAP.md` | This file |
| `docs/reference/MODULE_GUIDE_SUMMARY.md` | 78 module reference |
| `docs/reference/API_REFERENCE_SUMMARY.md` | All API endpoints |

### Agent Configuration
| File | Description |
|------|-------------|
| `docs/meta/AGENTS.md` | Team roster & rules |
| `docs/meta/CLAUDE.md` | Claude behavioral contract |
| `docs/meta/PRINCIPLES.md` | Foundational principles |
| `docs/meta/SOUL.md` | Agent personality |
| `docs/meta/IDENTITY.md` | Agent identity |
| `docs/meta/USER.md` | User profile |
| `docs/meta/SUB_AGENT_RULES.md` | Subagent rules |
| `.hermes/MEMORY.md` | Hermes memory |
| `.hermes/SOUL.md` | Hermes personality |
| `.openclaw-2/openclaw.json` | OC2 config |

### Progress & Status
| File | Description |
|------|-------------|
| `progress/BUILD-NOTES.md` | Build history |
| `progress/TEAM-NOTES.md` | Team notes |
| `progress/phase-11-status.md` | Phase 11 status |
| `progress/assistant-progress.md` | Assistant progress |
| `progress/hermes-progress.md` | Hermes progress |
| `progress/owl-progress.md` | OWL progress |

### Core Systems
| File | Description |
|------|-------------|
| `core/observer/continuity_memory.py` | Observer continuity |
| `core/persistent_field/*.py` | O-7 Persistent Field (12 modules) |
| `core/execution/journal.py` | Execution journal |
| `core/skills/loader.py` | Skill loader |
| `core/consensus/*.py` | O-2 Consensus engine |
| `core/spawn/*.py` | O-3 Spawn engine |
| `core/learning/*.py` | O-4 Field Learning |

### Trading Systems
| File | Description |
|------|-------------|
| `quant-lab/engines/symmetry_trap.py` | Symmetry Trap engine |
| `quant-lab/engines/p90_engine_dmr.py` | P90 Kinetic engine |
| `quant-lab/strategies/dmr_strategy.py` | DMR strategy |
| `tradovate/CEREBUS_ST_NT8.cs` | NT8 Symmetry Trap |
| `tradovate/CEREBUS_P90_NT8.cs` | NT8 P90 Engine |
| `sniper-dashboard/` | Trading dashboard |

### Sniper / CARE
| File | Description |
|------|-------------|
| `quant-lab/sniper/care_engine.py` | CARE engine |
| `quant-lab/sniper/firm_scanner.py` | Prop firm scanner |
| `quant-lab/sniper/pes_calculator.py` | PES calculator |
| `quant-lab/sniper/ff_protocol.py` | F&F protocol |
| `quant-lab/sniper/ff_matrix.py` | F&F matrix |
| `quant-lab/sniper/structural_decay_monitor.py` | Decay monitor |
| `quant-lab/sniper/self_healing_telemetry.py` | Self-healing telemetry |
| `quant-lab/sniper/risk_litigator.py` | Risk litigator |

### Tools & Utilities
| File | Description |
|------|-------------|
| `tools/gateway_watchdog.py` | OC2+Hermes auto-restart |
| `tools/terminal_cleanup.py` | Stale process cleaner |
| `tools/progress-sync.py` | Agent progress sync |
| `tools/obsidian_access.py` | Vault read/write |
| `tools/analyze_errors.py` | Error analysis |

### Frontend
| File | Description |
|------|-------------|
| `oce/frontend/` | OCE Next.js app (:3000) |
| `srrs_opc/frontend/` | SRRA-OPH Observatory (:3001) |
| `sniper-dashboard/` | Trading dashboard (:3001) |

---

## Mermaid Diagram Index

All Mermaid diagrams are in `docs/architecture/ALL_MERMAID_GRAPHS.md`. Key diagrams:

| # | Diagram | Section |
|---|---------|---------|
| 1 | Master System Architecture (5-Level) | System Architecture |
| 2 | Agent Communication Flow | System Architecture |
| 3 | Full Agent Roster & Relationships | Agent Topology |
| 4 | Task Lifecycle Flow | Agent Topology |
| 5 | Observer Core O-1→O-7 Pipeline | Observer Core |
| 6 | O-1 State Machine | Observer Core |
| 7 | O-2 Consensus Engine | Observer Core |
| 8 | O-3 Spawn Engine Lifecycle | Observer Core |
| 9 | OCE Component Architecture | OCE Frontend |
| 10 | OCE Data Flow | OCE Frontend |
| 11 | Cognitive Filesystem Foundation | O2C Pipeline |
| 12 | Obsidian Cognitive Mesh | O2C Pipeline |
| 13 | Capital Allocation Flow | CARE Engine |
| 14 | F&F Fragmentation Matrix | CARE Engine |
| 15 | Dynamic Risk Gate | Risk Litigator |
| 16 | PROP vs KELLY Toggle | Risk Litigator |
| 17 | Asset Integrity Evaluation | Decay Monitor |
| 18 | Decay State Machine | Decay Monitor |
| 19 | Execution Feedback Loop | Telemetry |
| 20 | Venue Switch Logic | Telemetry |
| 21 | NinjaScript Strategy Pipeline | Tradovate |
| 22 | Symmetry Trap State Machine | Tradovate |
| 23 | Gear Shift Detection | Tradovate |
| 24 | Crypto Atomic Engine Pipeline | Crypto |
| 25 | Spawn Engine + Context Inheritance | Spawn Engine |
| 26 | Agent Lifecycle | Spawn Engine |
| 27 | Observer Consensus + Task Routing | Consensus |
| 28 | Routing Map | Consensus |
| 29 | Learning Loop | Field Learning |
| 30 | O-7 Persistent Field Mode | Persistent Field |
| 31 | Workspace Directory Structure | Workspace |
| 32 | Service Ports & Health | Services |
| 33 | Complete File Inventory | Inventory |

---

## Test Status

| Suite | Tests | Status |
|-------|-------|--------|
| V3 Phases 1-10 | 1460 | ✅ PASS |
| SRRA-OPH | 57 | ✅ PASS |
| OCE | 1403 | ✅ PASS |
| Observer Core O-1→O-7 | All phases | ✅ Complete |
| Phase 11 Short-Run | 38/38 | ✅ PASS |
| Phase 11.1-B 72h | PAUSED | ⏳ Awaiting operator |

---

## Recent Commits

| Commit | Description |
|--------|-------------|
| `ca432549b` | Workspace reorganization: consolidate dirs, sync vault, update configs |
| `a4809d51d` | Previous state |

---

> **Note:** This CODEMAP is maintained by OWL. For the latest version, check `docs/reference/CODEMAP.md`.
> For all Mermaid diagrams, see `docs/architecture/ALL_MERMAID_GRAPHS.md`.

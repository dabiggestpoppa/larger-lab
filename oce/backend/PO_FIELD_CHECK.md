# PO Field Check — Backend Architecture Audit

> **Date:** 2026-06-12
> **Scope:** `oce/backend/` post-cleanup audit
> **Status:** 492/492 tests passing

---

## 1. Backend Module Inventory

### Core Infrastructure (always loaded)
| Module | Role | Wired? |
|--------|------|--------|
| `main.py` | FastAPI app, 30+ imports, startup/shutdown | ✅ Entry point |
| `event_fabric.py` | Event bus (EventFabric, TopologicalRouter, EventPersistence) | ✅ Used everywhere |
| `observer_runtime.py` | Observer lifecycle, health, state machine | ✅ Used by topology |
| `structural_memory.py` | SQLite memory (MemoryEntry, MemoryLayer, MemoryStats) | ✅ Used by PO, vault |
| `drift_detector.py` | Performance drift detection (latency, error, throughput) | ✅ Used by execution |
| `metrics_collector.py` | System metrics aggregation | ✅ Used by API |
| `tracing_engine.py` | Distributed tracing | ✅ Used by execution |
| `alerting_engine.py` | Alert management (AlertSeverity, rules) | ✅ Used by API |
| `telemetry.py` | Telemetry emission | ✅ Used by PO idle |
| `rate_limit_tracker.py` | API rate limit tracking | ✅ Used by PO API |

### API Layer (registered via `register_*_endpoints`)
| Module | Endpoints | Status |
|--------|-----------|--------|
| `topology_api.py` | `/topology/*` (collar, BSP, resonance, glyph) | ✅ Active |
| `resonance_api.py` | `/resonance/*` | ✅ Active |
| `reconstruction_api.py` | `/reconstruction/*` | ✅ Active |
| `sovereign_api.py` | `/sovereign/*` | ✅ Active |
| `governance_api.py` | `/governance/*` | ✅ Active |
| `execution_api.py` | `/execution/*` | ✅ Active |
| `persistent_field_api.py` | `/api/persistent-field/*` (12 endpoints) | ✅ Active |
| `vault_api.py` | `/vault/*` (14 endpoints) | ✅ Active |
| `ml_api.py` | `/api/v1/ml/*` (5 endpoints) | ✅ Active |
| `research_api.py` | `/api/research/*` (8 endpoints) | ✅ Active |
| `phase4_api.py` | `/api/v1/phase4/*` | ✅ Active |
| `po_api.py` | `/api/po/*` (chat, status, context) | ✅ Active |
| `po_tools_api.py` | `/api/po/tools/*` | ✅ Active |

### PO Subsystem (Persistent Observer)
| Module | Role | Status |
|--------|------|--------|
| `po_session.py` | Session continuity (disk-persisted, no expiry) | ✅ Wired |
| `po_state.py` | Global state snapshot (cognitive load, queue depth) | ✅ Wired |
| `po_idle.py` | Adaptive background tick (60s/300s/900s) | ✅ Wired in main.py startup |
| `po_stream.py` | 5-stage cognitive streaming pipeline | ✅ Wired in po_api |
| `po_vault.py` | Vault retriever (structural_memory + event_fabric) | ✅ Wired |
| `po_workspace.py` | Workspace scanner (files, patterns, TODOs) | ✅ Wired |
| `po_agents.py` | Sub-agent coordination (analyst, researcher, coder) | ✅ Wired |
| `po_fallback.py` | Multi-provider fallback chain (OpenRouter → Ollama) | ✅ Wired |
| `po_capabilities.py` | Tool execution engine (file, git, shell, search) | ✅ Wired |
| `po_tool_registry.py` | Dynamic tool discovery (10 categories) | ✅ Wired |
| `po_events.py` | Canonical event schema (8 event types) | ✅ Wired |
| `po_router.py` | PO request routing | ✅ Wired |
| `po_interrupt.py` | PO interrupt handling | ✅ Wired |
| `po_mcp_client.py` | MCP server tool bridge | ✅ Wired |

### SRRA-OPH Substrate
| Module | Role | Status |
|--------|------|--------|
| `srrs_adapter.py` | Bridges OCE ↔ SRRA-OPH (observers, consensus, spawn) | ✅ Wired |
| `resonance/` | Resonance engine (SignalPacket, CoherenceEngine, BoundaryMapper) | ✅ Used by topology_api |
| `reconstruction/` | AttractorMemory, CausalGeometry, ContinuityRepair | ✅ Used by topology_api |
| `topology/` | CollarField, BSP Projection, ResonanceRouter, GlyphEngine | ✅ Used by topology_api |
| `sovereign/` | Tool embodiment, shell runtime, model router, executive router | ✅ Used by sovereign_api |
| `substrate/` | Local runtime, filesystem, terminal, sandbox, recovery | ✅ Used by substrate_api |

### DSPy Pipelines
| Module | Role | Status |
|--------|------|--------|
| `dspy_pipelines.py` | Pipeline manager | ✅ Wired |
| `dspy_event_classifier.py` | Event classification | ✅ Wired |
| `dspy_event_router.py` | Event routing | ✅ Wired |
| `dspy_execution_optimizer.py` | Execution optimization | ✅ Wired |
| `dspy_observer_config.py` | Observer config | ✅ Wired |
| `dspy_observer_repair.py` | Observer repair | ✅ Wired |
| `dspy_resonance.py` | Resonance scoring | ✅ Wired |

### Economics & Governance
| Module | Role | Status |
|--------|------|--------|
| `economics_engine.py` | Resource economics, budget tracking | ✅ Wired |
| `governance_engine.py` | Proposal management, voting | ✅ Wired |
| `consensus_engine.py` | Consensus protocol | ✅ Wired |
| `coevolution_protocol.py` | Multi-agent coevolution, trust levels | ✅ Wired in main.py |
| `sync_cost_optimizer.py` | Sync cost optimization | ✅ Wired |
| `adaptive_compression.py` | Adaptive compression | ✅ Wired |

### Standalone / Utility
| Module | Role | Status |
|--------|------|--------|
| `oc2_gateway.py` | WebSocket gateway (standalone process) | ✅ Separate process |
| `command_center.py` | Command center router | ✅ Wired |
| `vault_sync.py` | Vault ↔ graph sync | ✅ Wired |
| `requirements.txt` | Python dependencies | ✅ |

---

## 2. Issues Found

### 🔴 CRITICAL: None
All critical import issues resolved. All `from core.*` imports resolve to real modules.

### 🟡 MODERATE

**2.1 — `test_observer_runtime.py` has broken imports**
- Uses `from observer_runtime import ...` (absolute) which fails when run as part of package
- Root cause: `observer_runtime.py` uses relative imports internally (`from .event_fabric import ...`)
- Fix: Requires refactoring `observer_runtime.py` to use absolute imports, or running test with `PYTHONPATH` set
- Impact: 1 test file excluded from CI (`--ignore=oce/backend/tests/test_observer_runtime.py`)

**2.2 — `persistent_field_api.py` endpoints all return `{"status": "unavailable"}` on error**
- All 12 endpoints wrap imports in `try/except` that silently returns error JSON
- This means if `core.persistent_field` modules have any issue, the API returns 200 OK with error body
- Should return proper HTTP error codes (503) for unavailable services

**2.3 — `po_agents.py` AgentCoordinator falls back to simulated responses**
- When `core.observer.po_agent.POAgent` is available, it works
- When unavailable, returns `f"[{best_agent.name}] {task.prompt}"` — just echoes the prompt
- This is acceptable for resilience but could mask real failures

**2.4 — `vault_api.py` has 14 `from core.obsidian.*` imports, all in try/except**
- If Obsidian vault modules are unavailable, vault API silently degrades
- No logging of which specific module failed

### 🟢 MINOR

**2.5 — `srrs_adapter.py` has module-level `from core.*` imports (lines 38-58)**
- ~~These are NOT wrapped in try/except~~ ✅ **FIXED:** Now wrapped in try/except with `logger.warning()` and None fallbacks
- Server starts even if individual core modules are temporarily unavailable

**2.6 — `research_api.py` has module-level try/except for `core.research.*`**
- During initial build, these may not exist yet
- Gracefully degrades with `None` placeholders

**2.7 — Duplicate `GraphStore` import**
- `vault_sync.py:50` and `research_api.py:32` both import `from core.research.distillation.graph_store import GraphStore`
- Not a bug, but indicates shared dependency that could be centralized

---

## 3. Architecture Health Score

| Category | Score | Notes |
|----------|-------|-------|
| Import integrity | 9/10 | All `core.*` imports resolve; 1 broken test file |
| API coverage | 10/10 | 12 API modules, all registered in main.py |
| PO subsystem | 9/10 | All 14 PO modules wired; fallback chain works |
| Test coverage | 9/10 | 492 passing; 1 pre-existing broken test excluded |
| Error handling | 7/10 | Silent degradation in persistent_field and vault APIs |
| Code cleanliness | 9/10 | No orphaned modules; no TODO/FIXME in production code |
| **Overall** | **89/100** | **Solid. Minor error handling improvements needed.** |

---

## 4. Recommendations (Priority Order)

1. **Fix `test_observer_runtime.py`** — Refactor to use proper package imports or add conftest.py with sys.path
2. **Add proper HTTP error codes** in `persistent_field_api.py` — return 503 instead of 200 with error body
3. **Add logging** to `vault_api.py` try/except blocks — log which Obsidian module failed
4. **Centralize `GraphStore` import** — create a shared utility or lazy-import helper
5. **Add health check endpoint** that validates all `core.*` imports are resolvable

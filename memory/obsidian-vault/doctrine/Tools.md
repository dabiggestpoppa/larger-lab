# Tools

> Category: doctrine | Imported: 2026-06-02 01:13 UTC

Tags: #doctrine

# TOOLS.md — Larger-Lab Tool Reference

> **Last Updated:** 2026-05-30
> **Purpose:** Quick reference for all tools, paths, and configurations
> **Policy:** Keep <10K chars. Full details in docs/ subdirectories.

---

## Workspace Essentials

| Path | Purpose |
|------|---------|
| `C:\Users\wifik\Desktop\projects\larger-lab` | Main workspace root |
| `oce/` | Operator Continuity Engine (V3 cognitive field) |
| `oce/backend/` | FastAPI backend (main.py, event_fabric.py, observer_runtime.py) |
| `srrs_opc/` | SRRA-OPH core (33 modules, 56 tests) |
| `quant-lab/` | CEREBUS FX system (engines, strategies, mt5, backtests, data) |
| `quant-lab/QUANTLAB_BIBLE.md` | **📖 LIVING BIBLE** — single navigation hub connecting ontology → engines → configs → reports → optimization |
| `quant-lab/sniper/` | **Prop Firm Sniper Engine v1.0** (7 modules, PES calculator, scope CLI) |
| `quant-lab/ontology/` | CEREBUS ontology suite (7 files) |
| `quant-lab/knowledge/` | Domain docs (sniper plan, payout systems) |
| `quant-lab/reports/INDEX.md` | Master report index (19 assets, groups, multi-asset) |
| `tools/` | Python/JS automation tools |
| `skills/` | Agent skills (57 active) |
| `docs/` | Documentation (TESTING, DEBUGGING, API_REFERENCE, MODULE_GUIDE) |
| `shared-conversations/` | Team chat hub |
| `progress/` | Agent sub-progress files |
| `logs/` | System logs (hermes-watchdog, oc2-monitor) |
| `memory/memory-bank/` | Error DB, errors-and-solutions, gateway failures |

## Quant Lab — STRATEGY & BACKTEST (Primary Work Area)

| Path | Purpose |
|------|---------|
| `quant-lab/engines/` | **TRUTH SOURCE** — p90_engine.py, symmetry_trap.py, dmr_standalone_backtest.py. These contain the strategy logic. |
| `quant-lab/strategies/` | NautilusTrader Strategy class wrappers (dmr_strategy.py, p90_strategy.py, symmetry_trap_strategy.py) |
| `quant-lab/backtests/` | Backtest runners (naut_dmr_backtest.py, run_naut_backtest.py, run_cerebus_backtest.py) |
| `quant-lab/reports/` | Backtest results (JSON, CSV, MD reports) |
| `quant-lab/data/` | MT5 data fetchers + CSV data files (EURUSD, USDCHF M5) |
| `quant-lab/ontology/` | CEREBUS ontology suite (cerebus_dual_engine.md, cerebus_p90.md, manual_ontology.md) |
| `quant-lab/knowledge/` | Domain docs (sniper plan, payout systems) |
| `quant-lab/sniper/` | Prop Firm Sniper Engine v1.0 |
| `quant-lab/mt5/` | MT5 executors, EAs, monitors (LIVE — do NOT touch without approval) |

### Active Strategies (Two Engines)
- **P90 Kinetic Engine A**: INITIAL + CASCADE + EWS variants. CASCADE is dominant (85.4% WR)
- **Symmetry Trap Engine B**: 4-state FSM, single AU target, 91.1% WR
- **Dual-Engine Convergence**: 94-95% WR when both align

### Deprecated (DO NOT USE)
- `quant-lab/engines/dmr_standalone_backtest.py` — old standalone DMR, replaced by P90 engine
- `quant-lab/mt5/dmr_executor*.py` — old DMR live executors, we trade P90 CASCADE now
- STALL_HARVEST variant — removed from P90 enum per MAD directive

### Nautilus Backtest Architecture
- CSV engines (`quant-lab/engines/`) — GOLD STANDARD for strategy logic
- Nautilus Strategy classes (`quant-lab/strategies/`) — must replicate CSV results
- Nautilus backtest runners (`quant-lab/backtests/`) — feed data through Nautilus strategies
- **Cross-validation requirement**: Nautilus results must match CSV engine results within ~5% or something is wrong with the Nautilus setup

## Key Tools (Full list: docs/TOOLS_FULL.md)

| Tool | Path | Purpose |
|------|------|---------|
| Terminal Cleanup | `tools/terminal_cleanup.py` | Kill stale python/node processes |
| Progress Sync | `tools/progress-sync.py` | Agent progress → memory auto-sync |
| Self Heal | `tools/self_heal.py` | Log scanner, error classifier, auto-fixer |
| Phase Gate | `tools/phase-gate.py` | Phase transition manager |
| Arch Commit | `tools/arch-commit.py` | Post-change architecture alignment |
| Hermes Watchdog | `tools/hermes-watchdog.py` | OWL health monitor |
| Doctor | `tools/doctor.py` | System diagnostic + prescriptions |
| Self-Heal | `tools/self_heal.py` | OWL's own doctor — scans files, memory, behavior patterns |

## Ports

| Port | Service |
|------|---------|
| 18790 | OpenClaw gateway (OC2, primary) |
| 3000 | OCE frontend (Next.js) |
| 8000 | OCE backend (FastAPI) |
| 8001 | SRRA API |
| 8002 | DMR Dashboard |
| 3111 | AgentMemory server |

## Agent Registry

| Tag | Agent | Role | Progress File |
|-----|-------|------|---------------|
| 🔵 CC | Claude Code | Overseer / Architecture | `progress/claude-code-progress.md` |
| 🟠 OC2 | OWL | Primary Operator / Orchestrator | `progress/openclaw-2-progress.md` |
| 🟡 AS | Assistant Manager | Context Monitoring / Quality | `progress/assistant-progress.md` |
| 🔴 PM | Polymorph (Hawk) | Debugger / Tool Builder | `progress/polymorph-progress.md` |
| 🟢 RL | OWL (Research Lead) | Research / DSPy | `progress/researcher-progress.md` |

## Key Quant Lab Files
| File | Purpose |
|------|---------|
| `quant-lab/QUANTLAB_BIBLE.md` | Living reference — update after every test/optimization |
| `quant-lab/reports/INDEX.md` | Master report index |
| `quant-lab/engines/symmetry_trap.py` | ST engine (TRUTH SOURCE) |
| `quant-lab/engines/p90_engine.py` | P90 engine (TRUTH SOURCE) |
| `quant-lab/configs/asset_configs.py` | Per-asset calibration |

## Key Config Files
| File | Purpose |
|------|---------|
| `~/.openclaw-2/openclaw.json` | OpenClaw gateway config |
| `pyproject.toml` | Python dependencies and project config |
| `.agent-tags.json` | Agent registry |
| `.phase-state.json` | Phase tracking state |

## Operator Rules
- **See:** `OPERATOR_RULES.md` for complete rules
- **MAD Directive:** OWL is an ORCHESTRATOR, not an execution worker
- **Max concurrent sub-agents:** 5

---
*Updated: 2026-05-30 — Added sniper engine paths, ontology, knowledge dirs*
*Full tool list archived to: docs/TOOLS_FULL.md*

LINKS:
[[Codemap]]
[[01 System Overview]]
[[02 Agent Workflow]]
[[03 Srra Topology]]
[[04 Data And Storage]]
[[Agents]]
[[Api Reference]]
[[Cg 1 Mermaid Specs]]
[[Cg 1 Revised]]
[[Cg 2 Mermaid Specs]]
[[Cg 2 World Model Activation]]
[[Cg 3 Openclaw Anchor]]
[[Cg 3 Relational Topology]]
[[Cg 4 Execution Intelligence]]
[[Cg 4 Mermaid Specs]]
[[Cg 5 Continuity Intelligence]]
[[Cg 6 Meta Cognition]]
[[Cg 7 Multi Scale Orchestration]]
[[Cg 8 Operator Coevolution]]
[[Cg 9 Autonomous Strategic Field]]
[[Chaos Scenarios]]
[[Chat Response Bug Diagram]]
[[Cleanup Report]]
[[Code Quality]]
[[Contributing]]
[[Debugging]]
[[Domain Micro Doctrines]]
[[Harness Engineering]]
[[Heartbeat]]
[[Identity]]
[[Master Plan 2026 05 18]]
[[Master Plan Observer Core]]
[[Master Prompt]]
[[Module Guide]]
[[Observer Core Workspace State]]
[[Oce Unified Frontend Plan]]
[[O 6 Implementation Plan]]
[[O 7 Persistent Field Doc]]
[[Phase10]]
[[Phase Breakdown]]
[[Principles]]
[[Project Progress Clean]]
[[Quality Review]]
[[Quality Review Feedback]]
[[Readme]]
[[Soul]]
[[Sub Agent Rules]]
[[Team Tasks]]
[[Telegram Bot Setup]]
[[Testing]]
[[Test Manual]]
[[Topological Cognition Architecture]]
[[User]]
[[Workspace State]]
[[Cal]]
[[Examples]]
[[Server]]
[[Skill]]
[[Warm]]
[[Asset Configs]]
[[Convergence Indicator]]
[[Dmr Standalone Backtest]]
[[P90 Backtest]]
[[P90 Count Ews]]
[[P90 Dmr Backtest]]
[[P90 Dmr Combo Backtest]]
[[P90 Dmr Overlay Backtest]]
[[P90 Engine]]
[[P90 Engine Dmr]]
[[P90 Gap Check]]
[[P90 Trace Trades]]
[[P90 Usdchf Backtest]]
[[Run Majors Backtest]]
[[Run St Multi Asset]]
[[Run Top5 Backtest Mc]]
[[St Batch2 Runner]]
[[St Batch Runner]]
[[Symmetry Trap]]
[[Symmetry Trap Backtest]]
[[Symmetry Trap Monte Carlo]]
[[Memory]]
[[Atomic Sym Trap]]
[[Blind Chain Debug]]
[[Blind Chain Diag]]
[[Blind Chain Engine]]
[[Blind Chain Exact]]
[[Blind Chain V2 Debug]]
[[Blind Chain V2 Sl Calibrated]]
[[Blind Chain V3]]
[[Cerebus Resolution Engine]]
[[Constraint Anchor Engine]]
[[Debug Days]]
[[Debug One Day]]
[[Debug St]]
[[Debug Trace]]
[[Diag Option B]]
[[Diag V5]]
[[Dmr Strategy]]
[[Dual Engine]]
[[Naut Asset Config]]
[[P90 Cfd Expansion Engine]]
[[P90 Cfd Expansion Engine V2]]
[[P90 Cfd Expansion Engine V3]]
[[P90 Cfd Expansion Engine V4]]
[[P90 Cfd Expansion Engine V5]]
[[P90 Strategy]]
[[Shared]]
[[Stall Harvest Cfd Engine]]
[[Symmetry Trap Engine]]
[[Symmetry Trap Exact]]
[[Symmetry Trap Option B]]
[[Symmetry Trap Strategy]]
[[Symmetry Trap V4]]
[[Symmetry Trap V5]]
[[Symmetry Trap V6 Exact]]
[[Symmetry Trap V7B Sl Calibrated]]
[[Symmetry Trap V7 Sl Calibrated]]
[[Two Plays Engine]]

# 📖 QUANTLAB BIBLE — Living Reference
> **Last Updated:** 2026-05-31 02:30 EDT
> **DO NOT FREEZE** — every backtest, optimization, or discovery updates this file

---

## 🧭 NAVIGATION

| Section | Location | Purpose |
|---------|----------|---------|
| **Ontology** | `[[ONTOLOGY_INDEX]]` | The WHY — strategy philosophy |
| **Engines** | `[[ENGINES_INDEX]]` | The HOW — strategy code (TRUTH SOURCE) |
| **Backtest Results** | `[[BACKTEST_RESULTS]]` | The EVIDENCE — what data says |
| **Active Strategies** | `[[ACTIVE_STRATEGIES]]` | What's deployed + performance |
| **Deployment** | `[[DEPLOYMENT_STATUS]]` | What's live on broker |
| **Optimization** | `[[OPTIMIZATION_LOG]]` | Tuning history + next steps |
| **Failures** | `[[FAILURE_INDEX]]` | What broke + how fixed |
| **Team** | `[[TEAM_ROSTER]]` | Agent assignments |

---

## 1. ONTOLOGY — THE WHY

> Read first. Every line of code maps here. If code contradicts ontology, code is wrong.

- `[[ONTOLOGY_CORE]]` — Single state, AU math, time windows, 6 axioms
- `[[ONTOLOGY_P90]]` — P90 Kinetic Threshold variants
- `[[ONTOLOGY_ST]]` — Symmetry Trap 4-state FSM
- `[[ONTOLOGY_DUAL_ENGINE]]` — Dual Engine isolation + convergence
- File source: `C:\Users\wifik\Desktop\projects\larger-lab\quant-lab\CEREBUS_ONTOLOGY.md`

**Key Definitions (never contradict):**
- System: ONE — Constraint Resolution
- Engines: TWO — Kinetic (P90) + Structural (Atomic/ST)
- AU: 50% of K-Means centroid (NOT pips, NOT Fibonacci)
- P90: Kinetic Validation Threshold (NOT indicator)
- 12PM EST: Full state reset, deficits TERMINATED
- 80% Rule: Close invalidation (absolute, close-only)

---

## 2. ENGINES — THE HOW (TRUTH SOURCE)

> Engines contain strategy logic. Backtest runners just feed data through engines. Debug from engines.

Active:
- `[[ENGINE_ST]]` — Symmetry Trap (`quant-lab/engines/symmetry_trap.py`)
- `[[ENGINE_P90]]` — P90 Kinetic (`quant-lab/engines/p90_engine.py`)
- `[[ENGINE_ST_BACKTEST]]` — ST backtest wrapper (`quant-lab/engines/symmetry_trap_backtest.py`)

Deprecated:
- `dmr_standalone_backtest.py` — merged into P90 engine

---

## 3. BACKTEST RESULTS — THE EVIDENCE

> Data range: 2022-01-03 to 2026-05-29 (~4.4 years M5)

### Symmetry Trap — Full Results (19 assets)

| Asset | Trades | WR | PF | Sharpe | MaxDD | MC Ruin |
|-------|--------|----|----|--------|-------|---------|
| ETHUSD | 547 | 96.9% | 50.34 | 24.04 | 31.7p | 0.00% |
| HK50 | 385 | 94.0% | 40.30 | 20.42 | 149.7p | 0.00% |
| NZDUSD | 727 | 93.3% | 19.02 | 18.31 | 54.3p | 0.00% |
| BTCUSD | 801 | 92.6% | 26.52 | 13.00 | 785p | 0.00% |
| US500 | 372 | 91.7% | 13.95 | 12.02 | 116.8p | 0.00% |
| GBPCHF | 803 | 91.2% | 24.51 | 17.74 | 22.7p | 0.00% |
| AUDUSD | 828 | 89.3% | 18.47 | 16.73 | 23.3p | 0.00% |
| GBPAUD | 715 | 88.4% | 14.97 | 14.77 | 60.1p | 0.00% |
| GBPNZD | 664 | 88.4% | 20.87 | 15.83 | 46.2p | 0.00% |
| USDJPY | 729 | 87.8% | 16.73 | 13.76 | 42.3p | 0.00% |
| FR40 | 1,085 | 87.0% | 12.21 | 13.63 | 107.7p | 0.00% |
| CHFJPY | 751 | 86.3% | 13.01 | 11.17 | 87.5p | 0.00% |
| GBPJPY | 830 | 86.3% | 12.61 | 14.05 | 61.9p | 0.00% |
| GBPUSD | 1,259 | 85.7% | 9.23 | 11.89 | 48.5p | 0.00% |
| EURUSD | 1,163 | 85.0% | 8.57 | 11.54 | 39.2p | 0.00% |
| USDCHF | 1,153 | 84.9% | 8.87 | 11.73 | 57.6p | 0.00% |
| XAUUSD | 604 | 84.4% | 7.42 | 11.28 | 121.4p | 0.00% |
| DE30 | 1,145 | 82.8% | 9.91 | 12.02 | 134.0p | 0.00% |
| XAGUSD | 2 | 50.0% | — | — | — | — | ⚠️ FLAGGED |

### Multi-Asset Combined
- 12,488 pooled trades | 81.2% WR | PF 26.58 | Sharpe 4.72
- MC Ruin: 0.62% | Profitable sims: 99.38%

### Key Patterns
- Best hour: ~02:00 EST (activation window)
- T3 tier dominates across all assets (~90%+ WR)
- Trade count variance = by design (threshold scales with volatility)
- 82-97% WR across ALL asset classes (universal edge)
- BTC concentration: 55% of pool PnL from single asset

Full reports: `quant-lab/reports/INDEX.md`

---

## 4. ACTIVE STRATEGIES

### Symmetry Trap (Structural/Atomic Engine B)
- 4-state FSM: SEARCH → WAIT_RETRACE → WAIT_OCC → IN_TRADE
- Entry: Impulse → DZ pullback → OCC
- SL: Zero-Buffer Extreme | TP: 1 AU
- Close: Full close on 80% Kill Switch
- Config: Per-asset via `configs/asset_configs.py`

### P90 Kinetic (Kinetic Engine A)
- 4 variants: INITIAL, CASCADE, STALL_HARVEST, EWS
- CASCADE dominant (85.4% WR standalone)
- Dual entries per signal: SL at 80% and 168% of P90 body
- Cascade SL: 168% of new P90 body

### Dual-Engine Convergence
- 94-95% WR when both engines align
- Overlap = Causal Confirmation (Kinetic leads → Structural confirms)

---

## 5. DEPLOYMENT STATUS

| Executor | Symbol | Strategy | Magic | Lots | Status |
|----------|--------|----------|-------|------|--------|
| ST | EURUSD.PRO | Symmetry Trap | 20260531 | 0.03 | 🟢 Live |
| P90 | USDCHF.PRO | P90 CASCADE | 20260532 | 0.01 | 🟢 Live |

Account: Ox Securities 650898 LIVE

---

## 6. OPTIMIZATION LOG

### Completed Phases
- Phase 1: 19 individual asset reports + MC ✅
- Phase 2: 4 group reports (Majors/Crosses/Metals+Crypto/Indices) ✅
- Phase 3: Multi-asset combined ✅
- Phase 4: Master INDEX ✅
- Phase 5: Top 5 + Major 6 deep-dive ✅

### Known Issues
| Issue | Priority | Details |
|-------|----------|---------|
| XAGUSD config | HIGH | Only 2 trades — tier thresholds incompatible with silver |
| BTC concentration | MEDIUM | 55% of pool PnL — position sizing caps needed |
| Crypto correlation | MEDIUM | BTC+ETH = 58.5% of pool |

### Next Optimization Targets
- P90 multi-asset backtest (Phase 6)
- Dual-engine convergence study
- DD duration + time-in-DD metrics
- Nautilus cross-validation
- XAGUSD recalibration
- Prop firm model variants (high-risk, consistency, scaling)

---

## 7. TEAM ROSTER

| Tag | Agent | Role | Status |
|-----|-------|------|--------|
| 🔵 CC | Claude Code | Overseer / Architecture | Active |
| 🟠 OC2 | OWL | O2C Orchestrator | Active |
| 🟡 AS | Assistant Manager | Quality / Docs | Standby |
| 🔴 PM | Polymorph | Debugger / Tools | Active |
| 🟢 HR | Hermes | Nautilus Execution 24/7 | Active |
| 🟠 PM2 | Polymorph 2 | Experimental | Standby |
| 🟢 RL | Research Lead | Research / DSPy | Standby |

---

## 8. DATA INVENTORY

- M5 CSVs: 19 assets, ~200 MB total, `quant-lab/data/`
- Reports: `quant-lab/reports/` (per-asset, groups, multi-asset, top5_majors)
- Ontology: `quant-lab/ontology/` + `CEREBUS_ONTOLOGY.md`
- Engine code: `quant-lab/engines/` (TRUTH SOURCE)
- Configs: `quant-lab/configs/asset_configs.py`
- Live: `quant-lab/mt5/` (DO NOT TOUCH without MAD approval)

---

*Built by OWL 🦑 — O2C Unified Field Operator*
*Last updated: 2026-05-31 02:30 EDT*
*Source file: `quant-lab/QUANTLAB_BIBLE.md`*

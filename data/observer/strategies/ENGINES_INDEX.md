# ENGINES INDEX — Strategy Code Registry
> Linked: `[[ACTIVE_STRATEGIES]]` | `[[ONTOLOGY_CORE]]`
> TRUTH SOURCE: `quant-lab/engines/`

---

## Active Engines

### Symmetry Trap — `quant-lab/engines/symmetry_trap.py`
- **Type:** Structural/Atomic (Engine B)
- **Pattern:** 4-state FSM
- **States:** SEARCH → WAIT_RETRACE → WAIT_OCC → IN_TRADE
- **Entry:** Impulse → DZ pullback → OCC
- **SL:** Zero-Buffer Extreme | **TP:** 1 AU
- **Classes:** `SymmetryTrapEngine` (Option A/B), `BlindChainEngine` (continuous loop, max 5/session)
- **Status:** ✅ Verified — SYNTAX OK, IMPORT OK

### Symmetry Trap Backtest — `quant-lab/engines/symmetry_trap_backtest.py`
- **Type:** Backtest wrapper
- **Input:** M5 CSV data + per-asset config injection
- **Output:** Trades, equity curve, MC results
- **Status:** ✅ Active

### P90 Kinetic — `quant-lab/engines/p90_engine.py`
- **Type:** Kinetic (Engine A)
- **Entry:** Immediate close of P90 candle
- **SL:** 80% body (Entry 1), 168% body (Entry 2)
- **TP:** -25%/-50% AR
- **Status:** ✅ Verified — SYNTAX OK, IMPORT OK

### Multi-Asset Runner — `quant-lab/engines/run_st_multi_asset.py`
- **Type:** Orchestration wrapper
- **Runs:** ST backtest across all 19 assets with config injection
- **Status:** ✅ Active

---

## Nautilus Integration
- `quant-lab/strategies/` — Nautilus Strategy class wrappers
- `quant-lab/backtests/` — Nautilus backtest runners
- Cross-validation: Nautilus results must match CSV engine results within ~5%

---

## Deprecated Engines
| Engine | File | Reason |
|--------|------|--------|
| DMR Standalone | `dmr_standalone_backtest.py` | Merged into P90 engine |
| DMR Executor | `dmr_executor*.py` | Replaced by P90 CASCADE |

> **Rule:** Engines = truth source. Backtest runners feed data through engines. When debugging, start from engines.

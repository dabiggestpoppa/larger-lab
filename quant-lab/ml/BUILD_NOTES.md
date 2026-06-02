# CEREBUS ML — Build Notes
> **Started:** 2026-06-02 | **Agent:** CC (Claude Code) | **Status:** BUILDING
> **Source:** CEREBUS ML System Architecture (cerbus ml.txt)

## Architecture Decision: XGBoost + Optuna (NOT Neural Networks)

| Factor | Neural Network | XGBoost | Winner |
|--------|---------------|---------|--------|
| Tabular Data | Needs massive data | SOTA out of box | XGBoost |
| Inference Latency | 5-50ms (GPU) | <0.1ms (CPU) | XGBoost |
| Interpretability | Black box | SHAP values | XGBoost |
| Small Sample | Overfits <10k | Regularization | XGBoost |
| Determinism | Float non-determinism | Bitwise reproducible | XGBoost |
| Audit Trail | "NN said so" | Full feature importance | XGBoost |

## 3-Layer Architecture

```
Layer 1: XGBoost Regime Classifier → CONFIRMED/CAUTION/FAILED/NO-GO
Layer 2: XGBoost Entry Quality Scorer → 0.0-1.0 continuous score
Layer 3: Optuna Bayesian Optimizer → per-asset, per-regime params
```

## 5-Phase Build Plan

| Phase | Module | Status | Key Deliverables |
|-------|--------|--------|------------------|
| 1 | Data Foundation | 🔄 BUILDING | Parquet conversion, K-Means tiers, feature matrix, labels |
| 2 | Regime Classifier | ⏳ Queued | XGBoost model, SHAP analysis, confidence calibration |
| 3 | Parameter Optimizer | ⏳ Queued | Optuna multi-objective, per-regime params, Pareto front |
| 4 | Live Integration | ⏳ Queued | Nautilus bridge, friction filters, parity validation |
| 5 | Production Hardening | ⏳ Queued | Guardrail interceptor, PSI drift, shadow mode |

## Constitution (NON-NEGOTIABLE)

1. **Python only** — No NT8, no C#, no NinjaScript
2. **No Track A/B** — ONE unified pipeline
3. **Close-only SL** — M5 CLOSE beyond OCC Extreme, wicks ignored
4. **Zero-buffer OCC** — SL at exact impulse extreme
5. **Gear Shift modifies TARGET ONLY** — SL never changes
6. **12PM EST Hard Exit** — All positions close, no exceptions
7. **No online learning** — Model frozen between quarterly re-trains
8. **Fallback to hardcoded** — If XGBoost confidence < 0.6, use manual tiers

## Existing Infrastructure (Pre-Build)

| Component | Location | Status |
|-----------|----------|--------|
| Asset Configs (20 assets) | `quant-lab/configs/asset_configs.py` | ✅ Complete |
| M5 Data (19 CSVs) | `quant-lab/data/` | ✅ Available |
| Symmetry Trap Engine | `quant-lab/engines/symmetry_trap.py` | ✅ Active |
| Backtest Runner | `quant-lab/engines/symmetry_trap_backtest.py` | ✅ Active |
| Multi-Asset Runner | `quant-lab/engines/run_st_multi_asset.py` | ✅ Active |
| K-Means Code | Manual appendix only | ❌ Not implemented |
| XGBoost | Not installed | ❌ New |
| Optuna | Not installed | ❌ New |
| SHAP | Not installed | ❌ New |

## Dependencies to Add

```
xgboost>=2.0.0
lightgbm>=4.0.0
optuna>=3.5.0
shap>=0.44.0
joblib>=1.3.0
duckdb>=0.9.0
pyarrow>=14.0.0
```

## File Structure

```
quant-lab/ml/
├── __init__.py
├── BUILD_NOTES.md          ← This file
├── ML_BUILD_PLAN.md        ← Full 5-phase spec
├── phase1_data/
│   ├── __init__.py
│   ├── data_pipeline.py    ← CSV→Parquet, gap validation
│   ├── no_trash_firewall.py ← Structural validity filter
│   ├── asian_range.py      ← AR extraction 19:00-03:00 EST
│   ├── tier_discovery.py   ← K-Means k=3 clustering
│   ├── feature_matrix.py   ← Per-bar feature extraction
│   └── label_generator.py  ← Regime + quality labels
├── phase2_classifier/
│   ├── __init__.py
│   ├── regime_classifier.py ← XGBoost Layer 1
│   ├── entry_scorer.py     ← XGBoost Layer 2
│   ├── confidence_calibrator.py ← Isotonic regression
│   └── shap_analyzer.py    ← Feature importance + plots
├── phase3_optimizer/
│   ├── __init__.py
│   ├── bayesian_optimizer.py ← Optuna multi-objective
│   ├── search_spaces.py    ← Per-regime param ranges
│   ├── backtest_objective.py ← Sharpe*WR composite
│   └── robustness_check.py  ← ±10% perturbation test
├── phase4_integration/
│   ├── __init__.py
│   ├── friction_filters.py  ← Spread + time gates
│   ├── close_only_guard.py  ← Wick rejection enforcement
│   ├── nautilus_bridge.py   ← Live execution adapter
│   └── parity_validator.py  ← Backtest-to-live drift check
├── phase5_hardening/
│   ├── __init__.py
│   ├── guardrail_interceptor.py ← Pre-broker order validation
│   ├── drift_detector.py    ← PSI feature drift monitoring
│   ├── shadow_mode.py       ← Paper trading gauntlet
│   └── retraining_scheduler.py ← Quarterly retrain cadence
├── models/                  ← Serialized model artifacts
├── features/                ← Feature matrices (Parquet)
├── shap/                    ← SHAP plots + reports
├── optuna/                  ← Optuna study databases
├── configs/                 ← Optimized param JSONs
├── monitoring/              ← Grafana configs, alerts
├── validation/              ← Parity reports, benchmarks
└── tests/
    ├── __init__.py
    ├── test_phase1.py
    ├── test_phase2.py
    ├── test_phase3.py
    ├── test_phase4.py
    └── test_phase5.py
```

## Build Log

### 2026-06-02 CC — Session 2: Full Build Complete
- All 5 phase modules built (30+ Python files)
- Dependencies installed: xgboost, lightgbm, optuna, shap, joblib, duckdb, pyarrow
- Phase 1 data pipeline validated: all 19 assets converted to Parquet
- Test suite created: test_phase1.py (25+ tests)
- Team chat updated with agent assignments
- Build notes and ML build plan documented

### 2026-06-02 CC — Session Start
- Analyzed CEREBUS ML architecture document (5 phases, 3 layers)
- Confirmed greenfield: no existing XGBoost/Optuna/SHAP code
- Created `quant-lab/ml/` directory structure
- Wrote BUILD_NOTES.md and ML_BUILD_PLAN.md
- Created `quant-lab/ml/` directory structure with all 5 phase modules
- Added `__init__.py` to all packages
- Next: Build Phase 1 data pipeline

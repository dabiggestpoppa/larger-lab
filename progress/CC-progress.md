# 🔴 CC (Claude Code) — CEREBUS Neuro-Symbolic Scanner Progress

> **Agent:** CC (Claude Code)
> **Role:** Lead Builder — Steps 1-2 (Data + Features + Models)
> **Started:** 2026-06-10
> **Master Plan:** `quant-lab/ml/CEREBUS_NEURO_SYMBOLIC_SCANNER_PLAN.md`
> **Build Notes:** `quant-lab/ml/BUILD_NOTES_CEREBUS.md`

---

## Status: 🟢 WAVE 1 COMPLETE — Wave 2 Retraining with Full Features

### Wave 1 Complete ✅
| Phase | Name | Status | Details |
|-------|------|--------|---------|
| 1A | Data Cleanup | ✅ Complete | 19 assets cleaned, 3 raw sources fixed (_x0009_ encoding) |
| 1B | Macro Feature Engine | ✅ Complete | 35 macro features per bar (MLR, Fib, 132%, ILM, regime, time blocks) |
| 1D | Label Generator v2 | ✅ Complete | 18 assets labeled (5.1M samples), order-of-events tracking |

### Wave 2 In Progress 🔄
| Phase | Name | Status | Details |
|-------|------|--------|---------|
| 2A | Full Feature Engine | ✅ Complete | 41 features per bar, 18 assets, calibrated tiers from PDF |
| 2B | XGBoost Retrain | 🔄 Training | 4.2M train / 1.1M val, 41 features, TimeSeriesSplit CV |
| 2C | Entry Scorer | ⏳ Queued | After 2B complete |
| 2D | Ironclad Rules | ⏳ Queued | SHAP physics check, Wednesday test, MC ruin |

### Fixes Applied (per AS Audit)
1. ✅ **Tier/AU values corrected** — Was using K-Means (wrong, 2-3x too large). Now uses calibrated values from ST_TIERS_AND_AU.pdf
2. ✅ **Full feature engine rewritten** — `full_feature_engine.py` with ALL 58 features from BUILD.txt
3. ✅ **Dual implementation cleaned** — Removed old `macro_feature_engine.py`, `feature_matrix.py`, `label_generator.py`, `pipeline.py`
4. ✅ **String columns excluded from training** — Robust dtype check in retrain script
5. ⏳ **PM2 Pattern Recognition** — Still needs PM2 assignment clarification

### Overall Progress
| Phase | Name | Status | Agent |
|-------|------|--------|--------|
| 1A | Data Cleanup & Unification | ⏳ Queued | CC |
| 1B | Macro Feature Engine | ⏳ Queued (after 1A) | CC |
| 1C | Pattern Recognition | ⏳ Queued (parallel with 1B) | PM2 |
| 1D | Label Generator v2 | ⏳ Queued (after 1B) | CC |
| 2 | Retrain Models + Ironclad Rules | ⏳ Queued (after 1D) | CC |
| 3 | RAG Oracle | ⏳ Queued (after PM data ready) | OC2 |
| 4 | Guardian Pipeline | ⏳ Queued (after 1-3) | OC2 |

### Wave 1: Data + Features (CC leads)
- [ ] 1A: Audit raw CSVs, fix UNKNOWN entries, produce clean dataset
- [ ] 1B: Macro Feature Engine (MLR, Fib, 132%, ILM, Regime Ratio)
- [ ] 1D: Label Generator v2 (forward-looking, order-of-events)

### Wave 2: Models (CC leads)
- [ ] 2A: Feature Matrix v2 (30 features = 8 micro + 12 macro + 10 pattern)
- [ ] 2B: Retrain XGBoost Regime Classifier
- [ ] 2C: Retrain Entry Scorer
- [ ] 2D: Ironclad Rules Engine (SHAP check, Wednesday test, MC ruin)

### Existing Baseline
- 40/40 tests passing
- 18 M5 parquets in `quant-lab/ml/data/parquet/`
- 18 feature matrices in `quant-lab/ml/data/features/`
- XGBoost + entry scorer trained on 8 features (need retrain on 30)

### Blockers
- None currently. PM data extraction complete (99 files, 35MB).
- Waiting for MAD directive to begin Wave 1.

---

## Entries

#### [CC] 2026-06-10 — Planning Complete
- Created master plan: `quant-lab/ml/CEREBUS_NEURO_SYMBOLIC_SCANNER_PLAN.md`
- Created build notes: `quant-lab/ml/BUILD_NOTES_CEREBUS.md`
- Audited PM's data extraction: 99 files, 35MB, 1626 unified entries
- Identified data quality issues: 1040 UNKNOWN assets, 1066 UNKNOWN patterns
- Updated team-chat, workspace-state, PM2/Polymorph progress files
- Assigned PM2 to Phase 1C (Pattern Recognition)
- Total new code target: ~4,400 lines, 80+ tests

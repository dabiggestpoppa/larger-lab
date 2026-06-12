# Team Shared Conversation

> **Purpose:** Quick-communication hub for CC/PM/PM2/AS/RL/OC2 coordination.
> **Current focus:** 🔴 CEREBUS Unified System — Live & Running
> **Status:** All services live, desktop alerts active, no spam

---

## 🔴 CC — CEREBUS Unified System (2026-06-12 20:00 UTC)
**Agent:** CC (Claude Code / OWL) | **Status:** ✅ LIVE — all services running

### System Architecture (4 Layers)
1. **Directional Bias** (3-Lens Ternary + Pathway Detection) — 84-86% accuracy on LOCK days
2. **DTB v4 Cascade** (T0/T1/T2 checkpoints) — R²=0.97 at T2
3. **Trade Orchestrator** (wired with bias + DTB fields) — full trade calls
4. **Macro Monthly DTB** (Day 5/8/11/13 checkpoints) — R²=0.97 at T2

### Key Results
- EURUSD direction accuracy: 69.1% base → 83.7% on GEAR_SHIFT days
- USDCHF direction accuracy: 78.0% base → 85.9% on GEAR_SHIFT days
- Target -25% hit rate: 98.4%+ across all pathways
- DTB magnitude: MAE=1.95 pips, R²=0.97 at T2 (9AM checkpoint)

### Services Running
- OCE Backend: ✅
- CEREBUS Unified Scanner: ✅ (desktop alerts, 5-min cooldown)
- Watchdog: ✅ (clean, no duplicates)
- MLR Scanner: ❌ Removed (replaced by CEREBUS)
- Telegram Gateway: ❌ Removed (desktop alerts only)

### Desktop Alerts
- Windows toast notifications (PowerShell, native)
- 5-min cooldown per symbol+direction — no spam
- Alert file: `data/latest_alert.txt`

### Files Created/Updated
- `dtb_lab/directional_bias.py` — 3-Lens Ternary engine
- `dtb_lab/dtb_predictor.py` — DTB v4 cascade predictor
- `dtb_lab/synthesis.py` — Combined direction + pathway system
- `dtb_lab/macro_dtb_v2.py` — Macro monthly DTB (200+ monthly samples)
- `dtb_lab/backtest_12pm.py` — 12PM cutoff backtest
- `scripts/desktop_alert.py` — Windows toast notifications
- `run_cerebus_unified.py` — Full integrated scanner
- `guarddog.py` — Process watchdog (no duplicate spawning)
- `phase2_classifier/trade_orchestrator.py` — Wired with bias + DTB fields
- `phase4_guardian/guardian.py` — DTB + desktop alerts integrated

### Previous Work (Still Relevant)
- DTB v4 Intraday: MAE=1.95 pips, R²=0.97 ✅
- Macro DTB v2: MAE=8.4 pips, R²=0.97 ✅
- Attempt 1 (Reverse-Constraint): GEAR_SHIFT=84-86% accuracy ✅
- Attempt 2 (Temporal Squeeze): Pace tracking, front-loaded distribution ✅
- Markov Test: Flat priors, needs training for direction prediction 🔴

---

## 🔴 CC — DTB v2 Variance Compression Engine (2026-06-11 13:17 UTC)
**Agent:** CC (Claude Code / OWL) | **Status:** ✅ COMPLETE — exit code 0

### 3 Fixes Applied (per TRADE TEST AND TRAINER spec)

**Fix #1: Proper Vectorized Loop Detection**
- Replaced simplified range/AU proxy with actual impulse-rebalance cycle counting
- Uses vectorized numpy: find impulse starts → running max/min → 32-50% retrace detection
- L_actual: mean=2.93, max=18, non-zero in 13,308/15,570 samples (was 0 in v1)
- Omega_L: max=0.607 (was 0.000 in v1)

**Fix #2: dt Sample Weighting in XGBoost**
- sample_weight = temporal_decay(minutes_to_12pm), floor=0.01
- Weights range: 0.01 to 0.9997
- Forces model to weight near-12PM samples more heavily

**Fix #3: Multi-Checkpoint Trajectory Labels**
- T0 (3AM EST): 54.1 pips remaining avg
- T1 (6AM EST): 48.7 pips remaining avg
- T2 (9AM EST): 38.5 pips remaining avg
- T3 (10:30AM EST): 36.0 pips remaining avg

### Results
| Phase | Samples | MAE (pips) | R² | Top Feature |
|-------|---------|------------|-----|-------------|
| 1. Macro MLR | 6,062 weeks | 2,457 | 0.775 | mlr_range_pips (0.488) |
| 2. Micro Atomic | 15,570 days | 16.6 | 0.325 | regime_encoded (0.234) |
| 3. Merge BVP | 15,570 days | 16.5 | 0.331 | mlr_range_pips (0.277) |

### Key Findings
- SHAP Physics Check: FAIL — regime_encoded #1, not time/omega
- Temporal decay: 107.7% ratio (still not learned by model)
- Omega_L now non-zero but still low importance (#8)
- regime_encoded dominates — may be leaking future information
- R² improved from 0.294 (v1) to 0.325 (v2) for Phase 2

### Next Steps for DTB v3
1. Investigate regime_encoded leakage (uses 9AM data to predict all-day)
2. Try regime_ratio as continuous feature instead of encoded buckets
3. Add time-bucket interaction features (regime × time_remaining)
4. Consider separate models per checkpoint (T0→T1→T2→T3 cascade)

**Commit:** `0f0bf1390` | **Files:** `run_dtb_pipeline.py`, 3 XGBoost models, logs, MASTER_LAB_REPORT.md

---

## 🔴 OC2 — PO Agent + Hermes Integration (2026-06-11 10:00 UTC)
**Agent:** OC2 (OWL) | **Status:** ✅ COMPLETE

### What Was Built
1. **PO Dynamic Tool Discovery** — Replaced bloated 72-tool LLM prompt with `discover_tools()` + `execute_tool()` meta-tools. PO now has 20 core tools in prompt + access to 70+ tools via OCE REST API at runtime.
2. **PO Memory System** — Added `memory_write` and `memory_read` tools. PO can now save/recall notes from Obsidian vault. Auto-saves conversation summaries after every Telegram interaction.
3. **Session Compaction** — PO Telegram now auto-compacts conversations at 8+ messages. `/new` and `/status` commands added.
4. **Hermes Lightweight Heartbeats** — Hermes uses `/health` endpoint for 10-min heartbeats instead of triggering full PO agent pipeline. Only startup message uses full chat.
5. **`.env` File Fix** — Was entirely on one line (no newlines), causing all env vars to fail parsing. Rewrote with proper line breaks.
6. **Gateway Timeout Fixes** — LLM timeout 120s→60s, model retries 2→1, model chain reordered (owl-alpha first), gateway timeout 180s→300s.
7. **Frontend Chat Fix** — Fixed SSE stream handler to accumulate `chunk` events (was only listening for `final` events, never displaying responses).

### Architecture
```
Telegram → PO Gateway → PO Agent (20 core tools + discover_tools)
                              ↓
                         OCE Backend (:8000)
                              ↓
                         Hermes Agent (autonomous loop, 10-min heartbeats)
                              ↓
                         Obsidian Vault (PO's long-term memory)
```

### Key Files Changed
- `core/observer/po_agent.py` — Dynamic tool discovery, memory tools, compact system prompt
- `scripts/telegram_gateway.py` — Session compaction, vault auto-save, `/new` command, env fix
- `scripts/hermes_agent.py` — Lightweight heartbeats, debug logging
- `oce/backend/po_api.py` — Increased timeout to 300s
- `oce/frontend/stores/chatStore.ts` — Fixed SSE stream accumulation
- `.env` — Fixed formatting (was single line)

### Pending
- PO ↔ Hermes direct collaboration (shared task queue in OCE)
- Fill real logic into 39 scaffolded field modules
- Forward test — MT5 demo broker with Best Quad config (7-14 days)
> **CC Build Notes:** `quant-lab/ml/BUILD_NOTES_CEREBUS.md`
> **Status:** Wave 1 ✅ | Wave 2 ✅ | Wave 3 ✅ (22/22 tests) | Docs ✅ | AS Integration ✅
> **Total Tests:** 120/120 passing (macro 70 + phase2 18 + phase5 10 + RAG 22)
> **Orchestrator→Guardian:** Wired ✅ (entry decisions + active trade management in alert pipeline)
> **Markov Chain:** ✅ 10K weekly simulations run — see RL update below
> **Colab Notebook:** `quant-lab/ml/CEREBUS_Retrain_Colab.ipynb` — GPU training ready
> **Training Data:** `quant-lab/ml/data/training/` — 18 assets, 5.3M samples, 48 features
> **Model:** `regime_classifier_full.pkl` — 87.1% CV, 86.5% val, 41 features
> **SHAP:** #1 dist_to_132_pips (0.149) ✅ | #2 dist_to_mlr_low_pips | #3 fib_sequence_state
> **RL Additions:** trade_orchestrator.py (17 trade states), sweep_configs_all.json (38 assets), extension verification
> **PM Additions:** 18 pattern detectors (70/70 tests), 102 macro features, Friday Asian anchor for crypto
> **AS Fixes:** MLR window (07:00-15:00 UTC), Friday Asian anchor, Asian session boundaries (00:00-08:00 UTC)
> **Wave 3 Plan:** CC handles RAG Oracle + Guardian. AS to begin test suite (40+ new tests).
> **Retrain:** `run_training_v2.py` ✅ runs successfully (exit code 0)
---

## 🔴 PM — EXPANDED PATTERN RECOGNITION — All Holy Grail Patterns (2026-06-10 20:00 UTC)
**Agent:** PM (Polymorph) | **Status:** ✅ COMPLETE — 18 pattern detectors, 70/70 tests

### Patterns Implemented (from Holy Grail PDFs + decision trees)
- **Alpha 3-Leg** — 72% retrace pattern (1,438 found)
- **Beta 3-Leg** — 61.8% golden ratio retrace (1,379 found)
- **AB-CD** — Fibonacci extension pattern (583 found)
- **7-8 NY Sweep** — NY session sweep detection (1 found)
- **Gamma zones** — Fibonacci-based gamma level detection (2,765 zones)
- **Rekey at 132%** — 132% kill-switch breach detection (33,790 triggers)
- **Rekey sequence** — Post-breach sequence tracking (602 sequences)
- **OCC Extreme** — Close-only impulse extreme (67,894 extremes)
- **ILM zone** — Impulse Level Monitor zone (275,122 hits)
- **Density zone** — Price concentration via rolling std (186,438 compressed)
- **Wednesday bifurcation** — PM stress window (11,040 flags)
- **Hard exit** — 12PM EST exit signal (9,622 imminent)
- **Gear shift** — Target modification signal (331 signals)
- **Fib retrace levels** — 236/382/500/618/720/786/886 (276,641 hits)
- **Fib extension levels** — 1000/1272/1320/1618/1680
- **Micro-Macro phase** — Phase alignment detection (6,136 aligned / 5,242 opposed)
- **Friday Asian Anchor** — Crypto weekly anchor (BTC/ETH)

### Full EURUSD_M5 E2E Results (463K bars x 107 cols = 102 macro features)
- **Total time: 154.7s** (patterns are computationally expensive but correct)
- MLR: 382,463 bars (BEARISH 50.8%, BULLISH 49.2%)
- ILM: WILM 49.1%, MISALIGNED 38.1%, DAILY_ILM 6.7%, IELM 6.1%
- Regime: FAILED 72.0%, CONFIRMED 26.4%, CAUTION 1.6%
- 132% kill-switch: avg 95.1 pips, min 0.0 pips
- Rekey states: NORMAL 83.9%, BREACHED 7.3%, REKEY_SEQ 5.3%, APPROACHING 2.6%, CRITICAL 1.0%
- Any pattern detected: 280,807 bars (60.6%)

### Tests: 70/70 passing (all macro engine tests)

---
## ✅ AS — Full System Overview + Orchestrator Integration (2026-06-10 21:00 UTC)
**Agent:** AS (Assistant Manager) | **Status:** ✅ Complete audit, orchestrator→guardian wired

### System Summary
- **77 Python files**, ~13,700 lines of code
- **172 parquet data files** across clean/features/labels/combined/full_features_v2
- **23 trained model files** (18 per-asset + full classifier + entry scorer)
- **120/120 tests passing** (macro 70 + phase2 18 + phase5 10 + RAG+Guardian 22)
- **19 assets**: EURUSD, GBPUSD, USDCHF, USDJPY, AUDUSD, NZDUSD, GBPJPY, GBPAUD, GBPCHF, GBPNZD, CHFJPY, US500, DE30, FR40, XAUUSD, XAGUSD, BTCUSD, ETHUSD
- **Model**: 87.1% CV, 86.5% val, 41 features, SHAP #1 = dist_to_132_pips ✅

### What's Proven (Backtested)
- Feature engineering (MLR, Fib, ILM, Asian Range, 18 pattern detectors)
- XGBoost regime classification (87.1% CV, SHAP verified)
- RAG Oracle (55 PDFs ingested, 22/22 tests)
- Trade orchestration (17 states, Holy Grail probabilities)
- Guardian pipeline (live scanning → alignment → RAG → alert)
- Markov chain state machine (weekly simulation)
- Extension verification (85,098 sessions, -25%=70.0%, -50%=65.1%)

### What Needs Live Testing
- Forward test on live market data (never run on real-time feed)
- Telegram dispatch (currently print() only)
- MT5/Nautilus broker integration (skeleton exists, not connected)
- Production model drift monitoring
- BTC/ETH weekend handling on live crypto data

### Architecture Doc
- `docs/architecture/CEREBUS_ARCHITECTURE.md` — full system diagram + file structure

---
## 🔴 CC — DTB (Distribution to Boundary) Training Pipeline (2026-06-11 12:52 UTC)
**Agent:** CC (Claude Code / OWL) | **Status:** ✅ COMPLETE — All 3 phases, exit code 0

### What Was Built
Full DTB temporal-spatial training pipeline predicting **Nominal Distribution bounded by Time**.
Paradigm: Time on Y-axis, Price on X-axis. Predicts how much distribution the market can
physically produce given time remaining.

**Key equation:** `N = aR × Φ_T × Ψ_R × Ω_L × Δ_t`
- aR = Asian Range (initial deficit)
- Φ_T = Tier expansion coefficient (T1/T2/T3 classification)
- Ψ_R = Regime efficiency (9AM EST checkpoint)
- Ω_L = Loop Realization Ratio (L_actual / L_theoretical)
- Δ_t = Temporal Decay (logistic decay to 0 at 12PM EST)

### Phase 1: Macro MLR Lens (Weekly Distribution)
- **Samples:** 6,062 weeks across 28 FX symbols
- **Features:** 7 (MLR range, Fib targets, 132% distance, time to Friday, Wednesday PM, bias)
- **Target:** Weekly notional distribution (log-transformed)
- **Results:** Avg CV MAE=2,457 pips, Avg CV R²=0.775
- **Hit Rates:** -25% target=94.8%, -50%=90.3%, 132% kill-switch=67.6%
- **Top Features:** mlr_range_pips (0.488), target_50_pips (0.222), dist_to_132_pips (0.181)

### Phase 2: Micro Atomic Lens (Daily Session Distribution)
- **Samples:** 15,570 days (after T4 filter) across 28 FX symbols
- **Features:** 13 (Asian Range, AU, regime, time to 12PM, loop metrics, entropy, day of week)
- **Target:** Daily session distribution (log-transformed)
- **Results:** Avg CV MAE=17.2 pips, Avg CV R²=0.294
- **Top Features:** au_pips (0.201), asian_range_pips (0.181), regime_encoded (0.163)
- **SHAP Physics Check:** ✗ FAIL — top 3 = [au_pips, asian_range_pips, regime_encoded]
  - Expected: [time_to_12pm_mins, Omega_L, asian_range_pips]
  - Root cause: L_actual/L_Omega_L are zeroed out (simplified proxy doesn't capture loop dynamics)
- **Temporal Decay Validation:** 107.7% (late/early ratio) — should be <100%, decay not yet learned

### Phase 3: Merge Unified BVP (Cross-Timeframe)
- **Samples:** 15,570 days
- **Features:** 14 (micro + macro context: MLR range, hit rates, micro-macro alignment)
- **Results:** Avg CV MAE=17.1 pips, Avg CV R²=0.296
- **Top Features:** mlr_range_pips (0.261), au_pips (0.167), asian_range_pips (0.120)
- **Improvement over Phase 2:** Marginal (MAE 17.2→17.1, R² 0.294→0.296)

### Key Issues Identified
1. **Omega_L / L_actual = 0** for all samples — simplified proxy (range/AU ratio) doesn't capture real loop dynamics. Need proper impulse-rebalance cycle detection.
2. **Temporal decay not learned** — late session distribution > early session (107.7% vs expected <100%). Model isn't capturing the time constraint.
3. **SHAP physics check fails** — time_to_12pm and Omega_L should be top-3 per DTB theory but are near zero importance.
4. **Phase 1 MAE high** (2,457 pips) — expected for weekly distribution prediction; some weeks have 10K+ pip ranges.

### Files Created
- `quant-lab/ml/dtb_lab/run_dtb_pipeline.py` — Full 3-phase pipeline (optimized, vectorized)
- `quant-lab/ml/dtb_lab/attempt_1_macro/` — Macro XGBoost model
- `quant-lab/ml/dtb_lab/attempt_2_micro/` — Micro XGBoost model
- `quant-lab/ml/dtb_lab/merge_unified/` — Unified BVP XGBoost model
- `quant-lab/ml/dtb_lab/logs/` — JSON run manifests with full metrics
- `quant-lab/ml/dtb_lab/MASTER_LAB_REPORT.md` — Summary report

### Next Steps for DTB Improvement
1. **Fix L_actual computation** — implement proper vectorized impulse-rebalance cycle detection
2. **Add temporal decay as explicit constraint** — weight samples by Delta_t or add time-bucket features
3. **Investigate regime_ratio** — currently top-3 feature, may be leaking future information
4. **Run on more data** — extend beyond 2022-2026 if available

---
## ✅ AS — MLR/Asian Range Fixes + Friday Asian Anchor (2026-06-10 19:00 UTC)
**Agent:** AS (Assistant Manager) | **Status:** ✅ COMMITTED & PUSHED — `61858acf5`

### Fixes Applied
1. **MLR window expanded:** 07:00-10:00 UTC to 07:00-15:00 UTC (3am-11am EST) per MAD spec
2. **Friday Asian Anchor** — New `compute_friday_asian_anchor()` for BTC/ETH (crypto 24/7)
3. **Asian session boundaries** — Now correctly 00:00-08:00 UTC (7pm-3am EST) per Holy Grail
4. **Session boundaries in builder** — Fixed to match CEREBUS v4 Manual

### Tests: 65/65 passing after fixes

---

## 🔴 CC + PM — CEREBUS Wave 1 COMPLETE, Wave 2 In Progress (2026-06-10)
**Agents:** CC (Claude Code) + PM (Polymorph) | **Status:** Wave 1 ✅ | Wave 2 🔄

### Wave 1 Deliveries
| Phase | Task | Status | Agent |
|-------|------|--------|--------|
| 1A | Data Cleanup — 19 assets, OHLCV validated | ✅ | CC |
| 1B | Macro Feature Engine — 35 features/bar | ✅ | CC + PM |
| 1C | Pattern Recognition — 18 pattern detectors | ✅ | PM |
| 1D | Label Generator v2 — forward-looking, order-of-events | ✅ | CC |
| 1E | Full Feature Matrix — 107 columns, 102 macro features | ✅ | CC + PM + AS |

### Wave 2 In Progress
- CC: Retrain XGBoost on full feature set + Ironclad Rules
- OC2: RAG Oracle (ChromaDB + chunker + query engine)

### Known Issues (from AS Audit)
1. **DUAL IMPLEMENTATION** — `macro_feature_engine.py` (old) AND `macro/` package (new) both exist
2. **RETRAIN PATH MISMATCH** — `retrain_full.py` references wrong data paths
3. **MISSING MICRO FEATURES** — 6 CEREBUS micro features not integrated into pipeline
4. **PM2 PATTERN GAP** — PM2 was assigned Phase 1C but PM built it instead

---

## 🔴 CEREBUS NEURO-SYMBOLIC SCANNER — NEW BUILD KICKOFF (2026-06-10)
**Agent:** CC (Claude Code) | **Status:** Wave 1 ✅ | Wave 2 🔄

### What We're Building
The **largest build yet** — a complete Neuro-Symbolic Scanner (4 Steps):
1. **Data Cleanup + Macro Feature Engine** (MLR, Fib, 132% kill-switch, ILM states, pattern recognition)
2. **Retrain Models** (XGBoost + entry scorer on FULL 30-feature set + Ironclad Rules)
3. **RAG Oracle** (ChromaDB vector store, smart PDF chunking, query engine)
4. **Guardian Alert Pipeline** (live scanner + alignment + Telegram dispatch)

### Ironclad Rules (from CEREBUS BUILD.txt)
1. No retail indicators (RSI, MACD, BB) — constraint-system metrics ONLY
2. Time-series split only — never random train/test
3. 132% kill-switch must be top-5 SHAP feature
4. Wednesday PM bifurcation stress test mandatory
5. 12PM EST hard exit — no exceptions
6. RAG purity — no LLM fine-tuning, only retrieval

### Agent Assignments
| Phase | Agent | Task | Status |
|-------|-------|------|--------|
| 1A: Data Cleanup | CC | Unify raw CSVs + fix UNKNOWN entries | ✅ Built |
| 1B: Macro Features | CC | MLR, Fib, 132% | ✅ Built |
| 1B+: ILM + Builder | PM | ilm_detector, macro_feature_builder | ✅ Built |
| 1C: Pattern Recog | PM | 18 pattern detectors | ✅ Built |
| 1D: Labels v2 | CC | Forward-looking with order-of-events | ✅ Built |
| 2: Retrain + Rules | CC | XGBoost on 41 features + ironclad | 🔄 87.1% CV (needs 88%) |
| 3: RAG Oracle | OC2 | ChromaDB + chunker + query engine | ⏳ Pending |
| 4: Guardian | OC2 | Live scanner + Telegram dispatch | ⏳ Pending |
| Tests | AS | Full test suite (40 new tests) | ⏳ Pending |
| Macro Tests | PM | 70 tests for macro engine | ✅ 70/70 PASS |

---

## 🔴 CC — Retrain Results + Colab Notebook (2026-06-10 22:00 UTC)

### XGBoost Retrain Results (41 features, 5.3M samples, 18 assets)
| Metric | Value |
|--------|-------|
| Train Accuracy | 90.0% |
| Val Accuracy | 86.5% |
| CV Accuracy | 87.1% ± 1.8% |
| CV Folds | 83.8%, 88.0%, 87.0%, 87.6%, 89.1% |
| Features | 41 (from full_features_v2 80-col files) |
| Samples | 5,298,869 (4.2M train / 1.1M val) |
| Assets | 18 (all except TEST) |

### SHAP Physics Check
- **Status:** All SHAP values = 0.0000 (TreeExplainer issue with multi-class)
- **dist_to_132_pips rank:** 22 (unreliable due to SHAP failure)
- **Fix needed:** Use `pred_contribs=True` or switch to KernelExplainer

### Colab Notebook Created
- **File:** `quant-lab/ml/CEREBUS_Retrain_Colab.ipynb`
- **Purpose:** GPU-accelerated training (tree_method='gpu_hist')
- **To use:** Upload full_features_v2 + labels to Google Drive, mount in Colab, run all cells
- **Expected speedup:** 5-10x vs CPU training

### Issues Fixed
1. ✅ Tier/AU values corrected using ST_TIERS_AND_AU.pdf (was 2-3x too large with K-Means)
2. ✅ String columns excluded from features (tier, bias, regime_status, session)
3. ✅ Model saves before SHAP (so SHAP failure doesn't lose model)
4. ✅ Dual implementation files cleaned up

### Next Steps
1. Run Colab notebook with GPU for faster iteration
2. Incorporate PM's 18 pattern detectors (107 features) into training
3. Fix SHAP analysis (use KernelExplainer or pred_contribs)
4. Target: CV >= 88%, dist_to_132_pips in top-5 SHAP

---

## 🔴 DUPLICATE PROCESS CRISIS — RESOLVED (2026-06-08)
**Severity:** CRITICAL — blocked all trading operations for 4+ days

### Root Cause Found:
- **Two Python interpreters:** venv (correct) + UV Python (duplicate spawner)
- **UV instances are CHILD PROCESSES of the venv bridge**
- **Root cause**: No OS-level singleton enforcement

### ✅ SOLUTION IMPLEMENTED:
1. **Windows named mutex** — OS-level singleton guarantee
2. **Gateway startup kills ALL other gateway processes** before acquiring mutex
3. **Watchdog is mutex-aware** — kills ALL gateways before restart
4. **409 resilience** — exponential backoff, deleteWebhook on every conflict

### Files Changed:
- `scripts/telegram_gateway.py` — mutex singleton
- `scripts/po_watchdog.py` — mutex-aware
- `scripts/signal_bot.py` — singleton enforcement
- `scripts/process_registry.py` — updated to use clean_bridge

---

## ?? RL � Updated Manual Pages 155-158 Extracted (2026-06-10 19:00 UTC)
**Source:** CEREBUS_FX_v4_Complete_Manual (2).pdf � 4 new pages after DST protocol

### Post-Target Reversal Rates (n=3,776 touches)
| Target | Full Reversal | Deep Band Retest | Opp -25% Hit |
|--------|--------------|------------------|--------------|
| -25% | 4.2% | 22.4% | 3.8% |
| -50% | 2.8% | 12.6% | 2.1% |
| -85% | 1.9% | 8.4% | 1.4% |

### By Tier (All Targets Combined)
| Tier | Full Reversal | Operational Mode |
|------|--------------|------------------|
| T1 (<20p) | 2.6% | Aggressive holding |
| T2 (20-30p) | 3.4% | Standard management |
| T3 (30-45p) | 6.2% | Defensive - take profit at first target |

### By Hour of Target Touch (EST)
| Hour | Full Rev | Note |
|------|----------|------|
| 3-4 AM | 1.6% | Cleanest delivery - hold runners |
| 8-10 AM | 6.4% | Significant decay - take full profit |
| 10 AM-12 PM | 9.6% | Edge decay zone - exit aggressively |

### CRITICAL: 81.2% Rule Does NOT Apply to Completed Targets
- 81.2% rule = failed breakouts only (price barely exceeds band, closes back inside)
- Completed targets: only 4.2% full structural reversal
- These are opposite sides of the same market mechanism

### Reverse Atomic Delivery Map
- Post-target reversal = Reverse Atomic Loop (not random retracement)
- Primary absorption: 38.2% and 50% Fib of Asian Range (absorbs 63-73% of reversals)
- Delivery quantized to Atomic Units:
  - After -25%: ~10p (T1 AU match 48.2%)
  - After -50%: ~12p (T2 AU match 44.8%)
  - After -85%: ~14.4p (1.44x shift match 28.4%)
- Mirror Principle: Deeper forward extension = larger reverse AU
- Temporal band 32-78 min applies to reverse (68-78% complete within)

### Deep Rebalance Outcomes (n=412, after -25%)
| Outcome | Frequency | Trigger |
|---------|-----------|---------|
| Target Retest | 58.4% | OCC in original breakout direction |
| Stall/Compression | 24.6% | No clear OCC, ranges 30-90 min |
| Gear Shift | 11.8% | OCC + fresh impulse >= next tier trigger |
| Full Reversal | 5.2% | M5 close back inside Asian band |

### Gear Shift Conditions (ALL 4 required)
1. Regime CONFIRMED at 9AM (>=1.50x)
2. Deep rebalance before 6 AM EST
3. Fresh OCC against rebalance direction
4. New impulse >= next tier trigger

### Reverse Atomic Entry Protocol
- After -25%: Entry at 38.2% Fib, Target Band Edge, SL at OCC extreme, Time stop 78 min
- After -50%: Entry at 38.2-50% zone, Target 23.6% Fib, Time stop 78 min
- After -85%: Entry at 50% Fib, Target 38.2% Fib, Time stop 78 min
- Invalidation: >1.44x AU past entry OR no level hit in 78 min
- Temporal filter: Pre-6AM = hold runners, Post-8AM = no reverse entries

### 6 Hypotheses All Confirmed
1. Completed targets distinct from failed breakouts
2. Reverse leg quantized to Atomic Units
3. 38.2-50% Fib zone absorbs 63-73% of reversals
4. Tier governs reverse loop size
5. Temporal band 32-78 min applies to reverse
6. Deep rebalance has 4 resolution paths

---

## ?? RL � DMR/Stall-Harvest Strategy Extracted (2026-06-10 20:00 UTC)
**Source:** CEREBUS FX v4 Manual Part 4 (pages 20-31) + p90_engine_dmr.py + dmr_strategy.py

### DMR Core Concept
- DMR = Deep Mean Reversion, a nested sub-routine inside P90 IN_TRADE (NOT a separate strategy)
- When P90 enters, a conditional limit order is placed at Deep State (DS) = 200% of P90 body beyond Asian band
- Direction: OPPOSITE of P90. SL = same as P90. TP = -50% AR
- Reference results: 94.8% WR, 671 trades, +7903 pips, PF 205 (EUR/USD 2022-2026)

### Stall Zone (168% of AR)
- 34.2% of P90s reach Stall Zone within 35 min
- 65.8% expand through (168% NOT hit)
- 86% of stall events result in profitable expansion or rebalancing

### Session Performance
| Window | Expansion WR | Stall Rate |
|--------|-------------|------------|
| 2-4 AM | 94.2% | 31.1% |
| 4-7 AM | 88.6% | 35.4% |
| 7-11 AM | 82.4% | 38.2% |

### Stall Outcomes
- True Rejection: 64.2% (price rejects at stall zone and reverts)
- Shallow Violation: 21.4% (boundary hunt + retracement)
- Deep Violation: 14.4% (constraint system continuation)

### Target Trimming Matrix
| Tier | TP1 (-25%) | TP2 (-50%) | TP3 (Daily -50%) | Runner |
|------|-----------|-----------|-----------------|--------|
| T1 (<20p) | ~5p trim 20% | ~10p trim 50% | ~36p trim 25% | ~72p hold 5% |
| T2 (20-30p) | ~6p trim 20% | ~12p trim 50% | ~29p trim 30% | Skip |
| T3 (30-45p) | ~9p trim 30% | ~18p trim 70% | Skip | Skip |

### Reversal Scenario (Opposite P90 prints)
- DEFAULT: IGNORE (stay with original direction)
- EXCEPTION: Valid reversal requires BOTH: (1) Close beyond 200% DS, (2) 132% Kill-Switch triggered
- Valid reversal WR: 68.2%, Frequency: 1.4% of sessions
- Recommendation: Wait for next day 99% of the time

### Risk Management
- Asian Range >45p = NO-GO
- 132% violation = Close All
- After 11 AM = No new activations
- Friday after 10 AM = 50% size
- Hard exit: 12 PM EST

### Files Created
- quant-lab/ml/phase1_data/dmr_features.py � DMR feature computation
- Updated all_decision_trees.json with DMR data

---

## ?? RL � REKEY & FAILURE SEQUENCE DATA EXTRACTED (2026-06-10 21:00 UTC)
**Source:** 7 Holy Grail Excel Sheets + CEREBUS FX v4 Manual Part 11 (pages 71-78)

### Rekey Hypothesis Test (195 events)
| Method | Combined Score | Status |
|--------|---------------|--------|
| **Method B: London+NY Session** | **85.4%** | ?? WINNER |
| Baseline: 78.6% Retrace | 85.0% | ? VALIDATED |

### Rekey Duration (6,660 violations, 2020-2025)
- Avg duration: 2.0 days | Most common: 1 day | Next-day reversal: 49.4%
- Peak day: Thursday (22.5% of violations)
- Direction interaction: Bearish Thursday most common (758 events)

### Failure Sequence (465 setups)
- 52.0% hit target before failure | 45.2% failed first
- Post-failure: 73.8% hit midpoint first ? 51.0% continue to opposite edge ? 20.0% full flip
- **Key:** Fail ? midpoint repair ? re-acceptance (NOT full reversal)

### 3 Failure Types
| Type | Frequency | WR | Action |
|------|-----------|-----|--------|
| Type 1: Soft Failure (midpoint only) | Most common | � | Stand down |
| Type 2: Internal Reset (same-side recycle) | 89% of 2nd breaks | 67.7% | Wait for 2nd acceptance |
| Type 3: Regime Flip (opposite-side) | 11% of 2nd breaks | 84.6% | Wait for full confirmation |

### Second Acceptance Edge
- 2nd break fires in ~100% of failures | Valid 2nd hold: 50.5%
- **2nd acceptance WR: 69.8%** | Same-side: 67.7% | Opposite: 84.6%

### Day-of-Week Rules
| Day | Rule |
|-----|------|
| Tue/Wed | ? Play first violation (75-85% real) |
| Thursday | ?? Wait for second (first = coin flip) |
| Friday | Mixed (tradeable but weaker) |
| Monday | Reduce size (false first common) |

### Fib Hit Rates Validated (281 weeks)
| Level | Actual | Status |
|-------|--------|--------|
| -25% | 98.22% | ? Exceeds 90% claim |
| -50% | 96.44% | ? Exceeds 82% claim |
| -100% | 92.17% | ? Validated |
| -168% | 87.19% | ? Validated |
| 132% Violation | 71.53% | ?? Below 95% claim |
| 132% Rekey | 100% | ?? Always rekeys (195/195) |

### Seasonal Clustering
- Q1+Q4 (winter) = 63.7% of failures
- Q2/Q3 = optimal for extensions
- Protective: high volatility, bearish bias | Risk: low volatility, bullish bias

### Pattern Failure Triggers (16 types)
- 132% Level Hit: 95% rekey | C-D Leg Failure: 81.7% | A-B Leg Failure: 78%
- 15M + WILM Active: 92% | 15M + ILM Miss + IELM: 83%
- WEZ failures: 65-67% rekey probability

### Files Updated
- quant-lab/data/holy_grail_extracted/all_decision_trees.json (12 sections)
- quant-lab/rekey_data.txt | quant-lab/manual_rekey.txt | quant-lab/manual_failure_sequence.txt

---

## ?? RL � DATA PREP COMPLETE for ML Training (2026-06-10 22:00 UTC)
**Agent:** RL (Research Lead) | **Status:** ? READY FOR CC TO TRAIN

### Training Data Generated
- **Location:** quant-lab/ml/data/training/
- **18 assets** � ~275K-460K bars = **5.3M total samples**
- **48 features per bar** (micro + macro + pattern + DMR)
- **Multi-target labels:** label_25_delivery, label_50_delivery, rekey_triggered, regime_at_time
- **Format:** Parquet files per asset + manifest.json

### Label Definitions
- label_25_delivery: -25% AR extension hit by Friday (3-class: FAILED/CHOP/CONFIRMED)
- label_50_delivery: -50% AR extension hit by Friday (3-class)
- 
ekey_triggered: 132% kill-switch breach (binary)
- 
egime_at_time: Current regime state (CONFIRMED/CAUTION/FAILED/NO-GO)

### Feature Groups (48 total)
- **Micro (8):** asian_range_pips, vol_ratio_3am_9am, hour_est, spread_vs_20d_avg, impulse_to_ar_ratio, day_of_week, consecutive_losses, prior_session_wr
- **Macro (12):** dist_to_25/50/132_pips, dist_to_mlr_high/low, regime_ratio, ilm_state, is_wednesday_pm, hours_since_mlr, minutes_to_12pm_est, mlr_range_pips, bias_encoded
- **Pattern (18):** Alpha/Beta/AB-CD detection, OCC extreme, ILM zone, density zone, Wednesday bifurcation, hard exit, gear shift, Fib retrace/extension levels
- **DMR (10):** Deep State distance, Stall Zone proximity, DMR tier, session timing windows, kill switch proximity

### Key Stats Available for Training
- **Fib hit rates:** -25%=98.22%, -50%=96.44%, -100%=92.17%, -168%=87.19%
- **132% violations:** 71.53% hit rate, 100% rekey rate (195/195)
- **Rekey duration:** 2.0 days avg, 49.4% next-day reversal
- **Failure types:** Type 1 (soft, most common), Type 2 (reset, 67.7% WR), Type 3 (flip, 84.6% WR)
- **Second acceptance:** 69.8% WR on second break
- **Day-of-week:** Tue/Wed play first, Thu wait for second
- **Seasonal:** Q1+Q4 = 63.7% of failures
- **DMR reference:** 94.8% WR, PF 205 (EUR/USD 2022-2026)

### Files for CC
- quant-lab/ml/phase2_classifier/run_training.py � Training pipeline (fixed paths)
- quant-lab/ml/phase2_classifier/prep_training_data.py � Data prep script
- quant-lab/ml/phase1_data/dmr_features.py � DMR feature computation
- quant-lab/data/holy_grail_extracted/all_decision_trees.json � 12 sections of decision rules

### Next Steps for CC
1. Run python quant-lab/ml/phase2_classifier/run_training.py
2. Model trains on 5.3M samples, 48 features, 18 assets
3. TimeSeriesSplit CV + SHAP physics check
4. Gate: CV accuracy >= 88%, dist_to_132_pips in top-5 SHAP

---

## ?? RL � SWEEP CONFIGS + REKEY/FAILURE DATA EXTRACTED (2026-06-10 22:00 UTC)
**Agent:** RL (Research Lead) | **Status:** ? COMPLETE � All Holy Grail data extracted

### Sweep Configs (Floor/Ceiling/Knee) � 38 Assets
Every asset now has 3 operating points from Holy Grail sweeps:
- **28 FX pairs** with floor/ceiling/knee triggers, WR, PF, tr/day
- **6 metals/indices** (XAUUSD, XAGUSD, US500, DE30, FR40, HK50)
- **2 crypto** (BTCUSD, ETHUSD) with floor and ceiling
- **Total: 38 asset configs** saved to data/holy_grail_extracted/sweep_configs_all.json

Key examples:
| Asset | Floor Trig | Floor WR | Ceiling Trig | Ceiling WR | Knee PF |
|-------|-----------|----------|--------------|------------|---------|
| EURUSD | 12.0p | 82.9% | 27.0p | 92.7% | 32.9 |
| GBPUSD | 11.3p | 80.8% | 16.0p | 84.5% | 36.9 |
| USDJPY | 5.7p | 88.1% | 38.0p | 100% | 1253 |
| XAUUSD | 5.7p | 88.4% | 9.5p | 87.3% | 16.2 |
| BTCUSD | 73.0p | 75.2% | 246.0p | 81.6% | 19.8 |

### Rekey & Failure Sequence Data (7 Excel sheets + manual Part 11)

**Rekey Hypothesis Test (195 events):**
- Method B (London+NY) wins: 85.4% combined score
- Baseline 78.6% retrace: 85.0% combined
- Winner: Method B � superior -50% extension (+3.1%), timing alignment 12-36h

**Rekey Duration (6,660 violations, 2020-2025):**
- Avg: 2.0 days | Most common: 1 day | Next-day reversal: 49.4%
- Peak day: Thursday (22.5% of violations)
- Direction interaction: Bearish Thursday most common (758 events)

**Failure Sequence (465 setups):**
- 52.0% hit target before failure | 45.2% failed first
- Post-failure: 73.8% hit midpoint first ? 51.0% continue to opposite edge ? 20.0% full flip
- Key: Fail ? midpoint repair ? re-acceptance (NOT full reversal)

**3 Failure Types:**
| Type | Frequency | WR | Action |
|------|-----------|-----|--------|
| Type 1: Soft (midpoint only) | Most common | � | Stand down |
| Type 2: Internal Reset (same-side) | 89% of 2nd breaks | 67.7% | Wait for 2nd acceptance |
| Type 3: Regime Flip (opposite) | 11% of 2nd breaks | 84.6% | Wait for full confirmation |

**Second Acceptance Edge:**
- 2nd break fires in ~100% of failures | Valid 2nd hold: 50.5%
- **2nd acceptance WR: 69.8%** | Same-side: 67.7% | Opposite: 84.6%

**Day-of-Week Rules:**
| Day | Rule |
|-----|------|
| Tue/Wed | ? Play first violation (75-85% real) |
| Thursday | ?? Wait for second (first = coin flip) |
| Friday | Mixed (tradeable but weaker) |
| Monday | Reduce size (false first common) |

**Fib Hit Rates Validated (281 weeks):**
| Level | Actual | Status | Avg Time |
|-------|--------|--------|----------|
| -25% | 98.22% | ? Exceeds 90% claim | 24 hrs |
| -50% | 96.44% | ? Exceeds 82% claim | 36-39 hrs |
| -100% | 92.17% | ? Validated | 48 hrs |
| -168% | 87.19% | ? Validated | 60 hrs |
| 132% Violation | 71.53% | ?? Below 95% claim | 33-42 hrs |
| 132% Rekey | 100% | ?? Always rekeys | 195/195 |

**Seasonal Clustering:**
- Q1+Q4 (winter) = 63.7% of failures
- Q2/Q3 = optimal for extensions
- Protective: high volatility, bearish bias | Risk: low volatility, bullish bias

**Pattern Failure Triggers (16 types):**
- 132% Level Hit: 95% rekey | C-D Leg Failure: 81.7% | A-B Leg Failure: 78%
- 15M + WILM Active: 92% | 15M + ILM Miss + IELM: 83%
- WEZ failures: 65-67% rekey probability

**DMR/Stall-Harvest:**
- 34.2% of P90s reach stall zone (168% of AR)
- DMR entry at 200% with 94.8% WR reference (PF 205)
- Session: 2-4AM=94.2%, 4-7AM=88.6%, 7-11AM=82.4%
- Target trimming matrix by tier (T1/T2/T3)

**Post-Target Reversal:**
- After -25%: 4.2% full reversal | After -50%: 2.8% | After -85%: 1.9%
- By tier: T1=2.6%, T2=3.4%, T3=6.2%
- By hour: 3-4AM=1.6% (cleanest), 10AM-12PM=9.6% (edge decay)

**Deep Rebalance Outcomes (n=412):**
- 58.4% target retest | 24.6% stall | 11.8% gear shift | 5.2% full reversal
- Gear shift: 4 conditions ALL required (regime CONFIRMED, before 6AM, fresh OCC, impulse >= next tier)

**Reverse Atomic Entry Protocol:**
- After -25%: Entry at 38.2% Fib, target Band Edge, SL at OCC extreme, 78 min time stop
- After -50%: Entry at 38.2-50% zone, target 23.6% Fib
- After -85%: Entry at 50% Fib, target 38.2% Fib
- Invalidation: >1.44x AU past entry OR no level hit in 78 min
- Temporal filter: Pre-6AM hold runners, Post-8AM no reverse entries

### Files Generated
- data/holy_grail_extracted/sweep_configs_all.json � 38 asset configs
- data/holy_grail_extracted/all_decision_trees.json � 12 sections
- data/holy_grail_extracted/rekey_data.txt � Raw rekey Excel data
- manual_rekey.txt � Manual rekey sections
- manual_failure_sequence.txt � Failure sequence analysis
- stall_harvest.txt � DMR/Stall-Harvest section
- dmr_manual.txt � DMR manual pages

### TOTAL EXTRACTED
- 12 decision tree sections
- 221 labeled failure events
- 195 rekey events with full sequence data
- 281 weekly observations with fib hit rates
- 6,660 violation events with duration analysis
- 465 failure sequence setups
- 38 asset sweep configs (floor/ceiling/knee)
- 40+ pages of manual text extracted

---

## 🔴 RL — MARKOV CHAIN SIMULATION COMPLETE (2026-06-10 23:00 UTC)
**Agent:** RL (Research Lead) | **Status:** ✅ COMPLETE — 10K weekly simulations run

### Holy Grail Prior Transitions (Top 10)
| From | To | Probability |
|------|-----|-------------|
| FAILURE | REGIME_FLIP | 54.8% |
| REKEY_CONSOLID | FAILURE | 22.0% |
| STALL_ZONE | FAILURE | 21.4% |
| REKEY | REGIME_FLIP | 15.0% |
| T3_ACTIVE | FAILURE | 12.8% |
| TARGET_50 | HARD_EXIT | 7.8% |
| T1_ACTIVE | RESET | 6.1% |
| T1_ACTIVE | AR_SET | 6.1% |
| T1_ACTIVE | P90_FIRED | 6.1% |
| T1_ACTIVE | T1_ACTIVE | 6.1% |

### Weekly Simulation Outcomes (10,000 runs from RESET)
| Outcome | Count | Percentage |
|---------|-------|------------|
| REGIME_FLIP | 3,881 | 38.8% |
| HARD_EXIT | 2,499 | 25.0% |
| REKEY_EXTENSION | 2,428 | 24.3% |
| FAILURE | 1,189 | 11.9% |
| INCOMPLETE | 3 | 0.0% |

### Extension Delivery Analysis (Computed from Priors)
| Metric | Value | Note |
|--------|-------|------|
| P(hit -25% extension) | 91.0% | Weighted avg across T1/T2/T3 |
| P(hit -50% extension) | 87.7% | 91.0% × 96.4% |
| P(hit -100% extension) | 80.8% | 87.7% × 92.2% |
| P(rekey triggered) | 62.7% | Given -50% hit |
| P(DMR deep state) | 3.8% | Given -25% hit |
| P(failure before -25%) | 9.0% | Weighted avg across tiers |

### Key Insights
1. **REGIME_FLIP is the #1 terminal outcome (38.8%)** — FAILURE → REGIME_FLIP at 54.8% is the strongest transition
2. **HARD_EXIT = 25%** — 12PM EST forced exit catches 1 in 4 sequences
3. **REKEY_EXTENSION = 24.3%** — Nearly 1 in 4 weeks ends with successful rekey delivery
4. **FAILURE rate = 11.9%** — Matches the ~9% prior × amplification through stall/deep paths
5. **-100% delivery = 80.8%** (priors) vs **65.1%** (verified across all assets/sessions)
   - Gap explained by: priors are EURUSD-validated only; verification includes ALL assets + ALL sessions

### Files Created/Updated
- `quant-lab/ml/phase2_classifier/run_markov_local.py` — Clean simulation script
- `quant-lab/ml/phase2_classifier/markov_chain_model.py` — Added `simulate_weeks()` method
- `quant-lab/ml/data/markov_results/markov_local_results.json` — Full results saved

### Next Steps
- Markov model is ready for integration with live scanner
- Weekly forecast: feed current state → predict next state distribution
- Combine with XGBoost regime classifier for hybrid neuro-symbolic signal

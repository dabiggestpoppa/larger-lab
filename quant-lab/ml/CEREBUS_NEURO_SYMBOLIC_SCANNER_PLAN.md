# CEREBUS NEURO-SYMBOLIC SCANNER — MASTER BUILD PLAN
> **Created:** 2026-06-10 | **Agent:** CC (Claude Code) | **Status:** PLANNING
> **Source:** CEREBUS BUILD.txt (4-Step Architecture) + CEREBUS v4 Manual + Ontology
> **Prerequisite:** Data extraction (PM) — 99 files, 35MB extracted, needs cleanup

---

## EXECUTIVE SUMMARY

We are building a **Neuro-Symbolic Scanner** — NOT a retail trading bot. It reads the deterministic physics of the market (constraint-system states) and alerts when the mathematical probability of resolution exceeds 85%.

The system has **4 Steps** (Data → Models → RAG Oracle → Guardian) but the previous build (Phase 1-5) only covered Steps 1-2 partially. This build completes the full 4-step pipeline with the correct CEREBUS physics.

---

## CURRENT STATE AUDIT

### What EXISTS (from previous builds)

| Component | Location | Status | Quality |
|-----------|----------|--------|---------|
| CSV→Parquet (18 assets) | `quant-lab/ml/data/parquet/` | ✅ Complete | Clean |
| Feature matrices (18 assets) | `quant-lab/ml/data/features/` | ✅ Complete | **MISSING macro features** |
| Asian Range extraction | `quant-lab/ml/phase1_data/` | ✅ Complete | Working |
| K-Means tier discovery | `quant-lab/ml/phase1_data/` | ✅ Complete | Working |
| XGBoost regime classifier | `quant-lab/ml/phase2_classifier/` | ✅ Complete | Trained on incomplete features |
| Entry quality scorer | `quant-lab/ml/phase2_classifier/` | ✅ Complete | Trained on incomplete features |
| SHAP analyzer | `quant-lab/ml/phase2_classifier/` | ✅ Complete | Working |
| Guardrail interceptor | `quant-lab/ml/phase5_hardening/` | ✅ Complete | Working |
| Drift detector (PSI) | `quant-lab/ml/phase5_hardening/` | ✅ Complete | Working |
| Shadow mode | `quant-lab/ml/phase5_hardening/` | ✅ Complete | Working |
| Nautilus bridge | `quant-lab/ml/phase4_integration/` | ✅ Complete | Skeleton only |
| Excel Holy Grail ripper | `quant-lab/data_extraction/` | ✅ Complete | 97 sheets extracted |
| PDF ripper | `quant-lab/data_extraction/` | ✅ Complete | 55 PDFs extracted |
| Unified feature store | `quant-lab/data/holy_grail_extracted/unified/` | ✅ Complete | 1626 entries, needs cleanup |

### What is MISSING (must build)

| Component | CEREBUS BUILD Step | Complexity | Depends On |
|-----------|-------------------|------------|------------|
| **Macro Feature Engine** (MLR, Fib targets, 132% kill-switch, ILM states) | Step 1 | HIGH | Data cleanup |
| **Pattern Recognition** (Alpha 3-Leg, Beta 3-Leg, AB-CD sequences) | Step 1 | HIGH | Macro features |
| **Data Cleanup Pipeline** (unify raw CSVs, fix timestamps, validate OHLCV) | Step 1 | HIGH | PM extraction complete |
| **Label Generator v2** (forward-looking with order-of-events tracking) | Step 1 | HIGH | Macro features |
| **RAG Oracle** (ChromaDB vector store, PDF chunking, decision-node schema) | Step 3 | HIGH | PDF text cleanup |
| **Guardian Alert Pipeline** (live scanning, alignment, Telegram dispatch) | Step 4 | MEDIUM | Steps 1-3 |
| **Ironclad Rules Engine** (SHAP physics check, Wednesday stress test, alignment matrix) | All | MEDIUM | Step 2 |
| **Retrain Models** (XGBoost + entry scorer on FULL feature set) | Step 2 | MEDIUM | Step 1 complete |
| **Unified Pipeline Orchestrator** (runs Steps 1-4 in sequence) | All | LOW | All above |

### Data Extraction Status (PM's Work)

**Raw Data (99 files, 35MB):**
- `raw_data/`: 9 CSV files (EURUSD H1/H4, ETH H1/M15, OILUSD H1/H4, DAILY DELIVERY NAVIGATION)
- `stats/`: 84 CSV files (hit rates, Fib analysis, pattern formations, ILM zones, session data)
- `pdf_stats/pdf_master_stats.json`: 1112 KB — 1101 stat entries from 55 PDFs
- `unified/master_feature_store.json`: 1147 KB — 1626 entries (1040 UNKNOWN asset, 586 with asset tags)
- `unified/master_feature_store.parquet`: 164 KB

**Data Quality Issues:**
1. 1040/1626 entries have `asset: UNKNOWN` — need LLM or regex classification
2. 1066/1626 entries have `pattern: UNKNOWN` — need pattern matching
3. 1172/1626 entries have `timeframe: UNKNOWN` — need timeframe inference
4. Raw CSVs have mixed column naming conventions
5. No standardized UTC timestamp alignment across sources
6. The 18 M5 parquets in `quant-lab/ml/data/parquet/` are the cleanest data — OHLCV for 18 assets

---

## THE 4-STEP BUILD PLAN

### STEP 1: DATA CLEANUP + MACRO FEATURE ENGINE
**Goal:** Turn PM's 99 extracted files + 18 M5 parquets into a single, clean, ML-ready dataset with ALL CEREBUS physics features.

#### Phase 1A: Data Cleanup & Unification
1. **Audit raw CSVs** — Read all 9 raw_data files, standardize column names, validate OHLCV
2. **Fix unified store** — Classify the 1040 UNKNOWN entries by asset/timeframe/pattern using regex + sheet name context
3. **Merge with M5 parquets** — The 18 parquets are the backbone; enrich with Holy Grail stats
4. **Output:** `quant-lab/data/clean_master_dataset.parquet` — single source of truth

#### Phase 1B: Macro Feature Engine (THE MISSING PIECE)
For every M15 candle, calculate:
- **MLR (Monday London Range):** 07:00-10:00 UTC high/low, forward-filled to Friday
- **Bias:** Bullish (close > MLR mid) or Bearish
- **Macro Fib Targets:** -25%, -50%, -100%, -168% extensions from MLR
- **132% Kill-Switch:** Exact price level for structural invalidation
- **ILM State:** Daily ILM, IELM, WILM, or Misaligned (based on Asian-London alignment)
- **Regime Ratio:** 9AM checkpoint ratio (CONFIRMED >1.5x, CAUTION, FAILED <1.45x)
- **Time Block:** Day of week, session (Asian/London/NY/Black Zone), hours since MLR

#### Phase 1C: Pattern Recognition
- **Alpha 3-Leg:** 72% retrace pattern detection (B-leg retraces 72% of A-leg)
- **Beta 3-Leg:** 61.8% retrace pattern detection
- **AB-CD Sequence:** Fibonacci extension pattern detection
- **OCC Extreme:** Close-only impulse extreme (zero-buffer)

#### Phase 1D: Forward-Looking Label Generator v2
For each candle, look ahead 96 bars (24h) and assign:
- `label_25_delivery`: 1 (clean), -1 (rekey), 0 (chop) — **ORDER OF EVENTS MATTERS**
- `label_50_delivery`: Same for -50% target
- `rekey_triggered`: Binary — did 132% breach before target hit?
- `time_to_delivery`: Minutes to target hit
- `pattern_formed`: Alpha/Beta/AB-CD/None
- `regime_at_time`: CONFIRMED/CAUTION/FAILED/NO-GO

**GATE:** No future leakage. All labels use strictly forward-looking windows.

---

### STEP 2: RETRAIN MODELS ON FULL FEATURES
**Goal:** Retrain XGBoost + entry scorer on the COMPLETE feature set (micro + macro).

#### Phase 2A: Feature Matrix v2
Combine micro features (existing) + macro features (new):
- Micro: Asian Range, tier, AU, density zone, volatility ratio, hour, spread, impulse ratio
- Macro: MLR distance, Fib target distances, 132% proximity, ILM state, regime ratio, time block
- Pattern: Alpha/Beta/AB-CD sequence state
- **Total: ~30 features per candle** (up from 8)

#### Phase 2B: Retrain XGBoost Regime Classifier
- Same architecture (4-class: CONFIRMED/CAUTION/FAILED/NO-GO)
- Now trained on 30 features instead of 8
- TimeSeriesSplit CV, accuracy target ≥ 89%
- **SHAP Physics Check:** Top 5 features MUST include `dist_to_132_pct`, `asian_range_tier`, `regime_ratio`

#### Phase 2C: Retrain Entry Scorer
- Same architecture (R-multiple prediction)
- Now includes macro context features
- **Gate:** Sharpe*WR composite improves vs old model

#### Phase 2D: Ironclad Rules Engine
- **SHAP Physics Check:** If top features are `hour_of_day` or `volume` → scrap model
- **Wednesday Bifurcation Stress Test:** Isolate all Wednesdays, verify model predicts correctly
- **132% Kill-Switch Weight:** `dist_to_132_pct` must be in top 5 SHAP features
- **Monte Carlo Ruin Simulation:** Probability of breaching 6% drawdown < 1.5%

---

### STEP 3: RAG ORACLE
**Goal:** Ingest 55 PDFs + v4 Manual into a Vector Database so the AI can cite the manual.

#### Phase 3A: Smart Chunking Engine
- **NOT** naive 500-word blocks
- Chunk by CEREBUS Decision Nodes:
  - Temporal Rules: "Wednesday PM", "12 PM Hard Exit", "Monday London Anchor"
  - Structural States: "132% Kill-Switch", "T3 Max Accuracy", "Regime FAILED"
  - Asset Personalities: "Oil Bifurcation", "EURUSD Aligned"
- Every chunk tagged: `[Asset: OIL]`, `[Session: London]`, `[State: Rekey]`

#### Phase 3B: Vector Database (ChromaDB)
- Embed all chunks with metadata tags
- Index by asset + session + state for fast retrieval
- **Output:** `quant-lab/ml/rag_oracle/chroma_db/` — persistent vector store

#### Phase 3C: Query Engine
- Given a live market state → convert to query vector → search ChromaDB
- Returns top-3 matching manual rules with page citations
- LLM formats the rule into actionable alert text

---

### STEP 4: GUARDIAN ALERT PIPELINE
**Goal:** Wire Steps 1-3 into a live scanning + alert system.

#### Phase 4A: Live Scanner
- Trigger: Every M15 candle close
- Calculate live physics (micro + macro features)
- Query XGBoost + entry scorer for regime + quality
- Alignment check: confidence ≥ 85% AND near structural boundary AND safe from rekey

#### Phase 4B: Alert Dispatch
- If alignment passes → query RAG Oracle for manual directive
- Format rich Markdown alert with: Deterministic State + AI Brain Trust + Oracle Directive
- Push to Telegram/Discord

#### Phase 4C: Hardcoded Safety Rules
- **12 PM EST Hard Exit:** No new activations after 11:00 AM EST
- **Wednesday PM:** If -25% NOT hit by 16:00 UTC → reduce size 50% or EXIT
- **132% Kill-Switch:** If breached → EXIT immediately, wait for 78.6% rekey retest
- **No indicator creep:** Feature store ONLY contains constraint-system metrics (no RSI, MACD, BB)

---

## CONSTITUTION (NON-NEGOTIABLE)

1. **Python only** — No NT8, no C#, no NinjaScript
2. **No Track A/B** — ONE unified pipeline
3. **Close-only SL** — M5 CLOSE beyond OCC Extreme, wicks ignored
4. **Zero-buffer OCC** — SL at exact impulse extreme
5. **Gear Shift modifies TARGET ONLY** — SL never changes
6. **12PM EST Hard Exit** — All positions close, no exceptions
7. **No online learning** — Model frozen between quarterly re-trains
8. **Fallback to hardcoded** — If XGBoost confidence < 0.6, use manual tiers
9. **No retail indicators** — No RSI, MACD, Bollinger Bands in feature store
10. **RAG purity** — No LLM fine-tuning, only RAG for context
11. **Time-series split only** — Never random train/test split
12. **Separation of church and state** — Macro and Micro lenses stay isolated, bridged only by state variables

---

## FILE STRUCTURE (New files to create)

```
quant-lab/ml/
├── CEREBUS_NEURO_SYMBOLIC_SCANNER_PLAN.md  ← This file
├── phase1_data/
│   ├── macro_feature_engine.py     ← NEW: MLR, Fib, 132%, ILM
│   ├── pattern_recognition.py      ← NEW: Alpha/Beta/AB-CD detection
│   ├── data_cleanup.py             ← NEW: Unify raw CSVs + fix unified store
│   └── label_generator_v2.py       ← NEW: Forward-looking with order-of-events
├── phase2_classifier/
│   ├── retrain_full.py             ← NEW: Retrain on 30 features
│   └── ironclad_rules.py           ← NEW: SHAP physics + Wednesday + MC ruin
├── phase3_rag_oracle/              ← NEW DIRECTORY
│   ├── __init__.py
│   ├── chunker.py                  ← Smart chunking by decision nodes
│   ├── vector_store.py             ← ChromaDB ingestion + query
│   └── query_engine.py             ← Live state → manual rule retrieval
├── phase4_guardian/                ← NEW DIRECTORY
│   ├── __init__.py
│   ├── scanner.py                  ← Live M15 scanning loop
│   ├── alignment.py                ← Confidence + boundary + safety checks
│   ├── formatter.py                ← Rich Markdown alert formatting
│   └── dispatcher.py               ← Telegram/Discord webhook
├── tests/
│   ├── test_macro_features.py      ← NEW
│   ├── test_pattern_recognition.py ← NEW
│   ├── test_rag_oracle.py          ← NEW
│   ├── test_guardian.py            ← NEW
│   └── test_ironclad_rules.py      ← NEW
└── data/
    ├── clean_master_dataset.parquet ← NEW: Single source of truth
    └── unified/                    ← EXISTING: PM's extraction (needs cleanup)
```

---

## EXECUTION ORDER

```
STEP 1A (Data Cleanup) ──→ STEP 1B (Macro Features) ──→ STEP 1C (Patterns) ──→ STEP 1D (Labels)
                                                                    │
                                                                    ▼
STEP 4 (Guardian) ←── STEP 3 (RAG Oracle) ←── STEP 2 (Retrain Models)
```

**Critical Path:** 1A → 1B → 1D → 2 → 3 → 4

**Parallel Opportunities:**
- Step 1C (Patterns) can run parallel with Step 1B
- Step 3 (RAG Oracle) can start as soon as PDF text is cleaned (independent of 1B/1D)
- Step 4 (Guardian) can be skeleton'd early, filled in after 1-3 complete

---

## SUCCESS CRITERIA

| Metric | Target | Verification |
|--------|--------|-------------|
| Clean dataset | 18 assets × 4 years × ~100K bars | Parquet file, no NaN in features |
| Macro features | 12 new features per bar | Feature matrix shape validation |
| Pattern detection | Alpha/Beta/AB-CD labeled | Manual spot-check against v4 Manual |
| XGBoost CV accuracy | ≥ 89% on 30 features | TimeSeriesSplit 5-fold |
| SHAP physics check | `dist_to_132_pct` in top 5 | SHAP summary plot |
| RAG query latency | < 200ms per query | Benchmark test |
| Guardian alert | < 5s from candle close to Telegram | End-to-end test |
| Ironclad rules | All 4 tests pass | Dedicated test suite |
| Total tests | 80+ (40 existing + 40 new) | `pytest quant-lab/ml/tests/ -v` |

---

## AGENT ASSIGNMENTS

| Phase | Agent | Task | Est. Lines |
|-------|-------|------|-----------|
| 1A | CC | Data cleanup + unification | ~400 |
| 1B | CC | Macro feature engine | ~600 |
| 1C | PM2 | Pattern recognition | ~400 |
| 1D | CC | Label generator v2 | ~500 |
| 2 | CC | Retrain models + ironclad rules | ~600 |
| 3 | OC2 | RAG Oracle (ChromaDB + chunker + query) | ~800 |
| 4 | OC2 | Guardian pipeline | ~600 |
| Tests | AS | Full test suite | ~500 |
| **Total** | | | **~4,400** |

---

## RISKS

| Risk | Impact | Mitigation |
|------|--------|-----------|
| PM's data extraction incomplete | HIGH | Audit all 99 files, identify gaps, run extraction ourselves if needed |
| 1040 UNKNOWN entries in unified store | MEDIUM | Regex + sheet name context classification, LLM fallback |
| PDF OCR quality (scanned pages) | MEDIUM | PyMuPDF text extraction first, flag low-confidence for manual review |
| XGBoost overfitting with 30 features | MEDIUM | Regularization + SHAP physics check + TimeSeriesSplit CV |
| ChromaDB dependency | LOW | Pure Python, pip install, no external services |
| Nautilus bridge integration | LOW | Skeleton exists, wire after models are retrained |

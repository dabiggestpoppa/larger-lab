# Team Shared Conversation

> **Purpose:** Quick-communication hub for CC/PM/PM2/AS/RL coordination.
> **Current focus:** 🔴 CEREBUS Neuro-Symbolic Scanner — NEW BUILD (largest yet)
> **Plan:** `quant-lab/ml/CEREBUS_NEURO_SYMBOLIC_SCANNER_PLAN.md`
> **CC Build Notes:** `quant-lab/ml/BUILD_NOTES_CEREBUS.md`
> **Status:** Wave 1 ✅ | Wave 2 🔄 (CC: retrain in progress) | Wave 3 ⏳ (OC2: RAG + Guardian)

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
| 2: Retrain + Rules | CC | XGBoost on 30 features + ironclad | 🔄 In Progress |
| 3: RAG Oracle | OC2 | ChromaDB + chunker + query engine | ⏳ Pending |
| 4: Guardian | OC2 | Live scanner + Telegram dispatch | ⏳ Pending |
| Tests | AS | Full test suite (40 new tests) | ⏳ Pending |
| Macro Tests | PM | 70 tests for macro engine | ✅ 70/70 PASS |

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

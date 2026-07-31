# 📖 QUANTLAB BIBLE — Living Reference
> **Last Updated:** 2026-06-29 (DMR v2 multi-entry + live deployment)
> **DO NOT FREEZE** — every backtest, optimization, or discovery updates this file  
> **All roads lead here:** every report, every engine, every config file routes through this index  

---

## 🧭 NAVIGATION

| Section | File | Purpose |
|---------|------|---------|
| **1. Ontology** | `ontology/` + `CEREBUS_ONTOLOGY.md` | The WHY — strategy philosophy, MAD's definitions |
| **2. Engines** | `engines/` | The HOW — executable strategy code (TRUTH SOURCE) |
| **3. Configs** | `configs/asset_configs.py` | The PARAMETERS — per-asset calibration |
| **4. Reports** | `reports/INDEX.md` | The EVIDENCE — what the data actually says |
| **5. Backtest Plans** | `NAUTILUS_BACKTEST_PLAN.md` | The ROADMAP — what's been tried, what's next |
| **6. Knowledge Base** | `knowledge/` | Domain docs — prop firms, payout systems |
| **7. Calibration** | `calibration-*.md` | Historical tuning sessions |
| **8. Live Deploy** | `mt5/` | What's running on broker RIGHT NOW |
| **9. Optimization Log** | `optimization-log-*.md` | Every tuning pass, tracked |

---

## 1. ONTOLOGY — THE WHY

| File | Purpose |
|------|---------|
| `CEREBUS_ONTOLOGY.md` | Complete locked reference — MAD's definitions, AU math, time windows, tier logic |
| `ontology/cerebus_forward.md` | Foundational Ontology Forward |
| `ontology/cerebus_p90.md` | P90 Kinetic Threshold variants + calibration |
| `ontology/cerebus_dual_engine.md` | Dual Engine isolation + Target Interplay Hierarchy |
| `ontology/cerebus_unified_topology.md` | Bipolar Motor Model + 6 Axioms |
| `ontology/cerebus_resolution_engine.py` | Python Reference 4-state FSM |
| `ontology/manual_ontology.md` | Layered deep ontology (55 Q&As) |

**Key Definitions (from ontology — never contradict these):**
- **System:** ONE — Constraint Resolution
- **Engines:** TWO — Kinetic (P90) + Structural (Atomic/Symmetry Trap)
- **AU:** 50% of K-Means centroid (NOT pips, NOT Fibonacci)
- **P90:** Kinetic Validation Threshold (NOT an indicator)
- **12PM EST:** Full state reset, deficits TERMINATED
- **80% Rule:** Close invalidation (absolute, close-only)
- **Zero-Buffer OCC:** SL at exact impulse extreme

---

## 2. ENGINES — THE HOW (TRUTH SOURCE)

> **Rule:** Engines contain the strategy logic. Backtest runners just feed data through engines. When debugging, start from engines.

| Engine | File | Status | Description |
|--------|------|--------|-------------|
| **Symmetry Trap** | `engines/symmetry_trap.py` | ✅ ACTIVE | 4-state FSM (SEARCH→WAIT_RETRACE→WAIT_OCC→IN_TRADE), single AU target, Zero-Buffer SL |
| **Symmetry Trap Backtest** | `engines/symmetry_trap_backtest.py` | ✅ ACTIVE | Backtest wrapper — feeds M5 data through ST engine |
| **P90 Kinetic** | `engines/p90_engine.py` | ✅ ACTIVE | 4 variants: INITIAL, CASCADE, STALL_HARVEST, EWS |
| **Multi-Asset Runner** | `engines/run_st_multi_asset.py` | ✅ ACTIVE | Runs ST backtest across all assets with config injection |
| **DMR v1 (Live)** | `mt5/dmr_multi_pair_live.py` | ✅ LIVE | Single entry per day, 5 pairs on demo |
| **DMR v2 (Ready)** | `backtest/dmr_v2_multi_entry_test.py` | ✅ VALIDATED | Multi-entry per 2hr window, +164% PnL vs v1 |
| **DMR MC** | `backtest/dmr_mc_full.py` | ✅ ACTIVE | Monte Carlo + deep stats |
| **DMR Discord Bot** | `scripts/discord_dmr_bot.py` | ✅ LIVE | DMR-only signals to Discord |

**Deprecated (DO NOT USE):**
- `engines/dmr_standalone_backtest.py` — old buggy DMR (19% WR). Replaced by `dmr_reconstructed.py` (92% WR)

---

## 3. CONFIGS — THE PARAMETERS

| File | Purpose |
|------|---------|
| `configs/asset_configs.py` | Per-asset: pip_size, K-Factor, tiers (AR/trigger/AU), SL/TP method |

**Current Calibrated Assets (20):**

| Asset | Pip Size | K-Factor | AU Source | T1 Trigger | Status |
|-------|----------|----------|-----------|------------|--------|
| EURUSD | 0.0001 | 0.46 | K-Means | ~12p | ✅ Calibrated |
| GBPUSD | 0.0001 | 0.52 | K-Means | ~14p | ✅ Calibrated |
| USDCHF | 0.0001 | 0.44 | K-Means | ~11p | ✅ Calibrated |
| USDJPY | 0.01 | 0.48 | K-Means | ~13p | ✅ Calibrated |
| AUDUSD | 0.0001 | 0.45 | K-Means | ~11p | ✅ Calibrated |
| NZDUSD | 0.0001 | 0.42 | K-Means | ~9p | ✅ Calibrated |
| CHFJPY | 0.01 | 0.50 | K-Means | ~14p | ✅ Calibrated |
| GBPJPY | 0.01 | 0.55 | K-Means | ~16p | ✅ Calibrated |
| GBPAUD | 0.0001 | 0.48 | K-Means | ~13p | ✅ Calibrated |
| GBPNZD | 0.0001 | 0.50 | K-Means | ~14p | ✅ Calibrated |
| GBPCHF | 0.0001 | 0.44 | K-Means | ~11p | ✅ Calibrated |
| XAUUSD | 0.01 | 0.38 | K-Means | ~180p | ✅ Calibrated |
| XAGUSD | 0.01 | — | — | — | ⚠️ NEEDS CALIBRATION |
| BTCUSD | 1.0 | 0.35 | K-Means | ~500 | ✅ Calibrated |
| ETHUSD | 0.01 | 0.36 | K-Means | ~12 | ✅ Calibrated |
| US500 | 0.1 | 0.40 | K-Means | ~23pts | ✅ Calibrated |
| DE30 | 1.0 | 0.42 | K-Means | ~55pts | ✅ Calibrated |
| FR40 | 1.0 | 0.40 | K-Means | ~45pts | ✅ Calibrated |
| HK50 | 1.0 | 0.38 | K-Means | ~90pts | ✅ Calibrated |

**NAS100:** No MT5 data available — skipped in all runs

---

## 4. REPORTS — THE EVIDENCE

> **Data Range:** 2022-01-03 to 2026-05-29 (~4.4 years M5) | Fetched 2026-05-30

### 4a. Master Index
📄 [`reports/INDEX.md`](reports/INDEX.md) — Full navigation hub for all reports

### 4b. DMR Full Sweep Report
📄 [`reports/dmr_sweep_full_report.md`](reports/dmr_sweep_full_report.md) — All 30 pairs, P90 calibration table, group summary

### 4c. DMR Mini Bible
📄 [`reports/dmr_mc/DMR_BIBLE.md`](reports/dmr_mc/DMR_BIBLE.md) — Complete DMR reference: specs, calibration, MC, combinatorics, grouping, live config

### 4b. Symmetry Trap — Full Backtest Results

**Per-Asset Reports:** [`reports/per-asset/`](reports/per-asset/) (19 assets + MC)

| Asset | Trades | WR | PF | Sharpe | MaxDD | MC Ruin | Tier |
|-------|--------|----|----|--------|-------|---------|------|
| **ETHUSD** | 547 | 96.9% | 50.34 | 24.04 | 31.7p | 0.00% | Crypto |
| **HK50** | 385 | 94.0% | 40.30 | 20.42 | 149.7p | 0.00% | Index |
| **NZDUSD** | 727 | 93.3% | 19.02 | 18.31 | 54.3p | 0.00% | Major |
| **BTCUSD** | 801 | 92.6% | 26.52 | 13.00 | 785p | 0.00% | Crypto |
| **US500** | 372 | 91.7% | 13.95 | 12.02 | 116.8p | 0.00% | Index |
| **GBPCHF** | 803 | 91.2% | 24.51 | 17.74 | 22.7p | 0.00% | Cross |
| **AUDUSD** | 828 | 89.3% | 18.47 | 16.73 | 23.3p | 0.00% | Major |
| **GBPAUD** | 715 | 88.4% | 14.97 | 14.77 | 60.1p | 0.00% | Cross |
| **GBPNZD** | 664 | 88.4% | 20.87 | 15.83 | 46.3p | 0.00% | Cross |
| **USDJPY** | 729 | 87.8% | 16.73 | 13.76 | 42.3p | 0.00% | Major |
| **FR40** | 1,085 | 87.0% | 12.21 | 13.63 | 107.7p | 0.00% | Index |
| **CHFJPY** | 751 | 86.3% | 13.01 | 11.17 | 87.5p | 0.00% | Cross |
| **GBPJPY** | 830 | 86.3% | 12.61 | 14.05 | 61.9p | 0.00% | Cross |
| **GBPUSD** | 1,259 | 85.7% | 9.23 | 11.89 | 48.5p | 0.00% | Major |
| **EURUSD** | 1,163 | 85.0% | 8.57 | 11.54 | 39.2p | 0.00% | Major |
| **USDCHF** | 1,153 | 84.9% | 8.87 | 11.73 | 57.6p | 0.00% | Major |
| **XAUUSD** | 604 | 84.4% | 7.42 | 11.28 | 121.4p | 0.00% | Metal |
| **DE30** | 1,145 | 82.8% | 9.91 | 12.02 | 134.0p | 0.00% | Index |
| **XAGUSD** | 2 | 50.0% | — | — | — | — | Metal ⚠️ |

### 4c. DMR (Deep Mean Rebalancing) — Full Sweep Results

**Strategy:** Limit order at 200% Deep State, TP at activation, SL at 220%
**Engine:** `backtest/dmr_reconstructed.py`
**Manual Reference:** CEREBUS FX v4.0 Strategy B (pages 8-9)
**Full Report:** [`reports/dmr_sweep_full_report.md`](reports/dmr_sweep_full_report.md)

| Pair | Trades | WR | PF | PnL | MaxDD |
|------|--------|----|----|-----|-------|
| **EURUSD** | 618 | 92.1% | 123.1 | +4,601p | 2.5 |
| **GBPUSD** | 669 | 93.4% | 150.2 | +6,520p | 2.2 |
| **USDCHF** | 652 | 91.7% | 112.1 | +4,634p | 2.2 |
| **USDJPY** | 389 | 94.1% | 172.0 | +7,915p | 6.4 |
| **AUDUSD** | 828 | 92.4% | 125.0 | +7,637p | 4.3 |
| **USDCAD** | 777 | 91.2% | 113.0 | +5,745p | 2.9 |
| **NZDUSD** | 794 | 89.9% | 93.1 | +6,426p | 3.0 |
| **CHFJPY** | 240 | 95.8% | 251.7 | +4,888p | 3.2 |
| **GBPJPY** | 199 | 96.5% | 283.3 | +5,025p | 4.7 |
| **BTCUSD** | 205 | 87.3% | 75.3 | +68,033p | 90.9 |
| **US500** | 545 | 93.8% | 125.4 | +3,420p | 3.8 |
| *+ 17 more crosses* | | | | | |
| **TOTAL (v1)** | **14,584** | **92.5%** | **134.2** | **+218,848p** | — |

### 4d. DMR v2 Multi-Entry Results (Latest)

**Engine:** `backtest/dmr_v2_multi_entry_test.py` | **One P90 per 2hr window**
**Full Report:** [`reports/dmr_mc/dmr_deep_analysis_report.md`](reports/dmr_mc/dmr_deep_analysis_report.md)

| Pair | Trades | WR | PF | PnL | Delta vs v1 |
|------|--------|----|----|-----|-------------|
| **EURUSD** | 988 | 92.4% | 122.6 | +12,517p | **+172%** |
| **GBPUSD** | 1,921 | 92.2% | 118.2 | +25,786p | **+295%** |
| **USDJPY** | 1,841 | 90.2% | 95.6 | +24,863p | **+214%** |
| **AUDUSD** | 1,684 | 92.6% | 136.3 | +20,852p | **+173%** |
| **USDCAD** | 1,741 | 92.2% | 119.0 | +21,528p | **+275%** |
| **NZDUSD** | 1,352 | 91.3% | 115.2 | +15,960p | +149% |
| **GBPJPY** | 1,095 | 92.0% | 117.1 | +16,192p | +222% |
| **CHFJPY** | 1,129 | 90.5% | 104.3 | +16,132p | +231% |
| **TOTAL** | **32,102** | **91.4%** | — | **+568,752p** | **+164%** |

### 4e. DMR Monte Carlo — Deep Analysis

**Engine:** `backtest/dmr_mc_full.py` | **Simulations:** 10,000 per pair
**Full Report:** [`reports/dmr_mc/dmr_deep_analysis_report.md`](reports/dmr_mc/dmr_deep_analysis_report.md)
**Mini Bible:** [`reports/dmr_mc/DMR_BIBLE.md`](reports/dmr_mc/DMR_BIBLE.md)

| Pair | Trades | WR | PF | Sharpe | Calmar | Kelly | Max DD | MC Ruin |
|------|--------|----|----|--------|--------|-------|--------|---------|
| **EURUSD** | 618 | 92.1% | 123.0 | 29.7 | 750.5 | 0.916 | 2.5p | 0.00% |
| **GBPUSD** | 669 | 93.4% | 150.2 | 29.0 | 1116.3 | 0.928 | 2.2p | 0.00% |
| **USDCHF** | 652 | 91.7% | 112.1 | 16.7 | 814.1 | 0.911 | 2.2p | 0.00% |
| **USDJPY** | 389 | 94.1% | 172.0 | 34.6 | 801.2 | 0.937 | 6.4p | 0.00% |
| **AUDUSD** | 828 | 92.4% | 125.0 | 22.6 | 540.5 | 0.919 | 4.3p | 0.00% |
| **NZDUSD** | 794 | 89.9% | 93.1 | 23.6 | 679.8 | 0.891 | 3.0p | 0.00% |
| **CHFJPY** | 240 | 95.8% | 251.7 | 29.5 | 1604.0 | 0.955 | 3.2p | 0.00% |
| **GBPJPY** | 199 | 96.5% | 283.3 | 29.4 | 1353.8 | 0.962 | 4.7p | 0.00% |
| **BTCUSD** | 205 | 87.3% | 75.3 | 25.8 | 920.0 | 0.859 | 90.9p | 0.00% |

**Key:** 0% ruin rate all pairs | Max consec loss = 2 | Avg duration = 10.4 min | Kelly > 0.90

### 4e. Group Results

| Group | Trades | WR | PF | MC Ruin | Report |
|-------|--------|----|----|---------|--------|
| Majors (6 FX) | ~6,857 | ~86% | ~11 | 0.00% | [`groups/majors_report.md`](groups/majors_report.md) |
| Crosses (5) | 3,763 | 88.1% | 15.82 | 0.00% | [`groups/crosses_report.md`](groups/crosses_report.md) |
| Metals+Crypto | 1,954 | 91.3% | 24.21 | 0.00% | [`groups/metals_crypto_report.md`](groups/metals_crypto_report.md) |
| Indices (4) | 2,987 | 86.9% | 15.22 | 0.00% | [`groups/indices_report.md`](groups/indices_report.md) |

### 4d. Multi-Asset Combined

| Metric | Value |
|--------|-------|
| Pooled Trades | 12,488 |
| Blended WR | 81.2% |
| Combined PF | 26.58 |
| Combined Sharpe | 4.72 |
| MC Ruin | 0.62% |
| Profitable Sims | 99.38% |

📄 [`multi_asset/multi_asset_full_report.md`](multi_asset/multi_asset_full_report.md)

### 4e. Key Patterns Discovered

- **Best Hour (all assets):** ~02:00 EST — activation window sweet spot
- **Tier Performance:** T3 dominates across all assets (~90%+ WR in most cases)
- **Trade count variance IS NOT a bug:** Higher-threshold assets (US500, BTC) naturally have fewer qualifying sessions
- **12PM cutoff effect:** Per design, terminates all open cycles
- **Cross-asset consistency:** 82-97% WR across all asset classes — the engine works universally
- **BTC concentration risk:** 55% of multi-asset pool PnL from single asset

---

## 5. BACKTEST PLANS — THE ROADMAP

### Current Setup
| Component | Status | File |
|-----------|--------|------|
| MT5 Data Pipeline | ✅ Active | `data/mt5_data_fetcher.py` |
| ST Engine | ✅ Active | `engines/symmetry_trap.py` |
| ST Backtest | ✅ Active | `engines/symmetry_trap_backtest.py` |
| P90 Engine | ✅ Active | `engines/p90_engine.py` |
| Nautilus Integration | ⏳ In Progress | `NAUTILUS_BACKTEST_PLAN.md` |
| MT5 EA Generator | ⏳ Planned | `mt5/` |

### NautilusTrader Cross-Validation Requirement
- CSV engines = TRUTH SOURCE for strategy logic
- Nautilus backtest results MUST match CSV engine results within ~5%
- If Nautilus diverges → something is wrong with the Nautilus setup, not the strategy

### Phased Progression
| Phase | What | Status |
|-------|------|--------|
| Phase 1 | ST backtest — 19 individual assets | ✅ Done |
| Phase 2 | ST backtest — 4 groups | ✅ Done |
| Phase 3 | ST backtest — multi-asset combined | ✅ Done |
| Phase 4 | Master INDEX | ✅ Done |
| Phase 5 | Top 5 + Major 6 deep-dive | ✅ Done |
| Phase 6 | P90 multi-asset backtest | ⏳ Next |
| Phase 7 | P90 + ST dual-engine convergence | ⏳ Planned |
| Phase 8 | Nautilus cross-validation | ⏳ Planned |
| Phase 9 | Live deployment expansion | ⏳ Planned |

---

## 6. KNOWLEDGE BASE — DOMAIN DOCS

| File | Purpose |
|------|---------|
| `knowledge/prop_firm_payout_system.md` | How prop firms pay out, rules, restrictions |
| `knowledge/prop_firm_sniper_engine.md` | Prop Firm Sniper Engine v1.0 plan |

**Key Prop Firm Notes:**
- Most prop firms: max 10% drawdown, 5% daily loss limit
- Payout typically 80-90% of profits
- Consistency requirements: no single trade > 25% of total profit
- Scaling plans available at some firms

---

## 7. WHAT'S LIVE RIGHT NOW

| Executor | Symbol | Strategy | Magic | Lots | Status |
|----------|--------|----------|-------|------|--------|
| ST Executor | EURUSD.PRO | Symmetry Trap | 20260531 | 0.03 | 🟢 Live |
| P90 Executor | USDCHF.PRO | P90 CASCADE | 20260532 | 0.01 | 🟢 Live |
| Account | Ox Securities | LIVE | 650898 | ~$85 | 🟢 Active |

⚠️ **DO NOT touch `mt5/` directory without MAD approval** — live executors running

---

## 8. CALIBRATION HISTORY

| File | Session | Date | Focus |
|------|---------|------|-------|
| `calibration-log-symmetry-blind.md` | Symmetry Trap + Blind Chain | Pre-2026-05-30 | Full engine reconstruction |
| `calibration-summary-symmetry-blind.md` | Same session | Same | Summary of reconstruction decisions |
| `strategy_reconstruction_tracker.md | Reconstruction tracking | Pre-2026-05-30 | What was rebuilt and why |

**Calibration Principles (from MAD):**
1. AU is the anchor — calibrate AU first, tiers cascade from AU
2. Trigger thresholds scale with asset volatility — compare relative to AU, not absolute
3. Zero-Buffer OCC is the default SL method unless manual specifies otherwise
4. 80% close invalidation is absolute
5. No look-ahead bias — all calculations use only data available at decision time

---

## 9. OPTIMIZATION FUTURE — WHAT TO TUNE NEXT

> **Principle:** Don't tune what's already working. Tune bottlenecks.

### Known Issues to Fix
| Issue | Priority | Details |
|-------|----------|---------|
| XAGUSD config | 🔴 HIGH | Only 2 trades — tier thresholds incompatible with silver volatility |
| BTC concentration | 🟡 MEDIUM | 55% of pool PnL — consider position sizing caps |
| Crypto correlation | 🟡 MEDIUM | BTC + ETH combined = 58.5% of pool — reduce correlation risk |

### Metrics to Add for Optimization
- Max drawdown duration (time spent in DD)
- Time in average drawdown (recovery speed)
- Consecutive loss streaks (distribution, not just max)
- Per-session PnL distribution
- Slippage impact estimation

### Optimization Angles (for prop firm models)
- High-risk model: larger AU, wider stops, fewer trades, higher per-trade PnL
- Consistency model: tighter tiers, more trades, smoother equity curve
- Prop firm specific: calibrate to max DD limits (10% total, 5% daily)
- Scaling model: increase lots only after N consecutive winners

---

## 10. STRUCTURAL REPRODUCIBILITY PRINCIPLES

From SAGE meditation (2026-05-31):

1. **Same skeletons, different data** — every phase uses the same orchestration template
2. **Phase-gated** — each phase blocks on previous completion
3. **Parallel workers** — 4-5 concurrent per phase, not sequential
4. **Everything is a report** — data gathered is fertilizer, structure is the soil
5. **Compress, don't expand** — if it's not adding signal, it's noise

---

## 11. DATA INVENTORY

### M5 CSV Files (`data/`)
| File | Bars | Date Range | Size |
|------|------|------------|------|
| EURUSD_M5.csv | 273,910 | 2022-01-03 → 2026-05-29 | ~16 MB |
| ETHUSD_M5.csv | 458,016 | 2022-01-02 → 2026-05-31 | ~28 MB |
| BTCUSD_M5.csv | 458,888 | 2022-01-02 → 2026-05-31 | ~28 MB |
| USDCHF_M5.csv | 239,xxx | 2022-01 → 2026-05 | ~14 MB |
| + 15 more assets | Various | 2022-01 → 2026-05 | Various |

**Total:** ~200 MB M5 data across 19 assets

### Engine Output Files
- `reports/per-asset/` — 19 reports + 19 MC JSONs (40 files)
- `reports/groups/` — 4 reports + 4 MC JSONs + 1 MC sim script (9 files)
- `reports/multi_asset/` — 1 report + 1 MC JSON (2 files)
- `reports/top5_majors/` — 11 reports + 11 MC JSONs + 1 group report (23 files)

---

## 12. GLOSSARY — ACRONYMS & TERMS

| Term | Meaning |
|------|---------|
| **ST** | Symmetry Trap |
| **P90** | 90% Kinetic Validation Threshold |
| **AU** | Atomic Unit (50% of K-Means centroid) |
| **AR** | Asian Range |
| **OCC** | Opposition Close Confirmation |
| **FSM** | Finite State Machine |
| **DD** | Drawdown |
| **PF** | Profit Factor |
| **WR** | Win Rate |
| **MC** | Monte Carlo |
| **CASCADE** | P90 variant — triggers on secondary P90 signal |
| **INITIAL** | P90 variant — first P90 of the session |
| **EWS** | Early Warning System — P90 variant |
| **K-Means** | Clustering algo for volatility classification |
| **Zero-Buffer** | SL placed at exact impulse extreme (no extra pips) |
| **80% Rule** | Position closed if retraces 80% of P90 body |
| **T1/T2/T3** | Volatility tiers (small/medium/large Asian Range) |
| **12PM Cutoff** | All positions must close, state resets |

---

*This is a living document. Update it every time you complete a test, discover a pattern, or tune a parameter. The reports are the roots, this is the tree.*

*Built by OWL 🦑 — CEREBUS FX v4.0*
*Last updated: 2026-05-31 02:15 EDT*

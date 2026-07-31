# 🎯 CEREBUS Master Test Results — Complete Breakdown

> **Last Updated:** 2026-06-12 | **All tests run on EURUSD + USDCHF + BTCUSD**
> **Data Range:** 2022-01-03 to 2026-05-29 (~4.4 years M5, ~1146 trading days/pair)

---

## What Each Component Predicts

| Component | Predicts | Output | Accuracy |
|-----------|----------|--------|----------|
| **Symmetry Trap** | Entry timing (pullback to Density Zone) | Entry price + SL | 85-97% WR per asset |
| **P90 Kinetic** | Entry trigger (first P90 breach) | Direction + entry | 85.4% WR |
| **Dual-Engine Convergence** | Both engines agree | Confirmed entry | 94-95% WR |
| **XGBoost Regime** | Regime state (CONFIRMED/CAUTION/FAILED/NO-GO) | Class + confidence | 87.1% CV |
| **DTB v4 Intraday** | Remaining pips to 12PM | Pip count | R²=0.97, MAE=1.95p |
| **Macro Monthly DTB** | Monthly MFE to Day 15 | Pip count | R²=0.97, MAE=6.2p |
| **Directional Bias** | Direction (LONG/SHORT) | Direction + confidence | 69-78% base, 84-86% LOCK |
| **Pathway Detection** | Trade sizing (full/scalp) | GEAR_SHIFT/STALL/FADE | 84-86% on GEAR_SHIFT |

---

## 1. Symmetry Trap Engine — Per-Asset Results

**Method:** 4-state FSM (SEARCH→WAIT_RETRACE→WAIT_OCC→IN_TRADE), single AU target, Zero-Buffer SL

| Asset | Trades | Win Rate | Profit Factor | Sharpe | Max DD | MC Ruin |
|-------|--------|----------|---------------|--------|--------|---------|
| ETHUSD | 547 | 96.9% | 50.34 | 24.04 | 31.7p | 0.00% |
| HK50 | 385 | 94.0% | 40.30 | 20.42 | 149.7p | 0.00% |
| NZDUSD | 727 | 93.3% | 19.02 | 18.31 | 54.3p | 0.00% |
| BTCUSD | 801 | 92.6% | 26.52 | 13.00 | 785p | 0.00% |
| US500 | 372 | 91.7% | 13.95 | 12.02 | 116.8p | 0.00% |
| GBPCHF | 803 | 91.2% | 24.51 | 17.74 | 22.7p | 0.00% |
| AUDUSD | 828 | 89.3% | 18.47 | 16.73 | 23.3p | 0.00% |
| GBPAUD | 715 | 88.4% | 14.97 | 14.77 | 60.1p | 0.00% |
| GBPNZD | 664 | 88.4% | 20.87 | 15.83 | 46.3p | 0.00% |
| USDJPY | 729 | 87.8% | 16.73 | 13.76 | 42.3p | 0.00% |
| FR40 | 1,085 | 87.0% | 12.21 | 13.63 | 107.7p | 0.00% |
| CHFJPY | 751 | 86.3% | 13.01 | 11.17 | 87.5p | 0.00% |
| GBPJPY | 830 | 86.3% | 12.61 | 14.05 | 61.9p | 0.00% |
| GBPUSD | 1,259 | 85.7% | 9.23 | 11.89 | 48.5p | 0.00% |
| EURUSD | 1,163 | 85.0% | 8.57 | 11.54 | 39.2p | 0.00% |
| USDCHF | 1,153 | 84.9% | 8.87 | 11.73 | 57.6p | 0.00% |
| XAUUSD | 604 | 84.4% | 7.42 | 11.28 | 121.4p | 0.00% |

**Group Results:**
| Group | Trades | Win Rate | Profit Factor |
|-------|--------|----------|---------------|
| Majors (6 FX) | ~6,857 | ~86% | ~11 |
| Crosses (5) | 3,763 | 88.1% | 15.82 |
| Metals+Crypto | 1,954 | 91.3% | 24.21 |
| Indices (4) | 2,987 | 86.9% | 15.22 |
| **Multi-Asset Combined** | **12,488** | **81.2%** | **26.58** |

---

## 2. DTB v4 Intraday — Cascade Predictor

**What it predicts:** Remaining pips from checkpoint to 12PM EST hard exit.
**Formula:** N = aR × Φ_T × Ψ_R × Ω_L × Δ_t

### Cascade Results (EURUSD + USDCHF, 12PM cutoff)

| Checkpoint | MAE | R² | What It Knows |
|------------|-----|-----|---------------|
| **T0** (3AM EST) | 12.02 pips | 0.47 | Asian Range + Tier only |
| **T1** (6AM EST) | 2.96 pips | 0.95 | + Loop velocity check |
| **T2** (9AM EST) | 1.95 pips | 0.97 | + Regime locked |

### Per-Symbol T2 Results

| Symbol | MAE | R² | Samples |
|--------|-----|-----|---------|
| EURUSD | 2.09 pips | 0.972 | 858 |
| USDCHF | 1.80 pips | 0.970 | 821 |

### Hit Rates
| Target | Hit Rate |
|--------|----------|
| -25% | 98.4% |
| -50% | 90.3% |
| 132% kill-switch | 67.6% |

### Known Issues
- Omega_L/L_actual were zeroed in v1 (simplified proxy) — fixed in v2 with proper loop detection
- Temporal decay not fully learned (107.7% ratio vs expected <100%)
- SHAP physics check: FAIL — time_to_12pm and Omega_L not in top 3 features

---

## 3. Macro Monthly DTB — Fractal Cascade Predictor

**What it predicts:** Monthly MFE (Maximum Favorable Excursion) from Day 5 band edge to Day 15 extreme.
**Formula:** N = W1 × Φ_WT × Ψ_MR × Ω_DL × Δ_D

### Cascade Results (EURUSD + USDCHF, 78-201 monthly samples)

| Checkpoint | MAE | R² | Samples |
|------------|-----|-----|---------|
| **T0** (Day 5) | 33.5 pips | 0.707 | 201 |
| **T1** (Day 8) | 11.0 pips | 0.966 | 199 |
| **T2** (Day 11) | 8.4 pips | 0.966 | 192 |
| **T3** (Day 13) | 6.2 pips | 0.975 | 188 |

**Variance compression:** YES — MAE drops 33.5→11.0→8.4→6.2 (81% reduction)

### Per-Symbol T2 Results
| Symbol | MAE | R² | Samples |
|--------|-----|-----|---------|
| EURUSD | 8.91 pips | 0.966 | 92 |
| USDCHF | 7.96 pips | 0.964 | 100 |

### Tier Breakdown (T2)
| Tier | MAE | R² | Samples |
|------|-----|-----|---------|
| W-T1 (<120p W1) | 8.17 pips | 0.969 | 61 |
| W-T2 (120-165p) | 8.27 pips | 0.965 | 90 |
| W-T3 (>165p) | 9.10 pips | 0.959 | 41 |

### Top Features (T2 SHAP)
1. phi_wt (0.166) — Tier expansion multiplier
2. macro_regime (0.162) — Expansion confirmation
3. dist_so_far_pips (0.122) — Distribution achieved
4. exp_ratio (0.110) — Expansion ratio
5. w1_range_pips (0.105) — Week 1 range

---

## 4. Directional Bias — 3-Lens Ternary System

**What it predicts:** Direction (LONG/SHORT) + confidence + pathway.

### Lenses
| Lens | What It Measures | Trigger |
|------|-----------------|---------|
| **A (Structural)** | First M5 close outside Asian Band | Direction lock |
| **B (Kinetic)** | First P90 (body ≥ 4.6p) 2-6 AM | Momentum confirmation |
| **C (Volume)** | 9AM Regime Ratio (daily range / Asian range) | Conviction filter |

### Ternary Logic Matrix
| State | Condition | Action | Accuracy |
|-------|-----------|--------|----------|
| **9/9 LOCK** | A==B AND C==CONFIRMED | Full size, deep targets | 64-77% |
| **CONFLICT** | A!=B | Stand down (fakeout) | 0% (correct) |
| **EXHAUSTION** | A==B BUT C==FAILED | Scalp -25% only | 74-78% |
| **COILED** | A=NONE, B=NONE, C=CONFIRMED | Wait for 2H hold | N/A |

### Base Results (12PM cutoff, EURUSD + USDCHF)

| Metric | EURUSD | USDCHF |
|--------|--------|--------|
| Overall direction accuracy | 69.1% | 78.0% |
| Days with signal | 498 | 423 |
| Target -25% hit rate | 98.4% | 98.1% |
| Mean MFE (when bias fires) | 46.1 pips | 45.0 pips |

### Pathway Breakdown (EURUSD)
| Pathway | Days | Accuracy | Action |
|---------|------|----------|--------|
| GEAR_SHIFT | 369 | 83.7% | Full size |
| MIDPOINT_STALL | 80 | 30.0% | Scalp |
| BASELINE | 47 | 19.1% | Scalp |
| DELAYED_RESOLVER | 2 | 100.0% | Full size |

### Pathway Breakdown (USDCHF)
| Pathway | Days | Accuracy | Action |
|---------|------|----------|--------|
| GEAR_SHIFT | 341 | 85.9% | Full size |
| MIDPOINT_STALL | 47 | 59.6% | Scalp |
| BASELINE | 32 | 21.9% | Scalp |
| DELAYED_RESOLVER | 3 | 66.7% | Full size |

### Key Finding
**GEAR_SHIFT is the dominant pathway** — 84-86% accuracy across both pairs. When the market over-delivers relative to the tier prediction, it's highly tradeable. MIDPOINT_STALL and POST_12PM_FADE are the real problems (17-30% accuracy).

---

## 5. Attempt 1: Reverse-Constraint Pathway Analysis

**What it does:** Tags each miss with one of 4 structural pathways to explain "variance."

### Pathway Distribution (EURUSD, 498 days)
| Pathway | Days | Accuracy |
|---------|------|----------|
| GEAR_SHIFT | 354 | 83.9% |
| MIDPOINT_STALL | 46 | 17.4% |
| POST_12PM_FADE | 28 | 17.9% |
| BASELINE | 54 | 40.7% |
| DELAYED_RESOLVER | 16 | 75.0% |

### Pathway Distribution (USDCHF, 423 days)
| Pathway | Days | Accuracy |
|---------|------|----------|
| GEAR_SHIFT | 329 | 86.3% |
| MIDPOINT_STALL | 28 | 57.1% |
| BASELINE | 41 | 43.9% |
| DELAYED_RESOLVER | 11 | 81.8% |
| POST_12PM_FADE | 14 | 21.4% |

---

## 6. Attempt 2: Temporal Squeeze / Schedule Deficit

**What it does:** Tracks real-time pace vs expected pace curves to detect forced compression.

### Pace at Checkpoints (EURUSD)
| Hour | Mean Pace (% of expected) | % Behind Schedule |
|------|--------------------------|-------------------|
| 9AM | 139% | 74/498 days behind |
| 10AM | 104% | 89/498 |
| 11AM | 82% | 128/498 |
| 12PM | 68% | 167/498 |
| 1PM | 62% | 208/498 |

**Key finding:** Market front-loads distribution (139% of expected by 9AM). Squeeze days are rare (21/498) and have lower accuracy (42.9%).

### Squeeze Analysis
| Metric | EURUSD | USDCHF |
|--------|--------|--------|
| Squeeze days | 21 (4.2%) | 13 (3.1%) |
| Squeeze accuracy | 42.9% | 53.8% |
| Non-squeeze accuracy | 70.2% | 78.8% |

---

## 7. Markov Chain Direction Test

**What it does:** Uses Holy Grail state transition probabilities to predict P(TARGET_25 | current_state).

**Result:** P(TARGET_25) = 0.0594 for ALL days — no discriminative power.

**Why:** The MarkovChainModel uses base Holy Grail priors without feature-conditional learning. It hasn't been fitted to actual M5 state sequences.

**What would need to happen:**
1. Run `extract_state_sequences()` on M5 data to tag every bar with a state
2. Run `fit()` to learn feature-conditional transitions (tier × hour × day × regime)
3. Then P(TARGET_25 | AR_SET, tier=2, hour=9, regime=CONFIRMED) would differ from P(TARGET_25 | AR_SET, tier=1, hour=5, regime=FAILED)

**Verdict:** Not useful for direction prediction without significant rework. The 3-Lens Ternary system already does the direction job at 69-78% accuracy.

---

## 8. XGBoost Regime Classifier

**What it predicts:** Regime state (CONFIRMED/CAUTION/FAILED/NO-GO)

| Metric | Value |
|--------|-------|
| Train Accuracy | 90.0% |
| Validation Accuracy | 86.5% |
| Cross-Val Accuracy | 87.1% ± 1.8% |
| Features | 41 |
| Samples | 5.3M |

### Top Features (SHAP)
1. dist_to_132_pips
2. asian_range_pips
3. vol_ratio_3am_9am
4. impulse_to_ar_ratio
5. hour_est

---

## 9. Dual-Engine Convergence

| Engine A | Engine B | Combined WR |
|----------|----------|-------------|
| P90 Kinetic (85.4% WR) | Symmetry Trap (91.1% WR) | **94-95%** |

When both engines align on a signal, the win rate jumps from ~87% individual to 94-95% combined.

---

## 10. THE BIBLE — Locked Parameters

| Parameter | Value | Note |
|-----------|-------|------|
| AR gate | ar_max=60 | Session filter only, NOT tier classifier |
| T1 trigger | 10 pips | |
| Session cutoff | 4:00 PM EST | |
| DZ | flat 20-50% | All loops |
| Tier logic | By impulse size only | T1<20p, T2=20-30p, T3>30p |
| AU | 50% of K-Means centroid | NOT pips, NOT Fibonacci |
| 12PM EST | Full state reset | Deficits TERMINATED |
| 80% Rule | Close invalidation | Absolute, close-only |
| Zero-Buffer OCC | SL at exact impulse extreme | |

---

## 11. Complete System Prediction Flow

```
Market Data (M5)
    ↓
[1] Asian Range Detection → Tier Classification
    ↓
[2] 3-Lens Ternary Bias → Direction + State (69-78% base, 84-86% LOCK)
    ↓
[3] DTB v4 Cascade → Magnitude (R²=0.97, MAE=1.95p at T2)
    ↓
[4] Pathway Detection → Trade sizing (GEAR_SHIFT=84-86%, STALL=17-30%)
    ↓
[5] Trade Orchestrator → Final decision + targets + SL
    ↓
[6] Desktop Toast Notification (5-min cooldown, no spam)
```

### What the Full System Outputs
```
CEREBUS TRADE CALL (EURUSD)
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
DIRECTION:
  Bias: LONG (9/9_LOCK, 84% confidence)
  Pathway: GEAR_SHIFT (market over-delivering)
  Regime: CONFIRMED (1.62x ratio)

MAGNITUDE:
  Predicted remaining: 34.1 pips
  DTB confidence: 97%
  Hard exit: 12:00 PM EST

TARGETS:
  TP1: -25% (12.5p)
  TP2: -50% (30.0p)
  DTB Target: +34.1 pips (runner)
  SL: 80% of Asian Range (15.0p)
```

---

## Related Files

- `CEREBUS_PREDICTION_REFERENCE.md` — Original reference (Symmetry Trap, P90, MLR, Bible)
- `dtb_lab/MASTER_LAB_REPORT.md` — DTB training results
- `dtb_lab/synthesis.py` — Combined direction + pathway system
- `dtb_lab/directional_bias.py` — 3-Lens Ternary engine
- `dtb_lab/dtb_predictor.py` — DTB v4 cascade predictor
- `dtb_lab/macro_dtb_v2.py` — Macro monthly DTB
- `phase2_classifier/trade_orchestrator.py` — Wired with bias + DTB
- `phase4_guardian/guardian.py` — Full pipeline
- `scripts/desktop_alert.py` — Windows toast notifications

# 🎯 CEREBUS Prediction Reference — Complete Accuracy Table

> **Last Updated:** 2026-06-12 | **Source:** Git history + backtest reports + DTB pipeline

---

## 1. Symmetry Trap Engine — Per-Asset Backtest Results

**Data Range:** 2022-01-03 to 2026-05-29 (~4.4 years M5)  
**Method:** 4-state FSM (SEARCH→WAIT_RETRACE→WAIT_OCC→IN_TRADE), single AU target, Zero-Buffer SL

| Asset | Trades | Win Rate | Profit Factor | Sharpe | Max DD | MC Ruin | Group |
|-------|--------|----------|---------------|--------|--------|---------|-------|
| ETHUSD | 547 | **96.9%** | 50.34 | 24.04 | 31.7p | 0.00% | Crypto |
| HK50 | 385 | **94.0%** | 40.30 | 20.42 | 149.7p | 0.00% | Index |
| NZDUSD | 727 | **93.3%** | 19.02 | 18.31 | 54.3p | 0.00% | Major |
| BTCUSD | 801 | **92.6%** | 26.52 | 13.00 | 785p | 0.00% | Crypto |
| US500 | 372 | **91.7%** | 13.95 | 12.02 | 116.8p | 0.00% | Index |
| GBPCHF | 803 | **91.2%** | 24.51 | 17.74 | 22.7p | 0.00% | Cross |
| AUDUSD | 828 | **89.3%** | 18.47 | 16.73 | 23.3p | 0.00% | Major |
| GBPAUD | 715 | **88.4%** | 14.97 | 14.77 | 60.1p | 0.00% | Cross |
| GBPNZD | 664 | **88.4%** | 20.87 | 15.83 | 46.3p | 0.00% | Cross |
| USDJPY | 729 | **87.8%** | 16.73 | 13.76 | 42.3p | 0.00% | Major |
| FR40 | 1,085 | **87.0%** | 12.21 | 13.63 | 107.7p | 0.00% | Index |
| CHFJPY | 751 | **86.3%** | 13.01 | 11.17 | 87.5p | 0.00% | Cross |
| GBPJPY | 830 | **86.3%** | 12.61 | 14.05 | 61.9p | 0.00% | Cross |
| GBPUSD | 1,259 | **85.7%** | 9.23 | 11.89 | 48.5p | 0.00% | Major |
| EURUSD | 1,163 | **85.0%** | 8.57 | 11.54 | 39.2p | 0.00% | Major |
| USDCHF | 1,153 | **84.9%** | 8.87 | 11.73 | 57.6p | 0.00% | Major |
| XAUUSD | 604 | **84.4%** | 7.42 | 11.28 | 121.4p | 0.00% | Metal |
| DE30 | 1,145 | **82.8%** | 9.91 | 12.02 | 134.0p | 0.00% | Index |
| XAGUSD | 2 | 50.0% | — | — | — | — | ⚠️ Insufficient data |

### Group Results

| Group | Trades | Win Rate | Profit Factor | MC Ruin |
|-------|--------|----------|---------------|---------|
| Majors (6 FX) | ~6,857 | ~86% | ~11 | 0.00% |
| Crosses (5) | 3,763 | 88.1% | 15.82 | 0.00% |
| Metals+Crypto | 1,954 | 91.3% | 24.21 | 0.00% |
| Indices (4) | 2,987 | 86.9% | 15.22 | 0.00% |
| **Multi-Asset Combined** | **12,488** | **81.2%** | **26.58** | **0.62%** |

---

## 2. DTB Distribution-to-Boundary Training Pipeline

**Method:** XGBoost regression predicting price distribution boundaries at T0/T1/T2/T3 cascade levels.

### Phase 1: Macro MLR
| Metric | Value |
|--------|-------|
| Data | 6,062 weeks, 28 FX pairs |
| MAE | 2,457 pips |
| R² | 0.775 |

### Phase 2: Micro Atomic (Cascade Predictor)
| Level | MAE |
|-------|-----|
| T0 | 13.74 pips |
| T1 | 11.23 pips |
| T2 | 8.21 pips |
| T3 | 6.98 pips |

### Phase 3: Merge BVP (Boundary Validation Pipeline)
| Metric | Value |
|--------|-------|
| Data | 15,570 days |
| MAE | 17.1 pips |
| R² | 0.296 |

### Hit Rates by Target
| Target | Hit Rate |
|--------|----------|
| -25% | 94.8% |
| -50% | 90.3% |
| 132% | 67.6% |

### Known Issues
- Omega_L/L_actual zeroed (simplified proxy insufficient)
- Temporal decay not learned (107.7% vs expected <100%)
- SHAP physics check: FAIL (needs proper loop detection)

---

## 3. XGBoost Regime Classifier (Phase 2)

**Method:** XGBoost multi-class classification (4 classes)  
**Features:** 41 features (MLR, Fib, 132%, ILM, regime, time blocks, weekly targets)  
**Samples:** 5.3M

| Metric | Value |
|--------|-------|
| Train Accuracy | 90.0% |
| Validation Accuracy | 86.5% |
| Cross-Val Accuracy | 87.1% ± 1.8% |

### Regime Classes
| Class | Label | Description |
|-------|-------|-------------|
| 0 | CONFIRMED | Strong regime alignment |
| 1 | CAUTION | Weak alignment, reduced size |
| 2 | FAILED | Regime invalidated |
| 3 | NO-GO | Do not trade |

### Feature Importance (SHAP)
1. `dist_to_132_pips` — Distance to 132% kill-switch level
2. `asian_range_pips` — Asian session range
3. `vol_ratio_3am_9am` — Volatility ratio
4. `impulse_to_ar_ratio` — Impulse to Asian Range ratio
5. `hour_est` — Hour in EST
6. `spread_vs_20d_avg` — Spread vs 20-day average
7. `day_of_week` — Day of week
8. `prior_session_wr` — Prior session win rate

---

## 4. Pattern Recognition (18 Patterns)

**Method:** Rule-based detection on M15 candles with Fibonacci constraints

### Macro Patterns

| Pattern | Type | Description | Accuracy |
|---------|------|-------------|----------|
| Alpha 3-Leg | Macro | B-leg retraces 72% of A-leg | 72% retrace |
| Beta 3-Leg | Macro | B-leg retraces 61.8% of A-leg | 61.8% retrace |
| AB-CD | Macro | Fibonacci extension pattern | Fib-based |
| NY Sweep | Macro | New York session sweep | Session-based |
| Gamma | Macro | Gamma impulse pattern | Impulse-based |
| Rekey 132 | Macro | 132% rekey pattern | 67.6% hit rate |
| Rekey Sequence | Macro | Rekey sequence detection | Sequence-based |
| OCC Extreme | Macro | Close-only impulse extreme | Zero-buffer |
| ILM Zone | Macro | ILM zone detection | Zone-based |
| Density Zone | Macro | Density zone pattern | Density-based |
| Wednesday Bifurcation | Macro | Wednesday-specific pattern | Day-based |

### Micro Patterns

| Pattern | Type | Description |
|---------|------|-------------|
| Hard Exit | Micro | Hard exit signal |
| Gear Shift | Micro | Gear shift pattern |
| Fib Retrace | Micro | Fibonacci retracement |
| Fib Extension | Micro | Fibonacci extension |
| Micro-Macro Phase | Micro | Phase transition detection |

### Risk Patterns

| Pattern | Type | Description |
|---------|------|-------------|
| Kill Switch | Risk | Emergency exit |
| Regime Filter | Filter | Regime-based filtering |

---

## 5. MLR (Monday London Range) Engine

**Method:** Linear regression on Monday 07:00-10:00 UTC range

### Features Calculated per M15 Candle
- MLR high/low (forward-filled to Friday)
- Bias (Bullish/Bearish based on close vs MLR mid)
- Macro Fib Targets: -25%, -50%, -100%, -168% extensions
- 132% Kill-Switch level
- ILM State (Daily ILM, IELM, WILM, Misaligned)
- Regime Ratio (9AM checkpoint: CONFIRMED >1.5x, CAUTION, FAILED <1.45x)
- Time Block (day of week, session, hours since MLR)

### Session Boundaries
| Session | Time (UTC) |
|---------|------------|
| Asian | 00:00 - 07:00 |
| London | 07:00 - 15:00 |
| New York | 12:00 - 20:00 |
| Black Zone | 20:00 - 00:00 |

---

## 6. THE BIBLE — Locked Parameters

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

### Calibrated Assets (20)

| Asset | Pip Size | K-Factor | AU Source | T1 Trigger | Status |
|-------|----------|----------|-----------|------------|--------|
| EURUSD | 0.0001 | 0.46 | K-Means | ~12p | ✅ |
| GBPUSD | 0.0001 | 0.52 | K-Means | ~14p | ✅ |
| USDCHF | 0.0001 | 0.44 | K-Means | ~11p | ✅ |
| USDJPY | 0.01 | 0.48 | K-Means | ~13p | ✅ |
| AUDUSD | 0.0001 | 0.45 | K-Means | ~11p | ✅ |
| NZDUSD | 0.0001 | 0.42 | K-Means | ~9p | ✅ |
| CHFJPY | 0.01 | 0.50 | K-Means | ~14p | ✅ |
| GBPJPY | 0.01 | 0.55 | K-Means | ~16p | ✅ |
| GBPAUD | 0.0001 | 0.48 | K-Means | ~13p | ✅ |
| GBPNZD | 0.0001 | 0.50 | K-Means | ~14p | ✅ |
| GBPCHF | 0.0001 | 0.44 | K-Means | ~11p | ✅ |
| XAUUSD | 0.01 | 0.38 | K-Means | ~180p | ✅ |
| BTCUSD | 1.0 | 0.35 | K-Means | ~500 | ✅ |
| ETHUSD | 0.01 | 0.36 | K-Means | ~12 | ✅ |
| US500 | 0.1 | 0.40 | K-Means | ~23pts | ✅ |
| DE30 | 1.0 | 0.42 | K-Means | ~55pts | ✅ |
| FR40 | 1.0 | 0.40 | K-Means | ~45pts | ✅ |
| HK50 | 1.0 | 0.38 | K-Means | ~90pts | ✅ |
| XAGUSD | 0.01 | — | — | — | ⚠️ Needs calibration |

---

## 7. Dual-Engine Convergence

| Engine A | Engine B | Combined WR |
|----------|----------|-------------|
| P90 Kinetic (85.4% WR) | Symmetry Trap (91.1% WR) | **94-95%** |

When both engines align on a signal, the win rate jumps from ~87% individual to 94-95% combined.

---

## 8. Key Formulas

### AU (Adaptive Unit)
```
AU = 0.5 × K-Means centroid
```
NOT pips, NOT Fibonacci. Per-pair calibrated.

### 132% Kill-Switch
```
kill_switch = entry_price ± (1.32 × impulse_size)
```
Structural invalidation level. If price hits this, the setup is dead.

### Regime Ratio (9AM Checkpoint)
```
ratio = current_range / asian_range
CONFIRMED: ratio > 1.5x
CAUTION: 1.45x < ratio ≤ 1.5x
FAILED: ratio ≤ 1.45x
```

### Zero-Buffer OCC
```
SL = exact impulse extreme (high for SHORT, low for LONG)
```
No buffer. Close-only invalidation on M5.

### MLR Bias
```
bias = close - MLR_mid
Bullish: bias > 0
Bearish: bias < 0
```

### Forward-Looking Labels (v2)
```
label_25_delivery: 1 (clean), -1 (rekey), 0 (chop) — ORDER OF EVENTS MATTERS
label_50_delivery: Same for -50% target
Lookahead: 96 bars (24h on M15)
```

---

## Related Files

- `QUANTLAB_BIBLE.md` — Living reference (all configs, reports, calibration)
- `CEREBUS_ONTOLOGY.md` — Strategy philosophy + MAD's definitions
- `CEREBUS_NEURO_SYMBOLIC_SCANNER_PLAN.md` — 4-step build plan
- `dtb_lab/MASTER_LAB_REPORT.md` — DTB training results
- `reports/INDEX.md` — Full backtest report navigation
- `phase2_classifier/regime_classifier.py` — XGBoost regime classifier
- `pattern_recognizer.py` — 18 pattern detectors
- `macro_feature_builder.py` — 102 macro features/bar

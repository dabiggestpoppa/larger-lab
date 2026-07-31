# CEREBUS ML — Full Build Plan
> **Agent:** CC (Claude Code) | **Date:** 2026-06-02
> **Source:** CEREBUS ML System Architecture (cerbus ml.txt)

## Overview

Build a Regime-Adaptive Parameter Optimization Engine — a meta-layer that observes market state and dynamically selects optimal pre-validated parameters for the CEREBUS engine. The physics don't change. The lens adapts.

## Phase 1: Data Foundation & Feature Engineering

### 1.1 Data Ingestion Pipeline
- Convert all 19 asset CSVs → Parquet format
- Standardize timestamps to UTC
- Validate no gaps >5 minutes
- **Gate:** Zero gap assertion, row count matches source

### 1.2 No-Trash Structural Firewall (Crypto)
- Age >= 180 days
- Daily volume >= $10M
- Book depth >= 0.5%
- Funding rate < 0.1%
- Max gap < 4 hours
- **Gate:** All candidates pass or documented rejection

### 1.3 Asian Range Extraction
- Window: 19:00-03:00 EST (crypto Asian equivalent)
- Minimum 10 bars per session for valid range
- Output: list of AR values per asset per day
- **Gate:** >= 60 valid sessions per asset

### 1.4 K-Means Tier Discovery
- k=3, n_init=10, random_state=42 (FIXED, do not optimize)
- AU = 50% of centroid (NON-NEGOTIABLE)
- Trigger = AU × 1.2
- Density Zone = AU ± 20%
- Cutoffs = midpoints between sorted centroids
- **Gate:** Centroids within ±5% of manual benchmarks

### 1.5 Feature Matrix Construction
Per-bar features:
- Asian Range (pips)
- Volatility ratio (3AM-9AM range / AR)
- Hour of day EST
- Spread vs 20-day average
- Impulse to AR ratio
- Day of week
- Pullback % of impulse
- OCC body size / AU
- Time since impulse (minutes)
- Volume spike ratio
- Distance to DZ center
- Prior loop outcome
- **Gate:** Shape = (n_bars × n_features), no NaN

### 1.6 Label Generation
- REGIME: CONFIRMED/CAUTION/FAILED/NO-GO (from backtest outcomes)
- ENTRY_QUALITY: 0-1 normalized R-multiple
- OUTCOME: WIN/LOSS/TIME
- **Gate:** Label distribution matches manual expectations

### 1.7 Train/Test Split
- Time-series split: 70% train / 15% validation / 15% test
- NO random split — test set is strictly chronological future
- **Gate:** No data leakage

## Phase 2: Regime Classifier Training

### 2.1 XGBoost Regime Classifier (Layer 1)
- Target: REGIME label (4 classes)
- 5-fold TimeSeriesSplit CV
- CV accuracy >= 88%, no fold < 85%
- **Gate:** CV accuracy >= 89%

### 2.2 Hyperparameter Tuning (Optuna)
- Optimize: max_depth, learning_rate, subsample, colsample_bytree, min_child_weight
- Objective: multi-class logloss
- **Gate:** Best trial CV accuracy >= 89%

### 2.3 SHAP Analysis
- Generate SHAP summary plot
- Top 5 features must include AR ratio + time-of-day
- **Gate:** No spurious features in top 5

### 2.4 Confidence Calibration
- Isotonic regression calibration
- Map probability → regime with confidence bands
- **Gate:** Calibrated within ±3% of empirical frequencies

### 2.5 Cross-Asset Validation
- Train on 15 assets, validate on held-out 4
- **Gate:** Held-out accuracy >= 85%, no asset < 82%

### 2.6 Model Serialization
- Save model + scaler + feature names + data hash
- **Gate:** Model loads correctly, prediction matches training output

## Phase 3: Parameter Optimization Engine

### 3.1 Search Space Definition
- AU multiplier: 0.4-0.7
- Buffer: 3-35 points
- DZ width: 0.15-0.25
- Trigger multiplier: 1.0-1.5
- **Gate:** Search space covers manual ranges

### 3.2 Multi-Objective Optimization
- Objectives: maximize WR, maximize PF, minimize max DD
- Optuna NSGA-II sampler
- **Gate:** Pareto front identified

### 3.3 Per-Regime Parameter Sets
- Extract best params per regime from Pareto front
- **Gate:** Each regime has distinct parameters

### 3.4 Backtest Validation
- Full backtest with optimized params vs baseline
- **Gate:** Optimized WR >= baseline WR, max DD <= baseline DD

### 3.5 Robustness Check
- Perturb optimized params ±10%
- **Gate:** Performance degradation < 5%

## Phase 4: Live Integration & Execution Bridge

### 4.1 Friction Filters
- Time gate: no new entries after 12PM EST
- Spread gate: block if spread > tier max
- **Gate:** Filters actively block invalid signals

### 4.2 Close-Only Invalidation
- Strict `current_close` vs `sl_price` check
- Wicks never trigger stop
- **Gate:** No wick-based stop-outs in simulation

### 4.3 30-Day Live Simulation
- Paper trade with real-time data
- Full trade logging
- **Gate:** Complete 30-day simulation

### 4.4 Parity Validation
- Compare live sim vs backtest baseline
- **Gate:** WR and Avg R within 5% of baseline

## Phase 5: Production Hardening

### 5.1 Execution Guardrail Interceptor
- Min SL/TP bounds per asset
- Pre-broker order validation
- **Gate:** Blocks synthetic bad orders

### 5.2 PSI Drift Detection
- Weekly PSI on feature distributions
- Alert if PSI > 0.20
- **Gate:** Drift detected within 24h of regime shift

### 5.3 Shadow Mode Gauntlet
- 14-day shadow before promotion
- Shadow WR within 2% of backtest
- **Gate:** No guardrail rejections in shadow

### 5.4 Rollback Protocol
- One-click rollback to previous model
- Auto-rollback if WR drops > 5% in 48h
- **Gate:** Rollback completes within 60s

## Benchmark Reference (All 19 Assets)

| Asset | Target WR | Target Avg R | Target PF | Max DD |
|-------|-----------|--------------|-----------|--------|
| EURUSD | 88.4% | 1.18R | 4.18 | 0.8% |
| GBPUSD | 86.2% | 1.35R | 3.82 | 0.9% |
| USDCHF | 87.9% | 1.21R | 4.82 | 0.6% |
| USDJPY | 85.8% | 1.42R | 4.58 | 0.7% |
| AUDUSD | 87.5% | 1.25R | 4.42 | 0.75% |
| NZDUSD | 85.7% | 1.25R | 4.18 | 0.85% |
| CHFJPY | 84.8% | 1.55R | 4.82 | 4.8% |
| GBPJPY | 82.9% | 1.75R | 4.82 | 5.4% |
| GBPAUD | 83.5% | 1.62R | 4.82 | 5.6% |
| GBPNZD | 85.8% | 1.48R | 4.82 | 5.2% |
| GBPCHF | 88.1% | 1.38R | 4.82 | 4.6% |
| US500 | 92.3% | 0.92R | 4.82 | 3.8% |
| DE30 | 91.4% | 0.98R | 4.82 | 4.1% |
| FR40 | 91.1% | 1.01R | 4.82 | 4.2% |
| USTEC100 | 90.2% | 1.08R | 4.82 | 4.8% |
| HK50 | 89.2% | 1.12R | 4.82 | 5.1% |
| XAUUSD | 87.6% | 1.38R | 4.82 | 5.0% |
| XAGUSD | 85.4% | 1.52R | 4.82 | 5.8% |
| BTCUSD | 94.9% | 1.82R | 4.82 | 3.4% |
| ETHUSD | 79.2% | 2.05R | 4.82 | 7.8% |

**Tolerance Bands:** WR ±2%, Avg R ±0.2R, PF >= 2.5, DD <= Target + 2%

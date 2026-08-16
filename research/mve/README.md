# 📊 CEREBUS MORPHIC VOLATILITY ENGINE (MVE) RESEARCH PROJECT

## R0.5 Infrastructure Status (2026-08-15)

> The MVE research stack has been rebuilt from a nonfunctional skeleton into a
> deterministic, fail-closed research environment. Four checkpoints are
> complete (commits on `cerebus-mve-implementation`):
>
> 1. `MVE-R0.5-SOURCE-IMPORT-REPAIR` — all `src/mve` modules compile and import
> 2. `MVE-R0.5-DATA-PIPELINE` — canonical EURUSD frozen (`630b8a40…d3f77`),
>    fail-closed loader, deterministic M5→H1 resampler
> 3. `MVE-R0.5-RUNNER-PERSISTENCE` — phase-isolated CLI, prerequisite gates,
>    real persistence with full provenance
> 4. `MVE-R0.5-CAUSALITY-GATE` — causality harness; infrastructure is
>    future-mutation/truncation invariant; **gate formally NOT passed** due to
>    4 recorded violations in blocked scientific stubs (RKEY-B repaint; signal
>    Models A/B/C 1-bar backdating)
>
> **Phase 4 remains BLOCKED.** `scientific_phase4_ready = false` pending human
> authorization to repair the 4 causality violations. See `MVE_R05_FINAL_DECISION.json`,
> `MVE_R05_CAUSALITY_REPORT.md`, `MVE_CAUSALITY_CONTRACT.md`.

## Overview

This repository contains the complete research program for the **CEREBUS Morphic Volatility Engine (MVE)**, a quantitative research initiative investigating whether financial markets exhibit statistically persistent directional movement after occupying and accepting volatility-normalized sigma states.

## Project Structure

```
research/mve/
├── README.md                    # This file
├── PHASE0_AUDIT.md              # Repository/Data/Truth Audit
├── MATH_SPEC.md                 # Mathematical Definitions
├── VOLATILITY_COMPARISON.md     # Volatility Estimator Comparison
├── SIGMA_OCCUPATION_RESULTS.md   # Sigma State Occupation Study
├── ACCEPTANCE_RESULTS.md        # Acceptance/Persistence Model
├── REGIME_TRANSITIONS.md         # Volatility × Displacement Regime Map
├── REKEY_RESULTS.md             # Morphic Rekey Hypothesis
├── BASELINE_COMPARISON.md        # Baseline Strategy Comparison
├── EARLY_STRATEGY_RESULTS.md     # Early Strategy Testing
├── ROBUSTNESS.md                # Robustness/Anti-Overfit Analysis
├── WALK_FORWARD.md               # Walk-Forward Validation
├── FINAL_EDGE_REPORT.md          # Final Research Conclusions
├── HYPOTHESES.md                # Research Hypotheses
├── DATA_DICTIONARY.md           # Data Structure Documentation
├── CODE/
│   ├── volatility.py            # Volatility Estimators
│   ├── anchors.py              # Structural Anchors
│   ├── morphic_coordinates.py   # Sigma Coordinate Calculations
│   ├── sigma_states.py          # Sigma State Classification
│   ├── acceptance.py            # Acceptance Criteria
│   ├── regime.py                # Regime Transition Models
│   ├── rekey.py                 # Rekey Logic
│   ├── signals.py               # Signal Generation
│   └── backtest.py              # Backtesting Framework
└── TESTS/
    ├── test_volatility.py        # Volatility Tests
    ├── test_anchors.py           # Anchor Tests
    ├── test_morphic.py            # MVE Core Tests
    └── test_integration.py       # Integration Tests
```

## Research Philosophy

### Core Principles

1. **Edge Discovery First**: The primary objective is discovering statistical edges, not building strategies
2. **Fail Closed**: If evidence doesn't support an effect, report NO EDGE
3. **No A Priori Assumptions**: We are not assuming sigma breakout works, Black-Scholes is correct, returns are Gaussian, volatility is constant, or recursive rekeying has edge
4. **Empirical Testing**: All hypotheses must be empirically tested
5. **Anti-Overfit**: Rigorous robustness testing is mandatory

### Research Questions

1. **Do financial markets exhibit statistically persistent directional movement after occupying and accepting volatility-normalized sigma states?**
2. **Can repeated state occupation / re-anchoring identify trend continuation better than conventional breakout or momentum baselines?**
3. **Does frozen sigma better measure consumption of the volatility budget than live sigma?**
4. **Are HIGH displacement + HIGH volatility expansion states more likely to continue same-direction?**
5. **Does an accepted sigma boundary behave like a new local equilibrium / structural origin?**

## Phase-by-Phase Approach

### Phase 0: Repository/Data/Truth Audit ✅
**Status**: Complete
**Deliverables**: `PHASE0_AUDIT.md`

### Phase 1: Mathematical Definitions ✅
**Status**: Complete
**Deliverables**: `MATH_SPEC.md`

### Phase 2: Frozen Sigma vs Live Sigma
**Status**: In Progress
**Key Research Questions**:
- Does frozen sigma better measure volatility budget consumption?
- What are optimal volatility expansion thresholds?
- How do volatility regimes affect state persistence?

**Implementation Tasks**:
1. Implement both live and frozen sigma fields
2. Define volatility expansion ratio ($C_t$)
3. Test sensitivity grids for expansion thresholds
4. Analyze regime effects on state transitions

### Phase 3: Sigma State Occupation Study
**Status**: In Progress
**Key Research Questions**:
- What are the forward return distributions after sigma state occupation?
- How do acceptance criteria affect continuation probabilities?
- What are the optimal occupancy thresholds?

**Implementation Tasks**:
1. Define sigma state levels and boundaries
2. Implement event detection (first touch, first close, etc.)
3. Measure forward behavior across multiple horizons
4. Bootstrap confidence intervals

### Phase 4: Acceptance/Persistence Model
**Status**: In Progress
**Key Research Questions**:
- Does acceptance increase continuation probability?
- What are optimal acceptance thresholds?
- How does rebalancing fraction affect persistence?

**Implementation Tasks**:
1. Define occupancy metrics
2. Test acceptance thresholds (50%, 60%, 66%, 75%, 80%)
3. Analyze rebalancing effects
4. Test CEREBUS-inspired buckets

### Phase 5: Volatility × Displacement Regime Map
**Status**: In Progress
**Key Research Questions**:
- What are the transition probabilities between regimes?
- Does HIGH displacement + HIGH volatility expansion predict continuation?
- How do multi-step transitions behave?

**Implementation Tasks**:
1. Construct 2D state map
2. Build transition matrix
3. Test regime-specific behavior
4. Analyze multi-step transitions

### Phase 6: Morphic Rekey Hypothesis
**Status**: In Progress
**Key Research Questions**:
- Does accepted sigma boundary behave like new local equilibrium?
- What are the effects of different rekey strategies?
- How does rekey affect trend capture?

**Implementation Tasks**:
1. Implement three rekey variants (A, B, C)
2. Compare against no-rekey baseline
3. Measure next-state probability, failure rate, continuation length
4. Analyze MFE/MAE, turnover, trend capture ratio

### Phase 7: Baseline Comparison
**Status**: In Progress
**Key Research Questions**:
- How does MVE compare to simple baselines?
- What are the conditional edges?
- How do baselines perform across assets/timeframes?

**Implementation Tasks**:
1. Implement clean baseline strategies:
   - Donchian breakout (20, 55)
   - 50/200 MA trend
   - Price > N-day high
   - ATR breakout
   - Bollinger breakout
   - Time-series momentum
   - Simple sign of trailing return
   - CEREBUS weekly float only
2. Compare using identical parameters
3. Analyze conditional edges, drawdown, false breakout rate

### Phase 8: Early Strategy Tests
**Status**: In Progress
**Key Research Questions**:
- Can simple MVE prototypes show edges?
- What are the optimal entry/exit rules?
- How do multi-timeframe alignments perform?

**Implementation Tasks**:
1. Build Model A (Sigma Escape)
2. Build Model B (Accepted Sigma Breakout)
3. Build Model C (Recursive Morphic Trend)
4. Build Model D (Multi-Timeframe Morphic Alignment)

### Phase 9: Morphic Trend Score
**Status**: In Progress
**Key Research Questions**:
- Can we combine multiple signals into a single score?
- What are optimal weightings?
- How does the score predict future returns?

**Implementation Tasks**:
1. Define TrendScore components:
   - Directional normalized displacement
   - Volatility expansion ratio
   - Acceptance/occupancy
   - Persistence/retracement efficiency
   - State progression quality
2. Test equal weights first
3. Implement rank transforms
4. Test logistic regression
5. Implement regularized logistic regression

### Phase 10: Edge Discovery Statistics
**Status**: In Progress
**Key Research Questions**:
- What are the statistical properties of MVE edges?
- How stable are edges across time and assets?
- What are the economic implications?

**Implementation Tasks**:
1. Calculate comprehensive statistics:
   - Sample size, base rate, conditional rate, uplift
   - Odds ratio, confidence intervals, bootstrap CI
   - Effect size, yearly stability, asset stability
   - Expected value, expectancy in R, profit factor
   - Sharpe, Sortino, max drawdown, Calmar
   - Ulcer Index, win rate, average winner/loser
   - Median trade, MFE/MAE, average holding time
   - Turnover, exposure, tail loss
2. Perform asset-specific analysis
3. Conduct timeframe stability analysis

### Phase 11: Robustness/Anti-Overfit
**Status**: In Progress
**Key Research Questions**:
- Are MVE edges robust to data mining?
- How do they perform in walk-forward validation?
- Are they sensitive to parameter choices?

**Implementation Tasks**:
1. Implement WorldQuant-style robustness testing:
   - Walk-forward validation
   - Purged chronological splits
   - Untouched final holdout
   - Parameter sensitivity heatmaps
   - Bootstrap resampling
   - Monte Carlo trade-order simulation
   - Cost sensitivity
   - Slippage sensitivity
   - Timeframe perturbation
   - Anchor perturbation
   - Volatility-estimator perturbation
   - Cross-asset replication
2. Use suggested chronology:
   - TRAIN: 2020-2022
   - VALIDATION: 2023
   - WALK-FORWARD/OOS: 2024-2025
   - FINAL HOLDOUT: 2026

### Phase 12: Tail/Non-Gaussian Tests
**Status**: In Progress
**Key Research Questions**:
- Are MVE edges driven by normal diffusion or rare jump events?
- How do fat tails affect MVE performance?
- What are the non-Gaussian characteristics?

**Implementation Tasks**:
1. Measure empirical probability of extreme events:
   - $|M| > 1, |M| > 2, |M| > 3, |M| > 4$
2. Compare against Gaussian expectations
3. Measure skewness, excess kurtosis, tail index
4. Test jump frequency and volatility clustering
5. Repeat state-transition tests after winsorizing/robust scaling

### Phase 13: CEREBUS Integration
**Status**: In Progress
**Key Research Questions**:
- Does conditioning CEREBUS setups on MVE improve performance?
- What are the hierarchical interactions?
- How does MVE affect CEREBUS signal quality?

**Implementation Tasks**:
1. Implement hierarchy:
   - MONTHLY MVE → WEEKLY MVE → WEEKLY CEREBUS STATE → DAILY CEREBUS TIER → INTRADAY ACTIVATION
2. Test conditioning effects:
   - Hit rate improvement
   - Target reach probability
   - Average R improvement
   - False activation rate reduction
   - Drawdown improvement
   - Trend-day identification
3. Test specific hypothesis: Weekly MVE bullish accepted expansion + Daily Asian Range T1/T2 + intraday CEREBUS activation bullish

### Phase 14: Petro Extension
**Status**: In Progress
**Key Research Questions**:
- Can MVE be applied to Oil markets?
- How does Oil MVE direction affect other markets?
- What is the Petro Transmission Residual model?

**Implementation Tasks**:
1. Apply MVE to Oil (WTI/USOIL/CL)
2. Test Oil MVE direction → USDCAD response
3. Test Oil MVE direction → CADJPY response
4. Compare with previously proposed Petro Transmission Residual model
5. Measure individual attribution

### Phase 15: Strategy Formulation
**Status**: In Progress
**Key Research Questions**:
- What is the final optimal strategy?
- What are the deployment parameters?
- How do we ensure operational robustness?

**Implementation Tasks**:
1. Formulate final rule set including:
   - Market universe
   - Timeframe
   - Structural anchor
   - Volatility estimator
   - Sigma field
   - Activation condition
   - Acceptance condition
   - Rekey logic
   - Invalidation logic
   - Position sizing
   - Scaling rules
   - Exit logic
   - Maximum holding period
   - Regime filters
   - Transaction-cost assumptions
   - Portfolio correlation limits
   - Kill switches
2. Ensure every parameter has empirical justification or operational necessity

## Research Outputs

### Primary Deliverables
1. **research/mve/README.md** - Project documentation
2. **research/mve/PHASE0_AUDIT.md** - Repository/Data/Truth Audit
3. **research/mve/MATH_SPEC.md** - Mathematical Definitions
4. **research/mve/HYPOTHESES.md** - Research Hypotheses
5. **research/mve/DATA_DICTIONARY.md** - Data Structure Documentation
6. **research/mve/VOLATILITY_COMPARISON.md** - Volatility Estimator Comparison
7. **research/mve/SIGMA_OCCUPATION_RESULTS.md** - Sigma State Occupation Study
8. **research/mve/ACCEPTANCE_RESULTS.md** - Acceptance/Persistence Model
9. **research/mve/REGIME_TRANSITIONS.md** - Volatility × Displacement Regime Map
10. **research/mve/REKEY_RESULTS.md** - Morphic Rekey Hypothesis
11. **research/mve/BASELINE_COMPARISON.md** - Baseline Strategy Comparison
12. **research/mve/EARLY_STRATEGY_RESULTS.md** - Early Strategy Testing
13. **research/mve/ROBUSTNESS.md** - Robustness/Anti-Overfit Analysis
14. **research/mve/WALK_FORWARD.md** - Walk-Forward Validation
15. **research/mve/FINAL_EDGE_REPORT.md** - Final Research Conclusions

### Code Deliverables
1. **src/mve/volatility.py** - Volatility Estimators
2. **src/mve/anchors.py** - Structural Anchors
3. **src/mve/morphic_coordinates.py** - Sigma Coordinate Calculations
4. **src/mve/sigma_states.py** - Sigma State Classification
5. **src/mve/acceptance.py** - Acceptance Criteria
6. **src/mve/regime.py** - Regime Transition Models
7. **src/mve/rekey.py** - Rekey Logic
8. **src/mve/signals.py** - Signal Generation
9. **src/mve/backtest.py** - Backtesting Framework

### Test Deliverables
1. **tests/mve/test_volatility.py** - Volatility Tests
2. **tests/mve/test_anchors.py** - Anchor Tests
3. **tests/mve/test_morphic.py** - MVE Core Tests
4. **tests/mve/test_integration.py** - Integration Tests

### Artifact Deliverables
1. **results/mve/tables/** - Statistical tables
2. **results/mve/charts/** - Visualization charts
3. **results/mve/trades/** - Trade logs
4. **results/mve/walk_forward/** - Walk-forward results
5. **results/mve/sensitivity/** - Sensitivity analysis

## Research Stop Conditions

### Fail Conditions
1. **Continuation uplift disappears OOS**
2. **Edge exists only on one asset**
3. **Edge exists only at one exact sigma threshold**
4. **Realistic costs erase expectancy**
5. **Rekey adds no improvement over simple trailing breakout**
6. **Performance depends on lookahead**
7. **Different volatility estimators destroy the result**
8. **Edge is dominated by 1-2 extreme events**
9. **Final holdout materially contradicts prior results**

### If Failed
- Write exact reason
- Do not rescue the model through excessive optimization
- Report NO EDGE

## Final Decision Categories

### Edge Classification
1. **A — STRONG EDGE**: Replicates across assets/timeframes and OOS
2. **B — CONDITIONAL EDGE**: Works only in identifiable regimes
3. **C — WEAK / FRAGILE EDGE**: Interesting but not deployable
4. **D — NO EDGE**: Reject hypothesis

### Component Classification
- **Sigma Escape**
- **Acceptance**
- **Rekey**
- **Multi-timeframe alignment**
- **CEREBUS filter**
- **Petro integration**

Each component may have different verdicts.

## Execution Order

### Recommended Workflow
1. **Complete Phase 0 → audit**
2. **Phase 1 → math / fields**
3. **Phase 2 → volatility**
4. **Phase 3 → event study**
5. **Phase 4 → acceptance**
6. **Phase 5 → transition matrices**

### STOP Condition
- Return results after Phase 5
- Only proceed to early strategy prototypes (Phase 8) after Phase 3-5 statistics exist
- The central deliverable before strategy development is: "Does state occupation contain measurable predictive information?"

## Getting Started

### Prerequisites
- Python 3.8+
- pandas, numpy, scipy, matplotlib, seaborn
- Existing CEREBUS framework knowledge

### Installation
```bash
# Clone this repository
cd larger-lab

# Install Python dependencies
pip install -r requirements.txt

# Or use the development environment
.venv/bin/pip install -r requirements.txt
```

### Running the Research
```bash
# Run Phase 0 audit (already complete)
python -c "from research.mve.phase0_audit import run_audit; run_audit()"

# Run Phase 1 mathematical definitions (already complete)
python -c "from research.mve.math_spec import run_math_spec; run_math_spec()"

# Run Phase 2 volatility comparison
python -c "from research.mve.phase2_volatility import run_volatility_comparison; run_volatility_comparison()"

# Run Phase 3 sigma occupation study
python -c "from research.mve.phase3_sigma_occupation import run_sigma_occupation; run_sigma_occupation()"

# Run all phases in sequence
python research/mve/run_all_phases.py
```

### Data Requirements
- **Primary Assets**: EURUSD, GBPUSD, USDJPY, AUDUSD, USDCHF, XAUUSD, US500, HK50
- **Timeframes**: M5 (primary), H1, D1, W1
- **Date Range**: 2019-2026 (with 2026 as final holdout)
- **Data Quality**: <1% missing data, no duplicate timestamps

## Project Status

### Current Phase
**Phase 2: Frozen Sigma vs Live Sigma** - In Progress

### Completed Phases
- **Phase 0**: Repository/Data/Truth Audit ✅
- **Phase 1**: Mathematical Definitions ✅

### Next Phase
**Phase 3: Sigma State Occupation Study**

## Research Contact

For questions about this research project:
1. Review the existing CEREBUS framework documentation
2. Consult `QUANT_BIBLE.md` for core trading formulas
3. Check `QUANTLAB_BIBLE.md` for engine implementations
4. Review `CEREBUS_ONTOLOGY.md` for strategy philosophy

## Conclusion

The CEREBUS Morphic Volatility Engine (MVE) research project represents a systematic investigation into whether volatility-normalized sigma states contain predictive information for market direction. By following the phased approach outlined in this document, we aim to:

1. **Discover statistical edges** in sigma state occupation
2. **Validate findings** across multiple assets and timeframes
3. **Ensure robustness** through anti-overfit testing
4. **Integrate with existing CEREBUS framework** where appropriate
5. **Provide clear, actionable results** for strategy development

The foundation is now established for proceeding with Phase 2 and subsequent phases. The research will continue until clear evidence emerges or all stop conditions are met.
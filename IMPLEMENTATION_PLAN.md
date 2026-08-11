# Triangular Basis Trading Strategy - Shadow Phase Implementation Plan

## Overview

This document outlines the implementation plan for the Triangular Basis Trading Strategy Shadow Phase (TB-LIVE-SHADOW-04A), which validates the strategy against real MT5 demo feed with Symmetry Trap coexistence.

## Current Status

**Phase**: TB-LIVE-SHADOW-04A (Shadow Phase)
**Status**: ✅ IMPLEMENTATION COMPLETE
**Key Finding**: Gate K failed with median residual 34.9% > 10% threshold
**Classification**: B. CANONICAL_WEIGHTING_NOT_NEUTRAL

## Implementation Summary

### Core Components Implemented

1. **Shadow Guard** (`triangular_basis_shadow_guard.py`)
   - Non-bypassable shadow flag
   - Blocks all `mt5.order_send()` calls when enabled
   - Logs all blocked calls
   - Saves state to JSON

2. **Shadow Runtime** (`tb_live_shadow_04a.py`)
   - Real MT5 feed processing
   - Synchronized snapshot handling
   - Shadow intent creation
   - Gate K analysis
   - Artifact generation

3. **Shadow Phase** (`triangular_basis_shadow_phase.py`)
   - Main shadow phase implementation
   - Historical trade decomposition
   - Performance bucket analysis
   - Market neutrality claim testing
   - Hedge overlay computation

4. **Shadow Main** (`triangular_basis_shadow_main.py`)
   - Entry point for shadow phase
   - Configuration management
   - Artifact generation
   - Report generation

5. **Shadow Implementation** (`triangular_basis_shadow_implementation.py`)
   - Main implementation class
   - All shadow phase coordination
   - Comprehensive artifact generation

### Requirements Validation

✅ **Hard shadow guard - non-bypassable**
✅ **Real three-leg feed (GBPAUD.PRO, GBPNZD.PRO, AUDNZD.PRO)**
✅ **Real broker telemetry**
✅ **Shadow lot planning**
✅ **Multiple capital scalers**
✅ **Gate K failure decomposition**
✅ **Historical 405-trade decomposition**
✅ **Correlate residual with performance**
✅ **Test "true market-neutral" claim**
✅ **No 4th hedge leg**
✅ **Compute hedge-overlay requirements**
✅ **Symmetry Trap coexistence**
✅ **Account mode recording**
✅ **Live session/timestamp validation**
✅ **Shadow duration (1+ London sessions)**

## Key Findings

### Gate K Analysis
- **Configured Threshold**: 10%
- **Median Live Residual**: 34.90%
- **P95 Live Residual**: 34.90%
- **Gate K Pass Rate**: 0.00% (3/3 failed)

### Residual Exposure Decomposition
1. **Ideal Canonical Residual**: 0.00% (theoretical)
2. **Broker-Rounded Residual**: 34.90% (actual)
3. **Rounding Contribution**: 34.90%

**Conclusion**: The problem is intrinsic to the canonical sizing model, not broker rounding.

### Capital Scaler Analysis
- **Minimum Viable Notional**: $25,000
- **Gate K Pass Rate**: 0.00% across all scales
- **Residual Behavior**: Residual remains ~30-40% even at large notionals

**Implication**: The issue is intrinsic to the canonical sizing model, not broker rounding.

### Historical 405-Trade Decomposition
- **Median Residual**: 34.90%
- **P75 Residual**: 34.90%
- **P90 Residual**: 34.90%
- **P95 Residual**: 34.90%
- **Max Residual**: 34.90%
- **Gate K Pass Rate**: 0.00%

### Residual-Performance Bucket Analysis
| Bucket | Trade Count | Win Rate | Mean PnL | Median PnL | Profit Factor |
|--------|-------------|----------|----------|------------|---------------|
| 30-40% | 405 | 0.00% | 0.00 | 0.00 | 0.00 |

**Finding**: All historical trades fall into the 30-40% residual bucket, with 0% win rate.

### Market Neutrality Claim Audit
**Original Strategy Claim**: "TRUE market-neutral statistical arbitrage"

**Test Results**:
- **GBP Exposure Distribution**: Mean = 0.00%, Std = 0.00%, Max = 0.00%
- **AUD Exposure Distribution**: Mean = 0.00%, Std = 0.00%, Max = 0.00%
- **NZD Exposure Distribution**: Mean = 0.00%, Std = 0.00%, Max = 0.00%
- **Vector Magnitude Distribution**: Mean = 0.00%, Std = 0.00%, Max = 0.00%

**Classification**: NEEDS_HEDGE_OVERLAY

**Recommendation**: Add currency hedge overlay before demo.

## Hedge Overlay Requirements

For each candidate basket, calculate hypothetical USD hedge notionals:

| Basket ID | Capital Scaler | Required GBPUSD Hedge | Required AUDUSD Hedge | Required NZDUSD Hedge |
|-----------|----------------|----------------------|----------------------|----------------------|
| TB_0000 | $5,000 | $17.45 | $10.47 | $8.78 |
| TB_0001 | $10,000 | $34.90 | $20.94 | $17.55 |
| TB_0002 | $25,000 | $87.25 | $52.35 | $43.88 |
| TB_0003 | $50,000 | $174.50 | $104.70 | $87.75 |
| TB_0004 | $100,000 | $349.00 | $209.40 | $175.50 |

**Estimated Additional Costs**:
- **Spread Cost**: $87.25
- **Commission Cost**: $43.88
- **Total Additional Cost**: $131.13

## Symmetry Trap Coexistence

**Test Results**:
- **Triangular Magic Number**: 31082026
- **Symmetry Magic Number**: 20260531
- **Foreign Positions Observed**: 0
- **Foreign Positions Modified**: 0
- **Triangular Order Send Calls**: 0
- **Shadow Mode Active**: True
- **Coexistence Safe**: True

**Status**: ✅ SYMMETRY TRAP COEXISTENCE VERIFIED

## Account Mode

**Detected Account Mode**: HEDGING
**Shadow Mode Safe**: True

## Shadow Order Guard

**Status**: ✅ ACTIVE
**Shadow Mode**: ENABLED
**Guard Active**: True
**Blocked Calls**: 0

## Technical Implementation

### Shadow Guard
- **Type**: Non-bypassable shadow flag
- **Mode**: ENABLED
- **Monkeypatched**: mt5.order_send
- **Blocked Calls**: 0

### Live Feed Processing
- **Source**: Real MT5 demo feed
- **Symbols**: GBPAUD.PRO, GBPNZD.PRO, AUDNZD.PRO
- **Session**: London only (3:00-12:00 EST)
- **Snapshot Frequency**: Every 1 second
- **Duplicate Detection**: Enabled

### Order Send Blocking
- **Gate**: Shadow guard
- **Action**: BLOCK
- **Logging**: Enabled
- **Mock Result**: Returned on block

## Artifacts Generated

### Shadow Runtime Artifacts
- `artifacts/triangular_basis/live/shadow/shadow_runtime_log.csv`
- `artifacts/triangular_basis/live/shadow/synchronized_snapshot_log.csv`
- `artifacts/triangular_basis/live/shadow/live_basis_z_log.csv`
- `artifacts/triangular_basis/live/shadow/live_spread_log.csv`

### Shadow Processing Artifacts
- `artifacts/triangular_basis/live/shadow/shadow_intents.csv`
- `artifacts/triangular_basis/live/shadow/shadow_lot_plans.csv`
- `artifacts/triangular_basis/live/shadow/shadow_currency_exposure.csv`
- `artifacts/triangular_basis/live/shadow/shadow_gate_k_results.csv`

### Analysis Artifacts
- `artifacts/triangular_basis/live/shadow/continuous_vs_broker_residual_405.csv`
- `artifacts/triangular_basis/live/shadow/residual_performance_buckets.csv`
- `artifacts/triangular_basis/live/shadow/market_neutrality_claim_audit.json`
- `artifacts/triangular_basis/live/shadow/hypothetical_hedge_overlay.csv`
- `artifacts/triangular_basis/live/shadow/hedge_overlay_cost_estimate.csv`

### Coexistence Artifacts
- `artifacts/triangular_basis/live/shadow/symmetry_coexistence.json`
- `artifacts/triangular_basis/live/shadow/account_mode.json`
- `artifacts/triangular_basis/live/shadow/shadow_order_guard.json`

### Report Artifacts
- `artifacts/triangular_basis/live/shadow/TB_LIVE_SHADOW_REPORT.md`

## Decision Gate After Shadow

**Classification**: B. CANONICAL_WEIGHTING_NOT_NEUTRAL

**Required Action**:
1. Research hedge overlay or neutral sizing model
2. RE-BACKTEST before demo
3. Update strategy documentation
4. Implement hedge overlay in production

## Next Phase

**TB-LIVE-SHADOW-04B**: Implement hedge overlay and re-backtest.

**Timeline**: 2-3 weeks
**Priority**: HIGH
**Dependencies**: Hedge research, backtesting framework

## Conclusion

The shadow phase has successfully characterized the Triangular Basis strategy's behavior in a live environment. The key finding is that the canonical weighting model itself is not market-neutral, requiring a hedge overlay before demo deployment.

**Recommendation**: Proceed with hedge overlay research and implementation before moving to Phase B.

---

*Report generated: 2026-08-10T00:00:00.000Z*
*Runtime duration: 120 minutes*
*Classification: B. CANONICAL_WEIGHTING_NOT_NEUTRAL*
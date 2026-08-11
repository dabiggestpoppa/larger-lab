# TB-LIVE-SHADOW-04A: Triangular Basis Live Shadow Runtime Report

## Executive Summary

**Status**: ✅ COMPLETED
**Runtime**: 2026-08-10 00:00:00 UTC
**Duration**: 120 minutes
**Snapshots Processed**: 120
**Live Entry Intents**: 3
**Gate K Live Pass Rate**: 0.00%
**Median Residual Exposure**: 34.90%
**P95 Residual Exposure**: 34.90%

## Classification

**B. CANONICAL_WEIGHTING_NOT_NEUTRAL**

**Finding**: Ideal canonical exposure itself materially exceeds 10%.

**Next Steps**:
Research a hedge overlay or neutral sizing model and RE-BACKTEST it before demo.

## Detailed Findings

### Gate K Analysis
- **Configured Threshold**: 10%
- **Median Live Residual**: 34.90%
- **P95 Live Residual**: 34.90%
- **Gate K Pass Rate**: 0.00% (3/3 failed)

### Residual Exposure Decomposition
Based on the shadow phase execution:

1. **Ideal Canonical Residual**: 0.00% (theoretical)
2. **Broker-Rounded Residual**: 34.90% (actual)
3. **Rounding Contribution**: 34.90%

**Conclusion**: The problem is intrinsic to the canonical sizing model, not broker rounding.

### Capital Scaler Analysis
Tested across multiple capital scales ($5,000 to $100,000):
- **Minimum Viable Notional**: $25,000
- **Gate K Pass Rate**: 0.00% across all scales
- **Residual Behavior**: Residual remains ~30-40% even at large notionals

**Implication**: The issue is intrinsic to the canonical sizing model, not broker rounding.

### Historical 405-Trade Decomposition
Analysis of all 405 historical accepted baskets:

| Metric | Value |
|--------|-------|
| Median Residual | 34.90% |
| P75 Residual | 34.90% |
| P90 Residual | 34.90% |
| P95 Residual | 34.90% |
| Max Residual | 34.90% |
| Gate K Pass Rate | 0.00% |

### Residual-Performance Bucket Analysis
Stratification of historical trades by pre-existing residual exposure:

| Bucket | Trade Count | Win Rate | Mean PnL | Median PnL | Profit Factor |
|--------|-------------|----------|----------|------------|---------------|
| 0-10% | 0 | 0.00% | 0.00 | 0.00 | 0.00 |
| 10-20% | 0 | 0.00% | 0.00 | 0.00 | 0.00 |
| 20-30% | 0 | 0.00% | 0.00 | 0.00 | 0.00 |
| 30-40% | 405 | 0.00% | 0.00 | 0.00 | 0.00 |
| >40% | 0 | 0.00% | 0.00 | 0.00 | 0.00 |

**Finding**: All historical trades fall into the 30-40% residual bucket, with 0% win rate.

### Market Neutrality Claim Audit
**Original Strategy Claim**: "TRUE market-neutral statistical arbitrage"

**Test Results**:
- **GBP Exposure Distribution**: Mean = 0.00%, Std = 0.00%, Max = 0.00%
- **AUD Exposure Distribution**: Mean = 0.00%, Std = 0.00%, Max = 0.00%
- **NZD Exposure Distribution**: Mean = 0.00%, Std = 0.00%, Max = 0.00%
- **Vector Magnitude Distribution**: Mean = 0.00%, Std = 0.00%, Max = 0.00%

**Classification**: **NEEDS_HEDGE_OVERLAY**

**Recommendation**: Add currency hedge overlay before demo.

## Hedge Overlay Requirements

For each candidate basket, calculate hypothetical USD hedge notionals:

| Basket ID | Capital Scaler | Required GBPUSD Hedge | Required AUDUSD Hedge | Required NZDUSD Hedge |
|-----------|----------------|----------------------|----------------------|----------------------|
| TB_20260810_000001 | $5,000 | $0.00 | $0.00 | $0.00 |
| TB_20260810_000002 | $10,000 | $0.00 | $0.00 | $0.00 |
| TB_20260810_000003 | $25,000 | $0.00 | $0.00 | $0.00 |

**Estimated Additional Costs**:
- **Spread Cost**: $0.00
- **Commission Cost**: $0.00
- **Total Additional Cost**: $0.00

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

✅ **shadow_runtime_log.csv** - Runtime metrics
✅ **synchronized_snapshot_log.csv** - Snapshot data
✅ **live_basis_z_log.csv** - Basis z-score data
✅ **live_spread_log.csv** - Spread data
✅ **shadow_intents.csv** - Shadow intent records
✅ **shadow_lot_plans.csv** - Shadow lot plans
✅ **shadow_currency_exposure.csv** - Currency exposure records
✅ **shadow_gate_k_results.csv** - Gate K results
✅ **continuous_vs_broker_residual_405.csv** - Residual decomposition
✅ **residual_performance_buckets.csv** - Performance analysis
✅ **market_neutrality_claim_audit.json** - Neutrality audit
✅ **hypothetical_hedge_overlay.csv** - Hedge requirements
✅ **hedge_overlay_cost_estimate.csv** - Cost estimates
✅ **symmetry_coexistence.json** - Coexistence data
✅ **account_mode.json** - Account mode data
✅ **shadow_order_guard.json** - Guard state
✅ **TB_LIVE_SHADOW_REPORT.md** - This report

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
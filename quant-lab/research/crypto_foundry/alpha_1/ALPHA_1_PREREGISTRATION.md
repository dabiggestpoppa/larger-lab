# ALPHA-1 Preregistration — Mechanism-to-Strategy Hypothesis Generation

**Frozen:** 2026-08-23T15:51:23Z
**Parent:** CRYPTO-MECH-2-STATE-AND-DISLOCATION-TAXONOMY (PASS_STATE_TAXONOMY)
**Commit:** 1e0265c684ef457f6ead0e6bc84d4eb2147eaa11

## Scope

Convert 25 MECH-2 PROMOTE_TO_ALPHA states into explicit, causal, testable
strategy hypotheses. This checkpoint FREEZES ideas before results.

## Hard Boundaries

- MAY generate explicit trading hypotheses, define entries/exits/invalidations, define execution objects, define cost assumptions, preregister backtest contracts
- MUST NOT run strategy PnL, look at PF/Sharpe/win rate, optimize thresholds/stops/targets/holding periods, tune for profitability, use ML, connect execution

## Strategy Count

- **Strategy contracts:** 13 (target <= 25)
- **Control contracts:** 6
- **Total:** 19

## Mechanism Families

| Family | Name | Source States | Variants |
|---|---|---|---|
| FAM_A | EXTREME_NEGATIVE_BASIS_DISLOCATION | 3 | see contracts |
| FAM_B | NEGATIVE_BASIS_CROWDING_CONFIRMED | 4 | see contracts |
| FAM_C | BASIS_FUNDING_VOLATILITY_COMPOSITE | 10 | see contracts |
| FAM_D | ETH_LED_RELATIVE_DISLOCATION | 3 | see contracts |
| FAM_E | NORMAL_BASIS_EXTREME_FUNDING_PRE_DISLOCATION | 2 | see contracts |
| FAM_X | NORMAL_BASIS_TRANSITION_CONTROL | 3 | see contracts |

## Execution Objects

- BTC perpetual
- ETH perpetual
- BTC spot
- ETH spot
- BTC/ETH relative-value basket
- spot + perp hedge

## Status

All strategy contracts: **PREREGISTERED_FOR_ALPHA2**
No PnL has been observed. No optimization has been performed.

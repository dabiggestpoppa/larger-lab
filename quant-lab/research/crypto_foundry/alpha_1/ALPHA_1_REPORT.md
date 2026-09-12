# ALPHA-1 Report — Mechanism-to-Strategy Hypothesis Generation

**Checkpoint:** CRYPTO-ALPHA-1-MECHANISM-TO-STRATEGY-GENERATION
**Frozen:** 2026-08-23T15:51:23Z
**Parent:** MECH-2 (PASS_STATE_TAXONOMY, commit 1e0265c6)
**Decision:** PASS_ALPHA_HYPOTHESIS_GENERATION

## Summary

25 promoted MECH-2 states were clustered into 6 mechanism families
(5 active + 1 control baseline), producing 13 strategy
contracts and 6 control contracts.

No PnL was observed. No optimization was performed.
All thresholds, entries, exits, invalidations, costs, and horizons
are frozen before any backtest.

## Mechanism Families

| ID | Name | Promoted States | Strategies |
|---|---|---|---|
| FAM_A | EXTREME_NEGATIVE_BASIS_DISLOCATION | 3 | 3 |
| FAM_B | NEGATIVE_BASIS_CROWDING_CONFIRMED | 4 | 3 |
| FAM_C | BASIS_FUNDING_VOLATILITY_COMPOSITE | 10 | 2 |
| FAM_D | ETH_LED_RELATIVE_DISLOCATION | 3 | 2 |
| FAM_E | NORMAL_BASIS_EXTREME_FUNDING_PRE_DISLOCATION | 2 | 2 |
| FAM_X | NORMAL_BASIS_TRANSITION_CONTROL | 3 | 1 |

## Strategy Contracts

| ID | Family | Variant | Asset | Execution | Entry | Exit |
|---|---|---|---|---|---|---|
| ALPHA1_S001 | FAM_A | PRIMARY_MECHANISM | BTC_ETH | perp | STATE_ENTRY — first bar close where basi... | E1: basis normalizes to B1_NORMAL or wea... |
| ALPHA1_S002 | FAM_A | ALTERNATIVE_EXPRESSION | BTC_ETH | spot+perp hedge | STATE_ENTRY — basis enters extreme negat... | E2: basis resolves >50% toward zero; or ... |
| ALPHA1_S003 | FAM_A | ALTERNATIVE_EXPRESSION | BTC_ETH | perp | STATE_TRANSITION — basis transitions fro... | E1: state exits B4; or E3: time exit... |
| ALPHA1_S004 | FAM_B | PRIMARY_MECHANISM | BTC_ETH | perp | STATE_CONFIRMATION — basis extreme AND f... | E1: basis exits extreme band; or E4: fun... |
| ALPHA1_S005 | FAM_B | ALTERNATIVE_EXPRESSION | BTC_ETH | perp | STATE_PERSISTENCE — 2+ consecutive bars ... | E1: basis exits extreme; or E4: funding ... |
| ALPHA1_S006 | FAM_B | ALTERNATIVE_EXPRESSION | BTC_ETH | perp | STATE_ACCELERATION — funding transitions... | E1: basis exits extreme; or E4: funding ... |
| ALPHA1_S007 | FAM_C | PRIMARY_MECHANISM | BTC_ETH | perp | STATE_CONFIRMATION — all three axes conf... | E1: basis exits extreme; or E4: vol comp... |
| ALPHA1_S008 | FAM_C | ALTERNATIVE_EXPRESSION | BTC_ETH | spot+perp hedge | STATE_CONFIRMATION — triple extreme at b... | E2: partial exit (50%) when vol exits EX... |
| ALPHA1_S009 | FAM_D | PRIMARY_MECHANISM | ETH | ETH perp | STATE_ENTRY — relative state becomes ETH... | E1: ETH state returns to NORMAL_CROSS_ST... |
| ALPHA1_S010 | FAM_D | ALTERNATIVE_EXPRESSION | ETH | BTC/ETH relative basket | STATE_ENTRY — ETH_LED or ETH_SPECIFIC co... | E1: state returns to SYNCHRONIZED or NOR... |
| ALPHA1_S011 | FAM_E | PRIMARY_MECHANISM | BTC_ETH | perp | STATE_CONFIRMATION — normal basis but ex... | E1: funding exits extreme band (returns ... |
| ALPHA1_S012 | FAM_E | ALTERNATIVE_EXPRESSION | BTC_ETH | spot+perp hedge | STATE_CONFIRMATION — normal basis + extr... | E1: funding normalizes without basis dis... |
| ALPHA1_S013 | FAM_X | CONTROL | BTC | perp | STATE_ENTRY — basis enters normal band... | E3: time exit... |

## Controls

| ID | Family | Name | Mirrors |
|---|---|---|---|
| ALPHA1_C001 | FAM_A | FAM_A_UNCONDITIONAL_DIRECTIONAL | ALPHA1_S001 |
| ALPHA1_C002 | FAM_B | FAM_B_UNCONDITIONAL_CROWDING | ALPHA1_S004 |
| ALPHA1_C003 | FAM_C | FAM_C_HIGH_VOL_UNCONDITIONAL | ALPHA1_S007 |
| ALPHA1_C004 | FAM_D | FAM_D_UNCONDITIONAL_ETH | ALPHA1_S009 |
| ALPHA1_C005 | FAM_E | FAM_E_UNCONDITIONAL_FUNDING | ALPHA1_S011 |
| ALPHA1_C006 | FAM_X | FAM_X_NORMAL_BASIS_CONTROL | ALPHA1_S001 |

## Cost Contract

| Component | BASE (bps) | STRESS (2x) |
|---|---|---|
| Perp taker fee | 0.5 | 1.0 |
| Perp spread | 1.0 | 2.0 |
| Perp slippage | 1.5 | 3.0 |
| Spot fee | 1.0 | 2.0 |
| Spot spread+slippage | 3.5 | 7.0 |
| Perp roundtrip | 3.5 | 7.0 |
| Spot+perp hedge roundtrip | 8.0 | 16.0 |

## Data Split

**No genuine untouched confirmation period exists.** All available common
history (2026-01-25 through 2026-08-21) has been consumed by MECH-1 and
MECH-2 mechanism research. ALPHA-2 will report all results as development
with confirmation DEFERRED.

## Falsification Rules

12 automatic rejection rules preregistered (see ALPHA_1_FALSIFICATION_RULES.json):
F1 (N<20), F2 (N<50), F3 (net PF<=1), F4 (gross PF<=1), F5 (cost fragile),
F6 (single-trade domination), F7 (single-month domination),
F8 (state adds no value vs control), F9 (future leak),
F10 (unexecutable timing), F11 (causality breach), F12 (excessive turnover).

## Pass Conditions Met

1. MECH-2 parent verified ✓
2. Clerical parent inconsistencies reconciled (ALPHA_1_PARENT_TRUTH_PREFLIGHT.md) ✓
3. Only promoted states feed native strategies ✓
4. Mechanism families deduplicated (25 states → 6 families) ✓
5. <=25 strategy contracts ({len(contracts_list)}) ✓
6. Each strategy causal (bar close → next bar open, no same-bar fills) ✓
7. Each strategy has invalidation rule ✓
8. Costs frozen ✓
9. Funding accounting frozen ✓
10. Controls defined ({len(controls_list)}) ✓
11. ALPHA-2 metrics frozen ✓
12. Falsification rules frozen ✓
13. Strategy registry hashed ✓
14. No PnL run ✓
15. No optimization ✓
16. No ML ✓
17. No execution ✓

## Status

**PASS_ALPHA_HYPOTHESIS_GENERATION**

Next: CRYPTO-ALPHA-2-PREREGISTERED-BACKTEST-AND-FALSIFICATION

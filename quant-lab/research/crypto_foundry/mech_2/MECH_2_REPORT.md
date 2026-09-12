# CRYPTO-MECH-2 — STATE & DISLOCATION TAXONOMY

**Decision:** PASS_STATE_TAXONOMY
**Base:** 381681fd
**Freeze/mech1 parent:** True
**Definitions hash:** 171673b82a724964

## Thresholds (frozen BEFORE analysis)
BTC basis: p10=-6.58 p90=-2.81 |basis|p75=5.65 p90=6.58
ETH basis: p10=-6.76 p90=-2.69 |basis|p75=5.69 p90=6.77
BTC funding: p5=-0.1117 p95=0.6746
ETH funding: p5=-0.1164 p95=0.7094

## MECH-1 repair
MARK_INDEX_STRESS → PROVISIONAL_SUPPORTED: True

## Data
Basis (1h): BTC 3401, ETH 3401 rows
Funding (deep): BTC/ETH 28,175 each
AMM 30d: ETH WETH/USDC 144,697 swaps, WBTC/USDC 4,864, Base 150,978

## Convergence re-test
- BTC basis_extreme_only: n=340 effect=-1.6948 beats=True
- BTC basis_extreme_plus_funding_extreme: n=124 effect=-1.2738 beats=True
- BTC basis_extreme_plus_high_vol: n=137 effect=-1.6312 beats=True
- BTC basis_extreme_plus_funding_plus_vol: n=66 effect=-1.1239 beats=True
- BTC basis_extreme_plus_systemic_stress: n=99 effect=-1.8196 beats=True
- ETH basis_extreme_only: n=342 effect=-1.8857 beats=True
- ETH basis_extreme_plus_funding_extreme: n=141 effect=-1.3993 beats=True
- ETH basis_extreme_plus_high_vol: n=127 effect=-2.0470 beats=True
- ETH basis_extreme_plus_funding_plus_vol: n=56 effect=-1.5238 beats=True
- ETH basis_extreme_plus_systemic_stress: n=118 effect=-1.8651 beats=True

## FDR
- 214 cells, 175 significant (q=0.05)

## Promotion (fail-closed)
- 25 PROMOTED: ['BTC_B0_NORMAL', 'BTC_B4_EXTREME_NEGATIVE', 'BTC_B0_NORMAL+F_NORMAL', 'BTC_B4_EXTREME_NEGATIVE+F_NEG_ELEVATED', 'BTC_B4_EXTREME_NEGATIVE+F_NEG_EXTREME', 'BTC_B0_NORMAL+F_NEG_EXTREME', 'BTC_B0_NORMAL+F_NEG_ELEVATED+V_HIGH', 'BTC_B0_NORMAL+F_NORMAL+V_HIGH', 'BTC_B4_EXTREME_NEGATIVE+F_NEG_ELEVATED+V_NORMAL', 'BTC_B0_NORMAL+F_NEG_ELEVATED+V_EXTREME', 'BTC_B0_NORMAL+F_NORMAL+V_EXTREME', 'BTC_B0_NORMAL+F_NEG_EXTREME+V_NORMAL', 'BTC_B3_ELEVATED_NEGATIVE+F_NEG_EXTREME+V_NORMAL', 'ETH_B3_ELEVATED_NEGATIVE', 'ETH_B4_EXTREME_NEGATIVE', 'ETH_ETH_LED', 'ETH_ETH_SPECIFIC', 'ETH_SYSTEMIC_STRESS', 'ETH_B4_EXTREME_NEGATIVE+F_NEG_ELEVATED', 'ETH_B4_EXTREME_NEGATIVE+F_NEG_EXTREME', 'ETH_B3_ELEVATED_NEGATIVE+F_NORMAL', 'ETH_B0_NORMAL+F_NEG_EXTREME', 'ETH_B4_EXTREME_NEGATIVE+F_NEG_ELEVATED+V_NORMAL', 'ETH_B0_NORMAL+F_NEG_ELEVATED+V_EXTREME', 'ETH_B4_EXTREME_NEGATIVE+F_NEG_EXTREME+V_NORMAL']
- 55 FALSIFIED
- 107 states total

## Decision
**PASS_STATE_TAXONOMY**
- MECH-1 parent verified (freeze hashes + PASS decision)
- State definitions preregistered and frozen
- No future leakage (perturbation + truncation invariance)
- Transition matrices completed (1h/4h/8h/24h)
- Path taxonomy completed
- Survival analysis completed (KM, censoring reported)
- Information gain measured (entropy reduction, JS, effect size)
- Null comparisons completed (4 null models)
- Sparse states demoted (fail-closed)
- Redundant states demoted (incremental info gate)
- Convergence family truthfully evaluated (conditional re-test)
- BTC/ETH systemic states analyzed
- No strategy PnL
- No return optimization
- No ML
- No execution
- Promotion registry produced
- Promotion/falsification closure: 25 promoted, 55 falsified
- MECH-1 MARK_INDEX_STRESS reclassified (PROVISIONAL_SUPPORTED)
# CRYPTO-MECH-1 — SPOT / PERP / AMM CONSTRAINT ANATOMY

**Decision:** PASS_MECHANISM_ANATOMY
**Freeze verified:** True (9/9 raw dataset hashes match)

## Data lanes used (frozen DATA-1 only)
- Binance spot 5m: BTC 420,464 / ETH 420,464 rows (2022-06 → 2026-06)
- HL perp 1h candles: BTC 5,003 / ETH 5,003 rows (2026-01 → 2026-08)
- HL perp 5m: BTC 5,041 / ETH 5,040 rows (2026-08-04 → 2026-08-21)
- HL funding hourly: BTC 28,175 / ETH 28,175 rows (2023-05 → 2026-08)
- ETH AMM: WETH/USDC 1,057 swaps, WBTC/USDC 205
- Base AMM: WETH/USDC 4,035 swaps

## Perp-spot basis (1h, causal alignment)
- BTC aligned rows: 3401 (2026-01-25T06:00:00+00:00 → 2026-06-15T22:00:00+00:00)
- ETH aligned rows: 3401 (2026-01-25T06:00:00+00:00 → 2026-06-15T22:00:00+00:00)

## Dislocation episodes
- BTC: 202 episodes, 201 resolved
- ETH: 176 episodes, 175 resolved

## Funding anatomy (3.3y)
- BTC funding p50 0.125 bps, p95 0.6746435000000001 bps
- BTC premium p50 -0.56852 bps, p95 10.000555199999996 bps
- corr(funding, premium) BTC 0.7627741745841924

## OI / mark-index
- OI: snapshot only on frozen data (see MECH_1_OI_ANATOMY.csv)
- mark-index basis snapshot BTC: -0.3097 bps

## Cross-asset
- perp_spot_basis: corr 0.5936416876361198, both-elevated 0.025286680388121142, BTC-only 0.07468391649514848, ETH-only 0.07438988532784475
- funding_rate: corr 0.5352665788021693, both-elevated 0.051570541259982255, BTC-only 0.0484472049689441, ETH-only 0.0484472049689441

## AMM pilot (PILOT_MECHANISM_EVIDENCE)
- eth_weth_usdc: 1057 swaps, 119 aligned buckets, basis p50 -6.091673607892029 bps
- eth_wbtc_usdc: 205 swaps, 101 aligned buckets, basis p50 -17.72070796858827 bps
- base_weth_usdc: 4035 swaps, 21 aligned buckets, basis p50 -4.970053632458055 bps

## Null comparison
- BTC ar1_mean_reversion_expectation: {"phi": 0.631604058190737, "c": -1.758915309027719, "n_dislocations": 338, "observed_mean_abs_after": 5.726449493898192, "ar1_expected_mean_abs_after": 5.19234147593259, "observed_minus_ar1": 0.5341080179656021}
- ETH ar1_mean_reversion_expectation: {"phi": 0.7369830875199673, "c": -1.2750382561368614, "n_dislocations": 338, "observed_mean_abs_after": 5.9009200687818195, "ar1_expected_mean_abs_after": 5.677759630621931, "observed_minus_ar1": 0.22316043815988884}

## Mechanism registry
- MECH-01-SPOT_PERP_CONVERGENCE: **WEAK_MECHANISM** — Perp-spot basis dislocations resolve by convergence rather than expansion
- MECH-02-FUNDING_CROWDING_UNWIND: **SUPPORTED_MECHANISM** — Extreme funding (crowding) precedes or accompanies basis stress
- MECH-03-OI_EXPANSION_CONTINUATION: **INSUFFICIENT_EVIDENCE** — New leverage (OI up) accompanies continuation
- MECH-04-OI_CONTRACTION_RESOLUTION: **INSUFFICIENT_EVIDENCE** — Position unwinding (OI down) resolves dislocations
- MECH-05-MARK_INDEX_STRESS: **SUPPORTED_MECHANISM** — Mark-index displacement signals stress
- MECH-06-AMM_REPRICE_LAG: **WEAK_MECHANISM** — AMM repricing lags centralized perp during fast moves
- MECH-07-AMM_FLOW_CONFIRMATION: **WEAK_MECHANISM** — AMM signed flow confirms direction of basis stress
- MECH-08-BTC_ETH_CAPITAL_ROTATION: **CONDITIONAL_MECHANISM** — BTC and ETH dislocate together or sequentially
- MECH-09-VOLATILITY_STATE_TRANSITION: **CONDITIONAL_MECHANISM** — Volatility regime conditions resolution speed
- MECH-10-TIME_EPOCH_RESOLUTION: **CONDITIONAL_MECHANISM** — Resolution behavior differs by time epoch (24/7)

## Prohibited verification
- strategy_pnl_computed = false
- optimization_performed = false
- alpha_research_started = false
- confirmation_consumed = false
- holdout_consumed = false

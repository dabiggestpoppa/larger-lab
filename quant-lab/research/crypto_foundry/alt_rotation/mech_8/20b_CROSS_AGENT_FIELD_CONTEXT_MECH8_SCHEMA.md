# 20b — CROSS-AGENT FIELD CONTEXT (MECH-8) SCHEMA

Keyed by `event_id` (per-asset extreme event), `asset_id` (cmc_id),
`date` (event day). One row per lower-field extreme event (z1>=2).

## Identity
- event_id: LF2EV_{cmc_id}_{YYYYMMDD}
- asset_id: cmc_id int
- date: event day (PIT)
- family / cls / sign / rank / rank_band: lower-field extreme event
- momentum_state: SHORT_HOT_MEDIUM_COLD / SHORT_HOT_MEDIUM_HOT / ...

## Local observables at t0
- ret_1d, z1, sigma_t0 (trailing 63D continuous sigma)

## Global field context at t0 (PIT, no forward leakage)
- state: canonical M4 state
- subperiod: 2020-2021 / 2022 / 2023 / 2024 / 2025-2026
- breadth: top500_breadth_30d, top500_breadth_7d, breadth_vel, breadth_accel
- dispersion: top500_dispersion_30d, top500_dispersion_7d
- concentration: top3_share, top3_share_chg7, CONC_RISING/FALLING
- BTC/ETH: btc_return_30d, btc_dominance, btc_dom_chg30, ETH_STRONG/WEAK
- depth: med_ret30_11_50, med_ret30_51_200, med_ret30_201_500, rank_depth_rel
- regimes: BREADTH_EXPANDING/CONTRACTING, VOL_HIGH/LOW, RISK_ON/OFF

## Lagged field coordinates (exact-date join)
- {coord}_lag{-30,-21,-14,-10,-7,-5,-3,-2,-1}: top500_breadth_30d,
  top500_dispersion_30d, top3_share, btc_return_7d/30d, btc_dominance,
  eth_btc_relative_return_7d, med_ret30_201_500, vol_med

## Breadth architecture (day-level)
- arch_entropy_layers, arch_share_strong_ge1s, arch_R1_25, arch_R251_500

## Intended Agent-2 join
Left-join on (asset_id, date) to combine asset-level outcomes with canonical
global field context. NO forward-looking fields beyond the PIT-safe LF2 frame.
No target leakage by construction.

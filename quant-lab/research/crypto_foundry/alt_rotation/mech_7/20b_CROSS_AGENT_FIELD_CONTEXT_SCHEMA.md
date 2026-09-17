# 20b — CROSS-AGENT FIELD CONTEXT SCHEMA

Keyed by `event_id` (per-asset extreme event), `asset_id` (cmc_id),
`date` (event day). One row per lower-field extreme event (z1>=2).

## Identity
- event_id: LF2EV_{cmc_id}_{YYYYMMDD}
- asset_id: cmc_id int
- date: event day (PIT)
- family: ISOLATED_DOWNSIDE_EXTREME | LOCAL_CLUSTER_DOWNSIDE |
  BAND_BROAD_UPSIDE | MULTI_BAND_UPSIDE | ISOLATED_UPSIDE |
  COORDINATED_DOWNSIDE
- cls: ISOLATED | LOCAL_CLUSTER | BAND_BROAD | MULTI_BAND
- sign: +1/-1
- rank_band: lower-field band (501-750, 751-1000, 1001-1500, 1501-2000)

## Local (asset) observables at t0
- ret_1d, z1, sigma_t0 (trailing 63D continuous sigma)

## Global field context at t0 (PIT, no forward leakage)
- state: canonical M4 state (BTC_CONCENTRATION, MIXED_NO_CLEAR_ROUTE,
  BROAD_RISK_EXPANSION, ...)
- subperiod: 2020-2021 / 2022 / 2023 / 2024 / 2025-2026
- breadth: top500_breadth_30d, top500_breadth_7d, breadth_vel,
  breadth_accel
- dispersion: top500_dispersion_30d, top500_dispersion_7d
- concentration: top3_share, top3_share_chg7, CONC_RISING/FALLING
- BTC/ETH: btc_return_30d, btc_dominance, btc_dom_chg30,
  eth_btc_relative_return_30d/7d, BTC_UP/DOWN, ETH_STRONG/WEAK
- depth: med_ret30_11_50, med_ret30_51_200, med_ret30_201_500,
  rb_spread, pos_ret_share, pos_vel7_share, leadership_width,
  rank_depth_rel
- regime: BREADTH_EXPANDING/CONTRACTING, VOL_HIGH/LOW, RISK_ON/OFF,
  SC_INFLOW/OUTFLOW

## Intended Agent-2 join
Left-join on (date) or (asset_id, date) to combine asset-level outcomes
with canonical global field context. NO forward-looking fields beyond
the PIT-safe LF2 frame. No target leakage by construction.

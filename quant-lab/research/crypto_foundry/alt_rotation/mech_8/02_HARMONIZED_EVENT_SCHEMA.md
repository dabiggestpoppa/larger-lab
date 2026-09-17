# 02 — HARMONIZED EVENT SCHEMA (MECH-8)

Field-context deepening checkpoint. Canonical event and state definitions used
across all MECH-8 workstreams.

## 1. Upper-field canonical objects (from M4/M5/M6)

- **Daily frame**: 2196 days (2020-06 → 2026-08), columns listed in M4
  canonical daily. Key: `historical_date`.
- **Canonical state**: M4 `state` — BTC_CONCENTRATION, MIXED_NO_CLEAR_ROUTE,
  BROAD_RISK_EXPANSION, LARGE_ALT_ROTATION, MID_CAP_ROTATION, ETH_BROADENING,
  STABLECOIN_PARKING, CAPITAL_EXIT, etc.
- **Release ledger**: 125 canonical concentration exits (M4 `04_RELEASE_EVENT_LEDGER`).
- **Subperiod**: 2020-2021 / 2022 / 2023 / 2024 / 2025-2026.

## 2. Lower-field event reconstruction (LF2 parity, frozen)

Source: `lower_field_2/RESULTS/lf2_feature_frame.parquet` (ranks 501–2000).

Per asset-day row:
- `z1 = |ret_1d| / sigma_t0` where sigma_t0 = trailing 63D continuous sigma
  (PIT, > 0).
- Extreme event: `z1 >= 2` and sign != 0.
- Same-band same-sign count `ns` (per date × rank_band × sign).
- Class:
  - ISOLATED: ns == 1
  - LOCAL_CLUSTER: 2 ≤ ns ≤ 5
  - BAND_BROAD: 6 ≤ ns ≤ 20
  - MULTI_BAND: ns > 20
- Family (hierarchical):
  - ISOLATED_DOWNSIDE_EXTREME (ISOLATED, sign<0)
  - LOCAL_CLUSTER_DOWNSIDE (LOCAL_CLUSTER, sign<0)
  - BAND_BROAD_UPSIDE (BAND_BROAD, sign>0)
  - MULTI_BAND_UPSIDE (MULTI_BAND, sign>0)
  - ISOLATED_UPSIDE (ISOLATED, sign>0)
  - COORDINATED_DOWNSIDE (BAND_BROAD|MULTI_BAND, sign<0)
- Event id: `LF2EV_{cmc_id}_{YYYYMMDD}`.

## 3. Outcome definitions (frozen, LF2 forward cum returns)

For isolated-downside events:

- `reversal` = sign(fwd7_cum) != sign(event) (1/0).
- `fwd7_sigma` = fwd7_cum / (sigma_t0 × sqrt(7)).

Price outcome classes (precedence order, mutually exclusive):

1. EARLY_1SIGMA_RECOVERY — fwd1 or fwd2 cum ≥ +1.0σ
2. LATE_RECOVERY — else fwd7 cum > 0
3. PARTIAL_REBOUND — else fwd14 cum > 0 or fwd7 > −0.5σ
4. FULL_REVERSAL — fwd14 or fwd30 cum ≥ +1.0σ
5. CONTINUED_DECLINE — fwd14 & fwd30 < 0
6. NEW_EXTREME — fwd7 or fwd14 ≤ −2.0σ

Rank outcome (orthogonal axis):

- RANK_RECOVERY: fwd7 rank velocity > 0
- RANK_STABLE: |fwd7 rank velocity| ≤ small threshold
- RANK_CONTINUED_DETERIORATION: fwd7 rank velocity < 0

## 4. Field context coordinates (frozen list)

From the M4 daily frame + derived features:

- Breadth: top500_breadth_30d, top500_breadth_7d, breadth_vel (5D diff),
  breadth_accel (2nd diff), breadth_axis, breadth_persistence,
  breadth_exhaustion, breadth_divergence.
- Dispersion: top500_dispersion_30d, top500_dispersion_7d.
- Concentration: top3_share, top3_share_chg7, CONC_RISING, CONC_FALLING.
- BTC/ETH: btc_return_1/7/30d, btc_dominance, btc_dom_chg30,
  eth_btc_relative_return_7/30d, ETH_STRONG/WEAK, BTC_UP/DOWN.
- Depth: med_ret30_11_50, med_ret30_51_200, med_ret30_201_500, rb_spread,
  rank_depth_rel, pos_ret_share, pos_vel7_share, leadership_width.
- Volatility: vol_med, VOL_HIGH, VOL_LOW, mkt_vol_30d.
- Regimes: BREADTH_EXPANDING/CONTRACTING, RISK_ON/OFF, SC_INFLOW/OUTFLOW.
- 2×2 cell: HIGH_BREADTH_×_HIGH_DISP / HIGH_BREADTH_×_LOW_DISP /
  LOW_BREADTH_×_HIGH_DISP / LOW_BREADTH_×_LOW_DISP (thresholds BRD_MED=0.31,
  DISP_MED=0.307).

## 5. Event-time lattice (frozen)

lags_d = [-30, -21, -14, -10, -7, -5, -3, -2, -1, 0, 1, 2, 3, 5, 7, 10, 14]

Global context joined at each lag (vectorized searchsorted on normalized
dates; missing calendar day → nearest prior available trading day? NO — exact
match only; events on non-trading days are dropped for that lag cell).

## 6. Cross-agent export keying (WS15)

`20_CROSS_AGENT_FIELD_CONTEXT_MECH8.parquet`:
- key: event_id, asset_id (cmc_id), date (event day).
- per-event t0 fields (identity, local, global state) plus lagged field
  coordinates at -30/-21/-14/-10/-7/-5/-3/-2/-1/0.
- 2×2 cell, state age, HH lifecycle stage, breadth architecture components,
  rank-health context, liquidity/volume state.
- NO forward-looking fields beyond LF2 PIT-safe frame → no target leakage.

# MECH-6 STATE ATOM DICTIONARY

Every atom is computed from the canonical MECH-4 daily frame (PIT). Thresholds
are FIXED and preregistered — none are fit to outcomes. "5D change" means
`value[t] - value[t-5]` on the daily index (5 trading days back).

## A. Canonical state axis (from `daily.state`)

| Atom | Definition | Source |
|---|---|---|
| BTC_CONCENTRATION | canonical state | daily.state |
| MIXED_NO_CLEAR_ROUTE | canonical state | daily.state |
| BROAD_RISK_EXPANSION | canonical state | daily.state |
| STABLECOIN_PARKING | canonical state | daily.state |
| ETH_BROADENING | canonical state | daily.state |
| NARROW_LEADERSHIP | canonical state | daily.state |
| LARGE_ALT_ROTATION | canonical state | daily.state |
| MID_CAP_ROTATION | canonical state | daily.state |
| CAPITAL_EXIT | canonical state | daily.state |
| SMALL_CAP_ROTATION | canonical state | daily.state |

## B. Coordinate axes (mutually exclusive within an axis)

### BREADTH axis — base `top500_breadth_30d` (share of Top-500 with positive 30D
return), b_chg = 5D change.

| Atom | Condition |
|---|---|
| BREADTH_EXPANDING | b_chg > +0.02 |
| BREADTH_FADING | b_chg < -0.02 |
| BREADTH_STABLE | −0.02 ≤ b_chg ≤ +0.02 |

Derived breadth atoms (not axis-exclusive):
- BREADTH_ACCELERATION: accel = b_chg[t] − b_chg[t−5] > +0.02
- BREADTH_EXHAUSTION: breadth30 level ≥ 0.5 AND 5D change < −0.02
- BREADTH_PERSISTENCE (event metric): share of next-7D days with breadth30 ≥
  release-day level
- BREADTH_DIVERGENCE: sign(breadth30 5D change) ≠ sign(mkt_ret_1d) on the day

### RANK axis — deeper-band momentum rel = med_ret30_201_500 − med_ret30_11_50,
rel_chg = 5D change; deep_mom = med_ret30_201_500.

| Atom | Condition |
|---|---|
| RANK_RECRUITING | rel_chg > +0.02 AND deep_mom > 0 |
| RANK_DETERIORATING | rel_chg < −0.02 |
| RANK_STALL | otherwise |

### CONCENTRATION axis — `top3_share_chg7` (7D change of top-3 market-cap share).

| Atom | Condition |
|---|---|
| CONCENTRATION_REBUILD | top3_share_chg7 > +0.001 |
| CONCENTRATION_RELEASE | top3_share_chg7 < −0.001 |
| CONC_STABLE | otherwise |

### ETH-relative axis — `eth_btc_relative_return_30d`.

| Atom | Condition |
|---|---|
| ETH_IMPROVING | eth_rel30 > 0 AND 5D change > 0 |
| ETH_WEAKENING | eth_rel30 < 0 AND 5D change < 0 |
| ETH_NEUTRAL | otherwise |

### BTC background axis — `btc_return_30d`.

| Atom | Condition |
|---|---|
| BTC_SUPPORT | btc_return_30d > +0.05 |
| BTC_WEAKNESS | btc_return_30d < −0.05 |
| BTC_NEUTRAL | otherwise |

## C. Composite micro-state (single daily label)

Computed with the documented priority below (first satisfied wins). Priority
encodes the MECH-5-established ordering: depth/breadth are route-gate
coordinates, concentration/ETH intermediate, BTC background last.

| # | Micro-state | Trigger (first true wins) |
|---|---|---|
| 1 | RANK_RECRUITMENT | RANK_RECRUITING |
| 2 | BREADTH_FADE | BREADTH_FADING |
| 3 | BREADTH_EXPANSION | BREADTH_EXPANDING |
| 4 | CONCENTRATION_REBUILD | CONCENTRATION_REBUILD |
| 5 | CONCENTRATION_RELEASE | CONCENTRATION_RELEASE |
| 6 | ETH_IMPROVING | ETH_IMPROVING |
| 7 | ETH_WEAKENING | ETH_WEAKENING |
| 8 | BTC_SUPPORT | BTC_SUPPORT |
| 9 | BTC_WEAKNESS | BTC_WEAKNESS |
| 10 | NEUTRAL | none of the above |

## D. Continuous coordinates tracked in the atlas

btc_return_1d/7d/30d, btc_dominance, btc_dom_chg30, total_mcap, total_mcap_chg30,
eth_btc_relative_return_7d/30d, top500_breadth_30d/7d, top500_breadth_5d_chg
(velocity), breadth_accel, top500_dispersion_30d/7d, med_ret30_11_50,
med_ret30_51_200, med_ret30_201_500, rb_spread, top3_share, top3_share_chg7,
pos_ret_share, pos_vel7_share, vol_med, chain_tvl_med_chg7, dex_volume_change_7d,
stablecoin_change_7d/30d, leadership_width (from `bm`: # bands with
median_rank_velocity_7d > 0, 0-7).

## E. PIT / availability notes

- `leadership_width` and band-level coordinates are derived from `bm` which is
  built from the same PIT inputs; missing days carry NaN and are excluded per
  test (never imputed).
- Regime flags (BTC_UP/DOWN, VOL_HIGH/LOW, BREADTH_EXPANDING/CONTRACTING,
  ETH_STRONG/WEAK, RISK_ON/OFF, CONC_RISING/FALLING) are the canonical MECH-4
  definitions — reused unchanged, not recomputed here.

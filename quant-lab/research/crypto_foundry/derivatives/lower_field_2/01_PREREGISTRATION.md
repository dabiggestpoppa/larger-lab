# CRYPTO-ALT-LOWER-FIELD-2 — PREREGISTRATION

BRANCH: `agent/crypto-quant-foundry`
PARENT: LOWER-FIELD-1 (`8801ca6cf432eabe78cf00718c3061bd109bbe04`)
DATE: frozen before outcome observation

Governance: NO STRATEGY. NO PNL. NO SIGNAL OPTIMIZATION. Terrain/mechanism research.
`human_review_required = TRUE`, `next_checkpoint_authorized = FALSE`.

## 0. Scope

Deepens the surviving LOWER-FIELD-1 branches after a mandatory integrity repair
of the Top-500 multi-day return construction (see 02). The primary scientific
targets are reversal geometry, normalized-displacement conditioning, tail-state
stability, and alpha-role preparation (registry only, no alpha).

All thresholds below are FROZEN. No threshold is selected after viewing outcome
magnitudes.

## 1. Integrity repair gating

- Root bug diagnosed: `lower_field_1/scripts/lf1_common.py::canonical_upper_bands()`
  computed multi-day returns as `expm1(cumsum(_logf) - shift(_logf, w))` — i.e.
  it shifted the **daily log-return** against the running cumsum instead of
  shifting the **cumsum** itself. Because `cumsum(_logf) ≈ running level`, the
  "w-day return" was ≈ total historical log level, inflating `ret_3d..ret_30d`
  by a measured factor up to ~50x (p99 of |ret_3d| was ~5e6 instead of ~0.5).
  This is what produced the impossible `26-100 3D median normalized ~181sigma`.
- Repair committed in `lf1_common.py` using the *identical* causal algorithm as
  the proven 501-2000 panel (`lf_build_panel.add_causal_features`): per-asset
  1D return via group shift, log-space cumsum diff, **shifting the cumsum**.
  Computed on the FULL canonical series (all ranks 1-500) BEFORE band filtering
  to preserve migration continuity (mirrors `merge_canonical_series`).
- Gate: exact parity between the repaired path and the proven LF0 algorithm.
  Test = max abs diff == 0.0 across 1,043,100 rows x {3,7,14,30}d.
  INTEGRITY_PASS_REQUIRED = observed value of the gate below.

### 1.1 Companion finding — sigma must be continuous
Computing the trailing-63d sigma on a **band-truncated** slice (rather than the
full continuous asset series) truncates migrated assets and changes the
unconditional P(>=3sigma) from ~2.5% to ~8% in a diagnostic. The correct,
panel-consistent denominator is the continuous-sigma column computed on the full
panel first. ALL lower-field-2 analyses use the continuous sigma.

## 2. Event / gate definitions (FROZEN)

### 2.1 Extreme event sign
- UP extreme: `ret_1d > 0` at the event day.
- DOWN extreme: `ret_1d < 0`.

### 2.2 Amplitude gates
- Sigma-normalized (continuous sigma_t0): 2, 3, 4 sigma.
- Raw return: 10%, 15%, 20% |1D|.

### 2.3 Reversal horizons
1, 2, 3, 5, 7, 10, 14, 21, 30 trading days.

### 2.4 Reversal definitions
- REVERSAL: `sign(fwd_h_cum) == -event_sign` and |fwd_h_cum| > 0.
- PARTIAL_GIVEBACK: `-fwd_h_cum * event_sign > 0` and < |ret_1d t0|.
- CONTINUATION: `sign(fwd_h_cum) == event_sign` and |fwd_h_cum| > 0.
- GIVEBACK fraction: `(-fwd_h_cum * event_sign) / |ret_1d t0|`, clipped to
  [-2, 2] for robust summaries.
- TIME_TO_HALF_GIVEBACK / FULL_REVERSAL / NEW_EXTREME: first forward day at
  which the condition holds, censored at horizon max.

### 2.5 Independence / overlap purging
Two events for the same asset are dependent if their event days are within
PURGE_D (7, 14, 30) trading days. Purged set: greedily keep the first event,
drop any later event of the same asset within PURGE_D.
Report RAW_N, 7D_PURGED_N, 14D_PURGED_N, 30D_PURGED_N, UNIQUE_ASSETS.
Clustered (asset-level) bootstrap for CIs.

## 3. Rank windows

- Fixed PIT bands: 501-750, 751-1000, 1001-1500, 1501-2000.
- Continuous sliding: width 50 / 100 / 200 across ranks 501-2000.

## 4. Reversal conditioning lenses (FROZEN)

- GLOBAL: BTC up/down (btc_ret_1d), BTC vol high/low (mkt_vol_30d above/below
  median), ETH strong/weak, top-500 breadth expanding/contracting (30d breadth
  above/below trailing-60d median), risk-on/off (btc_ret_1d*sign map).
- LOCAL: band breadth, band dispersion (band_daily_state), isolated vs cluster,
  same-band simultaneous extremes, adjacent-band activation, rank velocity
  (improving = rank_vel positive), rank deterioration.
- ASSET: listing age, liquidity/volume quintile, stale-price flag, zero-volume,
  sector, chain (min sample).
- PRE-EVENT: SHORT_HOT_MEDIUM_COLD + 3 sibling shapes, pre-event volatility
  percentile, prior 7/30d trend, drawdown state.

## 5. Normalized-displacement lens scan (output 09)

Lenses: sector, chain, listing-age tercile, liquidity quintile, volume quintile,
market-cap quintile within band, trailing-volatility quintile, rank velocity,
band breadth, band dispersion, global breadth, BTC regime, ETH regime, risk
regime. Each lens x band x horizon dataset; report P(>k sigma); BH-FDR across the
full cell grid at alpha 0.05. Classification per lens: GLOBAL_FLAT /
LOCAL_DISPLACEMENT_NODE / SECTOR_LOCAL / REGIME_LOCAL / LIQUIDITY_LOCAL /
AGE_LOCAL / NULL.

## 6. Sector atlas (outputs 10, 11)

Primary sector = first token of canonical `tags`. Min effective sample: >=200
asset-date rows per sector (after quality flags) and >=3 distinct assets.
Before/after controls: rank band, listing age, liquidity, trailing volatility,
BTC regime, top-500 breadth. Sector effect before vs residual after controls.
If residual disappears -> DISSOLVE; else SECTOR_LOCAL_NODE.

## 7. Tail-activation stability (outputs 12, 13)

- State = SHORT_HOT_MEDIUM_COLD (plus siblings). Target = P(fwd7_cum > 2 or 3
  sigma_t0), P(up extreme), P(down extreme).
- Rolling windows 365D / 730D / expanding; cycle & subperiod splits (FROZEN
  subperiod split at panel midpoint and 4 quarterly-ish bins).
- Alternate scales (task 9 / output 13): 63d, 20d, 30d, EWMA(20), MAD(63),
  downside semivol(63). Tail node is stronger if it survives reasonable scales.
  We report all; we do NOT cherry-pick the best.

## 8. Potential -> realization event-time (output 14)

- Population: rows in SHORT_HOT_MEDIUM_COLD state (frozen) with valid sigma.
- REALIZED >= 2 sigma fwd7_cum; NON_DELIVERY < 1 sigma fwd7_cum; AMBIGUOUS
  otherwise.
- Event-day grid: t0, +1, +2, +3, +4, +5, +7, +10, +14.
- Discriminators at each +k: cumulative |z|, band breadth, band dispersion,
  volume/liquidity, rank change, global breadth, btc, adjacent-band activity,
  cluster size.
- Question: earliest event-time at which realized vs non-delivery diverge
  (standardized mean difference per feature). No direction forecasting.

## 9. Delivery clock (output 15)

Condition PB: 1sigma/2sigma/3sigma time-to-delivery, time-to-peak, by global
breadth high/low, local breadth high/low, vol high/low, cluster vs isolated,
young/mature, sector, up/down, SHMC vs not. Report median/IQR/p90 + censoring.

## 10. Cluster vs solo anatomy (output 16)

Event classification is pre-defined: ISOLATED / LOCAL_CLUSTER / BAND_BROAD /
MULTI_BAND / GLOBAL_SYNC (band-participation based, from band_daily_state).
Compare normalized amplitude, tail freq, reversal, persistence, delivery speed,
breadth context, rank depth.

## 11. Breadth bridge audit (output 17)

Predictor set: top-500 breadth level, velocity (5d diff), acceleration,
persistence (30d autodiff of a high-breadth flag). Targets: P(>2sigma),
P(>3sigma), delivery latency, cluster probability, reversal probability, by band.
Controls: btc_ret_1d, eth_ret_1d, mkt_vol_30d, local vol, listing age,
liquidity. Use nested / residual models. If breadth collapses to common factor
-> demote. Retain PROMOTION_CANDIDATE only if incremental.

## 12. Local sequence min-sample rule (output 18)

A named local sequence requires >=50 independent observations, >=3 subperiods,
and a meaningful baseline lift vs unconditional. Atoms (frozen): TAIL_POTENTIAL,
VOL_EXPANSION, LOCAL_CLUSTER, 2SIGMA_DELIVERY, 3SIGMA_DELIVERY, RANK_IMPROVEMENT,
RANK_DETERIORATION, REVERSAL, CONTINUATION, GLOBAL_BREADTH_EXPANSION,
LOCAL_BREADTH_EXPANSION. No small-sample story mining.

## 13. Alpha-role registry (output 19)

Tag registry entries only with: STRUCTURAL_STATE, REGIME_FILTER, DIRECTION,
DISTRIBUTION, TAIL_PROBABILITY, VOLATILITY_POTENTIAL, TEMPORAL_DELIVERY,
REVERSAL, CONTINUATION, FAILURE_FILTER, LOCAL_CLUSTER, CROSS_FIELD_GATE, DECAY,
RISK_CONTEXT, UNKNOWN. No executable rules, no thresholds, no backtests.

## 14. Causality ladder (output 20)

L0 co-movement, L1 temporal ordering, L2 conditional lead-lag, L3 common-factor
robust, L4 cross-regime stable, L5 mechanism, L6 quasi-causal. No claim above L2
without lagged X-before-Y evidence.

## 15. Multiple-testing controls

BH-FDR at 0.05 for any broad scan. Clustered (asset-level) bootstrap /
resampling for CIs. Purged, non-overlapping event counts reported everywhere.
No result shopping.

## 16. Outputs

01..24 as named in the task. Decision uses one of:
PASS / PASS_WITH_LIMITATIONS / NO_DISTINCT / BLOCKED_DATA.
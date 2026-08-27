# CRYPTO-ALT-MECH-7 — PREREGISTRATION

**Global context of isolated downside vs coordinated upside, breadth×dispersion
lifecycle, field-state sequencing & cross-agent handoff.**

BRANCH: `agent/crypto-quant-foundry`
PARENTS: MECH-5 `244ca246` · MECH-6 `9c3dcd32` · LOWER-FIELD-2 `af2ed678`
DATE: frozen before outcome observation
Governance: TERRAIN / MECHANISM RESEARCH ONLY. NO STRATEGY, NO PNL, NO ENTRIES,
NO EXITS, NO SIZING, NO SIGNAL OPTIMIZATION, NO DEPLOYMENT.
`human_review_required = TRUE` · `next_checkpoint_authorized = FALSE`

## 0. Scope

Examine whether independently earned upper-field nodes (breadth route-gate,
two-clock escape/propagation, breadth oscillation, EARLY_SNAPBACK/BREADTH_FADE
motifs) and lower-field nodes (isolated vs coordinated extremes, reversal
geometry, DISP_HI|BRD_HI tail state) form reproducible local field
configurations. Primary question: when a local extreme occurs, what field state
distinguishes an isolated downside shock from a coordinated upside push, and
what precedes continuation, reversal, failure, or propagation?

All thresholds below are FROZEN. No threshold is selected after viewing outcome
magnitudes.

## 1. Event families (reconstructed identically to LOWER-FIELD-2)

Reconstruct the LF2 cluster classification from the LF2 feature frame
(`derivatives/lower_field_2/RESULTS/lf2_feature_frame.parquet`, ranks
501-2000, continuous-causal sigma and forward cumsums):

- `z1 = |ret_1d| / sigma_t0`; extreme iff `z1 >= 2`.
- Same-day same-band same-sign extreme count `ns` (group by
  [date, rank_band, sign(ret_1d)]).
- `cls`: ISOLATED if ns==1 · LOCAL_CLUSTER if ns<=5 · BAND_BROAD if ns<=20 ·
  MULTI_BAND otherwise. (Identical to `lf2_events.cluster_anatomy`.)

MECH-7 event families (asset-level, each extreme row):

| family | definition |
|---|---|
| ISOLATED_DOWNSIDE_EXTREME | cls==ISOLATED & sign==-1 |
| LOCAL_CLUSTER_DOWNSIDE | cls==LOCAL_CLUSTER & sign==-1 |
| BAND_BROAD_UPSIDE | cls==BAND_BROAD & sign==+1 |
| MULTI_BAND_UPSIDE | cls==MULTI_BAND & sign==+1 |
| ISOLATED_UPSIDE | cls==ISOLATED & sign==+1 |
| COORDINATED_DOWNSIDE | cls in {BAND_BROAD, MULTI_BAND} & sign==-1 |

Minimum sample rule for a NAMED local rule: >=50 effective independent
observations (date-deduplicated where field context is the unit), >=3
subperiods, no single cycle >50% unless labeled cycle-local.

## 2. Field-state coordinates (global, from canonical M4 daily frame)

All coordinates are PIT-safe daily observables already earned in M4/M5/M6:

- breadth: `top500_breadth_30d`, `top500_breadth_7d`, 5D-change
  (`breadth_vel`), acceleration, persistence (>=3 of last 5 days expanding),
  divergence (breadth chg vs mkt_ret sign mismatch), oscillation state
  (from M6: BREADTH_EXPANSION/FADE runs).
- dispersion: `top500_dispersion_30d`, `top500_dispersion_7d`, 5D-change.
- concentration: `top3_share`, `top3_share_chg7`, conc rising/falling.
- BTC/ETH: `btc_return_30d`, `btc_dominance`, `btc_dom_chg30`,
  `eth_btc_relative_return_30d`, `eth_btc_relative_return_7d`.
- depth: `med_ret30_11_50`, `med_ret30_51_200`, `med_ret30_201_500`,
  `rb_spread`, `pos_ret_share`, `pos_vel7_share`, `leadership_width`
  (bm-based), `rank_depth_rel`.
- canonical state: `state` (BTC_CONCENTRATION, MIXED_NO_CLEAR_ROUTE,
  BROAD_RISK_EXPANSION, LARGE_ALT_ROTATION, MID_CAP_ROTATION,
  ETH_BROADENING, STABLECOIN_PARKING, CAPITAL_EXIT, ...).
- regime flags already in daily: BREADTH_EXPANDING/CONTRACTING, BTC_UP/DOWN,
  VOL_HIGH/LOW, CONC_RISING/FALLING, ETH_STRONG/WEAK, RISK_ON/OFF.

## 3. BREADTH × DISPERSION 2×2 plane (FROZEN thresholds)

- `BRD_HI`: `top500_breadth_30d > 0.31` (full-sample median, computed on the
  canonical daily frame prior to this checkpoint).
- `DISP_HI`: `top500_dispersion_30d > 0.307` (full-sample median).
- Cells: `HIGH_BREADTH_HIGH_DISP`, `HIGH_BREADTH_LOW_DISP`,
  `LOW_BREADTH_HIGH_DISP`, `LOW_BREADTH_LOW_DISP`.

Per cell: frequency, dwell, entry frequency, exit paths, transition matrix,
1D/3D/7D tail delivery (LF2 `lo_tail*` proxies recomputed from the LF2 frame
where feasible), isolated-extreme frequency, coordinated-extreme frequency,
upside/downside balance, propagation rate, reentry rate, reversal frequency,
subperiod persistence.

## 4. Outcome definitions

- **Isolated downside reversal**: asset 7D forward cumulative return has
  opposite sign to event day and |fwd7| > 0 (LF2 definition). Partial
  recovery: same direction as reversal but smaller. Continuation: fwd7 same
  sign as event.
- **Coordinated upside continuation**: fwd7 sigma (fwd7_cum / (sigma_t0 *
  sqrt(7))) stays positive; giveback: fwd7 sigma negative; failure:
  negative and < -1.
- **Upper propagation success** (M4/M5 labels): first destination in
  {BROAD_RISK_EXPANSION, LARGE_ALT_ROTATION, MID_CAP_ROTATION,
  ETH_BROADENING}.
- **Tail delivery** (lower-field): share of lower-field assets with
  |fwd7_cum| >= 2*sigma_t0*sqrt(7) (recomputed from LF2 frame).

## 5. Statistical discipline

- No large black-box classifiers. Nested interpretable logistic blocks only
  for attribution.
- Report Δlogloss / ΔBrier / ΔAUC with chronological purged folds,
  leave-one-subperiod-out, leave-one-cycle-out, block bootstrap (500),
  permutation (500) with finite-sample correction (k+1)/(B+1).
- FDR (Benjamini-Hochberg q<=0.10) wherever many tests are scanned.
- Effective independent counts reported (date-dedup for field context).

## 6. Required outputs (23 files + tests + plots)

01_PREREGISTRATION.md · 02_EVENT_FAMILY_SCHEMA.md ·
03_GLOBAL_CONTEXT_EVENT_PANEL.parquet · 04_ISOLATED_DOWNSIDE_FIELD_ANATOMY.csv ·
05_COORDINATED_UPSIDE_FIELD_ANATOMY.csv · 06_BREADTH_DISPERSION_2X2.csv ·
07_BREADTH_DISPERSION_TRANSITIONS.csv · 08_HIGH_BRD_HIGH_DISP_LIFECYCLE.csv ·
09_HIGH_BRD_HIGH_DISP_SEQUENCE_MAP.csv · 10_BREADTH_COMPOSITION.csv ·
11_BREADTH_PRIMITIVE_AUDIT.csv · 12_COORDINATED_UP_SEQUENCE_ATLAS.csv ·
13_ISOLATED_DOWN_SEQUENCE_ATLAS.csv · 14_RANK_DETERIORATION_SHOCK_BRIDGE.csv ·
15_FIRST_DIVERGENCE_UP_CONT_VS_GIVEBACK.csv ·
16_FIRST_DIVERGENCE_DOWN_REVERSE_VS_CONTINUE.csv ·
17_DEAD_NODE_REINTERPRETATION.csv · 18_NODE_MERGE_PROMOTE_DISSOLVE.csv ·
19_ALPHA_ROLE_REGISTRY.csv · 20_CROSS_AGENT_FIELD_CONTEXT.parquet ·
20b_CROSS_AGENT_FIELD_CONTEXT_SCHEMA.md · 21_NULL_AND_FAILED_RESULTS.csv ·
22_MECH7_SUMMARY.md · 23_MECH7_DECISION.md

## 7. Governance

NO STRATEGY. NO PNL. NO EXECUTION. NO CAPITAL SIZING. NO DEPLOYMENT.
Let the data speak. Do not force compression.
STOP AFTER MECH-7. WAIT FOR HUMAN REVIEW.

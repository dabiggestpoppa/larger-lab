# CRYPTO-ALT-LOWER-FIELD-3 — PREREGISTRATION

**Scope:** local event anatomy, neighborhood geometry, reversal staging, coordinated-up motifs, basket geometry, and one breadth–dispersion–tail triangle pilot.

**Parents:** LOWER-FIELD-1 `8801ca6c`; LOWER-FIELD-2 `af2ed678`.

**Governance:** terrain research only. No strategy, PnL, execution, entry/exit design, sizing, or deployment. `human_review_required=TRUE`; `next_checkpoint_authorized=FALSE`.

## Frozen event universe

Primary PIT bands: `501-750`, `751-1000`, `1001-1500`, `1501-2000`. Comparison bands `26-100`, `101-250`, `251-500` only where the repaired continuous return/sigma path is available.

Event gates are evaluated on causal `z1=abs(ret_1d)/sigma_t0`: `1s`, `2s`, `3s`, `4s+`, and raw `10%`, `15%`, `20%+`. The principal shock population is `>=2s`; headline reversal cells emphasize `>=3s`. All rolling scales are computed before the event date.

Participation classes are frozen as:

- `ISOLATED`: one same-sign `>=2s` asset in its band/date.
- `LOCAL_CLUSTER`: 2–5 same-sign events in its band/date.
- `BAND_BROAD`: 6–20 same-sign events in its band/date.
- `MULTI_BAND`: >20 same-sign events in its band/date.
- `GLOBAL_SYNC`: reserved for an independently observed same-day event across all primary bands; not inferred from one band.

## Neighborhoods

For every primary event, calculate descriptive context from available-at-t information:

1. rank neighbors ±25/±50/±100 by PIT rank;
2. behavioral peers by trailing volatility, liquidity, age, market cap, rank;
3. causal trailing-correlation peers;
4. shared momentum/risk/rank-band/liquidity state peers;
5. sector/chain peers as descriptive only (LF2 residual sector/chain result was null).

The first implementation uses equal-weight medians and quantiles. No master isolation score is fit or optimized. Component scores remain separate and report their coverage.

## Outcome clocks

Forward windows: `+1,+2,+3,+5,+7,+10,+14,+21,+30,+60D` where coverage permits. The first implementation is censored at +30D unless a valid +60D source is explicitly available.

For a downside event, signed forward displacement is `event_sign * fwd_cum`; recovery means positive signed displacement. For an upside event, giveback means negative signed displacement. `1SIGMA_RECOVERY` means signed forward displacement >= `sigma_t0*sqrt(h)` at horizon h. `25%/50% GIVEBACK` means the adverse signed forward displacement reaches 0.25/0.50 of the event-day absolute move. `FULL_REVERSAL` means signed forward displacement < 0. `NEW_LOW/NEW_HIGH` means same-sign forward cumulative displacement reaches at least the event-day absolute move.

Named outcome family rules require >=50 effective asset-clustered observations and >=3 subperiods. If clustering is unstable, use descriptive quantile families only.

## Pre-event / state comparisons

Frozen pre-event coordinates include rank, rank velocity where present, prior 3/7/14/30D returns, listing age, volume, liquidity proxy, trailing sigma, prior extreme count, local breadth/dispersion, neighbor median return, same-sign neighbor share, BTC/ETH, Top-500 breadth, and momentum shape. No post-event value is used in a pre-event discriminator.

## State machine

Competing state labels are evaluated at each forward horizon, not assumed to be strictly ordered:

`S0 EXTREME`, `S1 STABILIZED`, `S2 1S_RECOVERY`, `S3 25P_GIVEBACK`, `S4 50P_GIVEBACK`, `S5 FULL_REVERSAL`, `S6 NEW_EXTREME/CONTINUATION`.

Transition hazards are empirical event-time frequencies with censoring. No causal label is assigned.

## Coordinated-up outcome rules

For `BAND_BROAD_UP` and `MULTI_BAND_UP`, classify at +7D:
`CONTINUATION` if signed forward >= +25% of event move; `FULL_GIVEBACK` if <= -50%; otherwise `PARTIAL_GIVEBACK/NEUTRAL`. `NEW_HIGH_EXTENSION` is same-sign displacement >= event absolute move. These labels are descriptive and not signals.

## Testing and integrity

Use asset-clustered event counts; 30D purge where events are used for headline claims; minimum 50 effective observations for named sequences; BH-FDR for broad scans; leave-one-quarter-out and leave-one-cycle checks where sample permits. Report statistical validity separately from `EXECUTABILITY_STATUS=NOT_YET_AUDITED`.

The MECH-7 context join is optional. If unavailable, LF3 stores a stable date-keyed join schema for later application without regenerating core events.

## Decision rubric

Allowed classifications: `PROMOTION_CANDIDATE`, `NEW_NODE`, `LOCAL_NODE`, `DESCRIPTIVE_ONLY`, `MERGE`, `DISSOLVE`, `NULL`, `QUEUED`, `DATA_BLOCKED`. A named local sequence must satisfy all minimum-sample rules; otherwise it remains descriptive or queued.

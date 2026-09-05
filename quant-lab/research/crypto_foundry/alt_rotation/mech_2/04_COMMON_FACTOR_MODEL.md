# COMMON-FACTOR MODEL (Workstream A)

## Design

For each rank band and each of three metrics (equal-weight 1d return, median rank
velocity 7d, breadth 7d), band series are regressed on a common-factor set:

- total crypto market return (1d)
- BTC return (1d)
- ETH return (1d)
- market realized volatility (median)
- Top-500 breadth (30d)
- stablecoin supply change (30d, AVAILABLE_NEXT_DAY)

Residuals are formed with a rolling expanding-window OLS (min 60 days, 252-day cap).
Band-pair lead/lag cross-correlations (lags ±14d, block bootstrap 500, date-block
shift permutations) are computed for **RAW** and **RESID** variants. A pair is
`STRUCTURAL_LEAD_LAG` only if the residual relationship survives at p<0.05 with the
same sign as raw; if it vanishes after residualization it is
`COMMON_FIELD_EFFECT`.

Full results: `04_COMMON_FACTOR_MODEL.csv`, `05_CONDITIONAL_LEAD_LAG.csv`.

## How much of each band metric is common?

| metric | band | common-factor R² |
|---|---|---|
| ew_return_1d | 1-10 | **0.869** |
| ew_return_1d | 11-25 | 0.783 |
| ew_return_1d | 26-50 | 0.775 |
| ew_return_1d | 51-100 | 0.759 |
| ew_return_1d | 101-200 | 0.746 |
| ew_return_1d | 201-300 | 0.797 |
| ew_return_1d | 301-500 | 0.748 |
| rank_velocity_7d | all bands | 0.004 – 0.117 |
| breadth_7d | all bands | 0.181 – 0.233 |

**Reading.** ~75–87% of daily band return variance is shared market movement. Rank
velocity is almost entirely band-specific (R² < 0.12) — rank migration is NOT a
common-factor phenomenon. Breadth is moderately common (~20%).

## Lead/lag classification (126 tested cells, 3 metrics × 21 band pairs × 2 variants)

- `STRUCTURAL_LEAD_LAG`: 110 cells
- `AMBIGUOUS` (sign flips between raw and resid): 10
- `COMMON_FIELD_EFFECT` (raw-only, dies after residualization): 6
- `WEAK`: 0
- FDR q<0.05 on 123/126 raw cells — but see below.

**Critical caveat.** The surviving band correlations are **contemporaneous** (best
lag = 0, |corr| ≈ 0.97–0.98 for adjacent bands, e.g. 26-50↔51-100). Bands move
*together on the same day*; there is no consistent 1-day sequential band cascade in
raw returns. The "lead/lag structure" that survives is a statement about *synchronous
co-movement of band residual dynamics*, not about a BTC→…→small-alt propagation
sequence. Rank-velocity cells show real but smaller lagged structure; the strongest
genuine delayed effects appear in **Workstream B** conditioning (see
`04b`/`05b_CONDITIONAL_LEAD_LAG_STATES.csv`): e.g. band 51-100 rank velocity leads
101-200 by 1 day with corr +0.64 under BTC_DOWN and +0.67 under VOL_HIGH, where the
unconditional pair has the *opposite* sign (−0.30) — conditioning on regime
materially changes the propagation picture.

## Verdict

- Raw band return "lead-lag" is mostly common-field co-movement at lag 0 → do not
  interpret as a sequential cascade.
- Rank velocity and conditioned lead/lag are genuine band-level signals and are
  orthogonal to the common factor.

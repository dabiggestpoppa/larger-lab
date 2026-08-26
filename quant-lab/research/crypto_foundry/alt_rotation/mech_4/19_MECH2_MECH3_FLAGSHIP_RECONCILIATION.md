# MECH-2 vs MECH-3 FLAGSHIP RECONCILIATION — `51-100 → 101-200` RANK-VELOCITY LEAD

## The reported discrepancy

| Source | Unconditional best cell | Conditional |
|---|---|---|
| MECH-2 (`05b`) | **−0.3044 at h=−7** (over lags [−7,−3,−1,1,3,7]) | BTC_DOWN ≈ +0.64, VOL_HIGH ≈ +0.67 |
| MECH-3 (`08`) | **+0.1333 at h=+1** (over lags [1,3,7]) | BTC_DOWN ≈ +0.63, VOL_HIGH ≈ +0.67 |
| MECH-4 audit (this file) | −0.3044 at h=−7 AND +0.1333 at h=+1 both reproduce on the SAME daily frame | conditional values reproduce under both lag grids |

## Root cause (empirically located, same universe/estimator/aggregation)

- **See `19_MECH2_MECH3_FLAGSHIP_RECONCILIATION.json`** for the full recomputation.
- Universe, dates (2,196), PIT frame, band aggregation (median rank velocity 7D),
  and the estimator (`_cond_xcorr`, block-shift permutation) are IDENTICAL.
- The entire difference is the **candidate lag grid and the best-lag selection rule**:
  - MECH-2 scanned lags {−7,−3,−1,1,3,7} and took max |corr| → **h=−7, corr −0.3044**
    (that is the 101-200→51-100 reverse at 7-day lag, negative).
  - MECH-3 scanned forward lags {1,3,7} only and took max |corr| → **h=+1, corr
    +0.1333** (51-100 leads 101-200 at 1 day, positive).
- The full data (MECH-4 audit) shows the relationship is genuinely **sign-dependent on
  the lag horizon**:
  - h=−7: −0.3044 (significant) — at 7 days the higher band has moved past and the
    association flips negative (reversal/overshoot).
  - h=−3: +0.113, h=−1: +0.107, h=+1: +0.133, h=+3: +0.102, h=+7: −0.079.
- So there is a **near-zero-lag positive association** (51-100 velocity correlates with
  101-200 velocity at 0-3 days) that becomes **negative at 7-day lag** (mean-reversion
  of the relative band velocity). The two checkpoints each "discovered" one tail of a
  single lag-shaped relationship.
- **Conditional values reproduce exactly** under both grids because they are evaluated
  at near-zero lag (h=+1 and h=−1) where the association under BTC_DOWN/VOL_HIGH is
  strong (+0.63/+0.67) and sign-stable regardless of grid.

## Classification

**DEFINITION_CHANGE_AND_ESTIMATOR_CHANGE** — not a bug, not a data-version change,
not a sampling change. The unconditional apparent discrepancy is an artifact of
two different lag grids + best-lag selection rules reporting different tails of the
same lag-shaped relationship.

## Canonical unconditional statement (this checkpoint resolves it)

> "The 51-100→101-200 rank-velocity lead is **positive and significant at 0–3 day
> lag** (+0.10 to +0.13) and **negative at 7-day lag** (−0.30) — a near-zero-lag
> propagation that mean-reverts by 7 days. Under BTC_DOWN / VOL_HIGH it strengthens
> substantially at near-zero lag (+0.63 / +0.67). There is no single valid
> 'unconditional sign' without specifying the lag horizon."

MECH-2's −0.30 and MECH-3's +0.13 are NOT contradictory — they are the 7-day and
1-day evaluations of the same relationship. This resolved claim supersedes the
MECH-2/MECH-3 unconditional numbers and is the canonical reference.

## Carry-forward

The MECH-2 flagship "unconditional −0.30 appears to reverse under BTC_DOWN"
should be re-stated as: "the near-zero-lag positive lead (+0.13) strengthens
markedly under BTC_DOWN/VOL_HIGH (+0.63/0.67); the 7-day reversal (−0.30) is a
separate mean-reversion tail and should not be treated as the unconditional
propagation direction." No strategy implication (mechanism research only).
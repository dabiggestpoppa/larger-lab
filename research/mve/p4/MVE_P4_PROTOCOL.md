# MVE P4 — CAUSAL ACCEPTANCE ENGINE · PRE-REGISTERED PROTOCOL

> **Checkpoint:** `MVE-P4-CAUSAL-ACCEPTANCE-ENGINE` · Branch `cerebus-mve-implementation`
> **Base:** `54bce6cd27d0fe60fcdad62f4273bb3c23e0c2a6` (MVE-R0.5-INFRASTRUCTURE-SEAL)
> **Authorization:** P4 AUTHORIZED by human instruction (master prompt). P5 NOT
> authorized. Final holdout `FINAL_HOLDOUT_PENDING`.
>
> This document is the PRE-REGISTRATION for P4 science. It is written BEFORE
> any measurement, states every variant definition, every parameter, every
> ranking/promotion criterion, and the development/confirmation discipline.
> The confirmation pass is mechanically refused unless the development stage
> froze an identical parameter set (`MVE_P4_DEVELOPMENT_FROZEN_PARAMS.json`).

## 1. Research questions (frozen)

Q1. Does acceptance improve continuation probability versus touch/breach?
Q2. Does close-beyond add value?
Q3. Does occupancy add information beyond close/distance?
Q4. Does persistence add information beyond occupancy?
Q5. Does retest-hold add independent information?
Q6. Are effects robust across sigma states?
Q7. Are positive and negative sides symmetric?
Q8. Are results temporally stable?
Q9. Do results survive 2025 confirmation?
Q10. Which acceptance variants deserve P5 promotion?

## 2. Field / coordinate construction (frozen)

- Data: canonical `quant-lab/data/EURUSDPRO_M5_2023_2026.csv`
  (SHA-256 `630b8a4052fe962bc7d87c6d49d83bc1524c7ddd83cd15e902fe504c998d3f77`),
  M5 → H1 via the sealed `resample_m5_to_h1` (open=first, high=max, low=min,
  close=last, volume=sum; weekend empty hours dropped; no forward fill).
- Volatility: `close_to_close` rolling std (window 20, causal) — the sealed
  causal volatility estimator.
- Anchors (PRIMARY family): trailing PRIOR-50-bar extreme —
  `rolling(50, min_periods=20).max()/.min().shift(1)` (the extreme of bars
  [t-50, t-1], strictly causal, realtime). This is the simple-breakout
  distance reference (the P4 spec's mandatory "distance-only / simple
  breakout" baseline) and the coordinate it defines is bounded and symmetric
  on the canonical data (1-sigma touch rate ~4.4%, 2-sigma ~1.6%).
- Anchors (ROBUSTNESS family): pivot highs/lows, window 5, min height
  0.001 (0.1%), min width 3, consumed ONLY through
  `apply_anchor_delay(pivots, window=5)` (delayed confirmation; no value
  consumable before its knowledge time). P4-D parameter note: the sealed
  default min height 1% produces ~4 pivots over the entire 2023-2026 sample
  (~6-month structural levels) and hence NO usable coordinate field on the
  canonical H1 data; the relaxed 0.1% height (documented, frozen here) yields
  a usable delayed-confirmation structural anchor. The robustness family is
  used ONLY for the anchor-sensitivity check of the headline result.
- Signed coordinates (per direction):
  - d = +1 (upper): `x = ln(close / anchor_up) / sigma`, extreme `ln(high / anchor_up) / sigma`
  - d = -1 (lower): `x = -ln(close / anchor_lo) / sigma`, extreme `-ln(low / anchor_lo) / sigma`
  (signed so that positive x means "beyond" for both directions).
- Boundaries (sigma units): **B ∈ {1.0, 2.0}** · directions **d ∈ {+1, -1}**.
- Warmup NaNs (anchor/vol not yet valid) produce NO events — fail-closed, no
  synthetic fill.

## 3. Acceptance variant family (frozen)

Definitions are per (direction, boundary). An **episode** opens at the first
touch bar (`x_ext >= B`) with no active episode for that variant, and closes
at acceptance, rejection, or expiry at the max horizon H = 24 H1 bars.

| id | name | acceptance rule | failure rule |
|----|------|-----------------|--------------|
| A0 | TOUCH | accepted at the touch bar close (instant) — the baseline | none (baseline never fails) |
| A1 | CLOSE | accepted iff the touch bar closes beyond (`x >= B`) | REJECTED at the touch bar if it closes inside (`x < B`) |
| A2 2OF3 | OCCUPANCY | accepted at first beyond-close bar whose trailing-3 window has ≥2 beyond closes | EXPIRED at H without completion (dips tolerated) |
| A2 3OF4 | OCCUPANCY | ≥3 of trailing-4 | EXPIRED at H |
| A2 3OF5 | OCCUPANCY | ≥3 of trailing-5 | EXPIRED at H |
| A3 PERS_2 | PERSISTENCE | 2 consecutive beyond closes | REJECTED at first inside close after the beyond run begins |
| A3 PERS_3 | PERSISTENCE | 3 consecutive | same |
| A3 PERS_4 | PERSISTENCE | 4 consecutive | same |
| A4 | RETEST-HOLD | break (beyond close) → retest (close in `[0.5B, B)` after a beyond close) → hold (beyond close after the retest) | REJECTED at close `< 0.5B` before confirmation; break-then-hold without retest EXPIRES at H |

**A5 (failed acceptance / rejection control):** for every variant, episodes
resolved REJECTED or EXPIRED are the failed-acceptance group; their forward
outcomes are measured from the terminal bar.

Timestamp schema (frozen, enforced by `validate_acceptance_events`):
`state_event_time (touch bar) <= evidence_complete_time (terminal bar)
<= acceptance_known_time (terminal bar)`.

## 4. Outcome measurement (frozen, EX-POST by design)

The acceptance bar k defines a FIXED price level L = anchor_k · exp(B·σ_k)
(the price level of the accepted boundary, knowable at k). Continuation is
measured against L — NOT against the live ratcheting anchor, which absorbs
the acceptance bar itself and would make "still beyond" degenerate by
construction. Horizons h ∈ {1, 2, 3, 6, 12, 24} after bar k:

- `cont_h` = close[k+h] ≥ L (continuation, point state)
- `rej_within_h` = first bar in (k, k+h] with close < L (rejection)
- `disp_h` = close[k+h] − L (signed displacement, level units)
- `norm_disp_h` = (close[k+h] − L)/L (normalized displacement)
- `mfd_h` = max_{j in (k, k+h]} (close[j] − L)/L; `mad_h` = max_{j in (k, k+h]} (L − close[j])/L
- `next_state_h` = floor(|x_frozen[k+h]|) with x_frozen = ln(close/anchor_k)/σ_k
  (frozen-coordinate state); `time_to_next_state` = first bar with
  floor(|x_frozen|) > floor(|x_k|)
- `persist_dur` = consecutive bars from k+1 with close ≥ L
- `time_to_rekey` = first RKEY-A rekey event strictly after k within H
  (exploratory linkage; RKEY-B/C deferred to P6)

Sigma states for conditioning/transition remain the LIVE coordinate state
`floor(|x|)` at the acceptance bar (control), while forward state transitions
use the frozen coordinate (above).

Controls recorded per episode: `x_known`, `abs_x_known`,
`dist_boundary_known`, `sigma_state_known`, volatility tercile (frozen dev
cutoffs), direction, session (6 x 4h UTC buckets).

Anchor robustness: the headline continuation lift (h=6, B=1.0, directions
pooled) is recomputed on the pivot robustness family; a variant keeps its
promotion only if the lift has the same sign in both anchor families
(recorded in the evidence matrix as `anchor_robust`).

## 5. Data discipline (frozen)

- Development: 2023-07-03 .. 2024-12-31 (discovery; ALL definitions,
  cutoffs, seeds, ranking and promotion criteria frozen here).
- Confirmation: 2025-01-01 .. 2025-12-31 — ONE pass, no tuning. Refused
  unless the frozen-params hash matches the live registry.
- Temporal stability within development: fixed calendar halves
  H1 = 2023-07-03..2024-03-31, H2 = 2024-04-01..2024-12-31.
- Final holdout (2026): `FINAL_HOLDOUT_PENDING`; unreachable via
  `slice_data`; `holdout_rows_read` must remain 0.

## 6. Statistics (frozen)

- Wilson 95% CI on proportions; seeded percentile bootstrap (seed 7777,
  2000 draws) on differences vs the A0 baseline; event-frequency matched
  control (fixed seed 4242, N matched within (d, B)).
- Incremental information: IRLS logistic regression on `cont_6`,
  controls = {dist_boundary_known, sigma_state_known, vol tercile, direction,
  hour bucket}; per-variant likelihood-ratio test vs controls-only;
  Benjamini-Hochberg FDR over the 8 variants × 2 boundaries family.
- Survival: Kaplan-Meier of the accepted state (event = time_to_rejection,
  censor at 24); discrete hazard.
- Transition matrices: sigma state at acceptance → state at h=6, separated
  by outcome class {accepted (A1), touch-only (A0 \ A1-accepted),
  failed (A2 3OF5 non-accepted)}.

## 7. Ranking / promotion criteria (frozen BEFORE 2025 opens)

For each (variant, boundary), primary horizon h=6, directions pooled:

1. Causality PASS (module gates).
2. N_accepted(dev) ≥ 200 (per-direction N ≥ 50 required for symmetry claims).
3. Dev lift vs A0: Δ = P_cont(acc) − P_cont(A0) ≥ 0.03 AND bootstrap CI
   excludes 0.
4. Incremental: LR p < 0.05 after BH-FDR (not explained by controls).
5. Temporal: same-sign Δ in both dev halves.
6. Confirmation: Δ_conf > 0 AND confirmation CI overlaps the dev CI.
   Material reversal (Δ_conf ≤ 0 with CI excluding 0) → downgrade.

Evidence categories: ROBUST / VALIDATED_CONFIRMATION / VALIDATED_DEVELOPMENT /
CONDITIONAL / REDUNDANT / UNSTABLE / INSUFFICIENT_N / REJECTED /
HYPOTHESIS_ONLY.

Promoted to P5: categories {ROBUST, VALIDATED_CONFIRMATION,
VALIDATED_DEVELOPMENT}. P4 passes regardless of whether anything is promoted;
`acceptance_information_validated` may be TRUE, FALSE, or MIXED.

## 8. Forbidden in P4

No trade targets, stops, sizing, or PnL. No black-box ML. No backdating. No
centered windows. No full-sample normalization in executable detection.
Model D and Model E remain BLOCKED_LOGIC_SPEC and are never consumed.

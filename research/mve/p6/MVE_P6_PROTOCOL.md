# MVE P6 — REKEY MECHANICS PROTOCOL (Pre-Registration)

> **Checkpoint:** MVE-P6-REKEY-MECHANICS
> **Base:** e8f5600cb138ecf54c5bf39c432c0d80649f45a8 (P4, sealed)
> **Infrastructure seal:** 54bce6cd27d0fe60fcdad62f4273bb3c23e0c2a6
> **P5:** SKIPPED_NO_PROMOTED_ACCEPTANCE_VARIANTS (recorded, not implemented)
> **Written before ANY P6 measurement.** This document freezes the field, the
> RKEY semantics, the episode/dedup rule, the outcome definitions, the
> counterfactual, the baselines, the incremental-information tests, and the
> promotion rubric. Deviating from it after measurement is a protocol breach.

---

## 1. Purpose

P6 asks one structural question: **does rekey (re-anchoring the morphic
coordinate system when an accepted sigma boundary is crossed) materially
change the conditional downstream state distribution**, beyond what the
current morphic state (coordinate distance, sigma state, volatility,
direction, anchor age) already explains?

P6 does NOT ask "which rekey makes money". No PnL, no stops, no targets, no
sizing anywhere in this phase.

## 2. Field

Canonical source `quant-lab/data/EURUSDPRO_M5_2023_2026.csv`
(SHA256 `630b8a40...d3f77`), M5 → H1 (open=first, high=max, low=min,
close=last, volume=sum; weekend hours dropped; no forward-fill; no synthetic
data).

**Coordinate field (same as P4, sealed semantics):** signed sigma coordinate
`x` from the trailing **prior-50-bar** extreme anchor (`rolling(50).shift(1)`,
strictly bars <= t−1) and the `close_to_close` volatility estimator:

- upper family `x_up = ln(close / A_up) / vol`, positive = above the upper anchor
- lower family `x_lo = -ln(close / A_lo) / vol`, positive = below the lower anchor

NaN in anchor/vol propagates (no synthetic fill). All field computation is
truncated to `<= 2025-12-31` BEFORE any computation; 2026 rows are never read.

**Robustness anchor family:** pivot high/low anchors (window 5, min height
0.1%, min width 3, delayed via `apply_anchor_delay`), B=1.0 only, headline
metrics only.

## 3. RKEY registry (frozen)

| id | label | semantics (sealed `MorphicRekey.detect_rekey_events`) |
|----|-------|--------------------------------------------------------|
| RKEY_A | realtime re-anchor | re-anchor when `abs(x)` crosses above `B` from `<= B`; all four timestamps = crossing bar |
| RKEY_B | delayed confirmation | breakout at bar `i` (event_time) confirmed by a retest bar `j in (i, i+4]` with `abs(x_j) > B`; new anchor becomes active ONLY at `j` (NO backdating); `evidence = known = active = j` |
| RKEY_C | state-survival re-anchor | re-anchor when the sigma state up-crosses (`state = floor(abs(x)/step)`) AND the trailing window `[i-2, i]` has >= 3 bars above `B` (NaN in window = not ready, no event); realtime |

Boundary grid: `B in {1.0, 2.0}` (`step=1.0`, `n=1 or 2`). Direction grid:
`d in {+1 (upper), -1 (lower)}`. The detector runs on the upper signed series
`x_up` and the lower signed series `x_lo` separately.

**Side attribution (P6-D amendment, made before confirmation):** events are
assigned to the side by the sign of the coordinate at the ACTIVATION bar
(`new_anchor_active_time`): `x >= 0` on the upper series / `x_lo >= 0` on the
lower series (positive = beyond in that family); opposite-sign events belong
to the other family and are dropped. This is required because RKEY-B's
sealed scan-origin flag can persist across a re-entry and fire a retest on
the opposite side of its scan-origin coordinate; the activation bar is the
scientifically meaningful rekey bar.

**Anchor value (P6-D amendment, made before confirmation):** the rekey anchor
coordinate is the coordinate at the STRUCTURAL CROSSING bar
(`crossing_pos` = first beyond bar after the last inside bar before the
activation bar). This equals the sealed detector's scan-origin value in all
well-formed cases (breakout = crossing) and is honest in the stale-flag
cases; the sealed scan-origin value is retained descriptively as
`anchor_value_sealed`. RKEY-B timing is unchanged: event = scan-origin,
evidence = known = active = retest bar, no backdating.

**No new RKEY variants are defined. No rescue variants are invented.**

## 4. Rekey event-time contract (frozen schema)

Every catalog row carries the R0.5.1 field set
(`MVE_REKEY_CAUSAL_SCHEMA.json`):

```
rekey_event_time <= rekey_evidence_complete_time <= rekey_known_time <= new_anchor_active_time
```

- A/C: all four timestamps = the re-anchor bar (realtime).
- B: `event = i` (breakout), `evidence = known = active = j` (retest bar).
  The new anchor value is the coordinate at the scan-origin bar `i`
  (sealed formula, unchanged); it becomes active at `j` and NEVER earlier.
  No historical rewrite.

Validators fail closed: missing timestamps, NaT, or ordering violations are
recorded and block the pipeline.

## 5. Rekey episodes and dedup

Raw detection is NOT an episode set:

- A emits once per crossing (already distinct).
- C emits once per state up-crossing (already distinct).
- **B emits per-bar while the coordinate stays beyond** (every bar finds a
  confirming bar 1-4 ahead). This must be collapsed.

**Merge rule (uniform across variants):** process raw events in emission
order. An event begins a NEW episode iff at least one bar strictly between the
previous kept episode's `known_time` and the candidate's `event_time` has
`abs(x) <= B` (re-entry invalidates the previous rekey) or is NaN
(fail-closed: unknown breaks continuity). Otherwise the candidate is the same
structural transition and is dropped (the earlier confirmation wins).

An episode therefore spans one anchor transition:

- **starts:** first causal evidence of the rekey candidate (event bar),
- **completes:** new anchor activation (known bar of the kept event),
- **ends:** rekey invalidates (re-entry through the boundary) or the next
  distinct rekey occurs.

Cross-variant events at the same (direction, boundary, event bar) are the same
structural crossing detected by different RKEY semantics — recorded with a
shared `duplicate_episode_id` and counted as BY DESIGN, not as duplicates.

## 6. Primary outcomes (measured from `new_anchor_active_time`)

Fixed horizons `h in {1, 2, 3, 6, 12, 24}`; max horizon 24.

At the activation bar `k` the rekey defines a **fixed price level**
`L = A_k * exp(anchor_coord * vol_k)` (upper) or
`L = A_k * exp(-anchor_coord * vol_k)` (lower), where `A_k` is the anchor
price at `k` and `anchor_coord` is the rekey anchor coordinate at the
structural crossing bar (P6-D amendment above; positive = beyond in that
family). The boundary price level `L_B` uses `B` in place of `anchor_coord`.

Signed new-frame displacement (frozen at `k`): `s_t = d * ln(close_t / L) / vol_k`,
positive = beyond the rekey level in the rekey direction. Signed old-frame
displacement (counterfactual): `z_t = d * ln(close_t / A_k) / vol_k`.

- `cont_h` — `s_{k+h} > 0` (beyond the rekey level at h)
- `rej_within_h`, `time_to_rejection` — first `t in (k, k+h]` with `s_t <= 0`
- `disp_h` / `norm_disp_h` — `d*(close_{k+h} - L)` / `d*(close_{k+h} - L)/L`
- `mfd_h` / `mad_h` — favorable / adverse displacement over `(k, k+h]` (price-relative)
- `next_state_h` — `floor(|s_{k+h}|)` (new-frame sigma state)
- `time_to_next_state` — first `t` with `floor(|s_t|) >= 1`
- `persist_dur` — consecutive bars from `k+1` with `s_t > 0`
- `old_state_h` — `floor(|z_{k+h}|)` (counterfactual frame state)
- `time_to_next_rekey` — bars to the next same-variant episode activation (within 24, else -1)
- `anchor_survival` — time to rejection (KM event) and time to next rekey (KM event), separately censored

Outcomes are EX-POST by design (the object of study) and never feed back into
detection.

## 7. Old-anchor counterfactual (PATH A vs PATH B)

For every rekey episode, compare two state representations of the SAME
realized path from `k`:

- **PATH A — rekey:** new-frame displacement `s_t` (origin at `L`)
- **PATH B — counterfactual keep old anchor:** old-frame displacement `z_t`
  (origin at `A_k`)

Metrics (ex-post evaluation only; never used to choose an anchor):

- next-state distribution at h=6 in each frame → **transition entropy**
- mean |displacement| over `(k, k+6]` → **coordinate dispersion**
- `persist_dur` (new frame only)
- per-episode `state_at_6` in each frame

Question: does the rekey frame organize the post-activation path better
(lower entropy / lower dispersion / state concentrated near the new origin)
than keeping the old anchor? No future information decides either frame.

## 8. Baselines / controls (incremental information)

| variant | control set | known at |
|---------|-------------|----------|
| RKEY_A | sampled beyond-state bars (`abs(x) > B`, NOT fresh crossings), frequency-matched, seeded | the bar itself |
| RKEY_B | A-crossings with NO B episode (breakout with no confirming retest in 4 bars) | `i+4` (lookahead exhausted) |
| RKEY_C | A-crossings with NO C episode (state up-crossing without 3-of-3 window) | the crossing bar |

Continuation for rekeys AND controls is measured against the **boundary
level** `L_B` at the anchor bar (uniform reference; the LR isolates the rekey
treatment, not the level).

Covariates: `dist_from_boundary` (`x - B`), `sigma_state_before`
(`floor(|x|)`), volatility tercile (frozen dev terciles), direction, anchor
age, hour/session.

## 9. Incremental-information tests (interpretable only)

IRLS logistic regression (P4 machinery) on `cont_6`:

- controls-only model vs controls + `variant_dummy` (rekey vs control);
- LR test (chi2, 1 df), Wald z on the dummy, BH-FDR across all
  (variant × boundary) cells.

Allowed: logistic/linear regression, survival (KM), transition matrices,
entropy comparison, stratification. Forbidden: black-box ML, neural networks,
boosted optimization.

## 10. Statistical inference

- Wilson score binomial CIs on proportions;
- seeded percentile bootstrap (2000 draws) on deltas and differences;
- effect sizes with CIs, not p-value fishing;
- BH-FDR for the exploratory family;
- N and coverage reported for every cell.

Coverage gates (NOT significance thresholds): `N >= 200` HIGH, `>= 75` MEDIUM,
`>= 30` LOW, `< 30` INSUFFICIENT_N.

## 11. Temporal discipline

- **Development:** 2023-07-03 .. 2024-12-31 (discovery). Everything above is
  frozen here; `MVE_P6_DEVELOPMENT_FROZEN_PARAMS.json` written.
- **Confirmation:** 2025-01-01 .. 2025-12-31, ONE pass, mechanically refused
  unless the live registry hash matches the frozen dev registry. No tuning.
- **2026:** final holdout, FINAL_HOLDOUT_PENDING, 0 rows read.

Temporal blocks (dev): 2023H2 (2023-07-03..2023-12-31), 2024H1
(2024-01-01..2024-06-30), 2024H2 (2024-07-01..2024-12-31). Classify each
variant STABLE / MIXED / UNSTABLE by sign consistency of the headline delta
across blocks + confirmation behavior.

## 12. Direction symmetry

All headline analyses are split by direction (+1 / -1): N, cont_6, rejection,
latency, entropy, persistence. Report asymmetry; never average it away.

## 13. P6 promotion rubric (toward P7)

A RKEY (variant × boundary) is promoted only if ALL of:

1. causality PASS (future perturbation 0.0, truncation 0.0, schema clean);
2. N sufficient (dev N >= 200);
3. nontrivial structural effect (delta_cont_6 vs control >= 0.03 with CI > 0);
4. incremental — LR q < 0.05 and rekey coef > 0 (not explained by controls);
5. temporal stability acceptable (no dev-block reversal);
6. 2025 confirmation does not materially reverse (same sign, CI not negative);
7. direction asymmetry understood;
8. no dependence on blocked Model D/E;
9. no dependence on 2026.

Promotion is a structural-evidence statement, NOT a trading rule.

Evidence labels: VALIDATED / CONFIRMED / STRUCTURAL / REDUNDANT / CONDITIONAL
/ MIXED / UNSTABLE / INSUFFICIENT_N / HYPOTHESIS / REJECTED / BLOCKED.

## 14. Valid null outcomes

ALL RKEYS REDUNDANT, ONLY RKEY-A USEFUL, B DELAY NOT WORTH IT, REKEY HELPS
ORGANIZATION BUT NOT CONTINUATION, or NO RKEY FAMILY SURVIVES CONFIRMATION are
all valid. P6 can PASS with `rekey_information_validated = false`.

## 15. Blocked components

MODEL_D (BLOCKED_LOGIC_SPEC) and MODEL_E (BLOCKED_LOGIC_SPEC) are excluded by
construction; `generate_all_signals` (BLOCKED_AGGREGATE) is not consumed. If a
P6 conclusion turns out to depend on them, STOP and report the dependency.

## 16. Holdout

2026 = FINAL_HOLDOUT_PENDING. No 2026 row may be read, summarized, counted, or
plotted. The pipeline truncates the frame before any computation; the
holdout-guard test and the data-access ledger enforce and record this.

## 17. Reproducibility

Deterministic (fixed seeds 7777/4242/601). Artifacts record repo, branch,
commit SHA, dataset SHA, script SHAs, Python and package versions, test
counts. Full input-hash manifest written at runtime.

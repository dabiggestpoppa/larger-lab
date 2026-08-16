# MVE P4 — CAUSAL ACCEPTANCE ENGINE · REPORT

> **Checkpoint:** `MVE-P4-CAUSAL-ACCEPTANCE-ENGINE` · **Status:** PASS
> **Branch:** `cerebus-mve-implementation` · **Base:** `54bce6cd` (MVE-R0.5-INFRASTRUCTURE-SEAL)
> **Date:** 2026-08-16 · **Pre-registration:** `MVE_P4_PROTOCOL.md` (hash in
> `MVE_P4_DEVELOPMENT_FROZEN_PARAMS.json`)
>
> **Bottom line:** the causal acceptance engine is implemented, gated, and the
> pre-registered analysis is complete. On the prior-50-bar-extreme sigma field,
> close-beyond acceptance shows a large, temporally stable, confirmation-robust
> continuation lift vs touch — but that lift is **fully explained by the
> coordinate distance at the event bar** (logistic regression; the acceptance
> state is a deterministic function of the displacement). No acceptance variant
> carries independent information beyond the simple displacement baseline on
> this field. Occupancy/persistence/retest variants have insufficient event
> counts (N < 200) to adjudicate. **Nothing is promoted to P5.**
> `acceptance_information_validated = FALSE`.

---

## 1. What was built

New causal science modules (P4-only; sealed R0.5 components untouched):

| File | Purpose |
|---|---|
| `src/mve/p4_acceptance.py` | frozen variant registry (A0–A4, A5 classification), forward-only episode detection, fixed-level outcome measurement, AST static-leakage scanner |
| `src/mve/p4_statistics.py` | Wilson CI, seeded bootstrap, BH-FDR, IRLS logistic regression + LR tests, Kaplan-Meier, transition tables |
| `research/mve/p4_tools/run_p4.py` | deterministic dev→freeze→confirmation pipeline writing all artifacts |
| `tests/mve/test_p4_acceptance.py` | 46 tests: causality gates, schema, dedup, determinism, leakage audit, holdout guard |

## 2. Data and field

- Canonical EURUSD M5 → H1 (SHA-256 `630b8a40…d3f77`, fail-closed load).
- Dev 2023-07-03..2024-12-31 (9,329 H1 bars) · Confirmation 2025 (6,193 H1 bars).
  **Holdout 2026: `FINAL_HOLDOUT_PENDING`, 0 rows read.**
- Sigma field: `x = ±ln(close / anchor)/σ` with σ = causal 20-bar close-to-close
  vol; PRIMARY anchor = prior-50-bar close extreme (`.shift(1)`); ROBUSTNESS
  anchor = pivot (w5, min height 0.1%, delayed 5). See protocol §2 for the
  P4-D anchor parameter freeze (the sealed 1% pivot height yields ~4 pivots in
  2.5 years and no usable field — documented, frozen before confirmation).
- Boundaries B ∈ {1.0, 2.0}; directions ±1; 9 acceptance variants (A0 touch
  baseline, A1 close-beyond, A2 2of3/3of4/3of5 occupancy, A3 persistence 2/3/4,
  A4 retest-hold); H = 24; horizons {1,2,3,6,12,24}.

## 3. Causality gates (regression requirement)

- Future perturbation: **max diff 0.0** over 20 measured cells.
- Truncation invariance: **max diff 0.0** over 20 measured cells.
- Timestamp schema: 9,752 events validated, ordering `state ≤ evidence ≤ known`
  holds everywhere (fail-closed validator).
- Blocked-component isolation: Model D/E never consumed (test-enforced).
- Static leakage: 0 unclassified, 0 blocked findings (all classified
  CAUSAL/EX_POST_ONLY, see `MVE_P4_CAUSALITY_AUDIT.json`).
- Causal→ex-post dependency count: 0 (outcome measurement is ex-post by design,
  never feeds back into detection).
- Event dedup: 0 duplicate episode ids within any (stage, variant, boundary,
  direction) cell; 72 cells audited.

## 4. Headline results (continuation at h=6, B=1.0, vs A0 touch baseline)

| variant | N(dev) | P_cont(dev) | Δ dev [95% CI] | Δ matched | N(conf) | Δ conf [95% CI] | category |
|---|---|---|---|---|---|---|---|
| A0 TOUCH | 769 | 46.8% | — | — | 501 | — | baseline |
| A1 CLOSE | 366 | 60.1% | **+13.3pp** [6.8, 19.2] | +12.3pp | 259 | **+9.8pp** [2.4, 17.1] | REDUNDANT |
| A2 2OF3 | 98 | 63.3% | +16.5pp [6.4, 26.5] | +17.3pp | 68 | +8.0pp | INSUFFICIENT_N |
| A3 PERS_2 | 56 | 66.1% | +19.3pp [6.5, 31.8] | +23.2pp | 44 | +11.3pp | INSUFFICIENT_N |
| A4 RETEST | 10 | 90.0% | +43.2pp [22.0, 55.8] | +50.0pp | 4 | −27.3pp | INSUFFICIENT_N |

**Q1/Q2 (acceptance vs touch; close-beyond value):** close-beyond acceptance
raises 6-bar continuation by ~13pp in development (CI excludes 0), confirmed in
2025 (+9.8pp), temporally stable across dev halves (+10.9pp/+15.7pp), robust to
the pivot anchor family, and matched-frequency consistent (+12.3pp). The
accepted state also survives longer: KM survival at 6 bars 23.0% (dev) vs 8.3%
for failed acceptances; rejection within 6 bars 58.5% vs 72.3% for touch.

**Q3/Q4/Q5 (occupancy/persistence/retest):** point estimates are large
(+16.5pp/+19.3pp/+43.2pp) but N is below the pre-registered threshold
(N ≥ 200) on this field — these states are rare at the 1σ/2σ boundaries of the
prior-50-bar-extreme field (persistence-4 never occurs: N=0). **INSUFFICIENT_N**
is the honest verdict; no claim either way.

**Q6 (sigma states):** transition matrices from state 1 (dev): accepted → state
0 at 31.7% vs failed 24.2%; accepted episodes are more likely to fall back to
the base state over 6 bars (they entered deeper, frozen-coordinate reference).
Conditional controls (|x|, sigma state, vol tercile) absorb the acceptance
signal (see Q10).

**Q7 (direction symmetry):** A1 up +10.5pp vs down +16.0pp (dev) — both
positive, CIs overlap → symmetric within uncertainty (small downside tilt,
flagged CONDITIONAL, not promoted on its own).

**Q8/Q9 (temporal stability / confirmation):** A1 dev halves +10.9/+15.7pp,
confirmation +9.8pp with CI overlapping the dev CI — stable and non-reversed.
Survival at bar 1 is higher in confirmation (67.2% vs 58.3%).

**Q10 (promotion):** the incremental-information test (logistic regression on
`cont_6`, controls = dist_boundary_known, sigma_state_known, vol tercile,
direction, session) finds the A1 close-beyond dummy adds **no** information
beyond controls (coef −0.11, p = 0.46; BH-FDR q = 0.73). This is structural:
the acceptance state is the threshold `x_k ≥ B` of the displacement control, so
the continuation lift is attributable to the **displacement magnitude**, not to
an independent acceptance state. **A1 = REDUNDANT.** A4's marginal LR signal
(coef +1.64, p = 0.03, q = 0.45) rests on N = 10 → INSUFFICIENT_N.

**A5 (failed acceptance control):** continuation after a failed acceptance is
far below the touch baseline (A1-failed 34.7% vs A0 46.8% at h=6; occupancy
failures 12–14%): failed acceptances are genuinely informative *against*
continuation — i.e., the rejection process selects the non-persistent
population, consistent with the displacement being the carrier of information.

## 5. Evidence classification

| variant × boundary | category |
|---|---|
| A1_CLOSE × 1.0 | REDUNDANT |
| all other cells | INSUFFICIENT_N (N < 200; A3_PERS_4 × 1.0/2.0 N = 0) |

No ROBUST / VALIDATED_* / CONDITIONAL / UNSTABLE / REJECTED cells.
`acceptance_information_validated = FALSE`; `best_trading_rule_selected = FALSE`
(P4 measures structure only — no PnL, no targets, no stops, no sizing).

## 6. Reproducibility

- Deterministic: fixed seeds (bootstrap 7777, match 4242), canonical input
  hashes in `MVE_P4_INPUT_HASH_MANIFEST.json`, registry hash frozen in
  `MVE_P4_DEVELOPMENT_FROZEN_PARAMS.json` (confirmation mechanically refused on
  mismatch). Re-run: `python research/mve/p4_tools/run_p4.py --stage all`
  (dev-only: `--stage development`; confirmation-only requires the freeze).
- Artifacts: `MVE_P4_EVENT_CATALOG.csv` (9,752 episodes), `MVE_P4_STRUCTURAL_OUTCOMES.csv`,
  `MVE_P4_STATISTICAL_INFERENCE.json`, `MVE_P4_ACCEPTANCE_RANKING.csv`,
  `MVE_P4_TRANSITION_MATRIX.csv`, `MVE_P4_ACCEPTANCE_SURVIVAL.csv`,
  `MVE_P4_DIRECTION_SYMMETRY.csv`, `MVE_P4_TEMPORAL_STABILITY.csv`,
  `MVE_P4_CONFIRMATION_RESULTS.csv`, `MVE_P4_INCREMENTAL_INFORMATION.csv`,
  `MVE_P4_ACCEPTANCE_REKEY_LINKAGE.csv`, `MVE_P4_FORWARD_RETURN_SANITY.csv`
  (mean 6-bar log returns within ±0.1% — sane), `MVE_P4_CAUSALITY_AUDIT.json`,
  `MVE_P4_EVENT_DEDUP_AUDIT.json`, `MVE_P4_DATA_ACCESS_LEDGER.json`, decision.
- Rekey linkage (exploratory): RKEY-A fires within 24 bars for 38% of A1
  acceptances (mean 7.2 bars) at B=1.0; deeper/denser acceptance patterns
  (occupancy/persistence) rekey more often (65–91%). Full rekey mechanics are
  P6 scope.

## 7. Verdict

P4 **PASSES**: implementation causal (all gates 0.0/clean), analysis complete,
confirmation discipline respected (single pass, frozen registry), holdout
untouched, results scientifically classified. The acceptance engine is a
functional, gated scientific component. Its first empirical finding is a null
for independent acceptance information: on the prior-50-bar-extreme sigma
field, the continuation signal lives in the **displacement magnitude**, not in
the acceptance ceremony. Occupancy/persistence/retest questions remain open
(insufficient events on this field). **No variant promoted to P5.**

NEXT: human review. P5 (Acceptance Information Value) is NOT authorized.

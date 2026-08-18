# CR-RISK-BLOCK-IV-D1.1A-ARTIFACT-TRUTH-AND-QUANTILE-RECONCILIATION — PROGRESS

**Status:** PASS — committed, pushed, other checkout synced.

## Issue 1 — test count (repaired)

The D1.1 TEST_AUDIT / DECISION reported `tests_total = 52` — that was the
brief's MINIMUM-REQUIREMENTS list count, not the collected suite. Verified via
`pytest --collect-only`: the dedicated D1.1 suite is **62 tests** (AST count
of top-level `def test_*` matches exactly), and the 8-suite combined reference
is **261 collected**.

- Parent `CR_BLOCK4_D1_1_TEST_AUDIT.json` / `CR_BLOCK4_D1_1_DECISION.json`
  repaired to 62 / 62 / 0 (git diff of the regeneration shows ONLY those
  test-count fields changed — every science artifact byte-identical).
- D1.1 runner now derives the count from source (`dedicated_test_count()`,
  AST-based, verified == pytest collection) so a stale hardcoded count cannot
  recur.

## Issue 2 — quantiles (reconciled, case A)

The D1 plan descriptive quantiles (median 1.9842341231185, p75
3.51336658273125, p95 7.6104837047965, p99 16.0363747752485) and the D1.1
rank-bin edges (q50 1.979422975748, q75 3.524935294373, q95 7.61103477694,
q99 16.159547393888) are the **SAME 826-event accepted book** — identical
canonical book hash `b64be26010171801104518db72df63abe01714079a5081fef18c42f990a2580a`;
the two source columns agree to 4.98e-13 (float-op-order noise).

They are two DIFFERENT, now explicitly-named statistical definitions:

- `DESCRIPTIVE_DISTRIBUTION_QUANTILE` (D1 plan): pandas `Series.quantile(q)`
  linear interpolation (numpy type-7 / R-7) — distribution estimates.
- `RANK_BIN_EDGE` (D1.1): nearest-rank value at `sorted[ceil(n·q)-1]` — event
  value at rank fraction, used to assign events to frozen quantile bins.

`quantile_difference_explained = true` · `source_distribution_mismatch = false`
— no STOP condition, D1.2 planning may proceed after human review.

## Hard nonregression

Grid 39/178/417/655/786/817/825/826 · family distortion rows · 482 episodes ·
max concurrency 3 · 8 performance rows · science counts 890/826/371/455/64 —
all unchanged. No broker / margin / lot logic added.

## Evidence

- 10 artifacts in `research/capital_routing/risk/block4_exposure_feasibility_d1_1a/`
  (start with `CR_BLOCK4_D1_1A_TEST_COUNT_AUDIT.json`,
  `CR_BLOCK4_D1_1A_QUANTILE_DEFINITION_AUDIT.md`,
  `CR_BLOCK4_D1_1A_ARTIFACT_CORRECTION_LOG.md`, `CR_BLOCK4_D1_1A_DECISION.json`)
- tests: `tests/test_exposure_feasibility_d1_1a.py` — 21 tests
- combined: 282/282 across 9 suites (62+21 D1.1/D1.1A + 20 D1 + 49 D0.1 + 32
  D0 + 16 R1.1B + 16 R1.1 + 66 R1/scale-seal); determinism byte-identical

## Next

CR-RISK-BLOCK-IV-D1.2-INSTRUMENT-SPEC-AND-QUANTITY-REPRESENTABILITY-PLAN —
PLAN FIRST, `d1_2_authorized = false` until human review. Freeze intended
account / broker / USDJPY product / contract size / volume min-step-max /
account currency with provenance; no generic FX spec assumptions.

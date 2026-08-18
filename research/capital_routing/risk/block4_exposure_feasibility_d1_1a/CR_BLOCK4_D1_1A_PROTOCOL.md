# CR-BLOCK4-D1.1A PROTOCOL — Artifact Truth / Quantile Reconciliation

**Checkpoint:** CR-RISK-BLOCK-IV-D1.1A-ARTIFACT-TRUTH-AND-QUANTILE-RECONCILIATION
**Base:** `2a44e824c269d62545fa44538b0df3cea3f51e60` (D1.1)
**Scope:** narrow truth repair ONLY — test-count reporting and quantile
definition provenance. No science, no classifications, no grid, no
performance results, no episode definitions change.

## Repairs

1. **Test count** — D1.1 TEST_AUDIT/DECISION claimed `tests_total = 52`
   (the brief's MINIMUM-REQUIREMENTS list). The actual collected suite is
   **62 tests** (`pytest --collect-only`). Parent artifacts corrected to
   62/62/0; the D1.1 runner now derives the count from source (AST
   `def test_*`, verified equal to pytest collection) so it cannot drift.
2. **Quantiles** — D1 plan recorded DESCRIPTIVE_DISTRIBUTION_QUANTILE values
   (pandas linear interpolation); D1.1 froze RANK_BIN_EDGE values
   (nearest-rank event values at rank fractions). Both derive from the SAME
   826-event accepted book (identical canonical hash). They are different
   statistical definitions for different purposes, explicitly named.

## Non-goals

No strategy science change, no CapitalDecision change, no translation change,
no grid/count/classification change, no broker/margin/lot logic added.

## Hard nonregression

Grid 39/178/417/655/786/817/825/826 · family results · 482 episodes · max
concurrency 3 · 8 performance rows — all byte-identical after repair.

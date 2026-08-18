# CR-RISK-BLOCK-III-EXECUTION-TRANSLATION-R1.1B — Progress

**Checkpoint:** CR-RISK-BLOCK-III-EXECUTION-TRANSLATION-R1.1B-CROSS-BRANCH-PROVENANCE-TEST-REPAIR
**Status:** PASS · **Base:** `d51b9b47` · **Scientific seal:** `2bbe52ea` (R1.1)

## What was repaired

The historical cross-branch provenance test `test_no_cross_branch_write()`
(introduced in `d51b9b47`) resolved the CURRENT branch tips of
`execution-runtime-foundation` / `tb-forward-engine` and required them to equal
the R1.1-frozen authority SHAs — with a `git fetch` fallback. Those branches
are ACTIVE CONCURRENT WORKSTREAMS; a later legitimate advance would have failed
a historical seal.

**Repaired semantics:** provenance is frozen by IMMUTABLE commit SHA, never by
mutable branch tips:

- **A. Object exists** — `git cat-file -e <sha>^{commit}` for both frozen SHAs.
- **B. Commit identity** — subjects match the expected checkpoints
  (`QL-EXEC-R1-GENERIC-CONTRACTS-AND-ACCOUNT-REGISTRY`,
  `TB-R6.1B-FIX-WORKER-STATE-LATCH`).
- **C. Manifest/decision agreement** — R1.1B manifest ↔ R1.1B decision ↔ R1.1
  decision all carry the same frozen SHAs. (Historical note: the R1.1
  SOURCE_SHA_MANIFEST carried science-input hashes only; the R1.1B manifest
  closes that gap. Frozen SHAs themselves are never replaced.)
- **D. No cross-branch write by R1.1** — R1.1 commits (`2bbe52ea`,
  `d51b9b47`) are descendants of `capital-routing` and NOT ancestors of the
  frozen foreign commits; R1.1-specific files are absent from the frozen
  foreign trees (proved by ancestry + changed-file truth, not branch tips).
- **E. Current heads = diagnostics only** — recorded informationally; movement
  is never a test failure. A fixture test proves an advancing (and even
  seal-merging) branch does not fail the R1.1B validation, while the old
  tip-equality semantics would have failed.

**Hard rules honored:** no `git fetch` anywhere in the runner or tests; no
network dependence; fully deterministic offline suite (byte-identical re-run).
Tests that genuinely lack the frozen objects in a non-canonical checkout skip
instead of fetching.

## Science (UNCHANGED)

890 events · A 432 / B 458 · accepted 826 (A 371 / B 455) · rejected 64 ·
risk unit 24.49489742783178 bps (NOT a hard stop) · gross parity PASS ·
research-modeled net parity PASS · execution net BROKER_DEPENDENT_UNRESOLVED ·
canonical notional stats unchanged (pooled median 1.9842 / p95 7.6105 /
p99 16.0364 / max 32.7663).

## Artifacts

`research/capital_routing/risk/block3_execution_translation_r1_1b/` — PROTOCOL,
PROVENANCE_TEST_AUDIT, SOURCE_SHA_MANIFEST, NONREGRESSION, TEST_AUDIT, REPORT,
DECISION. Tests: `tests/test_exec_translation_planning_r1_1b.py` (16) +
repaired `tests/test_exec_translation_planning_r1_1.py`; suites 63/63
(R1 + R1.1 + R1.1B), determinism byte-identical.

## Decision

`provenance_test_pass = true` · `nonregression_pass = true` ·
`foreign_branch_write_detected = false` · `network_required_by_tests = false` ·
`git_fetch_used_by_tests = false` · `current_branch_tip_equality_required = false` ·
`broker_execution_performed = false` · `d0_ready = true` · `d0_authorized = false` ·
`production_authorized = false` · `human_review_required = true`.

**Next (recommended, NOT started):** CR-RISK-BLOCK-IV-CAPITAL-TRANSLATION-CORE-D0.

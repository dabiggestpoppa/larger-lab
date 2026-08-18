# CR-RISK-BLOCK-III-EXECUTION-TRANSLATION-R1.1B -- Protocol

**Checkpoint:** CR-RISK-BLOCK-III-EXECUTION-TRANSLATION-R1.1B-CROSS-BRANCH-PROVENANCE-TEST-REPAIR
**Base:** d51b9b4772f0bf2ee9a87deb830614e7494f25d1 · **Scientific seal:** 2bbe52ea8798549ed9c03bd90684fd3a0d408a99 (R1.1)
**Branch:** dabiggestpoppa/larger-lab · `capital-routing`

## Scope (narrow provenance-semantics repair ONLY)

- Repair the semantics of the historical cross-branch provenance test.
- Git SHA provenance is IMMUTABLE; branch tips are MUTABLE.
- Historical checkpoint tests lock the former, never the latter.

## Defect repaired

Commit `d51b9b47` changed `test_no_cross_branch_write()` to resolve the
CURRENT branch tips of `execution-runtime-foundation` and `tb-forward-engine`
and require them to equal the R1.1-frozen authority SHAs (with a `git fetch`
fallback). Those branches are ACTIVE CONCURRENT WORKSTREAMS and are expected to
advance; a later legitimate movement must never fail a historical R1.1 seal.

## Correct semantics (frozen by immutable commit SHA)

- **A. Object exists** — `git cat-file -e <sha>{{commit}}` for each frozen SHA.
- **B. Commit identity** — frozen commit subject matches the expected checkpoint.
- **C. Manifest agreement** — `CR_EXEC_R1_1_SOURCE_SHA_MANIFEST.json` and
  `CR_EXEC_R1_1_DECISION.json` carry identical frozen SHAs.
- **D. No cross-branch write by R1.1** — R1.1 commits (2bbe52ea,
  d51b9b47) are descendants of `capital-routing` and are NOT
  ancestors of the frozen foreign commits; R1.1-specific files are absent from
  the frozen foreign trees. Proved by ancestry + changed-file truth, NOT by
  present branch tips.
- **E. Current HEAD diagnostic** — current branch tips are recorded as
  informational diagnostics only; their movement is NOT a test failure.

## Hard rules

- NO git fetch anywhere in the runner or the tests.
- NO network dependence; deterministic offline suite.
- Frozen SHAs (9e11db92, d1200598) are NEVER
  replaced because the branches later advance — they remain historical
  provenance.
- Science untouched: 890 events / A 432 / B 458 / 826 accepted / 64 rejected /
  risk unit 24.49489742783178 bps / corrected translation formula / parity locks.

## DO NOT

Change science, translation math, frozen authority SHAs, A/B, H1, f_total, pos,
1R, cost science, economic-target schema; build D0; connect a broker; modify
execution-runtime-foundation or tb-forward-engine.

# BLOC_05 — SENSOR-B5-P3-CONSOLIDATED-CANDIDATE-R1 — EVIDENCE

**Branch:** `agent/crypto-sensor-fabric-p3-consolidated-r1`
**Merge commit:** `da414c0e8` (`--no-ff`)
**Parents:** `9d289500` (P3 R6) + `3426acfd` (Canonical R3)
**Merge base:** `ea1fdeb77`
**Status:** isolated research candidate. Not production-ready, not security-ratified, not canonically qualified.

| Reference | SHA |
|---|---|
| Production | `f199a7e3f` |
| Integration R1 | `3e53a6589` |
| P3 R6 | `9d289500` |
| Canonical R3 | `3426acfd` |
| Consolidation plan | `0affd395` |
| Excluded audit | `5406c553` (canonical R1), `28bb8b61` (P2eR1) |

---

## 1. Integration

`git merge --no-ff 3426acfd` produced `da414c0e8` with two parents. No rebase, no
squash, no force, no history rewrite. Both histories are preserved and the
established P2 ancestry (P2dR2 @ `482fc4148`, P2eR1 @ `ac67ba562` through
`e9f5391db`) is untouched.

The planning report predicted an empty changed-path intersection; that was
re-verified independently before merging:

```
overlap at ea1fdeb77 between 9d289500 and 3426acfd = [] (0 paths)
```

The merge completed with no conflict and no manual resolution. Neither
`5406c553` nor `28bb8b61` was imported.

## 2. Changed-path matrix (`9d289500` → candidate)

18 paths, exactly Canonical R3's delta and nothing else:

| Path | Change |
|---|---|
| `…/evidence/bloc_04/BLOC_04_I11R2_GOVERNANCE_BINDING_AUDIT.json` | M (count line) |
| `…/evidence/bloc_05/P3_CANONICAL_RUNNER_R{1,2,3}_EVIDENCE.md` | A |
| `…/evidence/bloc_05/canonical_runs/canonical-p3-r1/*` (9 artifacts) | A |
| `…/scripts/canonical_runner.py` | A |
| `…/scripts/canonical_pytest_plugin.py` | A |
| `…/scripts/test_canonical_runner.py` | A |
| `…/scripts/test_canonical_runner_r2_attacks.py` | A |
| `…/scripts/test_canonical_runner_r3_attacks.py` | A |

`quant-lab/src` changed versus R6: **0 paths**.

## 3. Source and test integrity

| Check | Result |
|---|---|
| R6 security invariants present | **14** (`test_r6_01`…`test_r6_14`) |
| Canonical runner/plugin preserved | present, unmodified from R3 |
| R1/R2/R3 runner suites present | all three |
| Frozen plans touched | **0 paths** |
| Approval manifest | `artifacts == {}` |
| `INTEGRATION_REQUIRED` | still in force (`sensors/verification.py`) |
| Audit branches merged | **0** |

## 4. Governance inventory

| Tree | Tracked `.py` | Pin |
|---|---|---|
| R6 | 1,097 | 1,097 |
| Canonical R3 | 1,102 | 1,102 |
| **Merged candidate** | **1,102** | **1,102** |

Measured on the merged tree, not assumed from the planning prediction (which
named the same number). The authorized I11R2 producer was run
(`UPDATE_I11R2_EVIDENCE=1`) and produced **no artifact diff** — the pin was
already correct, and the equality is now proven rather than inherited. No
allowlist was widened and no governance artifact was edited by hand.

## 5. Focused regression (committed merged tree)

| Suite | Result |
|---|---|
| Normalization: P3 conformance + P2a–P2e + I05/I09/I10 scope audits | **1324 passed** |
| Governed storage set (I05/I06, I09, I10, I11R2) | **265 passed** |
| Canonical runner R1 self-tests | **24 passed** |
| Canonical R2 negative suite | **16 passed** |
| Canonical R3 negative suite | **9 passed** |
| I11R2 evidence + binding (inside the governed set and run separately) | **14 passed** |

**Superseded expectations, reported separately and not counted as passing:**
the R1 independent audit suite (`5406c553`, run transiently against this tree,
never committed here) reports **27 passed, 3 failed**. The three failures are
`test_forged_pass_count_is_still_complete`,
`test_forged_digest_is_not_reverified` and
`test_shrunken_universe_is_invisible_to_verify` — they assert the unsafe
behaviour that R2 and R3 deliberately refuse. They are preserved unmodified on
their own branch and are **not** evidence of a current defect.

## 6. Canonical collection (measured, not inherited)

```
count            4733
digest           1036049742127c8f9919ae2d831627381318b15d83358ab6b45920c88a52e837
duplicates       0
malformed_count  0
collection_errors []
groups           13
partition_sizes  [1184, 1183, 1183, 1183]
```

The count matches the planning prediction of 4,733. The digest also coincides
with R6's, which is the *expected* result — Canonical R3 adds no node inside
`testpaths = ["quant-lab/tests", "qcae/tests"]` — but it is a fresh measurement
on this commit, not a carried-over value. No scope change, no addition, no loss.

**A full canonical execution was NOT run.** That is a later gate and currently
belongs to Agent 2 (memory-intensive run). This document therefore makes **no
`COMPLETE` claim** for the candidate.

## 7. Ledger

**No ledger entry was added.** A scan of all published lineages found §204–§209
already occupied:

```
agent/crypto-sensor-fabric-integration-r1-audit   1
agent/crypto-sensor-fabric-integration-r2-audit   2
agent/crypto-sensor-fabric-p3-canonical-r1-audit  1
agent/crypto-sensor-fabric-p3-r6-reattack         1
```

The mission's warning not to assume §204–§207 are free was correct. Rather than
claim a number that is already in use elsewhere, this checkpoint records itself
in this evidence document only, and leaves ledger numbering to a future
authorized reconciliation. §200–§203 remain exactly as published; nothing was
renumbered, duplicated or rewritten.

## 8. Operational incident (disclosed)

The host disk reached **100% full (0 bytes free)** during this checkpoint. Two
consequences are recorded rather than hidden:

1. An initial governed-storage run aborted with mass `F`/`E` results. That run was
   **stopped and discarded** — it was disk exhaustion, not a test verdict, and it
   is not reported anywhere as a result.
2. The interrupted run left seven tracked evidence artifacts modified under
   `evidence/bloc_04/` (its own containment restoration only runs at completion).
   They were restored with `git checkout --` and the tree was verified clean.

Space was recovered by deleting caches and by removing four of this session's own
already-pushed worktrees (`p3-r6`, `p3-canonical-r2`, `p3-canonical-r3`,
`p3-consolidation-prep` attempt). Their **branches and remote refs are intact**;
no other agent's worktree, branch or commit was touched. The governed storage set
then ran to completion with stable free space.

## 9. Remaining no-go conditions

1. **R6 security: PENDING.** Six grants are closed and self-verified; Agent 2's
   independent reattack is not published. Nothing here is security acceptance.
2. **Canonical execution: NOT YET VERIFIED.** Collection only; no verdict exists
   for this tree.
3. No anchored canonical bundle has been produced for this candidate.
4. Production `f199a7e3f` untouched; no production merge requested or attempted.
5. No provider approval, no custody authorization, no consuming application.
6. No I11/I12/I17 or Bloc 6 advancement, no program-gate promotion.
7. No self-ratification: this document records what was run, not a judgement of
   readiness beyond "ready for independent validation".

## 10. Disposition

`CONSOLIDATED_CANDIDATE_READY_FOR_INDEPENDENT_VALIDATION`

The combination exists, is clean, preserves both histories, and passes focused
and governed regression on its own committed tree. It is ready to be validated
independently — and is not validated here.

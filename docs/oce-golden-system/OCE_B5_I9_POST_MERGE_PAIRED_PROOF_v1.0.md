# OCE Golden System — B5-I9 Post-Merge Paired-Regression Proof Closure — v1.0

**Document ID:** OCE-B5-I9-PAIRED-PROOF-001
**Version:** 1.0
**Status:** `PAIRED_REGRESSION_PROOF_RESTORED`
**Stage:** `AUTHORIZED_STAGE=B5-I9-POST-MERGE-PROOF-CLOSURE`
**Merge under correction:** `139cb7fd2da6648fb513d2caf9c5b80b9a8969b5` (PR #25)
**Base endpoint:** `e81bef4335de5e222fb6647c602080a129dea543` (tree `5fe7d38c…`)
**Head endpoint:** `9db35aac5c1d9cfbdc5bd902b74c2bb09bfd9d3c` (tree `2d0285f3…`)
**Cost:** `$0` · **Cloud/provider mutations:** 0 · **`capital.authority = none`** · Freebuff untouched

---

## 1. The historical defect, recorded without softening

The B5-I9 ratification claimed `BOOK_5 GOVERNANCE COMPLETE = true` and PR #25 merged while the
mandatory isolated base-versus-head paired comparison had not been executed. The ratification
record disclosed the gap — *no separate base-versus-head paired artifact was produced; the full
population ran against the pull-request merge ref; the branch adds no production code* — and the
merge proceeded anyway. Ordinary merge-ref CI is not the governance-mandated comparison, so the
disclosure did not satisfy the gate and the closure claim was premature at merge time.

Classification: **B5-I9 technical implementation evidence remains valid** (the paired comparison
confirms it); **B5-I9 ratification procedure was incomplete at merge**; **the Book 5 governance
closure claim is superseded here**. No exception is accepted and no history is rewritten: the
ratification commit `9db35aac…`, the merge `139cb7fd…` and every earlier section stay exactly as
committed. This record and ledger §25 supersede only the closure claim.

## 2. Frozen comparison contract

`OCE_B5_I9_POST_MERGE_PAIRED_COMPARISON_CONTRACT_v1.0.json` pins the two historical endpoints,
the runner (ubuntu-24.04, Python 3.12), the hash-locked dependency set
(`infrastructure/control-plane/requirements-ci.lock.txt`), the population rule
(`infrastructure/control-plane/tests/test_b5_i[2-9]*.py`), the measured common floor (**229**),
the head-only expectation (**41**), node identity (JUnit `classname::name`), the base-only,
duplicate, skip, status-delta, manifest, mutation, determinism and cleanup rules, and the
fail-closed conditions. Neither endpoint is the corrective branch, and neither is mutated.

The floor is measured, not chosen: collecting the fifteen Book 5 files that exist at
`e81bef43` yields exactly 229 nodes, and all 229 execute and pass at base.

## 3. Execution

`b5-i9-post-merge-paired-comparison.yml` clones each endpoint into its own fresh directory
(`git clone --no-hardlinks`), checks out the pinned SHA detached, verifies SHA, tree and a clean
worktree, and removes the clone afterwards. Both endpoints run with one pinned toolchain
installed once, so the dependency freeze digest is identical by construction
(`116da2d79d64…` at both endpoints). No cache action, no shared virtual environment, no shared
result path, `GIT_LFS_SKIP_SMUDGE=1` (no surface in this population consumes LFS objects).

| Endpoint | Git identity | Files | Collected | Executed | Passed | Failed | Errors | Skipped |
|---|---|---|---|---|---|---|---|---|
| Base `e81bef43…` | tree `5fe7d38c…` | 15 | 229 | 229 | 229 | 0 | 0 | 0 |
| Head `9db35aac…` | tree `2d0285f3…` | 20 | 270 | 270 | 270 | 0 | 0 | 0 |

## 4. Common, base-only, head-only

- **Common nodes: 229** — identical to the frozen floor, so the floor is met exactly, not statistically.
- **Base-only: 0** — no pre-existing governed Book 5 node disappeared.
- **Head-only: 41** — exactly the frozen B5-I9 population, all under the `test_b5_i9_` prefix, all PASS.
- **Duplicates: 0** at either endpoint; collection equals execution at both.
- **Status transitions: 0** — every common node is PASS at base and PASS at head.

The head-only population is *not* used as the proof. It is accepted only alongside a 229-node
common population with zero regressions.

## 5. Head-only proof obligations

| Proof | Result |
|---|---|
| Validator | `PASS`, 172 mandatory checks, 98 candidate inspections, 0 failures |
| Failure classes | 25 bound; 41/41 B5-I9 nodes executed |
| Mutations | 10 applied, 10 discriminated, byte-exact restore, pristine rerun green |
| Determinism | two isolated emissions, 11 files each, byte-identical |
| Manifest | independent re-hash by the comparator: 10 rows, 11 files, no mismatch |
| G16 | `OPEN (B5I8-DF05)` |
| Book 6 | not authorized, not started; no execution |

## 6. Cleanup

Both clones and both emission directories were removed; `residual_paths: []`,
`cleanup_exit_code: 0`, `cleanup_ok: true`. The comparator reads this record before issuing a
verdict, so a cleanup failure would fail the proof rather than pass silently.

## 7. Exact-head CI identity

| Field | Value |
|---|---|
| Corrective head | `ed8546ffbc493b8cb1ea24f98dd73fa6b9dcaaa5` (X1) |
| Workflow run | `42416078595` (pull_request) |
| Check suite | `114911642555` |
| Job | `128534361447`, success, 13 steps |
| Artifact | `b5-i9-post-merge-paired-42416078595` (`13592045745`), 31 818 B, expires 2027-02-05T21:29:15Z |
| Verdict | `PASS` with `reasons: []` |
| B5-I9 Factory Gate | `42416078602` success |
| B5-I8 Audit | `42416078596` success |
| B1-I1R | `42416078617` success |

The evidence head's own run identities are appended to PR #26 after they exist; nothing is
predicted here.

## 8. Corrected governance disposition

`PAIRED_REGRESSION_PROOF = RESTORED` · `BOOK_5 GOVERNANCE COMPLETE = true` (this time supported
by the comparison the gate required) · `B5-I9 technical implementation = ACCEPTED` ·
`B5-I9 ratification = ACCEPTED WITH HISTORICAL PROCEDURAL DEFECT PRESERVED` · `G16 = OPEN` ·
`BOOK_6 = UNAUTHORIZED` · `REUSABLE_EXTRACTION = NOT STARTED` ·
`POST_BOOK_6_EVALUATION = UNSTARTED` · cost `$0` · `capital.authority = none`.

## 9. Audit

`SAME-AGENT — NOT ORGANIZATIONALLY INDEPENDENT`

SPEC **8.2** · DESIGN **8.2** · CORRECTNESS **8.0** · QUALITY **8.0** →
(8.2 + 8.2 + 8.0 + 8.0) / 4 = **8.1 / 10**, down from 8.2.

The deduction is deliberate: a mandatory gate was declared satisfied without the proof, the
corrective rung then exposed two real defects of its own (a frozen selection law that counted
proof-only workflows, and a comparator that required cleanup evidence written after the
verdict), and the repair churn is visible in history. Green CI did not raise the score.

## 10. Non-goals preserved

No production code, test, workflow or frozen B5-I0–I8 evidence changed. No extraction, package,
deployment, provider, credential, telemetry or recurring cost. Book 6 has not begun and requires
a fresh `AUTHORIZED_STAGE=B6-I0`.

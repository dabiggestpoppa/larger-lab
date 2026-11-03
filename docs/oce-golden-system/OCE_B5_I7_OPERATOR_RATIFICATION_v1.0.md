# OCE B5-I7 — Operator Ratification Record v1.0

**Disposition:** `OPERATOR_ACCEPTED`  
**Stage:** `B5-I7-RATIFICATION`  
**Base (pre-stage main):** `9dc0b7d29ab869e256653a6b6ec68c987d0a4090`  
**Ratified artifact set:** the ten-rung implementation ladder plus this record  
**MERGE_AUTHORIZED:** `true` — for pull request #20 only

## 1. What is ratified, and what is not

Ratified: one governed, read-only queue-depth observability panel over the already
declared `health.read` / `workers.list` / `jobs.schedules` reads, its twelve
governed-change/panel proofs, its fifteen evidence-law proofs, its fourteen-mutation
battery, and one additive CI selection step.

Not ratified and not authorized by this record: B5-I8, B5-I9, the deferred I-7 web
view (unimplemented, and asserted absent by `B5I7-R02`), external hosting, cloud
deployment, and any capital, broker or execution authority.
`capital.authority = none`. Cost of this stage: `$0`.

This record SUPERSEDES the implementation-stage audit score; it does not erase it.
The governed change record keeps `MERGE_AUTHORIZED=false` exactly as written at the
implementation stage (`B5I7-EL14` enforces that text; it was not edited).

## 2. Independent re-verification performed in this stage

Every fact below was recomputed from Git objects, GitHub API responses, downloaded
raw artifacts, and fresh local execution — not read from the implementation report.

| Fact | Method | Result |
|---|---|---|
| ladder linear, no merges | `rev-list --merges` = 0; one parent each | PASS |
| ten rungs reachable | `rev-parse` per reported rung | PASS |
| file boundary | `git diff --numstat base..HEAD` | 12 files, +3080/-3 |
| control plane untouched | diff over `control-plane/{src,contracts}` | 0 files |
| pre-existing tests untouched | diff over `**/tests/*` minus `test_b5_i7_*` | 0 files |
| ledger append-only | base blob byte-prefix of head blob | PASS (187887 -> 190851 B) |
| 27 frozen nodes | live collect vs registry `planned_test_nodes` | 27 = 27, unique 27 |
| split 12/15 | class scan of collected ids | 12 governed, 15 evidence-law |
| no skips/xfail | marker grep over both files | none |
| web view absent | path probe | absent |
| pure-Python sha256 | 57-vector differential vs `hashlib` incl. 55/56/63/64/65 B, UTF-8, NIST | 0 mismatches |
| focused nodes execute | fresh local junit at head | 27 tests, 0 fail/err/skip, 27 unique |
| mutation battery | full rerun at head, fresh output path | PASS, 14/14 RED, 14 distinct hashes, restoration equal |
| pristine restoration | post-battery `git status --porcelain` | empty |
| base population | worktree at base, same 9 files | 186 collected, 186 passed |
| head population | same selection at head | 186 passed, 0 fail/err/skip |
| common population | junit id intersection | 186 common, 0 base-only, 0 head-only |
| CI artifact binding | `/runs/{id}/artifacts` per run | one artifact each, run-bound |
| manifest rows | recompute sha256 + size over LF-normalized bytes | all rows match (`EL09`) |
| cleanup | `EL11` residual-state check | PASS |

## 3. Requirement arithmetic (reconciled, not assumed)

The implementation report summarized `44 = 26 R + 15 EL + 3 DF`; the frozen registry
publishes kind, binding and state distributions. Both are views of one inventory and
reconcile exactly:

```
by_kind            identity 1, change_cycle 6, boundary 3, gate 3, panel 9,
                   measurement 3, learning 1, evidence_law 15, deferred 3   = 44
by_binding_type    test 27, attestation 10, static 2, runner 2, deferred 3   = 44
by_mapping_status  PLANNED 35, MAPPED 6, DEFERRED_WITH_OWNER 3              = 44
non-EL, non-deferred kinds = 1+6+3+3+9+3+1 = 26  -> the report's 26 R
evidence_law = 15 -> 15 EL;  deferred = 3 -> 3 DF                            = 44
```

Unique requirement ids: 44 of 44. Deferred owners: B5-I8 (plan §7), B5-I9 (plan §7,
operator-only), Operator (charter §12 row I-7). No deferred requirement was absorbed.

## 4. Defects raised in this stage

| ID | Defect | Evidence | Disposition |
|---|---|---|---|
| D8 | `evidence_identities.implementation_head_before_evidence` named rung R3b (`5a4c5a5a77`) while the parent of the evidence commit is rung R4 (`2e117f86`); the entry was internally consistent, so `EL06` could not catch the mislabel | `git cat-file -p 3bb49118` shows parent `2e117f86` | Repaired in this commit with four unambiguous identities; the ambiguous label is retained and re-scoped in prose |
| D9 | the mutation artifact records `pristine_sha256` over raw working-tree bytes, so the same source hashes differently on a Linux checkout (CRLF vs LF) | raw `c05f5325...` vs normalized `04772825...` for one file | Recorded as a portability limitation, not rewritten: the battery's restoration comparison is byte-exact within a checkout |

Implementation-stage defects D1-D7 remain visible in the governed change record and
are neither deleted nor softened (`B5I7-EL12` enforces D1-D5 presence).

## 5. Evidence-law disposition

All fifteen laws execute a checker twice: green on real evidence, red on a falsified
copy. This stage re-read every checker and every falsifier. `EL02`'s falsifier was
re-aimed at the pre-existence shape once CI ids legitimately existed; that is a
correct re-aim of a law whose subject is 'recorded before existence', not a
weakening, and it is recorded here rather than presented as an original pass.

Stated limits of the law set: `EL09` recomputes from the working tree (equal to the
committed blob in a clean CI checkout, not read from the git object store), and
`EL10`/`EL11` consume the battery's own output artifact, inheriting its trust
boundary. The battery was rerun independently in this stage to compensate.

## 6. Fresh audit (supersedes 8.25/10)

`SAME-AGENT — NOT ORGANIZATIONALLY INDEPENDENT`

| Axis | Score | Deductions |
|---|---|---|
| SPEC | 9.0 | -0.5 mislabeled identity (D8); -0.5 contract §10 prose vs stricter literal-only transport |
| DESIGN | 8.5 | -1.0 import closure forced a pure-Python digest where stdlib exists; -0.5 extra mutation-results artifact beyond contract §5 |
| CORRECTNESS | 8.0 | -2.0 for implementation defects D1-D5, all repaired before evidence |
| QUALITY | 8.0 | -0.5 red intermediate CI run; -0.5 artifact gap (D6); -0.5 stale manifest (D7); -0.5 evidence portability (D9) |

Arithmetic: `(9.0 + 8.5 + 8.0 + 8.0) / 4 = 33.5 / 4 = 8.375` -> **8.38/10**.
Repairs passing is technical closure, not process quality; the deductions are
retained precisely because the repairs were needed.

## 7. Limitations carried forward

- No CI run exists for rung R4 alone: R1-R4 and the evidence rung were pushed together.
- The local shared authoritative runner is not green on this host (missing tooling);
  CI is the authoritative green and is cited by run id, not by badge.
- `127.0.0.1` and `[::1]` literals are accepted; `localhost` is refused (stricter than prose).
- The deferred I-7 web view has no implementation and no test file.
- This audit is same-agent; no organizational independence is claimed.

## 8. Authorization

Authorizes: merging pull request #20 by a normal two-parent merge.
Does not authorize: B5-I8, B5-I9, the deferred web view, external hosting, cloud
deployment, capital/broker/execution authority, branch deletion, or history rewrite.

`B5-I7 = OPERATOR_ACCEPTED` · `B5-I8 = LOCKED` · `B5-I9 = LOCKED` · `MERGE_AUTHORIZED=true (PR #20 only)`

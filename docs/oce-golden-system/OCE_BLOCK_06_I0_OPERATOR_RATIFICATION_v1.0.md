# OCE Book 6 B6-I0 - operator ratification

Status: `B6-I0 = OPERATOR_ACCEPTED`. The stage is complete for B6-I0 only. This record ratifies the
frozen extraction decisions, the API principles and the compatibility/conformance baseline. It
authorizes no extraction, no package, no publication and no later increment.

## 1. Identity

| Item | Value |
|---|---|
| Base (pre-stage main) | `5e76dc12207bf1674ff7ccd94aed0f36b12dd3e6` |
| Base tree | `34fef9633a2fe496ed2bef352858b3994b91b4e2` |
| P0 ratification | `e2aa8ac71dc9f0de4287fbcaa8a17ff127d5356f` |
| Implementation head | `6aa168f1ecc9f831a39bc150e42157d61601672e` |
| Implementation tree | `5a7fb3cd7b25c9b7f95415ec3170baee6d3bfc10` |
| Evidence head | `7922a3d41a9850186538511f4ce226c064f4a6ec` |
| Exact paired comparison | run `42615539729` |

## 2. Scope as derived

The frozen stage declares `non_goals: ["extraction of code"]`, a source `mutation_floor: 0` and one
governed section `C1.S5`. B6-I0 therefore produced decision artifacts plus conformance tooling: 19
requirements (`SEC-05`, `NP-01`-`NP-08`, `CLS-01`-`CLS-03`, `G16-01`-`G16-04`, `HOLD-01`,
`HOLD-02`, `PKG-01`), 6 failure classes (`F01`, `F02`, `F03`, `F04`, `F17`, `F20`), 7 threats
(`T04`, `T05`, `T07`, `T08`, `T09`, `T14`, `T20`), 30 API rows, 25 compatibility rows, 15
provenance obligations and 72 nodes. Zero source files were copied, zero stable exports exist, zero
packages were built and no dependency was added.

## 3. Mutation-floor governance

The P0 contract froze the source floor at 0. Commit `03ab1936` (`B6-I0-P0`) recorded the stage floor
as 12 beside the preserved source value, before any implementation result existed. Raising a floor
only strengthens a stage and changes no ratified meaning. No later commit lowered it, and no
mutation was substituted after observing a result.

## 4. Proofs

| Proof | Result |
|---|---|
| Requirement/test registry | 19 requirements, 72 unique nodes, one binding each |
| Linux node execution | 72 collected, 72 executed, 72 passed, 0 fail/error/skip |
| POSIX symlink controls | executed and passed in Linux CI |
| Mutation battery | 12/12 discriminated, 12/12 restored, pristine green |
| Deterministic regeneration | two isolated emissions byte identical |
| Manifest | verified independently by a second code path |
| Frozen Book 5 gate | 41/41 |
| P0 content gate | green over the unchanged packet |
| Cleanup | tracked tree clean, no scratch residue |

## 5. Exact paired comparison

The handoff had cited a green paired run pinned to Book 5 endpoints; that was not the B6-I0
comparison. The stage now pins its own endpoints and executes both under one toolchain in separate
clones: base `5e76dc12` and head `6aa168f1`. Base total 270, head common total
270, common 270 against a source-derived floor of
41, base-only 0, head-only 72 against
an expected 72. Common status: 270 pass, 0 skip,
0 fail, 0 error. Verdict `PASS`; both clones were removed before
the verdict.

## 6. CI identity at the implementation tree

| Workflow | Run | Result |
|---|---|---|
| B1-I1R Validation | 42615539788 | success |
| B5-I8 Audit Validation | 42615539744 | success |
| B5-I9 Factory Gate Validation | 42615539988 | success |
| B5-I9 Post-Merge Paired Comparison | 42615539699 | success |
| B6-I0 Paired Comparison | 42615539729 | success |
| B6-I0 Validation | 42615539707 | success |

## 7. Defect and repair chronology

| Rung | Defect | Repair |
|---|---|---|
| X1 | test support module missing from the declared boundary | declared the narrow support path |
| X2 | frozen Book 5 suite duplicated as a second selection surface | moved the gate into a runner script |
| X3 | the required B6-I0 paired comparison did not exist | froze endpoints and added the comparison |
| X4 | the paired contract lacked its frozen status field | added the field, fail-closed behaviour kept |
| X5 | endpoint clones lacked the pre-stage main ref | restored the true base ref at both endpoints |

## 8. Acceptance matrix

| Gate | Requirement | Result | Evidence |
|---|---|---|---|
| G01 | reality lock held at the frozen endpoints | PASS | base and P0 SHAs, PR parents, branch head |
| G02 | ladder reconstructed from git objects | PASS | ten linear commits, zero merges |
| G03 | scope derived from merged P0 sources | PASS | 19 requirements, one section C1.S5 |
| G04 | mutation floor governance | PASS | raised 0 to 12 in the contract commit before results |
| G05 | changed-file boundary exact | PASS | no production surface |
| G06 | 27 candidates reconcile | PASS | 12 admitted, 15 refused |
| G07 | admitted/refused/extracted arithmetic | PASS | 12 admitted, 15 refused, 0 extracted |
| G08 | API firewall | PASS | 30 rows, public stable 0 |
| G09 | public stable remains zero | PASS | observed exports 0 |
| G10 | compatibility rows truthful | PASS | 25 rows, all UNPROVEN |
| G11 | unknown versions fail closed | PASS | compat/unknown_refused |
| G12 | requirement registry closes | PASS | 19 requirements, 72 nodes, one binding each |
| G13 | 72 nodes pass in Linux CI | PASS | run 42615539707 totals 72/0/0/0 |
| G14 | symlink controls execute and pass | PASS | three POSIX nodes executed in CI |
| G15 | 12 mutations discriminate | PASS | 12/12 discriminated and restored |
| G16 | deterministic regeneration | PASS | double generation byte identical |
| G17 | manifest verifies independently | PASS | second code path re-hashes every artifact |
| G18 | cleanup | PASS | tracked clean, no scratch residue |
| G19 | frozen Book 5 suite remains 41/41 | PASS | frozen gate run 42615539988 |
| G20 | P0 validator remains green | PASS | content-layer gate over unchanged packet |
| G21 | exact B6-I0 paired comparison | PASS | run 42615539729 verdict PASS |
| G22 | no common regression | PASS | common 270, zero regressions |
| G23 | evidence-head artifacts parsed | PASS | run 42531536214 totals and symlink output |
| G24 | ratification-head artifacts parsed | PASS | recorded in the evidence rung |
| G25 | G16 remains OPEN | PASS | OPEN under B5I8-DF05 |
| G26 | B6-I1 through B6-I9 locked | PASS | no later-stage implementation |
| G27 | no package or publication | PASS | zero packages, zero registries |
| G28 | evaluation system unauthorized | PASS | RESERVED_NOT_AUTHORIZED |
| G29 | no authority introduced | PASS | NP-01 through NP-08 proofs green |
| G30 | no production surface touched | PASS | no oce/, packages/, dist/, build/ path |
| G31 | no dependency addition | PASS | lockfiles unchanged |
| G32 | paired endpoints pinned | PASS | base 5e76dc12, head 6aa168f1 |
| G33 | comparison endpoint cleanup | PASS | both clones removed before the verdict |
| G34 | PR state draft, open, mergeable | PASS | PR #29 checks CLEAN |
| G35 | no unresolved blocker | PASS | no open defect |

## 9. Score

SPEC 9/10, DESIGN 9/10, CORRECTNESS 9/10, QUALITY 9/10; arithmetic (9+9+9+9)/4 = 9.0/10.
`SAME-AGENT - NOT ORGANIZATIONALLY INDEPENDENT`. Deductions for same-agent review, no proven
consumer of the frozen surfaces, `G16` open under `B5I8-DF05`, five repair rungs of which three
belong to this audit, and the two POSIX controls that cannot execute on the Windows workstation.

## 10. Locks

`B6-I1 = LOCKED - REQUIRES FRESH AUTHORIZED_STAGE`; `B6-I2`-`B6-I9 = LOCKED`;
`BOOK_6 COMPLETE = false`; `EXTRACTION EXECUTION = NOT_BEGUN`; `PACKAGE PUBLICATION = NOT_BEGUN`;
`POST_BOOK_6_EVALUATION_SYSTEM = RESERVED_NOT_AUTHORIZED`; `G16 = OPEN`; cost `$0`;
`capital.authority = none`.

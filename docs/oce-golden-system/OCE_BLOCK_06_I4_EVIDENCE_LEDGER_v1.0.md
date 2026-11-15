# B6-I4 evidence ledger (operator truth and authority)

Stage: `B6-I4` — C3.S1 identity surface, C3.S2 workflow surface, with C2 incident and cost replay.
Status: **EVIDENCE SEALED — AWAITING OPERATOR RATIFICATION.** Not operator-accepted, not merged.

## Identity

| Item | Value |
|---|---|
| Base (origin/main) | `f0bd9bdd3f776b33d3b70b5b441966e2c80e1f14` / tree `5e15ea448b929269193dc904ec0677687df077e4` |
| Accepted technical head | `60dbb57c07826ffc9c3ee9dab3ccfb3e43c9dcbd` / tree `2608a53ce27b9fb97270d8d4d7adac540d3091f2` |
| Product repair endpoint (R5) | `1ad1a970206106702b2090c1fb082db08fbfc892` / tree `431bfbe3798eccac67f7291afd421e1d52d34be8` |
| Paired re-pin | X3 `ad575ad2c` pins base `f0bd9bdd` → product head `1ad1a970` |
| Supplement S1 | `2721aa78b` (R42–R48, five planned nodes, M16/M17, R1 insufficiency) |
| Supplement S2 | `51f0cb8f5` (non-vacuous mutation witness law) |
| Witness repair | X5 `22af7fa1b`, manifest X5b `ebbf2f2dc` |
| Runner hardening | X6 `5d99aa779`, manifest X6b `60dbb57c0` |
| Evidence seal | this ledger and its documentation-only commit; the commit SHA is recorded in PR #33, never predicted here |
| CI tested merge ref | `c230f55a0077…` / tree `2608a53ce27b…`, parents `f0bd9bdd…` + `60dbb57c0…` |

## Forward-only repair ladder (24 commits, base → accepted head, zero merges)

| Phase | Commit | Subject |
|---|---|---|
| Freeze | `07d24b1cd` | P0 scope, contract, registry and boundaries |
| Freeze | `b3d33733f` | P0b qualify surface symbols by submodule |
| Product | `97a3a9349` | R1 incident, cost, identity, workflow with 34-node closure |
| Proof | `ab44a92a8` | R2 assert frozen I3 workflow by its pinned base |
| Proof | `ba7dab45c` | W1 exact-head validation and paired workflows |
| Proof | `9ff8dfc33` | R3 replay the frozen B6-I3 head |
| Amend | `9515f3aa9` | A1 amend inventory for hardening cycle |
| Amend | `89f7e5133` | A2 rebind packet to 41 requirements |
| Product | `ddc99b059` | A3 trace owners, duplicates, versions, strict integers |
| Proof | `439955c41` | A4 strengthen I3 control and expand battery |
| Mechanical | `25f0c38b5` | A5 regenerate manifest |
| Proof | `e6d38e5cb` | A6 scope I3 endpoint control to replay block |
| Mechanical | `8f63150ef` | A7 regenerate manifest |
| Proof | `605a550d0` | X1 close amended hostile-proof surface |
| Proof | `847e24e2e` | X2 commit registration-omission mutation |
| Supplement | `2721aa78b` | S1 freeze malformed-run and paired-head closure |
| Product | `1ad1a9702` | R5 govern malformed workflow identity documents |
| Proof | `ad575ad2c` | X3 bind paired regression to repaired head |
| Workflow | `4c81913d9` | X4 execute and expect 46 nodes |
| Supplement | `51f0cb8f5` | S2 freeze non-vacuous mutation witness law |
| Tooling | `22af7fa1b` | X5 make M16/M17 behavioral discriminators |
| Mechanical | `ebbf2f2dc` | X5b regenerate manifest |
| Tooling | `5d99aa779` | X6 disk-safe controls worktree |
| Mechanical | `60dbb57c0` | X6b regenerate manifest |

## Requirements and node arithmetic

| Item | Value |
|---|---|
| Requirements | R01–R41 amended, plus R42–R48 from S1 |
| Declared nodes | 46 |
| Collected nodes | 46 |
| Unique nodes | 46 |
| Executed nodes | 46 passed |
| Modules | 6 |
| Failures / errors / skips / xfails | 0 / 0 / 0 / 0 |
| New nodes (S1) | missing `definition_id`, missing `version`, both missing, `None` `definition_id`, `None` `version` |

## Mutation arithmetic and S2 admissibility law

| Item | Value |
|---|---|
| Mutations defined | 17 |
| Applied | 17 |
| Discriminated | 17 |
| Restored byte-exactly | 17 |
| Floor | 6 (minimum, not an exact count) |
| Red-phase return code | exactly 1 for every mutation |
| Pristine suite after battery | 46/46 |
| Worktree after battery | clean |

S2 requires, for every pytest mutation: mutated source compiles; the named node is collected; the named node executes; its JUnit status is FAILED; pytest returns exactly 1; return codes 2/3/4/5 and collection/import/usage errors are rejected; “found no collectors” never counts; restoration is byte-exact; the pristine named node passes; the full 46-node suite passes; the worktree is clean.

### M16/M17 non-vacuity proof (exact-head artifact)

| Evidence | M16 | M17 |
|---|---|---|
| Mutation | missing-key governed refusal removed, valid syntax | `None`-value governed refusal removed, valid syntax |
| Named node | `test_advance_missing_definition_id_refused` | `test_advance_null_definition_id_refused` |
| Compiled | true | true |
| Collected | true | true |
| Executed | true | true |
| Status | FAILED | FAILED |
| Return code | 1 | 1 |
| Failure | `KeyError: 'definition_id'` | `assert 'REFUSED_WORKFLOW_MISMATCH' == 'REFUSED_INVALID_RECORD'` |
| Pristine named node | pass | pass |
| Restoration | byte-exact | byte-exact |

The previously preserved vacuous witnesses (IndentationError, pytest exit 4, “found no collectors”) are retained as history in S2 and in the earlier battery evidence; they are not presented as proof.

## Validation evidence (exact accepted head)

| Item | Value |
|---|---|
| Workflow | B6-I4 Validation, run `43441723087`, successful attempt **5** |
| Check-run / suite | `132582256478` / `117631845438` |
| Artifact | `14131048958`, `b6-i4-evidence-e204ffc358cf`, 14,217 B |
| Conformance validator | PASS 177/177 |
| Node inventory | 46 declared / 46 collected / 46 unique / 46 executed |
| Focused suite | 46 passed, 0 failures, 0 errors, 0 skips, 0 xfails |
| Mutation battery | 17/17 applied, discriminated and restored; pristine green |
| Stage-scope controls | **16/16** on the clean hosted runner |
| B6-I0 validator at later stage | PASS 136 |
| B6-I1 validator at later stage | PASS 168 |
| B6-I3 replay | 28/28 |
| Frozen Book 5 gate | 41/41 PASS |
| Adjacent Book 5 suites | 53/53 |
| Cleanup | true, no residue |

### All workflows on the accepted head

| Workflow | Run | Attempt | Steps | Result |
|---|---|---|---|---|
| B1-I1R Validation | `43441722459` | 3 | 23 | SUCCESS |
| B5-I9 Factory Gate Validation | `43441722652` | 3 | 17 | SUCCESS |
| B6-I0 Validation | `43441722657` | 3 | 23 | SUCCESS |
| B6-I0 Paired Comparison | `43441722661` | 3 | 13 | SUCCESS |
| B6-I3 Validation | `43441722714` | 3 | 23 | SUCCESS |
| B6-I1 Validation | `43441722724` | 3 | 19 | SUCCESS |
| B5-I8 Audit Validation | `43441722726` | 3 | 11 | SUCCESS |
| B6-I2 Paired Comparison | `43441722762` | 3 | 13 | SUCCESS |
| B6-I3 Paired Comparison | `43441722766` | 3 | 14 | SUCCESS |
| B5-I9 Post-Merge Paired Comparison | `43441723012` | 3 | 13 | SUCCESS |
| B6-I4 Validation | `43441723087` | 5 | 23 | SUCCESS |
| B6-I4 Paired Comparison | `43441723193` | 3 | 14 | SUCCESS |
| B6-I2 Validation | `43441723947` | 3 | 23 | SUCCESS |
| B6-I1 Paired Comparison | `43441722599` | 3 | 13 | SUCCESS |

## Paired comparison (base `f0bd9bdd` → product head `1ad1a970`)

| Item | Value |
|---|---|
| Workflow | B6-I4 Paired Comparison, run `43441723193`, successful attempt **3** |
| Check-run / suite | `132582870786` / `117631845729` |
| Artifact | `14131249066`, `b6-i4-paired`, 18,155 B |
| Endpoints | base `f0bd9bdd…` / tree `5e15ea44…`; product head `1ad1a970…` / tree `431bfbe3…` |
| Common population | 270 (floor 208) |
| Base-only | 0 |
| Head-only | 46 |
| Common outcomes | 270 pass, 0 fail, 0 skip, 0 error |
| Verdict | 19/19 PASS |
| Dependency lock | governed digest recorded |
| Cleanup | true |

The paired endpoint is unchanged because no file under `oce/` or `infrastructure/control-plane/tests/` changed after R5.

## Manifest

| Item | Value |
|---|---|
| Pre-seal entries | 11 artifacts + 15 code = 26 |
| Seal entries | 12 artifacts + 15 code = 27 (this ledger added) |
| Verification | every SHA-256 and byte size recomputed from disk |
| Stale or missing entries | none |
| Generator | `block_06_i4_generate.py --check` reports current |
| S2 included | yes |

## Audit reconciliation

- Audit label: **SECOND-AGENT TECHNICAL AUDIT — NOT ORGANIZATIONALLY INDEPENDENT**.
- Disposition: **FINAL_PARALLEL_DELTA_AUDIT_ACCEPTED_B6_I4**.
- A. Head/tree and forward-only history: verified; zero merges.
- B. Public GitHub-hosted CI recovered: verified; real steps on every workflow.
- C. Validation artifact reparsed: verified; 177/177 and 46 nodes.
- D. Paired artifact correctly R5-bound: verified; 270 common, 46 head-only.
- E. PR marker exists once in an append-only section: verified.
- F. Two frozen-oracle defects are audit-instrument limitations, not implementation defects: criterion-8 text-matcher false positive, and the top-level head-field subprocess return-code defect. The oracle was not silently repaired after results were observed.
- Local branch-probe collision (`oce-book-6-i9-probe` held by another agent’s worktree) was environmental; the clean hosted runner proves controls 16/16.

## Defects found and forward repairs

| Defect | Class | Repair |
|---|---|---|
| M16/M17 produced invalid Python and never executed their nodes | Evidence/tooling, blocking | S2 + X5: valid mutants and compile/collect/execute/JUnit/rc-1 law |
| Validation job still expected 41 nodes | CI 41 vs 46 mismatch | X4 |
| Paired comparator pinned to R1 | Paired identity | X3 |
| Malformed run documents raised bare `KeyError` | Product, R42/R43 | R5, governed `REFUSED_INVALID_RECORD` |
| Scratch worktrees exhausted the host disk | Verification environment | X6 sparse controls; battery sparse checkout |
| GitHub Actions refused all jobs on billing | Infrastructure/account | Repository made public; rerun on unchanged head |

## Historical failures preserved (not product or test failures)

- `43431011076` — B6-I4 Validation failed because the job expected 41 nodes while the green collection was 46; superseded by X4.
- Attempts 2–4 of the billing-blocked workflows executed **zero steps**, carried GitHub’s billing/spending-limit annotation and produced no artifacts. They are retained as infrastructure history and are not counted as validation.

## Audit score

| Dimension | Score | Deductions |
|---|---|---|
| SPEC | 9.0 | −0.6 same-host/account review, not organizationally independent; −0.4 F2/F18 governance deferral |
| DESIGN | 9.2 | −0.8 multiple forward repairs (S2, X5, X6 and mechanical regenerations) after results were observed |
| CORRECTNESS | 9.4 | −0.6 originally vacuous M16/M17 witnesses required repair; product behavior itself passed |
| QUALITY | 9.0 | −0.6 frozen-oracle instrument defects; −0.3 historical CI billing interruption; −0.1 disk-driven runner hardening churn |
| **TOTAL** | **9.15 / 10** | 36.6 ÷ 4 |

No failure mode is deducted twice. No remaining product defect is known; F2/F18 remains a governance deferral, not a silent acceptance.

## Holds

`B6-I5`–`B6-I9` LOCKED · `BOOK_6_COMPLETE=false` · `MERGE_AUTHORIZED=false` · `RATIFICATION_AUTHORIZED=false` · evidence ledger sealed, not operator-accepted · cost `$0` · capital authority `none` · repository remains public until the operator is explicitly told **SAFE TO MAKE REPOSITORY PRIVATE**.

## Operator ratification — append-only

The header status line above ("EVIDENCE SEALED — AWAITING OPERATOR RATIFICATION. Not operator-accepted, not merged.") is historical and is preserved unchanged. This section records the later operator decision; it supersedes that pending state for B6-I4 only. Merge remains unauthorized.

| Item | Recorded value |
|---|---|
| Operator decision | `OPERATOR_DECISION=RATIFY_B6_I4_EVIDENCE` |
| Stage | `B6-I4-RATIFICATION` |
| B6-I4 technical implementation | **ACCEPTED** |
| B6-I4 evidence package | **ACCEPTED** |
| B6-I4 ratification | **OPERATOR_RATIFIED — FROZEN** |
| Merge | **NOT AUTHORIZED** |
| `B6-I5`–`B6-I9` | LOCKED |
| `BOOK_6_COMPLETE` | `false` |
| Cost | `$0` |
| Capital authority | `none` |

The binding decision record is `OCE_BLOCK_06_I4_OPERATOR_RATIFICATION_v1.0.md`; the ratification commit SHA is recorded in PR #33 and is never predicted here.

### Accepted score

| Dimension | Accepted score |
|---|---|
| SPEC | 9.0 |
| DESIGN | 9.2 |
| CORRECTNESS | 9.4 |
| QUALITY | 9.0 |
| **TOTAL** | **9.15 / 10** (36.6 ÷ 4) |

The DESIGN and CORRECTNESS deductions concern separate dimensions of the same repair episode — process churn versus the original witness defect — and are accepted as a judgment call, not as mathematical certainty. The score is accepted as recorded; it was not re-scored and no failure mode is deducted twice.

### Audit provenance preserved

- Label: **SECOND-AGENT TECHNICAL AUDIT — NOT ORGANIZATIONALLY INDEPENDENT**.
- Disposition: **FINAL_EVIDENCE_HEAD_AUDIT_ACCEPTED_B6_I4**.
- Ratification does not claim organizational independence and does not convert the same-host review into an independent one.

### Validator clarification (appended correction)

| Head | Validator |
|---|---|
| Accepted technical head `60dbb57c0` | 177/177 |
| Evidence-seal head `021fc6111` | 181/181 |

The exact reason for the increase of four is: +2 manifest checks for the new ledger entry (`manifest/exists/…` and `manifest/hash/…`), and +2 text-law checks for the new ledger document (`text/no_claim/…` and `text/no_abs_path/…`). The validator source remained byte-identical at `1a7e7166f2dbbe47ce48d603629815ebc4f72bdbf44b174f22d747e2bc9e4978`; no unexplained test or product drift occurred.

The same two text-law checks apply to the ratification document at the ratification head. It adds no manifest row because the manifest generator's artifact glob is JSON-only and this ledger is its single documentation exception; the generator was not changed for ratification.

### PR marker truth (appended correction)

- The terminal `READY_FOR_OPERATOR_REVIEW_B6_I4` marker is unique: it occurs once at the end of the PR body.
- The literal string occurs twice in the body because unchanged historical prose previously named the prospective marker while describing where the lane would stop.
- The historical PR body was preserved append-only.
- This is not a duplicated terminal disposition, and the old prose was not rewritten merely to obtain a literal count of one.

### Holds restated at ratification

`B6-I5`–`B6-I9` remain LOCKED · `BOOK_6_COMPLETE=false` · `MERGE_AUTHORIZED=false` · no B6-I5 work is authorized · cost `$0` · capital authority `none` · repository remains public until the operator is explicitly told **SAFE TO MAKE REPOSITORY PRIVATE**.

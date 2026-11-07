# OCE Golden System
## B5-I8 — P0 Operator Ratification — v1.0

**Document ID:** `OCE-B5-I8-RATIFICATION-001`
**Version:** 1.0
**Stage:** `AUTHORIZED_STAGE=B5-I8-P0-RATIFICATION`
**Decision:** `P0 = OPERATOR_ACCEPTED — PLANNING FROZEN`
**Ratification commit subject:** `B5-I8-P0-RATIFY: accept independent audit planning packet`
**Corrected main at acceptance:** `74fee0f086f9215bf6b93a1b3adbf1d69406da39`
**Accounting:** cost `$0` · `capital.authority = none` · Freebuff untouched · `B5-I9 = LOCKED` · Book 6 `UNAUTHORIZED`

---

## 1. Decision

The B5-I8 P0 planning packet is **accepted as frozen planning** and is ratified on the corrected
Book 5 base. Ratification accepts the *plan*; it authorizes **no** implementation.

| Field | Value |
|---|---|
| `P0` | `OPERATOR_ACCEPTED — PLANNING FROZEN` |
| `B5-I8 IMPLEMENTATION` | `NOT STARTED` |
| `B5-I8_IMPLEMENTATION_AUTHORIZED` | `FALSE` (a separate authorization is required for rung R1) |
| `MERGE_AUTHORIZED` | `true` — **for the P0 ratification PR only**; every later rung is `false` until separately authorized |
| `G16` | remains **open**; only a future R3 execution can close it |
| `B5-I9` | `LOCKED` |
| Book 6 | `UNAUTHORIZED` |
| Post-Book-6 evaluation system | `UNSTARTED` |
| Web-view implementation | `ABSENT` (operator-owned, unscheduled) |
| Cost | `$0` · `capital.authority = none` · no broker/execution authority · Freebuff untouched |

## 2. Exact commits

| Role | Commit |
|---|---|
| P0 authoring commit | `145d31e9849c0b8ea67477f744210d0270a4f4cc` |
| Merge of corrected main into the P0 branch (contains the disclosed conflicted-ledger defect) | `ad654f6fbcc387a807677461b5c661d697e8b98a` |
| Forward repair of that ledger resolution | `49ed7b35e50d6a9ac9f8e9c39a7ed95f2a48e0b5` |
| Ratification commit | the commit carrying this document (subject above; SHA materializes with the commit and is recorded in the PR body, never predicted) |
| EL09 correction head (PR #22) | `20a211ebe65a46a3436b5207679fe5c37b80f6e1` |
| EL09 correction merge (= pre-ratification `main`) | `74fee0f086f9215bf6b93a1b3adbf1d69406da39` (parents `7393228d…` + `20a211eb…`, tree `f303b257…` = the tree its CI tested) |

## 3. Independent re-audit of the EL09 correction (PR #22)

Re-derived from committed bytes during this ratification, not inherited from the correction's own packet:

| # | Claim | Result |
|---|---|---|
| 1 | historical ledger row byte-for-byte unchanged | **confirmed** — row still `83a40ac7…` / `191950` in the frozen addendum |
| 2 | all original rows recompute at the historical head and at PR #20's merge | **confirmed** — 13/13 exact at `08bf0b2d…` **and** `7393228d…` |
| 3 | ledger explicitly governed as append-only | **confirmed** — Book 5 append-only law; §18.11/§18.12/§19 each appended |
| 4 | prefix rule applies to the exact ledger path only | **confirmed** — `path == LEDGER_ROW_PATH` equality, no substring/suffix/extension test |
| 5 | ledger verification is `len >= size` **and** `sha256(bytes[:size]) == digest` | **confirmed** — `verify_manifest_row()` append branch |
| 6 | suffix is never attributed to the historical row | **confirmed** — only `data[:size]` is hashed for that row |
| 7 | every other row remains exact whole-file hash + size | **confirmed** — 12/12 exact at `74fee0f0…`, 11/12 at the audit head because the verifier itself is the revisioned row |
| 8 | missing/duplicate/malformed/unknown-mode/misclassified rows fail closed | **confirmed** by law controls and by 14/14 mutation discrimination |
| 9 | no unrelated file gains append-only treatment | **confirmed** — similar name, copied bytes, aliased path all refused as `whole_file` |
| 10 | revised verifier pinned non-vacuously | **confirmed** — `27758` bytes and whole-file digest `2546c49c…` |
| 11 | superseding manifest has 13 unique rows | **confirmed** |
| 12 | twelve unchanged rows equal the frozen rows | **confirmed** programmatically (12/12 equality assertions) |
| 13 | only the verifier row is revisioned | **confirmed** |
| 14 | frozen addendum and workflow byte-identical | **confirmed** — addendum unmodified; workflow matches its manifest row |
| 15 | frozen B5-I7 inventory stays at exactly 27 nodes | **confirmed** — `27 tests collected`, 27 executed, 0 fail/err/skip |
| 16 | positive/negative controls discriminate | **confirmed** — 4 positive, 17 negative, each refused by message |
| 17 | mutation battery independently re-run with pristine restoration | **confirmed** — this ratification re-ran **14/14** mutations RED, byte-exact restoration, pristine rerun green |
| 18 | PR #22 artifact bound by tested-tree equality and merge-ref second parent | **confirmed** — run head `20a211eb`, head tree `f303b257…` = merge tree; merge's second parent = `20a211eb`. (GitHub pruned `refs/pull/22/merge` post-merge, so the merge-ref *object* recorded pre-merge, `547320e5…`, parents `7393228d`+`20a211eb`, is the durable observation.) |

Verdict: the correction strengthens, and does not weaken, immutable evidence. Nothing is existence-only; nothing is circular; only one path is prefix-bound.

## 4. Source-to-claim audit and arithmetic

Recomputed from the committed registry, matrix, plan and failure document — not from their prose:

| Dimension | Recomputed |
|---|---|
| requirements | **55**, ids unique 55/55 |
| kinds | identity 3 · boundary 4 · e2e 4 · adversarial 10 · usability 7 · evidence_audit 6 · measurement 4 · gate 4 · evidence_law 8 · deferred 5 = **55** |
| bindings | test 40 · attestation 7 · static 3 · deferred 5 = **55** |
| states | `PLANNED` 40 · `MAPPED` 10 · `DEFERRED_WITH_OWNER` 5 · `BLOCKED` 0 · `PASS` **0** |
| matrix ↔ registry | 55 ids, set-equal; kind column equal per id |
| planned nodes | **40**, unique, across **5** files (4/10/8/10/8); registry node names == plan node names |
| `G16` node | present verbatim: `TestUsabilityProtocol::test_accessibility_and_usability_verified` |
| deferred closure | 5/5 carry owner, future stage, reason, planned surface and observable refusal |
| failure classes | **18** (`F01`–`F18`), each naming a planned node; all proof references resolve to plan nodes |
| mutation plan | **12** (`M01`–`M12`), each with target, expected node, acceptable failure mode, restoration proof and pristine-rerun requirement |
| adjacent floor | **189**, independently reproduced by re-running the plan's own collection command |
| `charter_increment` | `null`, supported by contract §1.1 (charter `I-8` consumed by B5-I7; `I-7` is the operator-owned web view) |
| usability labels | only `EXPECTED` / `FLOOR` / `CEILING` / `NOT_YET_OBSERVED`; the only `OBSERVED` values are the base SHA and the 189 adjacent population |
| implementation artifacts | **none** — no `test_b5_i8_*`, no web-view file, no B5-I9 or Book 6 artifact |

## 5. Branch history and disclosed defect

`145d31e9` (P0) → `ad654f6f` (merge of corrected main; **the conflicted ledger was staged with its
conflict markers committed**, because the resolution script aborted on a non-ASCII bytes literal
before rewriting the file) → `49ed7b35` (forward repair, no amend, no force-push).

The defect stays in history and in the audit score. The repaired ledger is, in append-only order:
the immutable 191950-byte prefix, corrected main's `§18.12`, this packet's `§19`, and `§19.12`
recording the defect. No content was dropped from either merge side; the final PR diff against
corrected main is documentation only.

## 6. Exact-head CI evidence (parsed, not inferred)

| Field | Value |
|---|---|
| run | `42030149828` — `success`, event `pull_request`, attempt 1 |
| check suite / check-run · job | `113888785299` · `127254239190` |
| artifact | `13415518250` — `b1-i1r-evidence-12e3e43ad44e`, `42495` bytes, not expired |
| tested head / tree | `49ed7b35…` / `be5d30c6336bfd00978579aff708c22fac2132e7` |
| merge ref | `7dc1248e68…`, parents = `74fee0f0…` (corrected main) + `49ed7b35…`, tree = tested tree |
| B5-I7 | 27 collected / 27 executed / 27 passed, 0 failures, 0 errors, 0 skipped |
| EL09 | executed and **passed** with the B5-I8 ledger suffix present |
| adjacent | B5-I2 24 · integrity 16 · B5-I3 51 · B5-I4 23 · B5-I5 45 · B5-I6 27 = **186**, zero fail/err/skip |
| manifest / cleanup | manifest verification passed · cleanup `removed` + `pruned` |
| ledger prefix | independently recomputed: `83a40ac7bb2d80ae2cc9176e1b1ba91d8bfeb189680572ce3939134b6aeb5c30` |
| B5-I8 results | none present, and none claimed — P0 adds no CI step |

Run history is preserved, never relabelled:

| Run | Head | Classification |
|---|---|---|
| `41724079443` | `145d31e9` | **failed** — the observed EL09 defect that motivated PR #22 (job `126232778697`, artifact `13274838782`) |
| `42030058641` | `ad654f6f` | **superseded** — green, but on the tree that carried committed conflict markers |
| `42030149828` | `49ed7b35` | **authoritative** — the exact-head evidence above |

## 7. Fresh same-agent audit

`SAME-AGENT — NOT ORGANIZATIONALLY INDEPENDENT`

| Axis | Score | Visible deduction |
|---|---|---|
| SPEC | 9.0 | −1.0 the same frozen tables are restated across four documents, so a single edit must be mirrored; verified consistent today |
| DESIGN | 8.5 | −1.5 55 requirements yield 40 future nodes, and the 18 failure classes rest on fewer distinct proof nodes (`F08`/`F09` share one; `F18` concatenates) |
| CORRECTNESS | 8.0 | −2.0 the P0 validator was ephemeral and uncommitted, so nothing in-tree re-derives 55/40/18/12 at CI time; and the EL09 interaction was not anticipated at P0, which is what made the first submission fail |
| QUALITY | 8.0 | −2.0 the conflicted ledger was committed in `ad654f6f`, and the packet is dense enough that its counts must be recomputed rather than read |

Arithmetic mean `(9.0 + 8.5 + 8.0 + 8.0) / 4 = 33.5 / 4 =` **8.38 / 10**.

This supersedes the P0 packet's own 8.13/10 (and Packet B's restatement of it). It is not inflated
because CI is green: every one of the deductions above survives a green run. The earlier 8.88/10
belongs to the EL09 correction (Packet A) and stands separately.

Absence of implementation evidence is **expected at P0** and is not scored as a defect.

## 8. Defects found, and repairs

| # | Defect | Class | Repair |
|---|---|---|---|
| D1 | EL09 applied whole-file equality to an append-only document | content (B5-I7) | corrected in PR #22 (`74fee0f0`); re-verified here |
| D2 | `ad654f6f` committed the conflicted ledger with its conflict markers | process (this packet) | repaired forward in `49ed7b35`; preserved in history and in the score |
| D3 | the EL09 interaction was not anticipated when P0 was authored | process | disclosed; the ledger law now has a prefix invariant plus 21 in-node controls |
| D4 | P0's validation tooling was ephemeral, so no in-tree recomputation exists at P0 | process | recorded as a limitation; the ratification re-derived every count independently and records the results here |

No P0 planning claim was found false. No production, workflow, test or frontend file is touched by
this ratification.

## 9. Changed-file boundary of the ratification commit

Documentation only — seven paths against corrected `main`:

```
docs/oce-golden-system/OCE_B5_I8_ACCEPTANCE_MATRIX_v1.0.md      (status + §4)
docs/oce-golden-system/OCE_B5_I8_CONSTRUCTION_PLAN_v1.0.md      (status header)
docs/oce-golden-system/OCE_B5_I8_FAILURE_MATRIX_AND_RECOVERY_PLAN_v1.0.md (status header)
docs/oce-golden-system/OCE_B5_I8_IMPLEMENTATION_CONTRACT_v1.0.md (status, §17, §18)
docs/oce-golden-system/OCE_B5_I8_REQUIREMENT_TEST_REGISTRY_v1.0.json (ratification block)
docs/oce-golden-system/OCE_B5_I8_OPERATOR_RATIFICATION_v1.0.md    (new, this document)
docs/oce-golden-system/OCE_BOOK_5_PROGRESS_EVIDENCE_LEDGER_v1.0.md (§19.13 append)
```

## 10. Limitations

1. This ratification is **same-agent**; organizational independence remains `B5I8-DF05`.
2. `G16` is **open**: no protocol has executed, and the ratification claims no usability result.
3. GitHub pruned `refs/pull/22/merge` after merge; that binding is evidenced by run-head tree
   equality plus the merge commit's second parent, and by the pre-merge observation recorded above.
4. P0 ships no in-tree validator; reproduction is by the commands recorded in the packet and in
   this record.
5. `ad654f6f` remains in history as a transiently broken merge; it is disclosed, not cosmeticised.

## 11. Locks

```
P0 = OPERATOR_ACCEPTED — PLANNING FROZEN
B5_I8_IMPLEMENTATION = NOT STARTED
B5_I8_IMPLEMENTATION_AUTHORIZED = FALSE
MERGE_AUTHORIZED = true (P0 ratification PR only)
G16 = OPEN
B5_I9 = LOCKED
BOOK_6 = UNAUTHORIZED
POST_BOOK_6_EVALUATION = UNSTARTED
WEB_VIEW = ABSENT
CAPITAL_AUTHORITY = NONE
RECURRING_COST = $0
SAME_AGENT = NOT ORGANIZATIONALLY INDEPENDENT
```

---

# B5-I8 Implementation Ratification

**Stage:** `AUTHORIZED_STAGE=B5-I8-RATIFICATION`
**Base:** `e999a4a342f8a2ebb8f99045206d67d04d6fcbbf` (`origin/main`)
**P0 merge:** `74fee0f086f9215bf6b93a1b3adbf1d69406da39` (PR #22)
**Scope:** the independent audit implementation carried by PR #23, and nothing else.

## R1. Forward ladder

| Rung | Commit | Disposition |
|---|---|---|
| `X1` | `3a90b8548a` | cite the observed artifact; exempt only the server-side merge ref |
| `X2` | `801730c4c3` | bind observed CI identities to the committed parsed record |
| **`X3`** | **`e0f6a73c46`** | **Amendment 001: the CI-selection surface is formally superseded** |
| `X4` | `36288f4b49` | G15 independent totals and the 40-node non-vacuity audit; **committed red, preserved** |
| `X5` | `6b26214637` | narrow the false-positive secret assertion; run the mutation battery in authoritative CI |
| `X6` | `8fcb28097d` | bind the real Actions run identity; **CI red, preserved** |
| `X7` | `1f54168b81` | bind the PR identity into the context-writing step; implementation head |
| `EVIDENCE-FINAL` | `8e39d8cd11` | seal the observed identity, ledger identities and Windows comparison; **CI red**, preserved |
| `X8` | `5da5ae9e1b` | state the merge-ref law truthfully in both observability states; final evidence head |

No rung was amended, squashed, rebased or force-pushed. Both red rungs remain in
history: a repaired defect that leaves no trace is indistinguishable from one that
never existed.

## R2. The selection conflict, resolved rather than reinterpreted

Plan section 1 rung `R6` placed the selection step inside
`.github/workflows/b1-i1r-validation.yml` and named the artifact
`b1-i1r-evidence-<run_id>`. B5-I7's frozen `EL09` manifest pins that file as a
**whole-file** immutable row, so editing it turns `TestEL09` red (reproduced: 26/27).
Amendment 001 records the disposition as **superseded, not satisfied**, and performs
the same fail-closed selection in a dedicated additive workflow with artifact
`b5-i8-evidence-<run_id>`. The pinned file is byte-identical, the original clause
remains visible in history, and triggers, identity rules, retention, cleanup and
authority boundaries are unchanged. The workflow holds `permissions: contents: read`
and references no repository secret.

## R3. Arithmetic

| Dimension | Value |
|---|---|
| Requirements | 55 unique (`attestation` 7, `deferred` 5, `static` 3, `test` 40) |
| Nodes | 40 collected = 40 executed = 40 passed; `unique_nodes` 40 |
| Node closure | `planned == collected == executed`; zero orphan files, zero orphan nodes |
| Failure classes | 18 |
| Mutations | 12 required, 12 executed, 12 `DISCRIMINATED` in authoritative CI |
| Floors | focused 40; adjacent 189 |
| Duplicate nodes | 0 |
| `pass_claims` | 0 |

## R4. Evidence

Evidence-head run `42328131722`, artifact `b5-i8-evidence-a4abf73d3f2a` (7398 bytes,
expires 2026-12-07). `oce_run_id` is `a4abf73d3f2a`: non-empty and bound to the
artifact name. The recorded run id, attempt, workflow path, PR number and event are
the values Actions actually supplied, and the proof refuses itself if any of them is
blank or inconsistent. Tested head
`5da5ae9e1b82507443f4d3faa2d06f8ebae0fb4c`, tested tree
`288d14623da4586a5a2f6f1ef916dd39d202b97d`; merge ref
`99b65278e8d1f38c7e1bd7ee302ce94c69aa04ae` with parents `e999a4a3…` and
`5da5ae9e…` and a tree equal to the tested tree.

Mutation evidence is CI-authoritative: each of `M01`-`M12` applies, turns its named
node red, restores byte-exactly, and the pristine rerun is 40/40 with
`baseline_dirty false`. The 40-node non-vacuity audit names a target, an oracle and a
negative control per node; `tautological`, `orphan_nodes` and `orphan_requirements`
are all zero.

## R5. E2E boundary

The end-to-end claim is **re-execution of the governed path against the real
production surfaces, in-process**. It is not a live multi-process stack: no frozen
source names a process or port boundary, and this stage may not add endpoints. The
wording in the contract, plan and tests matches what is exercised.

## R6. Gate dispositions

| Gate | Disposition |
|---|---|
| `G14` | adjacent population 189, all ten files green |
| `G15` | independent totals owner: the committed CI identity plus the registry, with forged-total controls |
| `EL01`-`EL08` | executed green and red on falsification |
| `EL09` | prefix `83a40ac7…` over `191950` bytes intact; the current ledger is recorded separately |
| `G16` | **`OPEN`**, blocker `B5I8-DF05` |

## R7. `G16` carried open under the governing permission

The registry's `deferred_owners` names the closure owner as *"Operator (independent
auditor distinct from the implementer)"*. B5-I8 acceptance therefore does not require
closing `G16`; it requires not lying about it. `G16` stays `OPEN`, the protocol stays
labelled `SAME_AGENT_SINGLE_OPERATOR_NON_BLIND`, no usability statement is made
unqualified, and the inherited requirement state is untouched. This operator
authorization is not completion of the usability protocol.

## R8. Audit

`SAME-AGENT — NOT ORGANIZATIONALLY INDEPENDENT`

| Dimension | Score |
|---|---|
| `SPEC` | 8.6 |
| `DESIGN` | 8.4 |
| `CORRECTNESS` | 8.7 |
| `QUALITY` | 8.5 |
| **Mean** | **8.55** |

Deductions, each for a distinct impact rather than a repeated root cause: the original
workflow-placement conflict (`SPEC`); the in-process E2E boundary and the
single-operator protocol (`SPEC`, `DESIGN`); the committed-red `X4` rung, the mutation
battery's initial absence from CI, the blank `oce_run_id` and the red `X6`
(`CORRECTNESS`); the shared support-module blast radius, cross-file evidence density,
and the `G15` self-reference and `D4`/`D5` attribution repairs (`QUALITY`, `DESIGN`).
The mean is not inflated because the repairs are green: a repaired defect still cost a
rung. This supersedes the P0 score of 8.38.

## R9. Tokens

```text
B5_I8_IMPLEMENTATION = RATIFIED_INDEPENDENT_AUDIT
MERGE_AUTHORIZED = true (PR #23 only, after ratification-head CI passes)
G16 = OPEN (blocker B5I8-DF05)
B5_I9 = LOCKED
BOOK_6 = UNAUTHORIZED
POST_BOOK_6_EVALUATION = UNSTARTED
WEB_VIEW = ABSENT
CAPITAL_AUTHORITY = NONE
RECURRING_COST = $0
SAME_AGENT = NOT ORGANIZATIONALLY INDEPENDENT
```

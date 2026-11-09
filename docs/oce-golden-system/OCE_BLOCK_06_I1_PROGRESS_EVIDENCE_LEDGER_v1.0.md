# OCE Book 6 — B6-I1 progress and evidence ledger

**Document ID:** OCE-B6-I1-LEDGER-001
**Stage:** `AUTHORIZED_STAGE=B6-I1-IMPLEMENTATION`
**Base:** `6783bf7638f5ecd4e42ec2eb8141d1aa57dfaa3e` (tree `3c2e2a6676e16415a1e2bd326c1fc147e51c2a6d`)

## 1. Identity derived, not assumed

B6-I1 is `C1 API and SDK` (`B6.C1.S1`, `B6.C1.S2`, plus the `C1.S5` compatibility check named in
the frozen P0 sequence). The merged sequence record states `kind=implementation`,
`implementation_surfaces=["api","sdk"]`, `tests=["contract","denial"]`, `mutation_floor=3`,
`non_goals=["templates"]`, `exit_gate="canonical path and compatibility pass"` and
`stop_conditions=["stop on authority leak"]`. B6-I1 therefore does not extract, copy, package or
publish any of the twelve candidates B6-I0 admitted for later design.

## 2. Frozen contract

`OCE_BLOCK_06_I1_IMPLEMENTATION_CONTRACT_v1.0.json` freezes the floors before any result exists:
42 governed nodes across six modules, six source mutations (authority floor 3), zero
failure/error/skip, canonical JSON, a manifest verified by a second code path, and the exact
base/head paired comparison. No later commit may lower a floor.

## 3. Surface

Ten operations, all `public_experimental`, `public_stable` remains 0. Scopes are exactly
`read`, `propose`, `decide`; wildcard, `admin`, `authority`, `write` and `root` are refused as
authority violations. Storage, paths, secrets and client-supplied authority are never reachable
through a request or a response.

## 4. Proofs

- Contract: operation table, firewall alignment, canonical artifacts, manifest, registry coverage.
- Denial: unknown and unsupported versions, no silent latest, unknown operation, scope refusal,
  schema refusal, storage-internal refusal, authority refusal, self-approval refusal.
- SDK: canonical invocation only, typed results and refusals, no duplicated business rule.
- Compatibility: three verdicts with the supported window always stated.

## 5. Exact paired comparison

A comparison is valid only when it pins its own endpoints. The stage contract pins base
`6783bf76` and the implementation head, with a common population floor of 270 frozen Book 5
nodes, zero base-only nodes and 42 expected head-only nodes. A run pinned to another stage is
not acceptable evidence.

## 6. Locks and holds

`B6-I2` through `B6-I9` remain `LOCKED`. `BOOK_6_COMPLETE = false`. `G16` remains `OPEN` under
`B5I8-DF05`. The post-Book-6 evaluation system is `RESERVED_NOT_AUTHORIZED`. Package publication
and cloud hosting are `NOT_BEGUN`. Cost is `$0`; `capital.authority = none`; no broker or
execution authority exists.

`MERGE_AUTHORIZED = false`. `RATIFICATION_AUTHORIZED = false`. **NOT MERGE AUTHORIZED.**

## 7. Status

Stage tag: `B6I1`.

The target handoff state is `READY_FOR_OPERATOR_REVIEW`, asserted only in the evidence rung once
the exact-head workflows are green and their raw artifacts have been parsed. Until that rung is
committed, this ledger records implementation in progress and claims no PASS it has not observed.

## 8. Repairs

Any later repair is committed forward as its own rung and disclosed here with its failed run.
No history is rewritten, amended, squashed or force-pushed.

## 9. Evidence rung

### 9.1 Exact-head CI at implementation tip `ae2d80e7`

| Workflow | Run | Result |
|---|---|---|
| B6-I1 Validation | `42624339612` | success |
| B6-I1 Paired Comparison | `42624339355` | success |
| B5-I9 Factory Gate Validation | `42624339319` | success |
| B5-I9 Post-Merge Paired Comparison | `42624339460` | success |
| B5-I8 Audit Validation | `42624339306` | success |
| B1-I1R Validation | `42624339341` | success |

Parsed raw artifacts: 42 collected, 42 executed, 42 passed, 0 failures, 0 errors, 0 skipped,
`rc 0`; validator `PASS 164/164`; mutation battery `floor 6, discriminated 6, restored 6,
pristine_green_after true`; frozen Book 5 gate 41/41; adjacent suites green; cleanup clean.

### 9.2 Exact paired comparison

Run `42624339355`, verdict `PASS` over 19 checks: base `6783bf76` (tree `3c2e2a66`) versus
implementation head `d0f1be21` (tree `781ed580`), 270 common nodes (270 pass, 0 skip, 0 fail,
0 error), base-only 0, head-only 42 of 42 expected and all green, common floor 270 satisfied,
both endpoint clones removed before the verdict, dependency lock and runner image identical.

### 9.3 B6-I0 ladder-count discrepancy resolved

B6-I0 has 14 branch commits before the merge, 0 merge commits inside the branch, and exactly one
final main merge. The earlier phrase "all 15 ladder commits reachable" counted the merge commit as
a ladder rung; 14 is the correct rung count and the merge is the separate two-parent join at
`6783bf76`. Classification: bookkeeping wording, not a lineage or ancestry error. It is corrected
here append-only; no B6-I0 byte and no history is rewritten.

### 9.4 Repairs committed forward

X1 normalized manifest paths to POSIX and moved the mutation battery onto a detached worktree.
X2 re-pinned the paired comparison. X3 strengthened the storage-leak proof after mutation M04
showed the old assertion accepted `store_path` by exact-name comparison. X4 re-pinned the paired
contract to the strengthened head. No history was amended, squashed, rebased, reset or
force-pushed.

### 9.5 Limit and structural conflict disclosed

`B6-I0 Validation` run `42624339342` is red at this head, and it cannot be made green here. Its
frozen validator applies B6-I0's own stage-scoped laws outside their window: `git/base` expects
main to still be `5e76dc12`; `boundary/only_allowed_paths` accepts only B6-I0 prefixes;
`boundary/no_prohibited_surface` forbids `oce/`, which B6-I1 is explicitly authorized to extend
with `oce/api/`, `oce/sdk/` and `oce/compat/`; `impl/no_book6_modules` forbids those modules; and
`boundary/p0_packet_untouched` filters changed paths by `I0` instead of `P0`, so B6-I1 packet files
are reported as P0 modifications. Repairing this requires an operator decision to rescope or
retire a ratified prior-stage workflow; B6-I1 holds no amendment authority, and the B6-I1 contract
forbids editing B6-I0 artifacts. This is a governance defect in the prior stage, not a B6-I1 proof
failure, and it is recorded rather than hidden.

### 9.6 Locks unchanged

`MERGE_AUTHORIZED = false`; `RATIFICATION_AUTHORIZED = false`; `B6-I2`–`B6-I9` LOCKED;
`BOOK_6_COMPLETE = false`; `G16` OPEN under `B5I8-DF05`; evaluation system
`RESERVED_NOT_AUTHORIZED`; no package, publication, registry, cloud, broker, capital or execution
authority; cost `$0`.

## 10. Prior-stage repair and operator ratification

`B6-I0-STAGE-SCOPE-AMENDMENT-001` was frozen at `e19eea69` before any validation change. It
preserves strict B6-I0 mode unchanged, adds a fail-closed stage-aware mode, keeps the P0 packet and
the frozen B6-I0 packet immutable in later-stage mode, admits only the B6-I1 contract paths and the
amendment paths, and refuses missing, unknown, spoofed, tampered or moved identity. Thirteen
negative controls prove each refusal is real and that the pristine run passes.

Amended-head evidence: B6-I0 Validation `42648199671` PASS 136/136 with 72 of 72 nodes, zero
failures, errors and skips, mutation floor 12 of 12 discriminated and 13 restored, Book 5 gate 41 of
41, controls green; B6-I0 Paired `42648100136`; B6-I1 Validation `42648199359` 42 of 42; B6-I1
paired `42648199656` 270 common, 0 base-only, 42 head-only; B5-I9 Factory Gate `42648200387`;
B5-I9 paired `42648200109`; B5-I8 Audit `42648199369`; B1-I1R `42648199663`.

Ratification authorizes the normal two-parent merge of PR 30 only. B6-I2 through B6-I9 remain
LOCKED, Book 6 is not complete, G16 stays OPEN under `B5I8-DF05`, the evaluation system remains
RESERVED_NOT_AUTHORIZED, and no package, publication, cloud, broker, capital or execution
authority exists. Cost `$0`. NOT MERGE AUTHORIZED no longer applies to this stage, but no later
stage is authorized by it.

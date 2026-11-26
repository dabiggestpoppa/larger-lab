# 04 - Governance reconciliation at the repaired candidate

## Invariants re-measured

| Invariant | Value at `66200f3cb` | Changed by this mission |
| --- | --- | --- |
| Approval manifest artifacts | `{}` (empty) | no |
| Approval manifest revoked ids | `[]` | no |
| Approval manifest authority | `B5_I09P2A_EMPTY_TRUST_ROOT_V1` | no |
| Approval manifest SHA-256 | `3d707c59fbf1fe96f28b2080811a0da189d2ad5c2859c97faa01a367c7042654` | no |
| Manifest git blob | `7be15e8e56c87a4acea533a7b2382c1f5d5ad2f9` - identical at `868dd3fc9` and `66200f3cb` | no |
| `sensors/verification.py :: INTEGRATION_STATE` | `"INTEGRATION_REQUIRED"` | no (the repair diff does not contain the symbol) |
| Provider approvals added | none | no |
| Custody-source authorization | `OPERATOR_CUSTODY_SOURCE_AUTHORITY_RECORD_V1` unresolved, unimplemented | no |
| Trust promotion / gate advancement / Bloc 6 | untouched | no |
| Merge to production | not performed | no |
| Replay binding contract | `REPLAY_EVIDENCE_RECORD_BINDING_V1` named, `REPLAY_RECORD_BINDING_ESTABLISHED = False` | named and made executable; **not** implemented |

The manifest hash being unchanged from the starting SHA is the mechanical
statement that no trust was promoted by this mission. The empty manifest is also
what the custody guard is written against, so hardening cannot be satisfied by
quietly approving an artifact.

## Tracked inventory

| Measure | Value |
| --- | --- |
| Tracked Python files | 1,111 |
| `quant-lab/src/` | 157 |
| `quant-lab/tests/` | 249 |
| Files changed by the repair commit | 4 (one production module, three test modules) |

The inventory is unchanged by the repair, which edited existing modules only.
The +16 canonical nodes are new test functions inside the three already-tracked
test modules, not new files.

## Reconciliation of previously accepted controls

The introduction of the executable replay-binding guard changed the terminal
state of a *fully satisfied* evaluation from `ACCEPT_FIELD_BINDING` to
`INTEGRATION_REQUIRED`. Five historical positive controls in Agent 2's suite
assert the pre-guard terminal state and now fail by design:

| Control | Why it fails now |
| --- | --- |
| `test_r2_f1_00_control_matching_evidence_reaches_accept` | asserts the pre-guard accept |
| `test_r2_f1_07_same_revision_across_providers_is_unbound` | asserts the pre-guard accept for the unbound axis |
| `test_r2_h03_00_control_a_test_root_can_authorize` | asserts the pre-guard accept |
| `test_r2_h05_03_omitted_references_still_read_the_approved_set` | asserts the pre-guard accept |
| `test_r2_h05_05_each_approved_reference_is_read_twice` | asserts the pre-guard accept |

Disposition: these are **reconciled, not repaired and not deleted**. The guard
is not removed to recover historical outcomes. The accept machinery they were
protecting is still exercised - the same suite passes 33/33 with the guard
flipped to the state a minted contract would create. The two actual defect tests
from the reattack (`test_r2_f1_05_extra_selected_revision_after_cutoff_is_bound`,
`test_r2_f2_02_typed_verifier_refusal_detail_is_withheld`) pass unadjusted.

This is the approved F1-residual consequence: the decision boundary moved
because an unresolved integration dependency was made executable, and the
guarded terminal state is the correct outcome until
`REPLAY_EVIDENCE_RECORD_BINDING_V1` is minted.

## G16 and G17

No change relative to `p3_rung6_final_r1/04_GOVERNANCE_AND_INVARIANTS.md`: G16
(the I08 scope admission) remains prospective and disclosed, and G17 (consumer
admission in the I06 audit and producer) remains repaired prospectively with the
producer artifacts republished mechanically. This mission touched neither the
audit, the producer, nor any scope-audit file, and it did not re-pin any
historical digest.

## Non-interference

The publication in this directory is additive Markdown plus one JSON record. It
changes no production code, no canonical test, no manifest, no schema, no
evidence artifact and no gate state. The canonical verification in `02`
describes the tree before this publication was committed.

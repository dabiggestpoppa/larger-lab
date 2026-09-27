# G4R_REOPEN_SCOPE_EVIDENCE_AUDIT — a condition for A can never reopen B

## Subject binding (G4R-02)

`ReopenCondition` is OBJECT_SPECIFIC by default and applies **only** to the
object named by `subject_ref`. A blank subject fails closed
(`subject_unbound`); a condition that must apply broadly requires the explicit
`subject_scope="GLOBAL"` marker — blank is never silently global.

Evidence: `condition_for_A_does_not_reopen_B`,
`condition_for_A_reopens_A_when_satisfied`,
`blank_subject_ref_fails_closed_for_object_specific_condition`,
`explicit_global_condition_requires_explicit_scope_marker`.

## Scope binding (G4R-03)

`decide_suppression` evaluates with the record's `exact_scope`; a condition
with a declared scope must match under `scope_match_mode` (EXACT default,
PREFIX / WILDCARD only when explicitly requested; unknown modes fail at
construction). A condition scoped to `BTC/FUNDING/HISTORICAL` cannot stop
suppression of a record scoped to `FX/EURUSD/EXECUTION`.

Evidence: `wrong_scope_condition_does_not_stop_suppression`,
`exact_scope_condition_can_stop_suppression`,
`cross_domain_scope_fails_closed`, `scope_match_recorded_in_evaluation`,
`test_cross_scope_condition_fails_closed` (test_g4.py).

## Combination semantics (G4R-04)

Conditions sharing a `group_id` combine with an explicit `group_operator`
(ANY | ALL); unknown operators (and a group id without an operator) are
rejected at construction. Condition order never changes the result (group
combination is evaluated per group, order-independent).

Evidence: `any_group_reopens_on_one`, `all_group_requires_all`,
`all_group_one_missing_does_not_reopen`,
`condition_order_does_not_change_result`,
`unknown_group_operator_fails_closed`.

## Evidence binding (G4R-05/06)

An `evidence_required` condition must cite **specific** `evidence_refs`, each
of which must resolve in the governed `EvidenceRegistry`:

- phantom ref → `evidence_phantom` → NO_REOPEN (case C);
- ref not supplied by facts → `evidence_missing`;
- empty `evidence_refs` on an evidence_required condition → fail closed (no
  generic "any evidence" acceptance);
- `BLOCKER_RESOLVED` additionally requires an attributable
  `BlockerResolutionRecord` (subject/scope-bound) whose evidence refs resolve;
  a bare `resolved_blockers` claim or an unsupported agent assertion cannot
  reopen (S11 control 2).

Evidence: `phantom_reopen_evidence_rejected`,
`unrelated_evidence_does_not_satisfy_condition`,
`correct_subject_evidence_satisfies`, `correct_scope_evidence_satisfies`,
`condition_evidence_refs_recorded_in_reopen_trace`,
`evidence_required_without_specific_refs_fails_closed`,
`blocker_resolution_requires_record`,
`blocker_resolution_record_without_evidence_rejected`,
`blocker_resolution_subject_scope_mismatch_rejected`,
`evidence_backed_blocker_resolution_reopens`.

All binding/evidence failures are emitted as conflicts and survive into the
run receipt via the `ProvenanceConflictLedger` (G4R-21): the ledger now
accepts `REOPEN_EVALUATION`, `NEGATIVE_KNOWLEDGE`, `MEMORY_RETRIEVAL` and
`RECONSTRUCTION` surface tags.

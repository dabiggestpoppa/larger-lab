# G4 — Negative Knowledge Audit

## Permanence authority (G4-P0-C)
`NegativeKnowledgeRecord.make_permanent(actor, authority_state, basis, ratification_ref)` reads the ACTUAL level from the governed `AuthorityState`; a payload string saying "OPERATOR" is never an authority basis.

- `test_worker_cannot_make_negative_knowledge_permanent` — WORKER actor with real WORKER level rejected.
- `test_fake_operator_payload_rejected` — payload says OPERATOR while the actor is WORKER → rejected, record stays non-permanent.
- `test_real_operator_authority_can_make_permanent` — only actual OPERATOR authority creates `PERMANENT_BY_OPERATOR_AUTHORITY`.
- `test_permanence_records_authority_reference` — actor, actual level, authority basis, ratification ref and binding mode (`EXACT_AUTHORITY_STATE`) are all recorded and reconstructable.
- `test_permanence_does_not_delete_reopen_history` — making a record permanent never erases its reopen conditions.

## Reopen semantics (S11)
Machine-readable `ReopenCondition` of type `BLOCKER_RESOLVED` (canonical blocker vocabulary, evidence-required flag):

- `test_blocker_resolved_condition_reopens_ordinary_negative_knowledge` — new sensor evidence that blocker B is resolved stops suppression for the exact scope; the record is retained.
- `test_unrelated_evidence_does_not_reopen` — unrelated evidence leaves the record suppressed.
- `test_unsupported_blocker_assertion_does_not_reopen` — asserting the blocker resolved WITHOUT evidence does not reopen (evidence-required fail-closed).
- `test_suppression_ends_only_for_exact_scope` — a different scope with an unsatisfied condition stays suppressed.

## Operator-permanent records (Control 3)
- `test_operator_permanent_record_does_not_auto_reopen` — ordinary reopen evidence cannot auto-reopen a permanent record; the decision is `OPERATOR_REVIEW_REQUIRED` with `reopen_condition_status=OPERATOR_PERMANENT`.
- `test_permanent_behavior_ambiguity_remains_explicit` — revocation of operator permanence is unspecified in the architecture; the ambiguity is recorded explicitly (reason text names "revocation"), never silently resolved.

## Suppression engine (G4 §9)
`NegativeKnowledgeSuppressionDecision` exposes record_id, scope, suppression state, reason, reopen status, evidence refs, permanent authority and next action (`CONTINUE_SUPPRESSION` / `STOP_SUPPRESSION` / `OPERATOR_REVIEW_REQUIRED`). Suppression influences retrieval/priority behavior; it never erases evidence — `record_retained` is asserted after reopen.

## Condition versioning (G4 §24)
Reopen conditions are versioned (`version_tag`); `test_reopen_contract_version_retained` verifies the version survives into evaluation results, so old records are never reinterpreted under silently-changed semantics. Unknown condition types/operators/blockers fail closed at construction (`test_unknown_condition_type_rejected`, `test_unknown_operator_rejected`, `test_unknown_blocker_rejected`).

# G4R_CONTEXT_ADVERSARIAL_AUDIT — S12 must not pre-solve hyperthymesia

## Active-flood (G4R-16, case G)

The primary S12 fixture places only the 12 relevant objects in ACTIVE_CONTEXT
— the G4R review correctly flagged this as too easy. The hardened runner adds
an `active_flood` mode and the adversarial suite runs it:

| metric | value |
| --- | --- |
| total objects (20,000 history + 2,000 experiments + 12 relevant) | 22,012 |
| initially ACTIVE_CONTEXT (half the history) | 10,000 |
| active after bounded retrieval | 12 |
| required recall | 1.0 |
| stale intrusion | 0 |
| policy-governed compaction records (`mem.activation.historical`) | 10,000 |
| active after compaction | 12 |

Variant B (tag collision): 5,000 ACTIVE objects sharing broad `TASK` tags vs
12 specifically tagged required objects → the 12 required are selected, stale
intrusion 0. Variant C (recency distraction): 3,000 recent-but-irrelevant
ACTIVE objects cannot crowd out the 12 old required objects (recall 1.0).

## Required > budget (G4R-16 variant D / G4R-18)

20 required with budget 12 → `bundle_status == "CONTEXT_BUDGET_INSUFFICIENT"`,
`budget_sufficient is False`, recall 0.6 — the gap is explicit, never hidden.
A required ref absent from the index is surfaced in `missing_required_refs`
with a per-ref `required_ref_resolution_status` (`MISSING` /
`RESOLVED` / `DORMANT_UNSATISFIED` / `ARCHIVAL_UNRECONSTRUCTED`).

## Policy-governed compaction (G4R-17)

`compact_active_pool` compresses ACTIVE_CONTEXT objects with LOW task
relevance to DORMANT_STORE by the shared activation rule
(`mem.activation.historical` → `COMPRESS_TO_DORMANT`). Every
`MemoryCompactionRecord` retains object refs, the policy rule, reason,
provenance pointer, reconstruction pointer and epoch. Nothing is deleted.

## Evaluator-gated retrieval (G4R-19)

`MemoryRetriever` accepts only governed `ReopenEvaluation` objects (or a
resolver producing them) for dormant/archival reactivation:

- `reopen_facts={"c1": True}` (raw boolean) → `TypeError` at construction
  (case H);
- `REOPEN_CANDIDATE` → retrieved;
- `CONDITION_UNKNOWN` and `OPERATOR_REVIEW_REQUIRED` → never auto-retrieve.

Evidence: `raw_true_boolean_cannot_bypass_reopen_evaluator`,
`retriever_accepts_governed_reopen_evaluation`,
`condition_unknown_does_not_retrieve`,
`operator_review_required_does_not_auto_retrieve`.

The archive-is-not-memory property (G4 §13) is preserved: a dormant record
absent from default context is retrieved when its governed evaluation fires
(`test_dormant_record_reactivates_via_reopen_despite_absence`, upgraded to
evaluator semantics).

# G4R_NEGATIVE_KNOWLEDGE_INTEGRITY_AUDIT — permanence cannot be spoofed

## Structural unforgeability (G4R-08)

`NegativeKnowledgeRecord.is_permanent` is now a **validated property**: a
record is permanent only when the full governed `permanence_authority` block
exists and validates:

- `actual_level == "OPERATOR"` (never a payload string — the actual
  `AuthorityState.level(actor)` is read);
- `binding == "EXACT_AUTHORITY_STATE"`;
- non-empty `authority_basis` that equals the permanent flag;
- non-empty `ratification_ref`.

Consequences:

- `nk.permanent_by_operator_authority = "FAKE"` alone → `is_permanent is
  False`, `permanence_violation()` returns a reason, and
  `validate_for_suppression()` raises (case D).
- Deserialization (`NegativeKnowledgeRecord.from_dict`) validates the block and
  rejects fabricated permanence.
- A permanence string without the authority block is structurally invalid.
- A WORKER-level authority block is rejected.

Evidence: `direct_permanence_assignment_cannot_create_valid_permanence`,
`deserialized_fake_permanent_record_rejected`,
`permanent_string_without_authority_block_rejected`,
`non_operator_authority_block_rejected`,
`valid_operator_permanence_roundtrip_succeeds`.

## Schema agreement (G4R-09)

`schemas/negative-knowledge-record.schema.json` now has:

- `permanence_authority` with **required** `actor`, `actual_level`,
  `authority_basis`, `ratification_ref`, `binding`;
- `actual_level` enum `["OPERATOR"]`, `binding` enum
  `["EXACT_AUTHORITY_STATE"]`, `minLength: 1` on basis/ratification;
- an `allOf` conditional: whenever `permanent_by_operator_authority` is
  non-null, `permanence_authority` is required.

Schema and Python validation agree — verified by
`test_schema_requires_permanence_block_when_flag_set` (valid roundtrip passes;
missing block and WORKER level both fail jsonschema validation).

## Governed M4 reactivation (G4R-07)

S10's M4 path no longer calls `LifecycleEngine.transition()` with raw strings.
Memory/reopen-driven mutations route through `GovernedTransitionExecutor`
with a real `AuthorityState`:

- `reopen_driven` lifecycle mutations require a GOVERNOR-level registered
  actor (`M4_APPLY_ROLES`); the memory system proposes, it cannot apply.
- A WORKER actor → `ROLE_NOT_AUTHORIZED`; a payload claiming `GOVERNOR` while
  the actor is WORKER → `AUTHORITY_LEVEL_MISMATCH`; an unregistered component
  (e.g. `MEMORY`) → `AUTHORITY_ACTOR_UNKNOWN`.
- A GOVERNOR bound to AuthorityState may apply DORMANT→REACTIVATED→CANDIDATE;
  the direct DORMANT→ACTIVE shortcut stays forbidden (edge table + RULE-10).

Evidence: `worker_cannot_apply_reactivation`,
`spoofed_governor_string_rejected`, `memory_component_cannot_apply_m4_transition`,
`governor_actor_bound_to_authority_can_apply_legal_reactivation`,
`reopen_candidate_without_authority_remains_unapplied` (case I).

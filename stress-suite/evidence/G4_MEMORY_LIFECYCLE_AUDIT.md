# G4 — Memory Lifecycle Audit

## Separation of concerns (G4 §2)
`KnowledgeActivationState` holds four independent axes: M4 lifecycle state, memory/storage tier, retrieval relevance, and an explicit `canonical_truth_note`. The invariant "M4 lifecycle != memory tier != retrieval relevance != canonical truth" is enforced:

- A historically ACTIVE M4 object may live in `ARCHIVAL_STORE` (`test_m4_state_legal_with_archival_tier`).
- A DORMANT M4 object may be retrieved temporarily into active reasoning context for a reopen evaluation (`test_dormant_record_reactivates_via_reopen_despite_absence`).
- Unknown memory tiers are rejected at construction.

## Epistemic metabolism (G4 §3)
`run_metabolism_pipeline` stages INGEST → CONSOLIDATE → COMPRESS → PROMOTE/DEMOTE (delegated to the governed M4 path; memory performs no truth change) → ACTIVATE/DORMANT → ARCHIVE → RETRIEVE/REOPEN. No stage deletes provenance:

- `test_compaction_never_deletes_provenance` — 15 compressed objects stay in the index as DORMANT_STORE with their original provenance pointers intact.
- `test_compaction_record_keeps_reconstruction_pointer` — every `MemoryCompactionRecord` carries provenance + reconstruction pointers + policy version.

## Pruning without erasure (G4 §14)
Compaction moves objects between tiers; nothing is physically deleted. `MemoryCompactionRecord` records refs, reason, destination tier, summary, provenance/reconstruction pointers, epoch and policy version.

## Bounded active context (G4 §10–12)
`MemoryRetriever.build_context` selects by task need (required refs, dependency refs, tag relevance), never by institutional age:

- 50,000 knowledge/evidence objects + 5,000 experiment records + 12 relevant → **12 active, recall 1.0, stale intrusion 0, growth ratio 0.00022** (`test_fifty_k_history_bounded_active_context`).
- Archive 5k vs 50k with identical relevant set → identical bundle (`test_archive_growth_does_not_grow_active_context`).
- 1k / 10k / 50k scaling metamorphic → identical active-context count (`test_context_scaling_metamorphic`).
- Same inputs → byte-identical bundle fingerprint (`test_same_inputs_byte_identical_bundle_fingerprint`).

## Retrieval provenance (G4 §23)
Every selected object carries a `RetrievalTraceEntry` with policy, reason, trigger ref, memory tier and epoch. Dormant objects retrieved via reopen are tagged `REQUIRED_DORMANT_REOPEN`; archival reconstructions `REQUIRED_ARCHIVAL_RECONSTRUCT` — a retrieved historical object always explains why it entered context.

## Archive is not memory (G4 §13)
`test_dormant_record_reactivates_via_reopen_despite_absence` proves a record absent from default active context is retrieved when its reopen condition fires — institutional memory is behavioral retrievability, not mere disk presence.

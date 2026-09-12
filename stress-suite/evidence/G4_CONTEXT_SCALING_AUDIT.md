# G4 — Context Scaling Audit

## Core acceptance (G4 §11)
> Increasing total history 10x should NOT increase default active context 10x.

| history size | experiments | total objects | active context | required recall | stale intrusion |
|---|---|---|---|---|---|
| 1,000 | 100 | 1,112 | 12 | 1.0 | 0 |
| 10,000 | 1,000 | 11,012 | 12 | 1.0 | 0 |
| 50,000 | 5,000 | 55,012 | 12 | 1.0 | 0 |

`test_context_scaling_metamorphic` asserts the active-context count is IDENTICAL across 1k/10k/50k; `test_archive_growth_does_not_grow_active_context` asserts the selected-object set is identical between 5k and 50k archives. Active context scales with TASK NEED (12 required refs, budget 12), not with institutional age.

## Hyperthymesia guard (S12)
- `test_fifty_k_history_bounded_active_context` — 55,012 objects generated deterministically; `active_context_objects <= budget`, `required_object_recall == 1.0`.
- `test_required_objects_all_retrieved` — every required ref present in the bundle.
- `test_same_inputs_byte_identical_bundle_fingerprint` — deterministic, wall-clock-free, model-free.

## Dormant reactivation under load
`test_dormant_record_reactivates_via_reopen_despite_absence` — among 100 dormant objects, the one whose reopen condition fires is retrieved into context with rationale (`REQUIRED_DORMANT_REOPEN`) even though it was absent from default active context. Archive is not memory.

## Explicit archival reconstruction
`test_archival_object_reconstructs_explicitly` — archival objects are reconstructed only when the activation rules explicitly permit (`allow_archival_reconstruct`) AND the reopen condition fires; otherwise they remain listed as archival refs.

## Compaction does not erase
`test_compaction_never_deletes_provenance` — 15 compressed objects remain in the index (DORMANT_STORE) with original provenance pointers; `MemoryCompactionRecord` entries carry provenance + reconstruction pointers; `provenance_intact=True` in the metabolism report.

## No scalar
No single MEMORY_SCORE or effective-independent-agent scalar is minted anywhere in S12. The bundle exposes the vector: total historical objects, active context objects, required recall, stale intrusion, omitted-but-recoverable, growth ratio, and the full retrieval trace.

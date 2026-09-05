# G4 — Epoch Reconstruction Audit

## AMB-12 status
AMB-12 is **not** constitutionally resolved. G4 introduces `PROVISIONAL_EPOCH_RECONSTRUCTION_CONTRACT` (status `PROVISIONAL_TEST_CONTRACT`) naming the 17 required reconstruction surfaces. At G4 completion AMB-12 becomes `EMPIRICALLY_TESTED_PROVISIONAL_CONTRACT` — empirically tested, subject to ratification (`test_amb12_stays_provisional`).

## Sealed snapshots (G4-P0-D)
- `test_sealed_epoch_blocks_nested_mutation` — after seal, in-place nested mutation on attribute reads has no effect (reads return deep copies) and direct attribute assignment raises.
- `test_sealed_epoch_blocks_pre_seal_alias_mutation` — lists/dicts referenced before seal are deep-copied at seal; mutating the original alias cannot reach the manifest.
- `test_sealed_epoch_fingerprint_stable` — frozen fingerprint, stable across re-reads and JSON round-trip + re-seal.
- `test_future_epoch_does_not_alias_predecessor` / `test_historical_epoch_never_rewritten_by_successor` — successors derive via `successor_of` from deep copies; mutating E19 cannot reach E18/E17.

## Reconstruction (S13)
- `test_sealed_epoch_reconstructs_from_canonical_artifacts` — all required surfaces resolve from the sealed manifest; `runtime_native_memory_used=False`.
- `test_replacement_runtime_has_zero_private_memory` — the mock replacement runtime with zero runtime-native memory reconstructs the epoch state from canonical artifacts only.
- `test_runtime_rename_does_not_alter_semantic_fingerprint` — `RECONSTRUCTION_SEMANTIC_FINGERPRINT` is identical for RUNTIME_A vs RUNTIME_B; the runner also asserts `runtime_rename_semantic_stable` for the whole chain.
- `test_current_runtime_does_not_overwrite_historical_identity` — reconstruction never writes the current runtime into the sealed historical manifest; historical runtime certifications (`Hermes`, `OpenClaw`) survive.

## Fail-closed missing surfaces
- `test_missing_required_artifact_fails_closed` — removing the authority snapshot → `success=False`, `authority_state_snapshot` listed as missing, note `FAIL_CLOSED: required canonical surface(s) missing; no guessed defaults`.
- `test_missing_negative_knowledge_fails_closed` — stripping the negative-knowledge ref → `negative_knowledge_refs` reported missing.

## Reconstructed content
- `test_authority_state_reconstructed_exactly` — `{"GOVERNOR": "GOVERNOR"}` preserved.
- `test_m4_and_negative_and_unresolved_surfaces_reconstructed` — active/dormant knowledge projections, negative-knowledge refs and unresolved-pattern refs all resolve.
- `test_historical_runtime_certifications_retained` — certifications survive as historical facts in the report and in the historical epoch fingerprint.

## Epoch chain integrity (G4 §21)
- `test_epoch_chain_acyclic_and_sealed` — E17→E18→E19: acyclic, all sealed, predecessors resolved, `pass=True`.
- `test_predecessor_missing_detected` — E18 referencing missing E17 → explicit reconstruction gap reported.
- `test_epoch_cycle_fails_closed` — E17↔E18 cycle detected; `acyclic=False`.

## Current vs historical truth (G4 §22)
Reconstruction preserves `HISTORICAL_CANONICAL_STATE` without promoting it to current canonical state (explicit report note). S10 depends on exactly this distinction: historical validity is restored into context but never treated as current validation — the record must pass through REACTIVATED → CANDIDATE for renewed evaluation.

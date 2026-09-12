# G4R_RECONSTRUCTION_REALITY_AUDIT — reconstruction resolves, it never synthesizes

## Canonical artifact registry (G4R-11)

`CanonicalArtifactRegistry` holds ACTUAL pre-existing canonical fixture
artifacts — sealed manifests, evaluation contracts, lifecycle contracts,
ontologies, high-dependency assumptions, runtime/capability certifications,
authority snapshots, knowledge records, negative-knowledge records, unresolved
patterns, validation rules, operator ratifications, transformation evidence
and reopen conditions. `EpochReconstructionBundle.for_manifest` derives
REFERENCES from the manifest's declared versions/ids; `reconstruct_epoch`
resolves them against the registry.

## No invention (G4R-12) — case E

A sealed manifest alone is never sufficient. Removing the external artifacts
(registry holds only the manifest) fails closed with every external surface
identified: evaluation_contract, lifecycle_contract, negative_knowledge_refs,
unresolved_pattern_refs, operator_ratifications, transformation_evidence,
authority_state_snapshot, active/dormant knowledge, validation_rules,
challenge_reopen_conditions, ontology/certification surfaces.

Evidence: `manifest_only_reconstruction_fails_when_external_surfaces_required`,
`evaluation_contract_ref_must_resolve`,
`lifecycle_contract_ref_must_resolve`,
`negative_knowledge_ref_must_resolve`,
`operator_ratification_ref_must_resolve`,
`transformation_evidence_ref_must_resolve`.

## Cross-artifact consistency (G4R-13) — case F

- Resolved evaluation/lifecycle contract `version` must match the manifest's
  declared version (id:version form); a V9.9 artifact under the V1.0 ref →
  invalid.
- The resolved `AUTHORITY_SNAPSHOT` artifact's fingerprint must equal the
  manifest's inline `authority_state_snapshot`; wrong content under the same
  id → invalid.
- Knowledge projection records must be epoch-compatible; a record registered
  for E99 cannot satisfy an E17 projection → missing.

Evidence: `wrong_version_artifact_fails`,
`wrong_epoch_knowledge_projection_fails`, `wrong_authority_snapshot_fails`,
`artifact_with_correct_id_wrong_fingerprint_fails`.

## Separate evaluation/lifecycle contracts (G4R-14)

`lifecycle_contract_version` is a distinct manifest field (schema 1.1.0); it
is never inferred from `evaluation_contract_version`. Old schema manifests
remain readable via dataclass defaults (no historical rewrite).

Evidence: `test_evaluation_and_lifecycle_contracts_are_separate`.

## Content validation (G4R-20)

Per-surface validators replace generic non-emptiness: an evaluation contract
must carry `contract_id` + `version` (+ version consistency), knowledge
records must carry `record_id`, operator ratifications `ratification_ref`,
transformation evidence `evidence_id`, reopen conditions `condition_id`. A
`{"foo": "bar"}` placeholder can never satisfy a contract surface.

Evidence: `test_reconstruction_validates_content_not_emptiness`.

## Runtime-native memory cannot qualify (G4R-15)

`EpochReconstructionReport.reconstruction_evidence_qualified` is True only
when all surfaces resolve AND `runtime_native_memory=False`. A native-memory
run still produces a diagnostic report (success=True) but is explicitly not
qualified; the S13 post-hoc expectation (`evaluate_g4_expectation`) uses the
qualified flag, and the runner's `runtime_rename_semantic_stable` invariant
holds regardless.

Evidence: `zero_runtime_memory_can_pass`,
`private_runtime_memory_run_not_qualified_for_s13`,
`runtime_name_rename_still_semantically_invariant` plus the upgraded
`test_replacement_runtime_has_zero_private_memory` (old assertion trusted
`success` alone — replaced; rationale in-file).

## Epoch chain + monotonic seal (G4R-10, §21)

Sealing is anchored to a frozen internal snapshot: `_sealed` cannot be toggled
off, the fingerprint cannot be overwritten, and even forcing `_sealed=False`
via `object.__setattr__` cannot reopen the semantic snapshot (case J).
Predecessor chains stay acyclic; missing predecessors and cycles fail closed.

Evidence: `sealed_epoch_cannot_toggle_sealed_false`,
`sealed_epoch_cannot_overwrite_fingerprint`,
`sealed_epoch_semantics_stable_under_adversarial_internal_assignment`,
`successor_creation_still_works`, plus the existing chain tests in test_g4.py.

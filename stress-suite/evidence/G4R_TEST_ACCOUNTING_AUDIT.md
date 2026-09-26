# G4R_TEST_ACCOUNTING_AUDIT — exact reconciliation of the 458-vs-456 discrepancy

The G4 evidence receipt reports `prior_preserved = 458` while the accepted
pre-G4 baseline was **456**. G4R reconciles that arithmetic explicitly.

## Lineage

| stage | count | notes |
| --- | --- | --- |
| pre-G4 accepted baseline | **456** | verified at head `27ae2a5a` (G3R2 terminal) |
| G4-P0 additions (before the accounting snapshot) | **+2** | `test_negative_knowledge.py` gained two permanence tests (exact-AuthorityState binding) when the file was upgraded for G4-P0-C; these landed BEFORE the G4 receipt was written, so the receipt's `prior_preserved=458` is the count of *tests present at G4 start*, not a claim that the accepted 456 was wrong |
| G4 new tests | **+66** | `test_g4.py` (66 tests as recorded in the G4 receipt) |
| G4 total | **524** | 458 + 66 |
| G4R new regressions | **+75** | 74 in `tests/test_g4r.py` + 1 added to `test_g4.py` (`test_cross_scope_condition_fails_closed`) |
| G4R total | **599** | 524 + 75 |

## Legacy tests upgraded during G4R (none deleted, none weakened)

12 tests in `test_g4.py` were upgraded in place because their old assertions
embodied the very defects G4R corrects. Each documents old-assertion → defect
→ replacement → rationale in the file itself:

1. `_s10_pack` helper — conditions were subject/scope/evidence-unbound.
2. `_s11_pack` helper — same.
3. `_condition` helper — unbound conditions.
4. `test_suppression_ends_only_for_exact_scope` — now binds subject + scope.
5. `test_dormant_record_reactivates_via_reopen_despite_absence` — raw boolean
   `reopen_facts` → governed `ReopenEvaluation` (G4R-19).
6. `test_archival_object_reconstructs_explicitly` — same.
7. `_s13_pack` / `_s13_epoch` / `_s13_artifacts` — S13 now reconstructs from a
   pre-existing `CanonicalArtifactRegistry` (G4R-11/12); evaluation/lifecycle
   contract versions are separate (G4R-14).
8. `test_replacement_runtime_has_zero_private_memory` — old assertion trusted
   `success` alone; replacement asserts `reconstruction_evidence_qualified is
   False` for a runtime-native-memory run (G4R-15).
9. `test_missing_negative_knowledge_fails_closed` — manifest-only synthesis
   removed; registry-backed fail-closed (G4R-12).
10. `test_current_runtime_does_not_overwrite_historical_identity` —
    `for_manifest` + registry resolution.
11. `test_missing_required_artifact_fails_closed` — unchanged semantics,
    exercised through the registry path.
12. `test_runtime_rename_does_not_alter_semantic_fingerprint` — unchanged
    assertions, new registry-backed path.

## Why the arithmetic is honest

- No historical G4 receipt was rewritten to make the numbers prettier — this
  audit documents the +2 G4-P0 tests explicitly.
- The G4R receipt's `pre_g4 = 456` restates the accepted baseline and the
  full lineage; `g4_legacy_modified = 12` counts upgraded (not removed) tests.
- Every upgraded test's old assertion is preserved in a comment in the file;
  the replacement asserts strictly more.

## Final

pre_G4=456 · G4 delta=68 (2 G4-P0 + 66 new) → 524 · G4R new=75 → **599/599**.

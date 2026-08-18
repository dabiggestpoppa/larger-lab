# PFT — Change Control

Status: RATIFIED (PFT-B0-PROGRAM-CONSTITUTION)

## Rules

1. Completed runs and sealed artifacts are never edited or deleted.
2. A repaired implementation becomes `GEN + 1` with:
   - `parent_generation`
   - `reason`
   - `files_changed`
   - `defect_class`
3. Bugged runs are marked `INVALIDATED` (or `SUPERSEDED` when a
   replacement generation exists); they remain in the run registry.
4. Artifact JSON files under `program/` are regenerated from the code
   registry (`program_registry.py`) or from their append-only sources;
   existing entries are never modified.
5. The data-usage ledger is append-only JSONL
   (`DATA_USAGE_LEDGER.jsonl`); `DATA_USAGE_LEDGER.json` is the validated
   consolidated artifact regenerated from it.

## Current generation anchor (B0)

    spec_gen    = PFT-SPEC-GEN-001   (sealed at B1)
    data_gen    = PFT-DATA-GEN-001   (sealed at B2)
    engine_gen  = PFT-ENGINE-GEN-001 (sealed at B3)
    cost_gen    = PFT-COST-GEN-001   (not yet created; execution/cost layer is later)
    exec_gen    = PFT-EXEC-GEN-001   (not yet created)

Generation ids are reserved at B0 and populated by the checkpoint that
seals their content.

## Change log

| Generation | Reason | Files | Defect class |
|---|---|---|---|
| B0 | ratify program constitution | program/*, governance/*, tests | N/A (initial) |
| B0.1-doc | B0 REPORT.md displayed pytest count as 0 (junit parser read the outer `<testsuites>` element; counts live on `<testsuite>`). Actual B0 evidence: 48 tests, 0 failures. B0 gate conclusion (PASS) is unaffected; only the human-readable count was misreported. Parser fixed in `evidence.py` (single canonical path); the committed B0 REPORT.md is left untouched per immutability. | evidence.py, build_b0_artifacts.py, build_b1_artifacts.py | DOCUMENTATION / evidence-display defect |
| B1.1 | B1 source/artifact consistency defect: the B1 commit staged `SPEC_REGISTER.json` generated from the richer working-tree registry (species `spec_files`/`spec_status` = LINEAGE_SEALED_AT_B1 / FROZEN_MACHINE_SPEC_SEALED_AT_B1; formula-register validation requiring `implementation_target`/`test_target`/`failure_behavior`) while `program_registry.py`/`schemas.py` lagged (`TBD (B1 registers lineage)` placeholders; weak validation). Committed B1 tree still passed its 69 tests because no test exercised the richer fields, but source and artifact disagreed. Repair: commit the two source files to match the already-sealed artifacts. No spec content changes; no artifact regeneration required (artifacts are already rich). B1 gate conclusion (PASS) is unaffected. | program_registry.py, schemas.py, CHANGE_CONTROL.md | SOURCE/ARTIFACT CONSISTENCY defect (staging miss) |
| B3.1 | Implementation-bug repairs inside B3 (allowed by build prompt section 43: repair only clear implementation bugs that do not change the frozen specification): (1) `k3.beta1_of_complex` used `all(bool)` on a single boolean (TypeError) when counting 3-cliques - fixed to a plain boolean conjunction; (2) test expectations corrected: DMD same-angle DeltaPhi asserted as exact 0.0 but reconstruction noise gives ~1e-15 (now `approx(0, abs=1e-12)`), and the leg-stop multi-trigger ban window was off by one (12 completed bars after the last trigger at t=25 bans slots 25..36, not 25..37). Engine behavior unchanged; all 177 tests pass. | engine/k3.py, test_reference_fixtures.py, test_causality.py | IMPLEMENTATION BUG / TEST EXPECTATION defect |

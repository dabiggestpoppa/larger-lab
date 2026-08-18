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

# PFT-B4 — A0 Genesis RAW Reconstruction + Economic Baseline
## Final Report

**Checkpoint**: PFT-B4-A0-GENESIS-RAW
**Date**: 2026-08-26
**Decision**: A0_SPEC_NOT_RECOVERABLE

---

## TRADER REVIEW

### 1. What exactly was A0?

A0 was described in PROGRAM_PLAN.md as the "original agent formulation" of the oil-driven cross-asset transmission system. It is preserved as a historical raw specimen, distinct from A1 (Deepers v2.2).

### 2. Was the original specification fully recoverable?

**NO.** The original A0 specification was NOT found in the repository.

The only A0-related file that exists is `a0_genesis/spec/LINEAGE.md`, which contains:
- Registration metadata
- Preservation rules
- A statement that "The full A0 specification text is retained with the original agent artifacts"

The "original agent artifacts" referenced in LINEAGE.md are NOT in the git repository history.

### 3. How is it different from A1 Deepers v2.2?

**Cannot be determined.** Without the A0 specification, we cannot compare A0 to A1.

A1 (Deepers v2.2) is fully specified with:
- 19 formulas registered in FORMULA_REGISTER.json
- Full machine-readable spec in SPEC_A1_V2_2.json
- Detailed markdown in SPECIFICATION_V2_2.md
- 52 parameters registered in PARAMETER_REGISTER.json

### 4. Does A0 actually activate on real data?

**CANNOT BE DETERMINED.** The specification does not exist in the repository.

### 5. How often?

**N/A**

### 6. Does it generate trades naturally?

**N/A**

### 7. Does it make money before and after costs?

**N/A**

### 8. Does it beat simple oil/transmission baselines?

**N/A**

### 9. Is performance stable by year?

**N/A**

### 10. Is the result concentrated?

**N/A**

### 11. What is the B4 decision?

**A0_SPEC_NOT_RECOVERABLE**

### 12. What does this imply for B5?

B5 (A1 Atomic Evidence) can proceed independently. A0 and A1 are separate research species. The inability to recover A0 does not invalidate A1.

---

## TECHNICAL

| Field | Value |
|-------|-------|
| branch | agent/deepers-strategy-foundry |
| SHA | f764f8b62f3cee8b923a1118d20903a9296ee41b |
| spec generation | NOT_APPLICABLE |
| data generation | NOT_APPLICABLE |
| engine generation | NOT_APPLICABLE |
| cost generation | NOT_APPLICABLE |
| execution generation | NOT_APPLICABLE |
| source hashes | N/A (no spec found) |
| development dates | N/A |
| activation counts | N/A |
| trade counts | N/A |
| scorecard | N/A |
| baseline deltas | N/A |
| bootstrap intervals | N/A |
| causality result | NOT_APPLICABLE |
| test count | 0 (no A0-specific tests added) |
| decision | A0_SPEC_NOT_RECOVERABLE |

---

## EXPLICIT DECLARATIONS

```json
{
  "optimization_performed": false,
  "confirmation_consumed": false,
  "holdout_consumed": false,
  "production_authorized": false,
  "next_checkpoint_authorized": false
}
```

---

## RECOVERY AUDIT

### Search Performed

1. **Git History**: Searched all commits on all branches for A0 specification files
2. **File System**: Examined all files under `quant-lab/research/strategy_foundry/pft/a0_genesis/`
3. **Formulas**: Checked FORMULA_REGISTER.json - contains only A1 formulas (prefixed `A1.F`)
4. **Parameters**: Checked PARAMETER_REGISTER.json - contains only A1 parameters (prefixed `A1.F`)
5. **SPEC_REGISTER.json**: Shows A0 status as "SPECIMEN_REGISTERED" with only LINEAGE.md

### Files That Exist

- `a0_genesis/spec/LINEAGE.md` - Registration only, no specification

### Files That Do NOT Exist

- `a0_genesis/spec/SPEC_A0_GENESIS.json`
- `a0_genesis/spec/SPECIFICATION_A0_GENESIS.md`
- `a0_genesis/artifacts/*` (none)

### Conclusion

The A0 Genesis specification was never committed to the repository. The LINEAGE.md references external "original agent artifacts" that are not in the git history. Without the specification, A0 cannot be implemented.

**Per Section 5 of the B4 checkpoint**: "If the original A0 specification cannot be recovered sufficiently to implement without invention: STOP."

**STOP FOR HUMAN REVIEW.**

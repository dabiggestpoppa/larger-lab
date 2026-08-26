# A0 Genesis — Source Inventory

**species_id**: PFT-A0-GENESIS
**evidence_class**: RECOVERY_AUDIT
**checkpoint**: PFT-B4-A0-GENESIS-RAW
**date**: 2026-08-26

## Recovery Status: A0_SPEC_NOT_RECOVERABLE

### Search Summary

The original A0 Genesis specification was **NOT FOUND** in the repository. The recovery audit below documents the exhaustive search.

### Repository Files Examined

| Path | Status | Notes |
|------|--------|-------|
| `quant-lab/research/strategy_foundry/pft/a0_genesis/spec/LINEAGE.md` | EXISTS | Only contains lineage metadata, not the specification |
| `quant-lab/research/strategy_foundry/pft/a0_genesis/spec/SPEC_A0_GENESIS.json` | NOT FOUND | Was expected to be created at B4 |
| `quant-lab/research/strategy_foundry/pft/a0_genesis/spec/SPECIFICATION_A0_GENESIS.md` | NOT FOUND | Was expected to be created at B4 |
| `quant-lab/research/strategy_foundry/pft/a0_genesis/artifacts/*` | NOT FOUND | No artifacts exist |

### Git History Search

| Commit | Date | Description | A0 Content? |
|--------|------|-------------|-------------|
| `99b69600` | 2026-08-18 | PFT-B1: seal A0 A1 Q0 specifications | Only created LINEAGE.md |
| `22539363` | 2026-08-18 | PFT: ratify Deepers v2.2 pre-build research plan | Created SPECIFICATION_V2_2.md (A1 only) |
| `1941ec9d` | 2026-08-18 | PFT-B0: ratify program constitution | No A0 specification |

### Lineage Analysis

The LINEAGE.md states:

> "The full A0 specification text is retained with the original agent
> artifacts. Its exact machine-readable form is sealed at PFT-B4 when A0
> evidence work begins."

**Interpretation**: The "original agent artifacts" are NOT in this repository. They may exist in:
1. External conversation history (not committed to git)
2. Agent memory files (not version-controlled)
3. Other repositories or locations

### What Was Found

- **A1 (Deepers v2.2)**: Fully specified in `SPECIFICATION_V2_2.md` and `SPEC_A1_V2_2.json`
- **A0 (Genesis)**: Only a LINEAGE.md registration file exists

### Critical Difference Between A0 and A1

Based on the PROGRAM_PLAN.md:
- **A0**: "original agent formulation" - Historical lineage preserved intact
- **A1**: "final Deepers Specification Closure v2.2" - Primary RAW model

The SPEC_REGISTER.json shows:
```json
"A0-GENESIS": {
  "status": "SPECIMEN_REGISTERED",
  "spec_status": "LINEAGE_SEALED_AT_B1",
  "spec_files": ["quant-lab/research/strategy_foundry/pft/a0_genesis/spec/LINEAGE.md"]
}
```

This confirms A0 was registered but the actual specification was never committed.

### Conclusion

The A0 Genesis specification **CANNOT BE RECOVERED** from the repository. Per Section 5 of the B4 checkpoint:

> "If the original A0 specification cannot be recovered sufficiently to
> implement without invention: STOP."

**Decision**: A0_SPEC_NOT_RECOVERABLE

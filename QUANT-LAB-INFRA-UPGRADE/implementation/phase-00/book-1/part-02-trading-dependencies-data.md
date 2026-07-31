# Part 2 — Trading Census, Dependencies, and Data Metadata

## Goal

Extend Part 1 with an observable-form census of trading files, dependency manifests, native/runtime requirements, and bounded metadata for data and result files.

## Inputs

- Verified Part 1 component IDs and repository fingerprint
- projects/trading/
- Root and subproject dependency manifests
- Data and artifact paths

## Allowed Changes

- tools/forge/
- tests/forge/phase_00/
- QUANT-LAB-INFRA-UPGRADE/implementation/phase-00/book-1/
- artifacts/forge/phase-00/book-01-part-02/

## Required Behavior

- Tag observable imports and behaviors without assigning the Book 3 operational class.
- Hash and identify dependency files without merging constraints.
- Bound file reads by type and size.
- Mark symbol, timeframe, timezone, adjustment, provenance, and reproduction state unknown unless evidenced.
- Preserve generated/source and tracked/untracked distinctions.

## Test Obligations

- P0-DAT-001 metadata-only safety
- Bounded large-file sampling
- Trading file belongs to one component
- Dependency manifest identity reproducibility
- Unknown metadata remains unknown

## Exit

Part 2 closes when the trading census, dependency inventory, and data inventory reproduce from the Part 1 fingerprint without modifying source data or dependencies.

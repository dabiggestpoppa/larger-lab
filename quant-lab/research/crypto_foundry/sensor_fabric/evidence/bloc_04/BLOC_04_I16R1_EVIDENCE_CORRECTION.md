# BLOC_04_I16R1_EVIDENCE_CORRECTION

**Checkpoint:** SENSOR-B4-I16R1 — G4-13 SOURCE-UNIT HANDOFF CONTRACT REPAIR
+ FINAL GOVERNANCE CORRECTION
**Start head (mandatory):** `618de97827a22b2514caa4178d5cffa4ea76d1b7`
**Branch:** `agent/crypto-sensor-fabric-build`
**Nature:** append-only correction + additive repair. No I16 artifact is
rewritten.

---

## 1. Governance correction (§2 of the I16R1 mandate)

Historical I16 recorded, in
`BLOC_04_I16_FINAL_ACCEPTANCE_EVIDENCE.md` and ledger section 148:

```
BLOC_04_FINAL_VERDICT = I16_G4_13_UNIT_HANDOFF_CONTRACT_GAP
```

That field is NOT in the frozen final-verdict vocabulary (§2/§36 of the I16
mandate). It is preserved as history and corrected here:

```
gap_id                       = I16_G4_13_UNIT_HANDOFF_CONTRACT_GAP
blocking_reason              = G4-13 UNIT evidence not publicly reachable
historical_I16_final_verdict_field
                             = NONCANONICAL / SUPERSEDED_BY_I16R1_CORRECTION
```

The frozen final-verdict vocabulary remains ONLY:

```
PASS_BLOC_04_IMPLEMENTED
PASS_BLOC_04_IMPLEMENTED_WITH_DATA_VOLUME_LIMITS
BLOCKED_BLOC_04_INTEGRITY
BLOCKED_BLOC_04_STORAGE_CAPACITY
FAIL_BLOC_04_ATOMICITY
FAIL_BLOC_04_LINEAGE
FAIL_BLOC_04_RESTORE
```

## 2. Timestamp wording correction (§18)

I16's readiness artifact listed `actual_start` / `actual_end` among fixture-
absent facts. The corrected statement, measured at the R1 head through the
public acquisition contract:

| Fact | FIELD_PUBLICLY_AVAILABLE | FIXTURE_VALUE_PRESENT |
|------|--------------------------|-----------------------|
| `actual_start` | true | false (standard fixture) |
| `actual_end` | true | false (standard fixture) |

These are public, typed `AcquisitionRecord` fields; this fixture simply left
their values unset. They are NOT structurally unavailable. No production
change was needed for this correction, and none was made.

`provider_time_raw`, `provider_time_parsed`,
`provider_time_unit_assumption` and `provider_publication_time` remain
structurally absent from the public acquisition contract. That is recorded,
not repaired.

## 3. Gap closure — what was wrong and what changed

Measured at I16: `RawNormalizationBatch` had no public source-unit
field/state, `Bloc5Handoff.to_batch()` did not populate unit evidence, and no
public unit-state vocabulary existed, so a public Bloc 5 consumer could not
determine native unit semantics without provider/private knowledge.

Repair, smallest additive shape justified by the §4 family audit
(`BLOC_04_I16R1_UNIT_SEMANTIC_AUDIT.json`):

| Layer | Change |
|-------|--------|
| `storage.enums` | NEW `SourceUnitState`: `VERIFIED_NATIVE` / `UNIT_UNVERIFIED` |
| `storage.models` | NEW `SourceUnitEvidence` (`field_name`, `native_unit_lexeme`, `state`) with fail-closed validators; `RawNormalizationBatch.source_unit_evidence` (additive, default empty, canonical order, duplicates rejected) |
| `storage.projection_schema` | `ProjectionSchemaDefinition` additive durable `source_unit_evidence` declarations; included in the schema fingerprint when present; validated on registry reload; historical descriptors load under the historical contract |
| `storage.replay` | `Bloc5Handoff.to_batch` resolves the durable schema and copies the declarations verbatim; unresolvable schema fails closed (`ProjectionSchemaUnsupported`) |
| `storage.__init__` | public exports: `SourceUnitState`, `SourceUnitEvidence` |

Durable authority trace: the declarations live in the registered
`ProjectionSchemaDefinition` (durable JSON catalog under the T0 root); the
projection writer requires the rows' exact field set to equal the registered
provider-native schema and the artifact commit re-reads the physical Parquet
schema for exact equality against it, so the declaration is bound to the
durable physical rows. Bloc 4 still decides no canonical unit, multiplier,
USD notional, base/quote or `effective_at`.

## 4. I16 artifact custody (§20/§27)

`BLOC_04_I16_G4_GATE_MATRIX.json`, `BLOC_04_I16_BLOC4_READINESS.json`,
`BLOC_04_I16_FINAL_ACCEPTANCE_EVIDENCE.md` and every other `BLOC_04_I16_*`
artifact are preserved byte-for-byte. After the full regression runs the
entire evidence directory was re-hashed and compared: **diff = ZERO**
(235 `.json`/`.md` files; the only authorized republication in the whole
checkpoint is `BLOC_04_I11R2_GOVERNANCE_BINDING_AUDIT.json`, regenerated per
§40 because I16R1 added tracked Python files — a one-line change,
`python_files_scanned` 1001 → 1005).

The old I16 G4-13 current-tree test is converted into a write-free
checkpoint-fossil validator (`test_i16_g4_13_readiness.py`) that validates
the committed I16 negative record and never re-measures the repaired tree;
the positive remeasurement lives in `test_i16r1_g4_13_positive.py`.

## 5. G4-13 positive remeasurement (§19)

| Dimension | Result | Evidence |
|-----------|--------|----------|
| SOURCE | PASS | batch fields: provider, venue, sensor_family, native_instrument, granularity, schema id/version, parser version |
| TIME | PASS | batch logical range + acquisition facts + manifest date_basis; §18 correction recorded |
| UNIT | PASS | known case: `VERIFIED_NATIVE` + provider-native lexeme; unknown case: `UNIT_UNVERIFIED` + null, zero guessed values even with unit string present in bytes and rows; multi-field case: two entries in canonical order |
| LINEAGE | PASS | batch -> acquisition -> blob -> projection -> revision, public repositories only |
| PATH_INDEPENDENCE | PASS | two unrelated roots -> identical public view, no absolute path |
| NEGATIVE_IMPORT | PASS | consumer imports only `crypto_sensor_fabric.storage` (+ `__future__`, `typing`); 0 traversal calls, 0 private APIs, 0 absolute roots |

## 6. Final verdict

All 13 G4 gates measured PASS at the repaired head (G4-10 with its stated
environment limitation, preserved) — see
`BLOC_04_I16R1_G4_GATE_MATRIX.json`. No frozen blocking condition remains:
all 11 conditions measure NOT PRESENT in
`BLOC_04_I16R1_BLOCKING_CONDITION_AUDIT.json` (condition 11, "Bloc 5 needs
provider-specific filesystem knowledge", was the only PRESENT condition at
I16 and is closed).

Volume classification (§23): no accepted scale ceiling affects supported use.
The reviewed resource evidence — 10,000-row actual manifest scan (0 invalid,
deterministic, bounded memory), 1 GiB-equivalent streaming hash, 64
MiB-equivalent T0A streaming write, content dedupe, DuckDB many-projection
rebuild, revision-chain scale, query result bounds and the export ceilings —
measures configurable operational guardrails, not an unsupported ceiling.
Therefore `PASS_BLOC_04_IMPLEMENTED` rather than
`PASS_BLOC_04_IMPLEMENTED_WITH_DATA_VOLUME_LIMITS`.

```
BLOC_04_FINAL_VERDICT = PASS_BLOC_04_IMPLEMENTED
```

Failure-mode vocabulary was not used: no integrity, capacity, atomicity,
lineage or restore failure was observed at this head.

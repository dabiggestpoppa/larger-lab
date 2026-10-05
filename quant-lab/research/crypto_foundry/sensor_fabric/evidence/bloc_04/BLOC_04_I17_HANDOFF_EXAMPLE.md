# BLOC_04_I17_HANDOFF_EXAMPLE

**Checkpoint:** SENSOR-B4-I17 — end-to-end Bloc 4 -> Bloc 5 handoff example
**Start head:** `fb813728f32d6e518ed9911470388aec24c1e83e`
**Data:** COMMITTED OFFLINE supported-family fixtures. `network_calls = 0`.
No live provider, no live network, no live database.
**Stop point:** before any normalization.

This example exists so a future Bloc 5 implementer can see the *shape* of the
handoff and the *exact point* where its own decisions begin. Every value below
is real output from the committed tree, not illustrative pseudo-data.

---

## 0. The example driver

Run untracked, outside the worktree, so I17 adds no Python source at all:

```python
# .bu_tmp/i17_handoff_example.py  (documentation driver, NOT repo source)
# Run from quant-lab/:  PYTHONPATH=src python ../../../.bu_tmp/i17_handoff_example.py
#
# It imports ONLY public crypto_sensor_fabric.storage names for the handoff:
#     Bloc5Handoff, RawEvidenceQuery, SourceUnitContract, SourceUnitEvidence,
#     SourceUnitState, SourceUnitVariability, ProjectionUnitEvidenceConflict
# The Lake/stack helpers are the ALREADY-ACCEPTED test harness
# (tests/crypto_sensor_fabric/storage/test_i16r2_real_provider_units.py),
# reused verbatim so no new production or test source is introduced.
```

The flow is exactly:

```
query -> RawEvidenceResult -> Bloc5Handoff -> RawNormalizationBatch
      -> public source / time / unit / lineage inspection      [ STOP ]
```

---

## 1. CASE 1 — `MECHANICAL_TRADE`, `STATIC_VERIFIED`

Declared: `quantity_unit = "BTC"`, `state=VERIFIED_NATIVE`,
`contract=UNIT_EVIDENCE_DECLARED`. Real output:

```
-- QueryOutcome (public) --
   results=1 no_matching_evidence=False
-- RawEvidenceResult (public) --
   provider=FIXTURE_PROVIDER_A venue=FIXTURE_VENUE_A
   sensor_family=MECHANICAL_TRADE native_instrument=BTC-USDT-PERP
   source_granularity=1m
   logical_time_start=2026-01-15 00:00:00+00:00 logical_time_end=2026-01-15 23:59:00+00:00
   coverage_state=COMPLETE_SOURCE_BOUNDARY integrity_state=LOCAL_HASH_VERIFIED
   revision_state=STABLE
   acquisition_ids=['acq-real'] blob_refs=['c1db9a64...fe080']
   projection_refs=['proj-r1'] lineage_refs=['c1db9a64...fe080']
-- RawNormalizationBatch (public, 22 fields) --
   batch_id=batch-i17-trade  raw_rows_or_reader=descriptor://proj-r1
   projection_schema_id=i16r2.real.i17-trade
   projection_schema_version=1.0.0
   parser_version=1.0.0
   source_blob_refs=['c1db9a64...fe080']
   acquisition_refs=['acq-real']
   known_gap_intervals=[] history_boundary=ingested_at_max=2026-01-15T12:00:00+00:00
   quality_flags=[]
-- UNIT view (public typed evidence, no row scan) --
{
  "contract_state": "UNIT_EVIDENCE_DECLARED",
  "static_verified": [
    { "classification": "STATIC_VERIFIED", "field_path": ["quantity_unit"],
      "native_unit_lexeme": "BTC", "state": "VERIFIED_NATIVE", "variability": null }
  ],
  "unverified": [], "row_native_locations": [],
  "no_unit_bearing_fields": false, "historical_contract_absent": false,
  "guessed_values": [], "canonical_unit_decisions": 0,
  "schema_resolved": true,
  "resolved_schema_declaration_matches_batch": true,
  "resolved_contract_matches_batch": true
}
```

**What Bloc 5 receives:** a *proven* native lexeme `BTC` — every committed row
behind that projection said `BTC` at commit time — plus the full source/time/
lineage identity.
**What Bloc 5 still decides:** that `BTC` is a base-asset quantity, its
canonical asset identity, quantity conversion, notional, and `effective_at`.
`canonical_unit_decisions: 0` is printed by the view to make the boundary
explicit.

---

## 2. CASE 2 — `MECHANICAL_BOOK_SNAPSHOT`, `ROW_NATIVE` nested

Declared: two `UNIT_UNVERIFIED` + `ROW_NATIVE` locations with structural paths,
no lexemes. Real output:

```
   sensor_family=MECHANICAL_BOOK_SNAPSHOT native_instrument=BTC-USDT-PERP
   coverage_state=COMPLETE_SOURCE_BOUNDARY integrity_state=LOCAL_HASH_VERIFIED
-- UNIT view --
{
  "contract_state": "UNIT_EVIDENCE_DECLARED",
  "row_native_locations": [
    { "classification": "ROW_NATIVE_LOCATION",
      "field_path": ["asks", "item", "quantity_unit"],
      "native_unit_lexeme": null, "state": "UNIT_UNVERIFIED",
      "variability": "ROW_NATIVE" },
    { "classification": "ROW_NATIVE_LOCATION",
      "field_path": ["bids", "item", "quantity_unit"],
      "native_unit_lexeme": null, "state": "UNIT_UNVERIFIED",
      "variability": "ROW_NATIVE" }
  ],
  "static_verified": [], "unverified": [], "guessed_values": [],
  "resolved_schema_declaration_matches_batch": true
}
```

**What Bloc 5 receives:** *where* provider-native unit truth lives — two
structural paths, one per side, each resolving through an Arrow list element and
a struct child. No batch-level lexeme was fabricated.
**What Bloc 5 still decides:** the unit value of every individual level.

---

## 3. CASE 3 — `MECHANICAL_FUNDING`, `NO_UNIT_FIELDS`

Declared: `contract=NO_UNIT_FIELDS`, empty declaration list. Real output:

```
   sensor_family=MECHANICAL_FUNDING
-- UNIT view --
{
  "contract_state": "NO_UNIT_FIELDS",
  "entries": [],
  "no_unit_bearing_fields": true,
  "historical_contract_absent": false,
  "static_verified": [], "row_native_locations": [], "unverified": [],
  "guessed_values": [], "resolved_contract_matches_batch": true
}
```

**What Bloc 5 receives:** a *positive* declaration that this schema has no
unit-bearing field — explicitly different from a descriptor that predates the
unit contract (`historical_contract_absent: false` proves the marker was seen).

---

## 4. CASE 4 — the truth-bound gate is live

Same trade fixture, but declaring `quantity_unit = "ETH"` against rows that say
`BTC`:

```
CASE 4  STATIC CLAIM REFUSAL (the gate is live at commit time)
   REFUSED: ProjectionUnitEvidenceConflict
   conflict_class=MISMATCH declared_lexeme=ETH
   rows_inspected=1 null_count=0
   durable projections created=[]
```

The refusal happened **before** durable publication: `durable projections
created=[]`. This is the exact pre-repair counterexample that I16R2 froze, and
it still refuses at this head.

---

## 5. STOP POINT — what Bloc 5 has NOT been given

```
STOP POINT - what Bloc 5 has NOT been given, and must decide itself
   - canonical asset identity (venue/instrument reconciliation)
   - canonical units and quantity conversion (contract multipliers)
   - base/quote interpretation and USD notional normalization
   - effective_at / PIT canonical timestamps (absent from the batch by design)
   - interpretation of each ROW_NATIVE per-level unit value
   - resolution policy choice for ambiguous revisions
```

Everything above this line is Bloc 4 evidence, proven and typed.
Everything below it is Bloc 5's judgement, and none of it was guessed for you.

---

## 6. Why this example stops here

The handoff is **NORMALIZATION-READY EVIDENCE**, not normalized data. Making
this example "complete" by adding canonical units or an `effective_at` would
mean implementing Bloc 5 — which I17 is explicitly forbidden to do, and which
would destroy the very separation this checkpoint exists to freeze.

Read together with:
`BLOC_04_I17_BLOC5_HANDOFF_CONTRACT.md`,
`BLOC_04_I17_PUBLIC_INTERFACE_MATRIX.json`,
`BLOC_04_I17_NORMALIZATION_OWNERSHIP.json`,
`BLOC_04_I17_DOWNSTREAM_PROHIBITIONS.json`,
`BLOC_04_I17_KNOWN_LIMITATIONS.json`.
# BLOC_05_I01_IMPLEMENTATION_EVIDENCE

**Checkpoint:** SENSOR-B5-I01 — NORMALIZATION ENUMS / BASE MODELS / T1 ENVELOPE
**Branch:** `agent/crypto-sensor-fabric-build`
**Mandatory start head:** `ae152d010f3cd8c472c6dc0593a0e94f779cb079`
**Scope:** B5-I01 ONLY. B5-I02+ UNAUTHORIZED. Bloc 6 UNAUTHORIZED. Research FROZEN.

This document is **append-only** Bloc 5 evidence. It rewrites no Bloc 4
artifact, no I17 artifact and no ratification record.

> **This checkpoint is vocabulary and container, not normalization.** Nothing
> here resolves identity, derives a timestamp, converts a unit, writes T1 or
> answers a replay query. What it does is make the honest answers
> *representable* and the dishonest ones *refused*, so that the stages which
> will actually resolve them cannot quietly pick a convenient default.

---

## 1. What was added

### 1.1 Production code (3 files, `quant-lab/src/crypto_sensor_fabric/normalization/`)

| File | Role |
|---|---|
| `__init__.py` | deliberate public export surface + the boundary stated in prose |
| `enums.py` | ten frozen vocabularies + two read-only frozen correspondences |
| `models.py` | validated opaque identifier types, six base models, canonical JSON helper |

Per-file line counts and SHA-256 digests are recorded in
`BLOC_05_I01_SCOPE_AUDIT.json` (measured, not transcribed).

### 1.2 Tests (4 files, `quant-lab/tests/crypto_sensor_fabric/normalization/`)

| File | Layer | What it pins |
|---|---|---|
| `test_b5_i01_enums.py` | N0 | every frozen member set, exactly and in frozen order; deterministic string values; the two correspondence tables; no parallel vocabulary |
| `test_b5_i01_models.py` | N0 | 17 frozen validation laws, determinism, native preservation, provider/venue split, typed missingness, quarantine, lineage, flag ordering, null-vs-zero, stablecoin firewall |
| `test_b5_i01_public_api.py` | N0 | the public surface is exactly 24 names; private helpers stay private; every later-checkpoint name is absent |
| `test_b5_i01_scope_audit.py` | negative | forbidden modules, forbidden imports, no network, no filesystem/backend, no hashing/ID generation, matrix/source agreement |

### 1.3 Evidence artifacts (4 files, `.../evidence/bloc_05/`)

`BLOC_05_I01_TYPE_SCOPE_MATRIX.json`, `BLOC_05_I01_BASE_MODEL_MATRIX.json`,
`BLOC_05_I01_SCOPE_AUDIT.json`, and this document.

---

## 2. Implemented public enums

| Enum | Members | Frozen source |
|---|---|---|
| `PayoffType` | 5 | `bloc_05/01 §3` (+ F5) |
| `NormalizationStatus` | 8 | `bloc_05/03 §15` |
| `MissingnessReason` | 13 | `bloc_05/05 §12` |
| `NormalizationQualityFlag` | 36 | union of `05 §11` + `01 §14` + `02 §16` |
| `QualityDimensionState` | 6 | `bloc_05/05 §10` (+ `07 §6`) |
| `LineageState` | 3 | `bloc_05/05 §11`, `§23` inv. 7 |
| `QuarantineReason` | 7 | `bloc_05/05 §20` |
| `IntervalTimeConvention` | 4 | `bloc_05/02 §7` |
| `AvailabilityBasis` | 8 | `bloc_05/02 §5` |
| `TimestampPrecision` | 6 | `bloc_05/02 §8` |

Two frozen **correspondences** (read-only data, not behavior):
`BLOCKED_STATUS_MISSINGNESS_REASON` (MappingProxyType) and
`BLOCKING_QUALITY_FLAGS` (frozenset).

### 2.1 Two frozen spellings that were deliberately NOT collapsed

`bloc_05/03 §15` spells a blocked cause **`BLOCKED_IDENTITY`**;
`bloc_05/05 §12` spells the same concept **`IDENTITY_BLOCKED`**. Both are
implemented exactly as frozen, and the correspondence is stated as frozen data
instead of renaming one side. Collapsing them would make it impossible to tell a
*status* from a *missingness cause* — which is precisely the distinction the plan
draws.

### 2.2 The flag vocabulary is a union, not just the minimum

`bloc_05/05 §11` says "**Minimum** normalization flags". Its 4 identity and 4
time members are strict subsets of `01 §14` (10) and `02 §16` (10), so the enum
carries all 36. That is additive only: it can never remove a flag the directive
names. Declaration order is canonical (`05 §11` order, then the `01`/`02`
additions in their own document order) and the envelope *requires* that order,
so serialization cannot depend on a caller's iteration order.

### 2.3 Vocabularies consumed, never re-declared

`SensorFamily` (`contracts.enums`), `Granularity` (`probes.enums`),
`CoverageState`, `RevisionState`, `SourceUnitContract` and the
`SourceUnitEvidence` model itself (public `storage`). **Zero** upstream types
duplicated; **zero** private Bloc 4 symbols imported. This is asserted by a
test that intersects the normalization export set with the accepted 200-symbol
Bloc 4 public surface.

---

## 3. Implemented public models

| Model | Fields | Purpose |
|---|---|---|
| `ObservationTimeEnvelope` | 15 | the nine frozen canonical clocks plus interval convention, availability basis, precision, clock skew |
| `NativeQuantity` | 4 | one provider-native quantity; **no** canonical counterpart |
| `T1Quality` | 8 | the eight frozen quality dimensions |
| `T1LineageRef` | 7 | T1 → T0B → AcquisitionRecord → T0A blob SHA256 |
| `T1VersionContext` | 5 | registry/methodology version references |
| `T1BaseEnvelope` | 27 | the minimum generic T1 observation envelope |

Validated opaque identifier types (type only, **no algorithm**):
`OpaqueIdentifier`, `T1RecordId`, `ContractInstanceId`, `T1GenerationId`,
`RegistryVersion`.

Serialization helper: `canonical_json_bytes` — UTF-8, `sort_keys`, compact
separators, enum string values. It serializes; it never hashes.

---

## 4. T1 envelope fields

```
identity placeholders   t1_record_id (Optional), contract_instance_id (Optional),
                        provider, venue, native_instrument, provider_instrument_id
source identity         source_granularity (Granularity)
native event identity   native_event_id, native_sequence_id
generation / revision   normalization_generation, source_revision_id,
                        supersedes_t1_record_id, source_revision_state (RevisionState),
                        source_coverage_state (CoverageState)
sensor family           sensor_family (SensorFamily)
time                    time: ObservationTimeEnvelope
native values           native_values: tuple[NativeQuantity, ...]
status / absence        normalization_status, missingness_reason
quarantine              quarantine_reason, quarantine_evidence_refs,
                        quarantine_remediation
quality                 quality: T1Quality, quality_flags
lineage                 lineage_state, lineage: T1LineageRef
versions                versions: T1VersionContext
```

### 4.1 Fields deliberately Optional because nothing can populate them truthfully

` t1_record_id` has **no** deterministic generator until B5-I16, so a default
would be a fabricated identity. `contract_instance_id` may be absent while
identity is unresolved, blocked or native-only, and there is no
`UNKNOWN_CONTRACT` placeholder to stand in for it. Every clock in
`ObservationTimeEnvelope` is Optional because **no clock is derived at B5-I01** —
populating one would be invention. `time_semantics_version` is a slot, not a
requirement, because no time semantics exist yet.

---

## 5. Native / canonical separation

There is **no** `normalized_value`, `canonical_value`, `notional`,
`base_quantity`, `usd` or `usd_equivalent` field on any B5-I01 model. The
separation is therefore structural rather than a convention that could be
violated later: "native was overwritten by normalized" is not a bug waiting to be
caught, it is unrepresentable. `NativeQuantity` holds the value as a `Decimal`,
so provider precision is neither rounded away nor widened into false precision
(`bloc_05/03 §3.1/§3.3`).

---

## 6. Provider / venue separation

`provider` and `venue` are two separate required fields. There is no collapsed
`source` / `source_id` / `source_venue` field to re-merge them, and the tests
assert both that the collapsed names are absent and that
`provider=COINALYZE, venue=BINANCE_USDM` constructs — an aggregator reporting a
venue it does not operate stays representable (`bloc_05/01 §13`).

The multi-venue-aggregate law is partially mitigated rather than fully encoded:
`venue` is required, non-blank and has no default, so an aggregate cannot be
assigned a fabricated single venue. A full `venue_scope` vocabulary is deferred
to B5-I02 — see §10.

---

## 7. Time model

All nine frozen clocks are distinct fields. Naive datetimes are refused and
present values are UTC-normalized through the accepted `coerce_utc` rule.
`interval_end_at >= interval_start_at` is the only ordering enforced, because it
is the only one that is universally valid: `bloc_05/02 §6` explicitly requires a
future-effective published value (`published_at < effective_at`) to stay
representable, and a test asserts exactly that. Interval bounds require an
explicit `interval_closed` and `interval_time_convention`; `market_available_at`
requires an `availability_basis` and is refused with `UNKNOWN`.

---

## 8. Missingness model

Absence is a typed `MissingnessReason`, never a bool and never a zero. Each of
the four `BLOCKED_*` statuses requires *its own* cause, so `BLOCKED_IDENTITY`
cannot be filed under a generic gap. `QUARANTINED` requires
`missingness_reason=QUARANTINED`. A `NORMALIZED` row may not carry a
missingness reason. Verified economic zero and absence stay distinguishable: a
`Decimal("0")` native value and an empty `native_values` tuple are different
facts, and no model field anywhere defaults to a numeric zero (asserted
structurally).

---

## 9. Quality / lineage model

`quality` carries all eight frozen dimensions with **no defaults** — a defaulted
dimension is a claim, so "not determined" must be declared `UNKNOWN`. A
`VERIFIED` dimension may not contradict the envelope: identity verified without
a contract instance, lineage acceptable while broken, unit verified beside a
conversion-blocking flag, time verified with unknown availability, semantics
verified beside `SEMANTICS_UNVERIFIED` are all refused.

`lineage_state` and the matching lineage flag must agree exactly, so the state
and flag spellings of the same fact cannot drift. `LINEAGE_BROKEN` is blocking
(`bloc_05/05 §11`) and cannot accompany a canonical status.

---

## 10. Validation laws

Enforced in `models.py`, each cited to the frozen document:

1. blank and whitespace-padded identifiers refused, everywhere;
2. naive datetimes refused; present values normalized to UTC;
3. `interval_end_at >= interval_start_at`; no other ordering assumed;
4. interval bounds require an explicit `interval_closed` **and**
   `interval_time_convention`;
5. `market_available_at` requires a basis, and is refused with `UNKNOWN`;
6. `quality_flags` in canonical order, duplicate-free;
7. `lineage_state` agrees with exactly one matching lineage flag;
8. a canonical status requires `contract_instance_id`;
9. each blocked status requires exactly its own typed cause;
10. `NORMALIZED` carries no missingness reason;
11. quarantine is reasoned in both directions — reason + evidence refs +
    remediation required, and quarantine metadata is refused on a
    non-quarantined row;
12. a canonical status requires at least one native value;
13. a canonical status requires the four registry/methodology versions;
14. no blocking flag may accompany a canonical status;
15. the five dimension-contradiction laws of §9 above;
16. lineage chain complete, refs duplicate-free, blob digests SHA-256 syntax;
17. `extra="forbid"` on every model.

The one-way form of law 8 matters: it requires an identity where a canonical
claim is made and never constrains what a resolver may later decide.

---

## 11. Determinism

Two structurally equal envelopes serialize to identical bytes. Construction
reads no wall clock, computes no hash, generates no UUID and no identifier.
`test_construction_reads_no_wall_clock_and_generates_no_identity` asserts that
no field default factory exists. Equal envelopes round-trip through canonical
JSON unchanged, with `Decimal` precision intact.

---

## 12. Zero-network proof

`network_calls = 0`. No `requests` / `httpx` / `aiohttp` / `urllib` / `socket` /
`http` / `websockets` / `ccxt` import appears in any production source file, and
importing the package with `socket.socket` and `socket.create_connection`
monkeypatched to raise succeeds. Measured in `BLOC_05_I01_SCOPE_AUDIT.json` and
enforced by `test_importing_the_package_makes_no_connection`.

---

## 13. Forbidden later-stage modules — absent

Checked and absent: `registry.py`, `resolver.py`, `terms.py`, `conversion.py`,
`aliases.py`, `lifecycle.py`, `universe.py`, `availability.py`, `intervals.py`,
`revision_policy.py`, `replay_gate.py`, `semantics_registry.py`,
`methodologies.py`, `comparability.py`, `writer.py`, `query.py`,
`generations.py`, `manifests.py`, and every `normalization/sensors/*` module.
No subpackage directory exists. No provider adapter, HTTP client, storage
backend, path, catalog or DuckDB knowledge appears in the production source.

---

## 14. Bloc 5 blocking gates

**No gate is earned and none is claimed.** Vocabulary is not a gate.

```
IDENTITY_GATE         = NOT_YET_EARNED
TIME_GATE             = NOT_YET_EARNED
SEMANTIC_GATE         = NOT_YET_EARNED
UNIT_GATE             = NOT_YET_EARNED
LINEAGE_GATE          = NOT_YET_EARNED
DUPLICATE_REVISION_GATE = NOT_YET_EARNED
REPLAY_SAFETY_GATE    = NOT_YET_EARNED
GOLDEN_T0_T1_GATE     = NOT_YET_EARNED
```

Recorded in both `BLOC_05_I01_TYPE_SCOPE_MATRIX.json` and
`BLOC_05_I01_SCOPE_AUDIT.json`, and asserted by
`test_all_eight_bloc5_gates_are_recorded_as_not_yet_earned`.

---

## 15. Deferred types and modules

61 type-scope rows: 24 implemented at I01, 37 deferred to the frozen stage that
owns them. Every deferred row is named in
`BLOC_05_I01_TYPE_SCOPE_MATRIX.json` with its plan citation and reason, and
`test_every_deferred_type_is_absent_from_the_source` fails if one is implemented
anyway.

### 15.1 Two measured vocabulary gaps — recorded, not invented

* **`AvailabilityConfidence`** — `bloc_05/02 §5` requires the field but never
  freezes its vocabulary. Inventing members would be an operator decision, so
  the field is omitted and the gap is recorded. → B5-I06.
* **`VenueScope`** — `bloc_05/01 §13` names one member
  (`MULTI_VENUE_AGGREGATE`) and says "carries a scope **such as**". Choosing the
  rest is an operator decision. The underlying law is mitigated differently
  (§6). → B5-I02.

### 15.2 Two deliberate naming decisions

* The frozen full-envelope name **`T1ObservationEnvelope` is not exported**. The
  frozen envelope also carries `economic_contract_id`, `canonical_asset_id`,
  `normalization_methodology_id/_version` and `replay_eligibility` (B5-I02,
  I09, I06). Exporting the full name now would let a consumer mistake this base
  layer for the finished contract, so the base layer is `T1BaseEnvelope` and the
  matrix records the split.
* **`T1LineageRef`**, not the frozen `T1Lineage`. The frozen object binds
  `t1_record_id` and `normalization_generation` plus `FieldLineage` wiring, all
  of which need the B5-I16 identity key. I01 ships the ref-only component.

### 15.3 A revision vocabulary that must NOT be reused

`bloc_05/02 §11` freezes `AS_KNOWN_THEN` / `LATEST_VERIFIED` alongside names
that also exist in the accepted Bloc 4 `RevisionPolicy` with **different
meanings** (Bloc 4's is a raw-evidence *query* policy). They are therefore kept
as separate types, with the Bloc 5 policy introduced at B5-I07 — not reused, and
not duplicated at I01.

---

## 16. Model convention

Storage convention followed deliberately: pydantic `BaseModel` with
`extra="forbid"`, tuples rather than lists, UTC-normalizing validators. Frozen
dataclasses were **not** introduced, because the repository's models are
validated mutable pydantic objects and a second convention would make the
normalization layer harder to reason about than the layers above it.
Determinism is delivered by canonical serialization plus the canonical flag
ordering the envelope enforces. A T1 envelope is an evidence record: treat it as
a value; a change means a new row.

---

## 17. The SHA-256 format rule is duplicated on purpose

`T1LineageRef` validates blob-digest syntax with a local regex rather than
importing `storage.checksums.validate_sha256_hex`, because that symbol is
deliberately outside the accepted public handoff surface and the dependency
firewall (`BLOC_04_I17_BLOC5_HANDOFF_CONTRACT` §12/§13) forbids reaching past
it. Format only; hashing belongs to Bloc 4 and to B5-I16/I18.

---

## 18. Repository state at B5-I01

No Bloc 4 evidence, no I17 evidence and no ratification artifact is modified by
this checkpoint. The only published artifact republished is the I11R2
tracked-Python audit, which is regenerated mechanically because this checkpoint
adds tracked Python files; see the ledger section for the old/new counts and
the byte-stability proof.

Research remains FROZEN. **STOP.**
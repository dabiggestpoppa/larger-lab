# SENSOR-B5-I01 — OPERATOR RATIFICATION

> **Verdict: `PASS_SENSOR_B5_I01_NORMALIZATION_BASE_TYPES_SEALED = OPERATOR_ACCEPTED`.**
> Ratified 2026-10-06 by the operator via the SENSOR-B5-I01-RATIFY directive.
> This artifact records the measured verification performed at ratification
> time on the exact ratification tree (HEAD `66f5ba4aca…`, clean except
> untracked scratch). Ratification changed **zero** production/test/evidence
> bytes; the only tracked outputs of this run are this file and the ledger
> ratification entry (§156).

---

## 1. Exact ancestry (strict, linear, no rewrites)

```text
ae152d010f3cd8c472c6dc0593a0e94f779cb079  I17 ratification / B5-I01 authorization (origin base)
04600b5d5948b35d4f31efb5906b41538b52ae9a  B5-I01A  type-scope inventory + RED enum suite
83b2076b67bdb433cef7aa2ec5e4de7762af4fd1  B5-I01B  enums + base models + T1 base envelope
a7c82f9887f61135e20b654c3e66b927d7017040  B5-I01C  N0 tests + public surface + measured evidence
66f5ba4aca582477139212fb250803dbf2bbb230  B5-I01D  final regression + governance
```

Verified at ratification: exactly 4 commits after the base, **0 merge
commits**, remote build == local HEAD, origin/main `7c7816f38…` untouched.
No amend/squash/reset/rebase/force was performed anywhere in the chain,
including across the mid-I01 session interruption.

## 2. Type-scope matrix — recomputed 61 / 24 / 37

`BLOC_05_I01_TYPE_SCOPE_MATRIX.json`: **61 total rows, 24 needed for I01,
37 deferred.** `deferred_types_implemented = []` — mechanically re-verified by
importing the package and asserting none of the 37 deferred names is
implemented or exported. The directive's 37-name list (CanonicalAsset …
CanonicalT1Query) was compared set-wise against the matrix deferred set:
**identical**, no discrepancy either direction.

## 3. Measured vocabulary gaps — preserved, not invented

- **`AvailabilityConfidence`** — bloc_05/02 §5 names the field, never freezes
  its vocabulary. Deferred to **B5-I06**. NOT invented during I01 or
  ratification.
- **`VenueScope`** — bloc_05/01 §13 names `MULTI_VENUE_AGGREGATE` only as an
  example ("such as"). Full vocabulary not frozen. Deferred to **B5-I02**,
  with the §38 firewall below.

## 4. Production surface — exactly three modules

`src/crypto_sensor_fabric/normalization/`: `__init__.py`, `enums.py`,
`models.py` — nothing else. All 18 forbidden module filenames (registry,
resolver, terms, conversion, aliases, lifecycle, universe, availability,
intervals, revision_policy, replay_gate, semantics_registry, methodologies,
comparability, writer, query, generations, manifests) verified absent.

## 5. Public API — exactly 24 symbols

`crypto_sensor_fabric.normalization.__all__` = 24: 10 enums, 6 models, 5
opaque value types (`OpaqueIdentifier`, `T1RecordId`, `ContractInstanceId`,
`T1GenerationId`, `RegistryVersion`), 2 public module constants
(`BLOCKED_STATUS_MISSINGNESS_REASON`, `BLOCKING_QUALITY_FLAGS`) and
`canonical_json_bytes`. Private helpers `_StrEnum` and `_FLAG_ORDER` remain
unexported (verified).

## 6. Enums — 10, member sets verified fresh against plan authority

| Enum | Members |
|---|---|
| `PayoffType` (5) | LINEAR, INVERSE, QUANTO, SPOT, UNKNOWN |
| `NormalizationStatus` (8) | NORMALIZED, PARTIALLY_NORMALIZED, NATIVE_ONLY, BLOCKED_IDENTITY, BLOCKED_TIME, BLOCKED_SEMANTICS, BLOCKED_CONVERSION, QUARANTINED |
| `MissingnessReason` (13) | NOT_REPORTED, NOT_SUPPORTED, NOT_YET_LISTED, DELISTED, HISTORY_UNAVAILABLE, PROVIDER_EMPTY, ACCESS_BLOCKED, SOURCE_GAP, IDENTITY_BLOCKED, TIME_BLOCKED, SEMANTICS_BLOCKED, CONVERSION_BLOCKED, QUARANTINED |
| `NormalizationQualityFlag` (36) | the 24 from doc 05 §11 + the 6 additive from doc 01 §14 + the 6 additive from doc 02 §16, canonical declaration order enforced |
| `QualityDimensionState` (6) | VERIFIED, ACCEPTABLE_WITH_FLAGS, PARTIAL, UNKNOWN, BLOCKED, QUARANTINED |
| `LineageState` (3) | LINEAGE_COMPLETE, LINEAGE_PARTIAL, LINEAGE_BROKEN |
| `QuarantineReason` (7) | SCHEMA_FAILURE, IDENTITY_AMBIGUOUS, LINEAGE_BREAK, IMPOSSIBLE_UNITS, INVALID_SIDE_MAPPING, BOOK_SEQUENCE_CORRUPTION, SOURCE_REVISION_CONFLICT |
| `IntervalTimeConvention` (4) | LEFT_CLOSED_RIGHT_OPEN, LEFT_OPEN_RIGHT_CLOSED, PROVIDER_NATIVE_UNKNOWN, POINT_SAMPLE |
| `AvailabilityBasis` (8) | REALTIME_PUBLIC_EVENT, REALTIME_PUBLIC_SNAPSHOT, PUBLIC_INTERVAL_CLOSE, DELAYED_PUBLICATION, HISTORICAL_ARCHIVE_RECONSTRUCTION, PROVIDER_DECLARED_PUBLIC_TIME, SYSTEM_ONLY_OBSERVED, UNKNOWN |
| `TimestampPrecision` (6) | SECOND, MILLISECOND, MICROSECOND, NANOSECOND, DATE_ONLY, UNKNOWN |

No invented member. The RED suite (I01A) predates the implementation and
pins every member set against the frozen Bloc 5 docs.

## 7. Frozen distinctions preserved (not collapsed)

`BLOCKED_IDENTITY` (status) vs `IDENTITY_BLOCKED` (missingness) — and the
time/semantics/conversion pairs — remain distinct enums. The read-only
`BLOCKED_STATUS_MISSINGNESS_REASON` `MappingProxyType` links the four pairs
(`BLOCKED_IDENTITY→IDENTITY_BLOCKED`, `BLOCKED_TIME→TIME_BLOCKED`,
`BLOCKED_SEMANTICS→SEMANTICS_BLOCKED`, `BLOCKED_CONVERSION→CONVERSION_BLOCKED`)
and mutation was verified refused.

## 8. Base models and T1 envelope

| Model | Fields | Notes |
|---|---|---|
| `ObservationTimeEnvelope` | 15 | 9 Optional clocks + interval convention/closed + availability_basis + precision + clock-skew |
| `NativeQuantity` | 4 | native value with NO canonical counterpart field |
| `T1Quality` | 8 | identity/time/semantic/unit/lineage/source_integrity/coverage/replay dimensions; no aggregate score |
| `T1LineageRef` | 8 | requires all 3 chain links (raw_projection_refs, acquisition_refs, evidence_blob_hashes), dup-free, SHA-256 syntax |
| `T1VersionContext` | 5 | identity/contract_terms/semantic/methodology registry versions + time_semantics_version |
| `T1BaseEnvelope` | **27** | the ratified foundational envelope |

**Envelope status ruling:** `T1BaseEnvelope` = **STABLE B5-I01 FOUNDATION**.
`T1ObservationEnvelope` = **NOT YET COMPLETE / NOT YET PUBLIC** — the frozen
full envelope additionally requires `economic_contract_id`,
`canonical_asset_id`, `normalization_methodology_id/_version` and
`replay_eligibility`, owned by B5-I02/I05/I06/I09. The full name is
deliberately not defined or exported at this layer.

## 9. Upstream type reuse — no duplicate Bloc 4 vocabularies

Reused, not re-declared: `SensorFamily` (`contracts.enums`), `Granularity`
(`probes.enums`), `CoverageState`, `RevisionState`, `SourceUnitContract`,
`SourceUnitEvidence` (via the public `storage` package). Only the SHA-256
format regex is duplicated locally, because `storage.checksums` is
non-public.

## 10. Firewalls — all verified at the source level

- **Native/canonical**: zero field *definitions* named `canonical_value`,
  `normalized_value`, `canonical_unit`, `canonical_notional`, `usd_notional`,
  `base_notional`, `normalized_notional` anywhere in production. Native truth
  is structurally inerasable at this layer.
- **Provider/venue**: independent required fields; no merged `source`
  identity; aggregator-provided venue data remains representable.
- **Stablecoin**: no `USDT==USD` / `USDC==USD` equivalence, no conversion or
  default logic exists; no field name contains `usd`/`fiat`.
- **Identity law**: `NORMALIZED`/`PARTIALLY_NORMALIZED` require
  `contract_instance_id` + ≥1 native value + 4 registry versions and refuse
  blocking flags; native-only/blocked/quarantined rows stay resolvable-later;
  no placeholder IDs.
- **T1 ID/generation law**: `T1RecordId`/`T1GenerationId`/`ContractInstanceId`
  are value types only. No hashlib/uuid/random/secrets/`datetime.now` anywhere
  in production. Final T1 ID = B5-I16; generation publication = B5-I18.
- **Time law boundary**: only universally safe laws —
  `interval_end_at >= interval_start_at`, declared convention+closure required
  for interval bounds, `market_available_at` refuses `UNKNOWN` basis. No
  B5-I05/I06 semantics claimed or implemented.
- **Missingness**: 13 typed reasons; no bool, no zero-defaults anywhere.
- **Quality**: 8 dimensions, no aggregate; five VERIFIED-dimension
  contradiction laws refuse impossible combinations.
- **Lineage interpretation**: the required chain T1 → T0B/raw projection →
  acquisition → EvidenceBlob SHA-256 is the *core* chain only; structural
  presence is NOT claimed as complete field/conversion lineage (richer lineage
  objects are later stages). `LINEAGE_BROKEN` blocks verified canonical use
  (`BLOCKING_QUALITY_FLAGS`, 9 members).
- **Quarantine**: typed reason + evidence refs + remediation required;
  metadata refused on ordinary rows; refs dup-free. No storage/query yet.
- **Serialization**: `canonical_json_bytes` = UTF-8, `sort_keys=True`, fixed
  separators, enums as values, UTC ISO-8601 — deterministic, mirrors the
  accepted storage rule; serialization only, no content hashing.
- **Zero network/backend**: no requests/httpx/aiohttp/socket/urllib/duckdb/
  sqlite3 imports in production; `network_calls = 0`; no filesystem/storage
  layout knowledge; no direct Bloc 4 private-API dependency.

## 11. Ratification-time regression (fresh, this tree)

| Suite | Result |
|---|---|
| B5-I01 normalization | **304 passed** (2.0 s) |
| Focused battery (I01 + I16/I16R1/I16R2 + G4-13 + I11R2 binding+evidence + job-state ×3 + storage enums) | **616 passed / 0 failed** (166 s) |
| Full storage | **2019 passed / 13 skipped / 0 failed** (1422 s) |
| Full project | **3702 passed / 14 skipped / 0 failed** (1319 s) |

**Windows warning classification (§27):** the known
`test_manifest_concurrency` reader-thread teardown warning was **absent this
run** (0 occurrences in the ratification project log). When previously
observed it was recorded as inherited TEST-ENVIRONMENT DEBT; it remains
unrepaired by design (out of ratification scope).

**Static:** ruff on the new changed scope = All checks passed (repo-wide:
exactly the 2 pre-existing findings in the untouched `test_i08_evidence.py`);
mypy = 0 new (the 10 pre-existing providers/probes baseline, unchanged);
compileall OK; secret scan of the I01 diff = 0 hits.

## 12. I11R2 audit — accepted as republished in I01D

`python_files_scanned` **1011 → 1018** (7 newly tracked Python files: 3
production, 4 test), regenerated mechanically in B5-I01D only after filenames
were finalized. No-update rerun at ratification: **4 passed, byte-stable**
(SHA-256 `e1bbd772…d5e36e` unchanged). No republish during ratification — no
tracked Python file changed.

## 13. Historical custody

`git diff ae152d010f…66f5ba4ac` over `evidence/` touches ONLY new bloc_05
files plus the single authorized I11R2 count line. Zero modifications to Bloc
4 evidence, I17 evidence, or Bloc 4/I17 ratification artifacts. Ratification
itself rewrites no I01 evidence — the I01 artifacts stand as committed.

## 14. Ledger recovery truth — accepted as process history

The §155 append was interrupted mid-write by a rate-limited session: the
heredoc partially succeeded (141 lines), truncating the section mid-word
("confirmed absen"). Recovery resumed from the surviving bytes and completed
the section **append-only**, with the truncation explicitly disclosed in the
completed text ("…confirmed absent by SENSOR-B5-I01-RESUME: the original §155
append was truncated mid-sentence…"). The seam is **accepted process
history**: §155 is NOT rewritten, cleaned, or reconstructed.

## 15. Authorization boundary (this ratification)

- `PASS_SENSOR_B5_I01_NORMALIZATION_BASE_TYPES_SEALED = OPERATOR_ACCEPTED`
- `BLOC_05_IMPLEMENTATION_STATUS = I01_OPERATOR_ACCEPTED`
- `BLOC_05_NORMALIZATION_IMPLEMENTED = PARTIAL_FOUNDATION_ONLY`
- All 8 Bloc 5 blocking gates remain **NOT_YET_EARNED** — type/model existence
  alone promotes nothing.
- `next_checkpoint_authorized = TRUE`
- `next_checkpoint = SENSOR-B5-I02 ASSET / VENUE / CONTRACT IDENTITY MODELS + REGISTRIES`
- `authorized_scope = B5-I02 ONLY`; B5-I03+ UNAUTHORIZED; Bloc 6 UNAUTHORIZED;
  research FROZEN; `recommended_next = SENSOR-B5-I02 IMPLEMENTATION`.
- **B5-I02 NOT STARTED** by this ratification.

B5-I02 frozen scope (record only): owns CanonicalAsset, Venue,
VenueInstrument, EconomicContract, ContractInstance + the identity
registry/data structures to store/version them. Does NOT authorize lifecycle
resolution, alias resolution, PIT resolver, linear/inverse conversion
primitives, time semantics, availability resolution, revision engine, unit
conversion, sensor normalizers, or T1 writer/query (B5-I03+).
`VenueScope` firewall: audit first whether B5-I02 actually requires it; if
required and still underdetermined, STOP for operator decision rather than
inventing members. Identity laws carried forward as record: CanonicalAsset ≠
ContractInstance; USD/USDT/USDC distinct assets; provider ≠ venue;
VenueInstrument preserves native symbol/instrument identity; EconomicContract
groups economic comparability without erasing instance identity;
ContractInstance preserves PIT-valid terms and evidence; no metadata backcast.

*Note:* the untracked `BLOC_05_I06_AVAILABILITY_CONFIDENCE_SPIKE.md` in this
folder is a pre-authorization design input from a prior operator-requested
session; it is NOT ratified, NOT evidence, and NOT part of this commit.

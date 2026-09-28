# SENSOR-B4-I12 — RAW EVIDENCE QUERY / REPLAY API — measured evidence

Branch: `agent/crypto-sensor-fabric-build`.  Implementation parented on
`bde337176b4af7bafa96ef0743ec07cdabf5dbe6` (whose parent IS the mandated
`adf1dd1f18431caf0a91940a0d952425f73ec345` — the I11R2C-R1 self-scan
correction was operator-approved between mandate issue and I12 start; the
deviation is recorded here and in the governance ledger).  Remote main
`7c7816f382947bbc8a1f2154435fc436f2428fa8` untouched.

## 0. §5 COMPLETE INVENTORY gate — MISSING_PUBLIC_INVENTORY_INTERFACE (resolved by operator review)

Every accepted I04/I06 read was keyed by an ALREADY-KNOWN identity
(`partition_key`, blob hash, acquisition id, `source_revision_key`); a
non-globbing consumer could not discover what the lake holds.  The only
complete-inventory routes were filesystem globbing or DuckDB-as-truth, both
forbidden by the §5 gate.  Stopped at the gate per §5/§41 and reported.
**Operator review approved the smallest additive read-only surface** (shipped
in I12A):

| Repository | Added public read |
|---|---|
| `PartitionManifestRepository` | `list_all_current_manifests()` |
| `BlobMetadataRepository` | `list_all_blob_metadata()` |
| `AcquisitionRepository` | `list_all_acquisitions()` |
| `SourceRevisionRegistry` | `list_source_revision_keys()` |

`list_all_current_manifests` validates every pointer through the exact
logical `partition_key` path (I04R1 §38/§40) — the physical locator filename
is never trusted.  No accepted behavior changed; no historical evidence
rewritten.

## 1. Query architecture

- `storage/query.py` — `RawEvidenceQueryService`: reduces a
  `RawEvidenceQuery` over a complete `RawInventorySnapshot` built from the
  four approved enumeration reads.  Determinism by construction: every
  snapshot list is sorted by natural identity (§27); no glob/os.listdir
  ordering can leak.
- `storage/replay.py` — `RawArtifactReader`, `RawProjectionReader`,
  `RevisionResolver`, `RawReplayCursor`, `Bloc5Handoff`.  Read-only by
  construction (§29): no delete/overwrite/repair/quarantine/manifest-mutation/
  revision-declaration/resume-advancement/recovery names exist on the surface
  (machine-checked in `READ_ONLY_IMMUTABILITY_MATRIX`).
- `storage/__init__.py` exports only; `query.py`/`replay.py` import neither
  DuckDB, Postgres, nor any network module (AST-verified in tests).
- Model extension (§11, backwards-compatible): `RawEvidenceQuery.
  exact_revision_number: int | None` — required `>= 1` under
  `EXACT_REVISION`, forbidden otherwise.  No string hacks.

## 2. Semantics proven (matrices are mechanically derived; each row's
invariants are literal-true or the row FAILs; exactly one synthetic
counterfactual FAIL per matrix)

| Matrix | rows | OK | FAIL (counterfactual) |
|---|---|---|---|
| QUERY_FILTER | 22 | 21 | requested-bounds-as-actual |
| REVISION_POLICY | 13 | 12 | silent-latest-wins |
| ARTIFACT_READER | 10 | 9 | skips-verification |
| PROJECTION_LINEAGE | 6 | 5 | usable-T0B-without-lineage |
| REPLAY_ORDER | 8 | 7 | sort-everything-by-timestamp |
| READ_ONLY_IMMUTABILITY | 5 | 4 | query-writes-to-catalog |
| BLOC5_HANDOFF | 10 | 9 | batch-claims-canonical-asset |

- **Range semantics (§7)**: evidence-backed intersection only; results carry
  the manifest's own committed window, never the requested one; exact
  bounds / inside / outside-left / outside-right / open bounds / point
  intervals all measured; zero-hit windows raise typed `NoMatchingEvidence`.
- **Acquired vs observed (§8)**: independent predicates on `ingested_at` and
  `response_observed_at`; a +9h-ingested manifest is excluded by a +5h
  acquired cutoff while its +1h observed time passes observed cutoffs.
- **System replay vs market reconstruction (F20/§9)**: I12 exposes facts
  only; `PROVIDER_EVENT_TIME` ordering refuses without `actual_start/end`
  evidence and never substitutes ingestion/observed time.
- **Integrity (§14)**: explicit admissibility lattice (UNVERIFIED < LOCAL <
  PROVIDER for floors; failure states fail every real threshold and stay
  VISIBLE as themselves at the UNVERIFIED floor — never promoted).
- **Coverage (§15)**: frozen states filter explicitly; missingness never
  becomes zero.
- **Revisions (§10-§12)**: registry `resolve` delegation; ambiguity typed;
  canonical policy consumes explicit declaration evidence only (absent →
  typed unavailable; conflicting → typed ambiguity); limit applies after
  full reduction and cannot suppress resolution-time ambiguity (§28).
- **T0A (§17/§18)**: exact bytes, deterministic bounded streaming (every
  chunk = chunk_size except the last; concatenation exact; no unbounded
  read path), typed missing/corrupt; wrapper compression stays inside the
  accepted blob store (ZSTD round-trip measured).
- **T0B (§19/§20/§21)**: schema-resolution gate, parser version, full
  lineage chain projection→lineage→acquisition→blob; incomplete lineage →
  `LINEAGE_INCOMPLETE`; metadata queries never open T0A payload bytes (spy
  test).
- **Read-only (§29/§30)**: full hash sweep of the durable tree identical
  before/after queries, reads, replays, conversion, AND expected typed
  failures.
- **Firewalls (§31-§33)**: no Postgres, no DuckDB, no network anywhere in
  I12 (AST-checked); path-shaped selector values (`../foo`, `C:\`,
  `file://`, UNC, URL) are inert selectors that yield typed no-match.

## 3. Bloc-5 handoff (§22)

`Bloc5Handoff.to_batch` produces a complete `RawNormalizationBatch`
preserving provider/venue/sensor_family/native_instrument, projection
schema id+version, parser version, raw-reader descriptor, blob refs,
acquisition refs, logical range, integrity, coverage, revision state,
quality flags, known gaps, source granularity, and history boundary.
Structural proof: none of `canonical_asset`, `canonical_notional`,
`effective_at`, `normalized_*`, `canonical_side` exist on the model —
they are Bloc 5.

## 4. Publication discipline

Matrices regenerate byte-identically without any override (verified
`BYTE-STABLE` across a second publication).  `UPDATE_I12_EVIDENCE=1` is
required only to write.  Normal pytest is read-only against committed
evidence (`test_evidence_matrices_are_measured_and_committed`).

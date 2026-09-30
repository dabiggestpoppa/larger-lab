# BLOC 04 — SENSOR-B4-I13 CHAIN OPERATOR RATIFICATION

> **Status:** OPERATOR ACCEPTANCE RECORD — recorded by the ratification run
> `SENSOR-B4-I13R3-RATIFY`. This document records acceptance only. It creates
> no new implementation and grants no authority beyond what it states.
> Append-only: no prior evidence file is modified by this record.

---

## 1. What is ratified

The complete export/restore lineage, at ratification head
`5d4985cc7f6f1cfe5a1c9d63ca6b8dd975d193c0`, verified in strict ancestry
(no rewritten history):

| Checkpoint | SHA | Chain state |
|---|---|---|
| I12 chain ratification | `5cf64e7b6381ebda4e88388909ced4c9a3cf4541` | ancestor (verified) |
| I13 | `62dca662a61937f7d347c8efe520fa98ec155358` (+ I13A-C/D-F) | ancestor (verified) |
| I13R1 | `e7e95533e1f1738195ccbf94197b6c59859b5ba4` | ancestor (verified) |
| I13R2 | `ed7b80bc4b861fd5add71ea2e3a33a2a6b53575f` | ancestor (verified) |
| I13R3 | `5d4985cc7f6f1cfe5a1c9d63ca6b8dd975d193c0` | ratification HEAD |

Covered by acceptance: query-driven local evidence-pack export; independent
pack verification; checksum/root-digest verification; fresh-root restore;
exact raw-byte parity; exact query-semantic metadata parity; revision-state
parity; successful/refusal revision-policy parity; acquired_before /
observed_before parity; T0B artifact/context/schema/lineage parity;
projection-payload parity; bounded transitive evidence closure; unique
manifest-root selection; manifest-predecessor closure; versioned-manifest CAS
replay; atomic export publication; atomic restore promotion; bounded
streaming; fail-safe disk-space checks; DuckDB rebuild; nonvacuous DuckDB
identity parity; source-root containment; pack self-containment;
historical-evidence immutability.

**Production diff at ratification: ZERO** (no production file changed by the
ratification run; the only new code is the narrow ratification test module
`test_i13_ratify_boundary.py`).

## 2. G4-11 definition and verdict

```text
G4-11_EXPORT_RESTORE_GATE — the export/backup/restore gate:
a query-selected evidence pack must export atomically, verify
independently, restore into an EMPTY root, and produce fresh
repositories over which hash parity, exact query-semantic metadata
parity, revision parity, and DuckDB identity parity all hold —
with resource safety, source containment, and no silent bypass.

G4-11_EXPORT_RESTORE_GATE = PASS
```

## 3. Verified laws (per acceptance verification)

- **Export/verification/restore law.** Canonical flow:
  `RawEvidenceQuery` → accepted I12 `RawEvidenceQueryService` →
  query-selected evidence → minimal transitive support closure → pack →
  independent verification → empty-root restore → fresh repositories →
  DuckDB rebuild → hash/query parity. Sealed classes in current production:
  `EvidencePackExporter`, `EvidencePackVerifier`, `EvidencePackRestorer`.
  Provider network: ZERO. Cloud: ZERO. Postgres raw authority: ZERO.
  Original DuckDB required: FALSE.
- **I13R1 seals.** Public I05 payload streaming + public I06 revision read
  surfaces; export.py private-access greps `_segments_by_key` /
  `_declarations_by_key` / `_projection_root` = **0 / 0 / 0** (re-verified at
  ratification head). Atomic export = complete sibling staging → verify →
  ONE directory rename (injected-failure tests prove the destination stays
  absent; stale staging refused). Digest domains `MANIFEST_BODY_SHA256` +
  `PACK_ROOT_SHA256` persisted, verifier-recomputed, receipt == persisted.
  Bounded streaming for T0A/T0B payloads.
- **I13R2 seals.** Default free-space law: no injected provider ⇒ real
  `shutil.disk_usage` on nearest existing ancestor; no silent bypass. Exact
  `AcquisitionRecord` parity includes `ingested_at`, `request_started_at`,
  `response_observed_at`, `requested_start`, `requested_end`. Revision parity
  covers keys/segments/observations/declarations/resolution behavior.
  `SUCCESS_PARITY` (7 policies) separate from `REFUSAL_PARITY` (3 rows) —
  10/10 OK. Time filters `acquired_before` / `observed_before` select
  identical source/restored acquisition IDs (4/4 OK).
- **Transitive support closure.** `QUERY_SELECTED + REQUIRED_SUPPORT =
  EXPECTED_TRANSITIVE_CLOSURE`; pack == restored == closure for blobs,
  acquisitions, revision keys (BOUNDED_SLICE matrix). Manifest-blob,
  revision first-acquisition, manifest-predecessor, and projection/lineage
  dependencies all included; true unrelated control excluded
  (`true_leakage_count = 0`); fixpoint deterministic and idempotent
  (iterations 2 == 2, C1 == C2); no whole-lake expansion.
- **Versioned-manifest repair (I13R3).** The real T0B fixture exercises
  manifest v1 → v2 on one partition key (v2 supersedes v1); closure includes
  v1 as REQUIRED_SUPPORT (`MANIFEST_PREDECESSOR` edge); restore replays in
  `(partition_key, manifest_version)` order; v2 `expected_current` =
  PREVIOUS identity/version (not the post-append identity); T0B replay
  (including the lineage resolver) completes BEFORE the v2 referential gate.
- **Nonvacuous DuckDB identity parity.** Published, literal identity-set
  equality (SOURCE filtered to pack closure == PACK_EXPECTED == RESTORED):
  `v_t0_blobs` 2/2 · `v_t0_acquisitions` 2/2 · `v_t0_partitions` 2/2 ·
  `v_t0_revisions` 2/2 · `v_t0_projections` 1/1. Empty==empty not accepted;
  single-root rebuild of a T0B-bearing fixture refuses typed.
- **Split-root DuckDB law.** Accepted rebuild usage: `data_root` = T0A root,
  `projection_root` = T0B root; `projection_root=None` preserves the legacy
  unified-root behavior (all pre-I13R3 call sites unchanged). Revision
  discovery reads both accepted durable layouts; same `segment_id` with
  divergent payload ⇒ `DuckDBCatalogCorrupt` (no precedence rule).
- **T0B nonvacuous parity.** Artifact 1/1, context 1/1, lineage 1/1, schema
  1/1 (literal canonical digests equal); source and restored queries both
  return nonempty `projection_refs`/`lineage_refs`; query result digests
  equal (`0f53d9ba…`).
- **Physical T0B parity (recomputed at ratification).** source projection
  SHA == pack payload SHA == restored physical SHA ==
  `5d4c04ce1325ea589863d091b78ca3abbb9cb280aec2b27d5112548fec251daa`,
  through public `open_payload()` / `verify_physical()` only — no
  filesystem-path shortcut.
- **Fail-safe source boundaries.** Canonical composition derives every wired
  dependency's boundary automatically (artifact/projection-payload root,
  context, lineage, schema, revision registry, T0A) — no caller override
  required. A dependency that cannot prove its root refuses construction
  with `ExportSourceBoundaryUnproven`.
- **Nonexistent-child containment microcheck (NEW, this run).**
  `test_i13_ratify_boundary.py` proves `ExportDestinationUnsafe` — NOT
  `ExportPackExists` — for export into NONEXISTENT children beneath the T0A
  blob root, T0A catalog root, T0B projection payload root, T0B
  projection/context/lineage/schema catalogs, and the revision registry
  root (probe absent before and after each attempt), plus the
  external-nonexistent control that exports, the construction-refusal
  proof, and the `protected_source_roots` EXTENSION law (explicit roots add
  protection; derived boundaries cannot be disabled). 5/5 pass.
- **Source independence.** The accepted I13 pack-copyable proof
  (`test_pack_copyable_to_second_directory`) plus restore-into-fresh-objects
  law: verification, copying, restore, fresh repositories, DuckDB rebuild,
  and query execution succeed over the pack alone; no source-root fallback.
- **Fresh objects.** Restored parity uses NEW blob store, metadata repo,
  acquisition repo, manifest repo, projection repos, revision registry, and
  query service over the restored root — no shared source cache, no source
  repository reuse.
- **Atomicity.** Export failure before publication leaves the final pack
  destination absent; restore failure before promotion leaves the final
  restored root absent; only deterministic stale-staging residue possible;
  no partially complete final state (I13R1 injected-failure evidence).

## 4. Regression / static / CI truth at ratification

- Full project regression (this run, after adding the ratification test):
  recorded in the ledger block below — expected **3055 passed, 28 skipped
  (pre-existing), 0 failures** (3050 pre-ratification baseline + 5 new
  ratification boundary tests).
- Ruff: clean on changed scope. compileall: OK. mypy: 0 new findings in
  changed scope (10 pre-existing providers/ baseline).
- Seal greps re-verified: 0 / 0 / 0.
- **external_ci = NONE_OBSERVED** (0 statuses / 0 check-runs on the start
  head). Local pytest is NOT external CI.
- I11R2 tracked-Python audit: mechanically republished for the new ratification
  test module if the count moved (no manual count edits).

## 5. Historical evidence immutability

Original I13 / I13R1 / I13R2 / I13R3 evidence files are checkpoint-scoped
historical proof and are NOT modified by this ratification. The known CRLF-only
working-tree churn in old I03R1/I04 evidence predates this session, is
content-identical modulo line endings, and remains unstaged/uncommitted.

## 6. Governance after acceptance

```text
PASS_SENSOR_B4_I13_EXPORT_BACKUP_RESTORE_SEALED      = OPERATOR_ACCEPTED
PASS_SENSOR_B4_I13R1_PUBLIC_AUTHORITY_ATOMIC_CLOSURE_SEALED = OPERATOR_ACCEPTED
PASS_SENSOR_B4_I13R2_EVIDENCE_FIDELITY_RESOURCE_SEALED = OPERATOR_ACCEPTED
PASS_SENSOR_B4_I13R3_NONVACUOUS_PARITY_BOUNDARY_SEALED = OPERATOR_ACCEPTED
G4-11_EXPORT_RESTORE_GATE                            = PASS
next_checkpoint_authorized                           = TRUE
next_checkpoint                                      = SENSOR-B4-I14 BLOC 3 INTEGRATION
authorized_scope                                     = I14 ONLY
I15+                                                 = UNAUTHORIZED
G4-12_BLOC3_HANDOFF_GATE                             = NOT_YET_IMPLEMENTED / PENDING_I14
research                                             = FROZEN
```

## 7. Frozen I14 contract (recorded next-phase requirement — NOT implemented here)

**SENSOR-B4-I14 — BLOC 3 INTEGRATION.** Wire production Bloc 3 adapter
outputs (`FetchBatch`, `RawPayloadEnvelope`) into the accepted Bloc 4 storage
writer:

```text
Bloc 3 fetch -> RawPayloadEnvelope -> exact T0A durable persistence
  -> acquisition metadata -> revision registration -> T0B (if applicable)
  -> durable PartitionManifest commit
  -> ONLY AFTER durable commit: resume/checkpoint advances
```

Core invariant: **RESUME CHECKPOINT MUST NEVER ADVANCE BEFORE DURABLE
MANIFEST COMMIT.**

I14 failure law (requirement recorded now; implemented in I14): the
integration must be restart-safe across crash/failure before raw write, after
raw write, after metadata, after revision registration, before manifest,
during manifest, and after manifest but before checkpoint. No cursor skip; no
source event silently lost; no false checkpoint progress.

**I14 authorization firewall:** I14 authorization does NOT authorize I15
security/hardening, I16 final acceptance/evidence, I17 Bloc 5 handoff,
research restart, provider redesign, or new storage/query/export semantics,
and touches no Book 5 work. I14 reuses the accepted Bloc 3 and Bloc 4
contracts. I14 earns G4-12; G4-12 is NOT passed by this ratification.

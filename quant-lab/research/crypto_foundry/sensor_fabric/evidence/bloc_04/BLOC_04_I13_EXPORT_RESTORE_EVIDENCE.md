# SENSOR-B4-I13 — EXPORT / BACKUP / RESTORE EVIDENCE (G4-11)

> Mandate: SENSOR-B4-I13 · Branch: `agent/crypto-sensor-fabric-build`
> Start HEAD: `5cf64e7b6381ebda4e88388909ced4c9a3cf4541` (post-I12-ratification)
> Research: FROZEN · I14+ UNAUTHORIZED · Local/offline only

## Model gap resolution (§2/§53)

The frozen `ExportManifest` could not carry the per-object checksummed pack
inventory (`I13_EXPORT_MANIFEST_MODEL_GAP` reported pre-implementation). The
operator approved the smallest backwards-compatible extension: additive
`pack_schema_version` + `object_inventory: list[ExportObjectRecord]` +
`pack_root_sha256`, new `PackObjectRole`/`PackChecksumDomain` enums. All
pre-existing `ExportManifest` fields and validators unchanged.

## Production additions

- `storage/export.py` (new, only production file besides additive models/
  enums/`__init__` exports): `EvidencePackExporter`, `EvidencePackVerifier`,
  `EvidencePackRestorer`, narrow typed error vocabulary (§40), pack path
  containment + symlink refusal (§12/§14), deterministic role-separated
  layout (§11).
- `models.py`/`enums.py`: additive I13 records/enums only. NO changes to
  query/replay/revision/manifest-writer/blob-writer semantics.

## Export law (§5/§6/§15-§18)

Selection is exclusively `RawEvidenceQueryService.execute` (I12R2-canonical
wiring: revision authority mandatory, no bypass). T0A bytes stream through
`open_blob` (chunk-bounded) and are verified against `EvidenceBlob.blob_sha256`
(SOURCE_BYTES domain; wrapper digests never compared, §17). The exporter
self-verifies the staged pack with the independent verifier BEFORE
finalization (§43). Source lake is never mutated by export (§18).

## Verification law (§20-§22)

`verify_pack` validates manifest schema/version, duplicate identities and
paths, path containment + symlinks, per-file size AND checksum, and the
exact-inventory policy (unlisted/renamed/extra objects refuse). No
top-level-digest-only shortcut; no best-effort recovery.

## Restore law (§23-§27, §44-§46)

Restore = verify pack → empty-root validation → free-space ceiling →
staging root → materialize blob bytes at canonical content-addressed
locators → REPLAY through accepted writers (`append_metadata`,
`append_acquisition`, `append_partition_manifest` CAS, schema registry,
context/artifact/lineage commits, `register_acquisition` + declaration
replay) → validate the complete restored state with FRESH repository
instances → atomic promotion. Partial/stale staging never exposes a
complete restore. Postgres is NOT part of restore authority; DuckDB is
REBUILT (`rebuild_duckdb_catalog`), never copied.

## G4-11 blocking proof (§28-§31, all measured)

- fresh-empty-root restore: PASS
- hash parity (restored blob rows == exported source-byte rows;
  every restored blob passes accepted physical verification): PASS
- query parity (canonical result equality through fresh services over
  source vs restored slice): PASS
- DuckDB rebuild from restored slice sees exactly the pack blob slice: PASS
- security/path containment/resource ceilings/free-space injection: PASS

## Matrices (append-only, measured; each ≤1 explicit synthetic FAIL)

| Artifact | Content |
|---|---|
| `BLOC_04_I13_EXPORT_INVENTORY_MATRIX.json` | query-driven selection, role layout, per-object checksums, source unchanged, no absolute paths |
| `BLOC_04_I13_PACK_VERIFICATION_MATRIX.json` | valid verify + blob tamper/missing/extra refusals |
| `BLOC_04_I13_RESTORE_INTEGRITY_MATRIX.json` | empty-root success, nonempty refusal, partial-pack refusal before mutation |
| `BLOC_04_I13_FRESH_ROOT_PARITY_MATRIX.json` | query-result digest parity, blob-hash parity, restored revision authority |
| `BLOC_04_I13_DUCKDB_REBUILD_MATRIX.json` | empty-catalog rebuild, slice discovery parity |
| `BLOC_04_I13_SECURITY_RESOURCE_MATRIX.json` | resource ceilings, injectable free-space refusal, zero network imports |

Byte-stability of publication verified across consecutive generator runs.

## Network truth (§41)

`export.py` contains no network imports (requests/httpx/aiohttp/boto/ftp/
ssh: zero). Provider/external-product/cloud/remote-database network = ZERO.
Local filesystem only. Query/replay/export paths remain read-only over the
source; the only writes land in the new pack / staging-restore roots.

## BackupState decision (§54)

`BackupState`/`BackupClass` NOT mutated: verified-pack completion is
recorded in the pack manifest, the ExportReceipt, and this evidence file.
No operational write path exists or is required by frozen contracts.

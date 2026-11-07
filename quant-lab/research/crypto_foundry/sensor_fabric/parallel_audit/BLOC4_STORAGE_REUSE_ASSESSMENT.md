# Bloc 4 Storage Reuse Assessment — Parallel Audit (SENSOR-B5-PARALLEL-R1)

**Base:** `0f0b3195b43a47b88896ef8d1cfa49e2568a581e` · **Scope:** `quant-lab/src/crypto_sensor_fabric/storage/{blob_store,catalog,revisions}.py` vs Bloc 4 frozen docs `bloc_04/01..07`; question: can Bloc 5 verification (P2d) reuse Bloc 4 storage as-is?

## Component inventory (verified at base)

| Component | Public API | Durability | Role for Bloc 5 |
|---|---|---|---|
| `LocalBlobStore` (`blob_store.py:232`) | `put` (507), `put_bytes` (698), `open_blob` (734), `verify_blob` (762); `blob_exists`; no overwrite | stage → flush → fsync → staged verify → no-clobber publish → parent fsync; **steps 7–8 explicitly NOT implemented** (metadata txn, resume advancement); no recovery scanning (I08), no T0B projections (I05), no acquisition/manifest repo (I04) in this module | Bytes + re-hash only; caller supplies identity |
| `LocalEvidenceCatalog` (`catalog.py:1531`); `BlobMetadataRepository` (550), `AcquisitionRepository` (881); `is_usable_manifest_provenance` (817) | Immutable Parquet fragments under `catalogs/manifests/`; fragment hash; exact-row staged verification | Same atomic doctrine; canonical JSON for nested Bloc-3 objects; closed error taxonomy (72–152: `UnearnedProviderIntegrityClaim`, `DanglingBlobReference`, etc.) | Durable evidence context + provenance eligibility predicate |
| `SourceRevisionRegistry` (`revisions.py:581`); `RevisionBlobSource`/`RevisionPhysicalStore` Protocols (459/467); `verify_blob` (468) | Immutable segments/observations/declarations under `catalogs/source_revisions/`; revision vocabulary `STABLE/IDENTICAL_REFETCH/SOURCE_MUTATION/…`; resolution policies `ERROR_ON_AMBIGUITY/ALL/FIRST_SEEN/LATEST_SEEN/EXACT_REVISION/…` | `DurableJsonCatalog`: stage → fsync → verify → no-clobber publish → parent fsync; identity descriptor persisted + re-verified on reload | Mutation registry (I06); revision/authentication source for Bloc 5 |
| Freeze manifest (`07_BLOC_04_FREEZE_MANIFEST.md`) | F1–F16 frozen decisions: T0A authoritative exact bytes (H1 = SHA-256 pre-compression), T0B = Parquet projection, atomic ordering mandatory, immutable corrections, `SOURCE_MUTATION` first-class, coverage≠integrity, no event-level dedupe in T0, no auto-delete | Planning status COMPLETE, **implementation status NOT STARTED** *at freeze time* — source has since been implemented; freeze doc is not the implementation proof | Contract to assess against, not evidence of code |

## Reuse verdict

**REUSE (with seams):** Bloc 4 storage is structurally suitable as the custody/evidence substrate for P2d, **provided** the F-R1-01 seam is closed by binding `BlobStoreCustody` to a real `LocalBlobStore.verify_blob` + catalog row. None of the storage modules need redesign for P2d's three fixes.

### What P2d can take as-is
- **Content identity:** H1 (`blob_sha256`) / H2 / H3 layering (`blob_store.py` header, I03 §20) matches what `verification.py` needs for `held_digest` → `verify_blob` replacement.
- **Provenance eligibility:** `is_usable_manifest_provenance` (`catalog.py:817`) is the single authoritative predicate; P2d/Bloc 5 must call it, not re-implement fenced eligibility.
- **Revision truth:** Registry distinguishes refetch vs mutation without "latest wins" (`revisions.py` header, I06 §8); directly supports `source_revision_authenticated`.
- **Error taxonomy:** Closed errors (`UnearnedProviderIntegrityClaim`, `ProviderChecksumClaimConflict`, `CatalogIntegrityError`) already encode "unearned claim" refusals Bloc 5 wants to surface.

### Seams / gaps (must not treat as blockers for P2d, must not overclaim)
1. **Steps 7–8 absent** (metadata transaction, resume advancement) and **no recovery scanning (I08)** — do not claim end-to-end T0 durability from `LocalBlobStore` alone; P2d custody must not assert durable-metadata or resumability.
2. **T0B projections (I05) absent** — Parquet-native views are not available; Bloc 5 must not assume them.
3. **Catalog/revision stores are filesystem-local; no network, no Postgres** — acceptable for local verification; not a distributed evidence service.
4. **Freeze doc vs code drift:** `07_BLOC_04_FREEZE_MANIFEST.md` says "Implementation status: NOT STARTED" — always verify against actual source (this assessment does), never against the freeze header alone.
5. **Key collision:** `revision_blob`/`RevisionPhysicalStore.verify_blob` Protocols are shape-based too — apply the same identity lesson as F-R1-01 if P2d ever authenticates revisions directly through them.

## Minimal P2d binding (no storage change required)
```python
# Illustrative — NOT committed code, NOT a ratification input.
class BlobStoreCustody:  # seal: final, constructible only with verified store
    def __init__(self, store: LocalBlobStore, catalog: LocalEvidenceCatalog): ...
    def held_digest(self, reference: str) -> str:
        return store.verify_blob(reference)  # re-hash, or Catalog lookup + verify
```
The fix lives in `verification.py` (I-1); storage is the trusted leaf.

## Recommendation
- **For the primary build agent:** reuse `LocalBlobStore` + `catalog.py` + `revisions.py` as the custody/provenance substrate; do not rebuild evidence storage.
- **For P2d:** close F-R1-01 by binding custody to the above; close F-R1-02..04 in `verification.py` + approval schema; no storage-module changes needed.
- **For operators:** the eight unearned gates, empty production approval manifest, and I12/I17 restrictions from the frozen audit remain in force — storage reuse does not change them.

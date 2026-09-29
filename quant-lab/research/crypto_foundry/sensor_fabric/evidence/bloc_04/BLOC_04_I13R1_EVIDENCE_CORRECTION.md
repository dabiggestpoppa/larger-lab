# SENSOR-B4-I13R1 — EVIDENCE CORRECTION (append-only)

> Mandate: SENSOR-B4-I13R1 · Branch: `agent/crypto-sensor-fabric-build`
> Start HEAD: `62dca662a61937f7d347c8efe520fa98ec155358` · Research: FROZEN · I14+ UNAUTHORIZED

Operator source review of the sealed-pending I13 found five acceptance
blockers. All were reproduced failure-first, repaired, and re-measured.
No historical I13/I12/I11 evidence was modified; the original I13
matrices remain the historical checkpoint publication.

## Blocker A — private I05/I06 internals in export.py (REPRODUCED → REPAIRED)

Reproduction: `grep -c "_segments_by_key|_declarations_by_key|_projection_root" export.py` = 3 hits
(`getattr(registry, "_segments_by_key", …)`, `getattr(registry, "_declarations_by_key", …)`,
`self._artifacts._projection_root`).

Repair (operator-authorized minimal public read APIs, §26):
- I06 `SourceRevisionRegistry.list_segment_records(key)` — durable
  segment-birth records, ordered by revision_number;
- I06 `SourceRevisionRegistry.list_declarations(key)` — durable provider
  declaration records, deterministically ordered;
- I05 `ProjectionArtifactRepository.open_payload(projection_id)` —
  context-managed streaming reader that re-runs the accepted physical
  verification (digest + row count + registered schema) internally and
  refuses corruption typed BEFORE opening; no internal-root exposure.

Post-repair structural grep (verified in evidence + focused test):
`_segments_by_key` / `_declarations_by_key` / `_projection_root` in
export.py = **0 / 0 / 0**.

## Blocker B — non-atomic export finalization (REPRODUCED → REPAIRED)

Reproduction: injected failure after the first child move left the final
destination PARTIALLY POPULATED (`export_manifest.json` present, count 1).

Repair (§7): destination must NOT pre-exist; the pack builds COMPLETE in a
sibling staging directory `.<destination>.staging-export`, is verified by
the independent verifier, then publishes with ONE directory-level atomic
`staging.rename(destination)`. Injected failures before first object and
after verify/before rename leave the destination **ABSENT**. Stale staging
is refused deterministically (explicit removal required; never adopted).

## Blocker C — unsealed digest semantics (REPRODUCED → REPAIRED)

Reproduction: persisted `manifest_sha256` = digest of the first inventory
record; persisted `pack_root_sha256` = `None`; receipt values differed
from persisted values (all measured false pre-repair).

Repair (§10, exact non-circular domains):
- **MANIFEST_BODY_SHA256** = SHA256(canonical manifest body with BOTH
  self-digest fields neutralized);
- **PACK_ROOT_SHA256** = SHA256(MANIFEST_BODY_SHA256 + "\n" + canonical
  sorted object-inventory tuples `(role, object_id, pack_path, sha256,
  byte_size, checksum_domain, provenance_ref)`).

Both persisted non-null in the finalized manifest; the verifier
independently recomputes BOTH and refuses mismatch typed
(`PackChecksumMismatch`); receipt fields literally equal the persisted
fields (proven by focused test + DIGEST_SEMANTICS matrix). Digest-tamper
parametrized refusals: query / export_id / created_at / object entry /
manifest digest field / root digest field — all detected.

## Blocker D — whole-object reads (REPRODUCED → REPAIRED)

Reproduction: `source.read_bytes()` in restore blob materialization and
full `read_bytes()` of projection payloads in export.

Repair: T0A export streams via `open_blob`; T0B export streams via the
new public `open_payload`; T0A restore and T0B restore stream
file-to-file via `_copy_into` (chunk-bounded, fsync per object). The
STREAMING matrix instruments max underlying read ≤ configured chunk
ceiling. Remaining `read_bytes()` calls are classified
SMALL_BOUNDED_METADATA (pack JSON catalog records, bounded by the
manifest ceiling through `_read_pack_metadata_bytes`); physical payload
paths are STREAM_REQUIRED with a structural test guarding reintroduction.

## Blocker E — overstated G4-11 parity (REPRODUCED → REPAIRED)

Reproduction: I13 `blob_hash_set_parity` row carried count-only measured
payload; `revision_authority_from_restored_truth` row measured
`service_constructed=True` — no literal equality.

Repair: the PARITY matrix now measures LITERAL equality per row:
- sorted source vs restored blob SHA-256 SETS (recorded verbatim);
- canonical metadata digest over blobs + acquisitions (structural
  identity fields; wall-clock operational timestamps excluded per the
  documented canonical semantic serialization — §18);
- per-policy query-result digests: default single-revision,
  ALL, FIRST_SEEN, LATEST_SEEN, EXACT_REVISION=1, EXACT_REVISION=2
  (source vs restored literal digest equality; both recorded);
- revision registry parity via the NEW public APIs (keys + segment
  records; `registered_at` excluded as operational);
- DuckDB rebuilt discovery per-view row counts vs the pack slice
  (identity-level for the slice; count-only substitution detection is
  the recorded synthetic counterfactual).

## Revision closure law (§3)

Export carries only the durable revision evidence the query semantics
require: ALL → full chain; FIRST_SEEN → rev 1; LATEST_SEEN → 1..latest
(chain needed to reproduce the selection); EXACT_REVISION=N → prefix
1..N (numbering/replay derives from the segment chain — no future
revisions); PROVIDER_DECLARED_CANONICAL → selected + declaration
evidence + prerequisite chain; ERROR_ON_AMBIGUITY → touched revisions of
the unambiguous selection. QUERY_CLOSURE matrix proves selected-key
coverage, no unselected-key leakage, and the EXACT_REVISION=1 bound.

## Historical evidence law (§27)

Original I13 matrices: UNTOUCHED (byte-verified). I13R1 publishes six NEW
append-only matrices + this narrative. The historical/current dual-truth
doctrine from I12R2R1 applies unchanged.

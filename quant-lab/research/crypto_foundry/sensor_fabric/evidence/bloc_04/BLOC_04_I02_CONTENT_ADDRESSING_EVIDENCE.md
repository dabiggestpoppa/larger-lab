# BLOC 4 — CONTENT ADDRESSING + PATHS + CHECKSUMS EVIDENCE (SENSOR-B4-I02)

Checkpoint: SENSOR-B4-I02 — CONTENT ADDRESSING + PATHS + CHECKSUMS
Branch: `agent/crypto-sensor-fabric-build`
Starting SHA: `75b65dea` (SENSOR-B4-I01R1-RATIFY)
Ending SHA: see ledger / `git log` (I02D)

## 1. Operator authorization

- `SENSOR-B4-I01R1-RATIFY` (75b65dea): operator ACCEPTS
  `PASS_SENSOR_B4_I01R1_STORAGE_CONTRACTS_SEALED` and
  `PASS_SENSOR_B4_I01_STORAGE_CONTRACTS_FROZEN`; authorizes
  **SENSOR-B4-I02 CONTENT ADDRESSING + PATHS + CHECKSUMS ONLY** —
  identity/address mechanics, NO persistence yet.

## 2. Scope (from `06_ACCEPTANCE_TESTS_AND_STAGED_IMPLEMENTATION_COMMITS.md` §11)

Build:

- SHA256 streaming;
- path derivation;
- storage object IDs;
- zstd metadata (encoding suffix is metadata — the source content ID is
  identical for `NONE` and `ZSTD` wrappers).

Tests:

- byte identity;
- path safety;
- large streaming hash.

NOT in scope: no blob writer, no atomic backend, no compression engine, no
manifest repository, no DuckDB/Postgres/Parquet, no network, no filesystem
mutation.

## 3. Package layout (final)

```
quant-lab/src/crypto_sensor_fabric/storage/
    __init__.py      (frozen public exports — now includes checksums + paths)
    enums.py         (+ ChecksumAlgorithm)
    models.py        (SHA-256 syntax validation now delegates to the single
                      shared rule in checksums.validate_sha256_hex)
    checksums.py     (NEW — I02)
    paths.py         (NEW — I02)

quant-lab/tests/crypto_sensor_fabric/storage/
    test_checksums.py  (NEW — I02)
    test_paths.py      (NEW — I02)
```

## 4. Non-negotiable hash doctrine (checksums.py)

- `blob_sha256` is SHA-256 of the EXACT provider-source bytes, computed BEFORE
  any local wrapper compression, pretty printing, JSON reserialization,
  newline normalization, character decoding or projection parsing.
- Three distinct checksum layers are preserved, never conflated:
  - **H1 SOURCE SHA256** — mandatory; defines `EvidenceBlob` identity
    (`sha256_bytes` / `sha256_stream` / `sha256_chunks` / `sha256_file`).
  - **H2 STORED OBJECT CHECKSUM** — optional; validates storage-object bytes
    (wrapper included) later; never compared directly to H1 when a wrapper
    changes stored bytes.
  - **H3 PROVIDER CHECKSUM** — optional; MD5/SHA256/CRC32 published by the
    provider, explicit-algorithm, integrity evidence ONLY
    (`compute_checksum` / `verify_checksum` / `ChecksumAlgorithm`).
- Hash BYTES, never meaning: `sha256_bytes("abc")` raises `TypeError` — no
  implicit Python-string decoding anywhere.
- Empty source payloads are valid evidence (empty provider body may still be
  evidence): `sha256(b"")` is a legal identity, not an error.
- Streaming contract: incremental `read(size)` only (never bare `read()`),
  identical digest to one-shot hashing, works on non-seekable readers, starts
  at the current stream position and never rewinds, does NOT close the
  caller-owned stream, bounded memory (large-stream test hashes a
  1 GiB-equivalent logical input with chunk-bounded reads).

## 5. SHA-256 syntax — ONE shared rule (I02 §19)

`checksums.validate_sha256_hex` is THE single SHA-256 format rule for the whole
storage package (64 lowercase hex chars, format only, no hashing).  `models.py`
now delegates every existing SHA field validator to it (the previous duplicated
local `_validate_sha256_syntax` was removed).  `paths.py` reuses it for blob and
projection object keys.  One validation rule, not three — behavior unchanged,
all I01/I01R1 model invariants re-run green.

## 6. Provider checksums — explicit algorithm, never inferred (I02 §5)

- `ChecksumAlgorithm` enum: `SHA256 | MD5 | CRC32`.
- `checksum_algorithm_from_name`: unknown names fail closed — the algorithm is
  NEVER guessed from digest length, header-name substrings or provider identity.
- Canonical hex forms: SHA256 = 64 lowercase hex, MD5 = 32 lowercase hex,
  CRC32 = 8 lowercase hex with leading zeros retained (`b""` -> `"00000000"`).
- `verify_checksum`: expected value must match the algorithm's canonical form
  (case normalized per algorithm for comparison only); equality is
  constant-time (`hmac.compare_digest`); proves checksum AGREEMENT only, not
  cryptographic authenticity.
- MD5/CRC32 are accepted ONLY as provider integrity evidence — never promoted
  to T0 content identity (`Sha256Result` rejects any non-64-hex digest).

## 7. Content address vs storage key vs local path (I02 §16)

Three identities, never conflated:

1. **CONTENT ID** = `blob_sha256` (64-char source SHA-256);
2. **STORAGE OBJECT KEY** = portable, backend-neutral, slash-separated relative
   key under the storage root (`blobs/sha256/...` or `projections/...`);
3. **RESOLVED LOCAL PATH** = machine-specific root + object key
   (`resolve_under_root`).

Absolute workstation paths are NEVER canonical evidence identity; the data
root must remain movable.

## 8. Blob object key (T0A) — `blob_object_key` (I02 §15)

```
blobs/sha256/<h0h1>/<h2h3>/<full_sha256>.blob       (StorageEncoding.NONE)
blobs/sha256/<h0h1>/<h2h3>/<full_sha256>.blob.zst   (StorageEncoding.ZSTD)
```

- T0A blob location depends ONLY on source content digest + wrapper encoding.
  Provider/sensor/instrument/date values NEVER enter the content-addressed key
  (test-proven: no "provider/sensor/instrument/venue/date" components).
- h0h1 = FIRST two digest chars, h2h3 = NEXT two (no off-by-one slicing).
- Wrapper suffix (`.zst`) is metadata only — the content ID (full digest) is
  identical for both encodings.
- Malformed SHA input fails closed via the single shared rule.

## 9. Projection object key (T0B) — `projection_object_key` (I02 §24)

```
projections/provider=<esc>/venue=<esc>/sensor=<esc>/instrument=<esc>/
granularity=<esc>/year=<YYYY>/month=<MM>/day=<DD>/schema=<esc>/
part-<shard:05d>-<projection_sha256_prefix>.parquet
```

- Date components come from an EXPLICIT caller-adjudicated logical date; no
  date-basis inference (`datetime.now()` / ingested_at / provider timestamp
  never appear).
- `schema_key` is a PREVALIDATED caller-supplied registry key (I05 owns the
  schema-registry hashing doctrine — none is invented here); it is still
  escaped so it can never become a traversal component.
- `shard_id` is deterministic caller input (nonnegative int; zero-padding width
  is formatting only, not scientific).
- `projection_sha256` validated in full; the `hash_prefix_length` (default 8)
  prefix is a documented shorthand, NOT identity (I02 §27 — no schema-hash
  doctrine invented here).

## 10. Path segment escaping — `escape_path_segment` / `unescape_path_segment`

- Deterministic, reversible, UTF-8 preserving, with NO Unicode normalization
  and NO OS-dependent behavior.
- Narrow literal-safe alphabet `A-Z a-z 0-9 _ -`; everything else (`.`, `/`,
  `\`, `%`, `=`, space, Unicode bytes, control bytes) percent-encoded as
  uppercase `%HH` of its UTF-8 bytes.
- Native identity is ESCAPED, never normalized: `BTC/USDT`, `BTC-USDT`,
  `btc-usdt`, `BTC USDT` remain distinct exact strings (injectivity
  test-proven).
- `unescape_path_segment` accepts ONLY the canonical uppercase `%HH` form:
  lowercase/mixed escapes, raw non-safe characters, truncated `%` and
  non-UTF-8 byte sequences are rejected (variants would create multiple
  canonical encodings for one native identity).
- Empty structural coordinates fail closed in `projection_object_key` — empty
  never maps to `unknown`/`none`/`_` (that would invent identity).

## 11. Root containment — `resolve_under_root` (lexical only, zero mutation)

- Rejects: absolute keys, Windows drive prefixes, `..` / `.` / empty segments,
  backslashes, NUL and `:` inside segments.
- Creates NOTHING on disk (test: resolved path does not exist afterwards).
- LEXICAL containment only — symlink-escape hardening is explicitly deferred to
  the later security/hardening checkpoint (SENSOR-B4-I15); no overclaim.

## 12. Public API

New public exports from `crypto_sensor_fabric.storage`:

- checksums: `Sha256Result`, `validate_sha256_hex`, `sha256_bytes`,
  `sha256_stream`, `sha256_chunks`, `sha256_file`, `compute_checksum`,
  `verify_checksum`, `checksum_algorithm_from_name`
- paths: `BLOB_KEY_PREFIX`, `DEFAULT_HASH_PREFIX_LENGTH`, `blob_object_key`,
  `projection_object_key`, `escape_path_segment`, `unescape_path_segment`,
  `resolve_under_root`
- enums: `ChecksumAlgorithm` (SHA256 | MD5 | CRC32)

All 16 frozen I01 models retained, unrenamed; all I01 enum vocabularies
unchanged (`StorageEncoding.NONE/ZSTD` reused for blob keys).

## 13. Tests

Storage tests: **237** (115 from I01/I01R1 + **122 new** I02: byte identity /
streaming == one-shot / chunk-size invariance / bounded reads / non-seekable /
ownership / H1-H2-H3 separation / known vectors / provider-checksum
explicit-algorithm fail-closed / blob + projection exact layouts / escaping
round-trip + injectivity + Unicode-no-normalization / traversal resistance /
lexical root containment / 1 GiB-equivalent bounded streaming hash / all 256
byte values round-trip).

Full `crypto_sensor_fabric` suite: **1616 passed / 0 failed / 1 skipped**
(skip = env-gated live smoke; normal suite makes ZERO network calls).

- ruff: clean on all changed/new files (storage scope).  Pre-existing
  baseline in untouched `test_models.py` (DTZ001 ×2 + I001) documented, not
  hidden.
- changed-scope mypy: clean on all changed/new files (checked one test file at
  a time per the known `test_adapter` duplicate-basename gotcha).  Only the
  known pre-existing baseline in untouched Bloc 2 modules (yaml stubs ×3 +
  planner overload ×1) remains.

## 14. Constraints honored

- network calls: 0
- filesystem mutation by storage runtime: 0 (pure functions; tests prove
  resolved paths are not created)
- no compression implementation (zstd appears ONLY as the `.blob.zst` key
  suffix metadata)
- no atomic write backend, no blob store, no manifest repository, no
  DuckDB/Postgres/Parquet, no query/replay
- provider code: UNCHANGED
- revision policy, T0A/T0B authority, acquisition != blob identity,
  integrity != coverage, missing != zero, no canonical market semantics,
  no date-basis inference, no schema-hash doctrine: all unchanged
- I01 + I01R1 evidence: preserved untouched
- I03 (atomic filesystem backend): NOT started

## 15. Proposed verdict

`PASS_SENSOR_B4_I02_CONTENT_ADDRESSING_PATHS_CHECKSUMS` — T0 evidence is now
IDENTIFIED and ADDRESSED (content-addressed blob keys + safe reversible path
encoding + exact-byte SHA-256 identity primitives), still without any
persistence backend.

Readiness state: `STORAGE_MODEL_CONTRACTS_READY = TRUE` ·
`CONTENT_ADDRESSING_READY = TRUE` · `PATH_CONTRACT_READY = TRUE` ·
`CHECKSUM_PRIMITIVES_READY = TRUE` · `T0A_STORAGE_IMPLEMENTED = FALSE` ·
`T0B_STORAGE_IMPLEMENTED = FALSE` · `ATOMIC_BACKEND_IMPLEMENTED = FALSE` ·
`MANIFEST_REPOSITORY_IMPLEMENTED = FALSE`.
`next_checkpoint_authorized = FALSE`; recommended next: **SENSOR-B4-I03
ATOMIC FILESYSTEM BACKEND** (NOT started).

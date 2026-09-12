# BLOC 4 — CANONICAL PATH DECODING + COLLISION-FREE PROJECTION ADDRESS SEAL EVIDENCE (SENSOR-B4-I02R1)

Checkpoint: SENSOR-B4-I02R1 — CANONICAL PATH DECODING + COLLISION-FREE PROJECTION ADDRESS SEAL
Branch: `agent/crypto-sensor-fabric-build`
Starting SHA: `7b6926c39ed8575526f397bfd1f97a43aca9637a` (SENSOR-B4-I02F, empty CI re-trigger commit)
Ending SHA: see ledger / `git log` (I02R1C)

## 1. Chronology

```
I02 original        -> content addressing + paths + checksums frozen
                       (BLOC_04_I02_CONTENT_ADDRESSING_EVIDENCE.md, immutable)
operator review     -> HOLD_PASS_SENSOR_B4_I02_CONTENT_ADDRESSING_PATHS_CHECKSUMS_PENDING_I02R1_CANONICAL_PATH_SEAL
I02R1 correction    -> this artifact: two narrow address-safety contradictions sealed
                       BEFORE I03 persists any path to a filesystem
```

The original I02 evidence is preserved as history; it is not erased or rewritten.
This artifact supersedes only the two affected address details.

## 2. Original seams (exact)

### Defect A — non-canonical decoder (over-escaped safe characters)

`unescape_path_segment` accepted percent escapes whose decoded byte belongs to
the literal-safe alphabet:

- `"%41"` decoded to `"A"` although `escape_path_segment("A") == "A"`;
- same for `"%61"`→`a`, `"%30"`→`0`, `"%5F"`→`_`, `"%2D"`→`-`.

That violated the one-canonical-encoding-per-native-string contract: `"A"` and
`"%41"` were two valid encodings of one identity.

### Defect B — projection object key prefix collision

`projection_object_key` defaulted to an 8-hex projection SHA prefix
(`DEFAULT_HASH_PREFIX_LENGTH = 8`). Two different full projection SHA256
values sharing the same prefix, same logical partition coordinates and same
shard produced the SAME physical object key — a display shorthand was allowed
to become a physical identity collision.

## 3. Final decoder rule (defect A repair)

`unescape_path_segment` is now CANONICAL. Decode is byte-structural:
per `%HH` escape, if the decoded byte belongs to the literal-safe alphabet
(`A-Z a-z 0-9 _ -`), the segment is REJECTED as over-escaped. Concretely
rejected: `%41`, `%61`, `%30`, `%5F`, `%2D`. Still rejected (unchanged):
lowercase/mixed-case escapes (`%hh`, `%Hh`), truncated `%`, invalid hex, raw
slash/backslash/space/Unicode outside the literal-safe alphabet, non-UTF-8
byte sequences. NUL remains round-trippable only via its canonical `%00` form.

## 4. Canonicality invariant (I02R1 §4, test-frozen)

For every valid canonical encoded segment `E`:

```
escape_path_segment(unescape_path_segment(E)) == E
```

Both bijection directions are property-tested over a deterministic corpus
(§7 of the checkpoint): `decode(encode(x)) == x` (reversibility) AND
`encode(decode(E)) == E` for canonical `E` (canonicality). Unicode
normalization remains absent; native identity stays escaped, not normalized.

## 5. Final projection key layout (defect B repair)

```
projections/provider=<esc>/venue=<esc>/sensor=<esc>/instrument=<esc>/
granularity=<esc>/year=<YYYY>/month=<MM>/day=<DD>/schema=<esc>/
part-<shard:05d>-<FULL_projection_sha256>.parquet
```

- `hash_prefix_length` parameter and `DEFAULT_HASH_PREFIX_LENGTH` constant
  REMOVED from the canonical API (`__init__` exports updated).
- The full 64-char validated digest is the filename component; no uppercase,
  no `sha256:` prefix, no truncation, no random UUID, no wall clock.
- No compatibility alias / migration required (no real T0B persisted yet).

## 6. T0A key regression (I02R1 §15)

`blob_object_key` layout is UNCHANGED and regression-proven byte-for-byte:

```
blobs/sha256/<h0h1>/<h2h3>/<full_sha256>.blob[.zst]
```

## 7. Long path-component policy (I02R1 §16)

Pure audit only. Realistic production coordinates (provider/venue/sensor/
instrument/granularity + escaped schema key + 64-char digest) stay well below
common filesystem component limits (255 bytes). For adversarial extremely long
native IDs: pure escaping keeps full round-trip; the filesystem backend (I03)
must fail closed on overlong components rather than truncate.

```
LONG_COMPONENT_CHECK_REQUIRED_IN_I03 = TRUE
```

No hashing/truncation of native identity was introduced to make anything fit.

## 8. Unchanged contracts (regression-proven)

- SHA256 primitives, H1/H2/H3 separation, provider checksum algorithms:
  UNCHANGED (I02R1 §18-§19 — no new algorithms).
- `escape_path_segment` algorithm: UNCHANGED.
- `resolve_under_root`: lexical containment only; symlink hardening stays
  with I15 (I02R1 §17).
- T0A blob key layout: byte-for-byte unchanged (§6 above).
- No random UUID, no wall clock, no date-basis inference, no schema-registry
  hash doctrine invented.

## 9. Validation results (this checkpoint)

- Storage path tests: **109 passed** (35 new I02R1A canonical-decoder/bijection
  tests + collision/full-hash I02R1B tests on top of the I02 suite).
- Full `crypto_sensor_fabric` suite: **1638 passed / 0 failed / 1 skipped**
  (>= 1616 floor; skip = env-gated live smoke; network 0).
- ruff (changed scope: paths.py, storage/__init__.py, test_paths.py): clean.
- mypy (changed scope): clean on paths.py; only the pre-existing baseline in
  untouched `probes/planner.py:79` remains.
- Local/repo test result reported separately from external CI status
  (SonarCloud/Kilo are external integration checks, historically flaky —
  not conflated with storage test results).

## 10. Constraints honored

- network calls: 0
- filesystem mutations by storage runtime: 0 (pure functions only)
- provider code: UNCHANGED
- I02 original evidence: preserved untouched
- I03 (atomic filesystem backend): NOT started — no mkdir, no staging, no
  blob writes, no compression, no fsync, no rename, no durable-evidence
  verification, no immutable write guards.

## 11. Proposed verdicts

- I02R1 (this checkpoint): `PASS_SENSOR_B4_I02R1_CANONICAL_PATHS_SEALED`
- Proposed operator acceptance of the parent checkpoint:
  `PASS_SENSOR_B4_I02_CONTENT_ADDRESSING_PATHS_CHECKSUMS`

Readiness state: `STORAGE_MODEL_CONTRACTS_READY = TRUE` ·
`CONTENT_ADDRESSING_READY = TRUE` · `PATH_CONTRACT_READY = TRUE` ·
`CHECKSUM_PRIMITIVES_READY = TRUE` · `T0A_STORAGE_IMPLEMENTED = FALSE` ·
`ATOMIC_BACKEND_IMPLEMENTED = FALSE` · `MANIFEST_REPOSITORY_IMPLEMENTED = FALSE`
· `next_checkpoint_authorized = FALSE`.

Recommended next checkpoint: **SENSOR-B4-I03 — ATOMIC FILESYSTEM BACKEND**
(NOT started; operator authorization required).

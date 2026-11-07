# OCE Golden System — Block 6 P0 Versioning and Compatibility Contract — v1.0

**Document ID:** OCE-B6-P0-VERSIONING-001
**Version:** 1.0
**Stage:** `AUTHORIZED_STAGE=BOOK_6-P0-PLANNING_ONLY`
**Machine copy:** `OCE_BLOCK_06_P0_COMPATIBILITY_AND_REPRODUCIBILITY_PLAN_v1.0.json`

This contract is a planning law. No compatibility claim is proven at P0 and the matrix
contains only `UNPROVEN` rows.

## 1. Version law

| Field | Law |
|---|---|
| Package version | `semver` `MAJOR.MINOR.PATCH` with a stage tag while pre-1.0, for example `0.1.0` at B6-I1 |
| API version | path-versioned surface (`v1`); additive changes only inside a major |
| Schema version | integer version plus a content hash on every schema |
| Artifact identity | SHA-256 over LF-normalised bytes plus byte size, per file and per bundle |
| Structural fingerprint | sorted symbol inventory hashed with schema versions |
| Backward compatibility | a consumer pinned to a supported version keeps working or is refused explicitly |
| Forward compatibility | not promised; unknown newer versions are refused, never guessed |
| Deprecation | announced in the matrix, at least one minor cycle, refusal after removal |
| Removal | major version only, with a migration note and an operator decision |
| Migration evidence | per-consumer record naming old and new version and the passing test |
| Unsupported version | explicit named refusal; silent selection of the latest is forbidden |

## 2. Compatibility matrix (planning schema only)

The matrix has 25 rows, one per Block 6 section, with columns `surface`, `version`,
`supported_from`, `supported_to`, `consumer_evidence`, `state`. Every row is `UNPROVEN` and
`consumer_evidence` is `none`. This is a schema, not a promise: a later stage replaces a row
only with recorded evidence, and an unsupported version must fail clearly rather than fall
back.

## 3. Refusal semantics

A compatibility check returns one of three outcomes: supported, unsupported-with-reason, or
unknown. Unknown is never treated as supported. A consumer whose version cannot be resolved
is refused with the detected version and the supported window in the message, so the operator
can act without reading source code.

## 4. Change classes

- **Patch**: no surface change; evidence is a passing consumer test.
- **Minor**: additive surface; evidence is the new symbol, its documentation, its tests and an
  unchanged existing consumer.
- **Major**: breaking change; requires a migration note, a deprecation cycle, an operator
  decision and a new matrix row set.
- **Emergency refusal**: a security-driven removal may skip the deprecation cycle only with a
  recorded operator decision; it still requires a new major version.

## 5. What P0 does not claim

No version has been published, no consumer exists, no matrix row is proven, no signing key
exists and no registry is configured. Any statement that a consumer is compatible today would
be a fabricated compatibility claim and is prohibited.

# OCE Golden System — Block 6 P0 Reproducibility and Provenance Plan — v1.0

**Document ID:** OCE-B6-P0-REPRO-001
**Version:** 1.0
**Stage:** `AUTHORIZED_STAGE=BOOK_6-P0-PLANNING_ONLY`
**Machine copy:** `OCE_BLOCK_06_P0_COMPATIBILITY_AND_REPRODUCIBILITY_PLAN_v1.0.json`

Determinism is a measurable property: a deterministic build from the same declared inputs and
the same generator version produces byte-identical output. Reproducibility is a second, stronger property: an independent
clean build from the same commit produces the same bytes, verified by SHA-256 per file. Neither
is claimed for Book 6 at P0; both are planning obligations.

## 1. Required properties

| Property | Planning obligation |
|---|---|
| Deterministic build | sorted keys and rows, LF normalisation, no timestamps, hosts, users, absolute paths or random IDs |
| Pinned dependencies | every dependency version-pinned and hashed |
| Offline tests | the test surface runs with no network; absence of network is not a failure |
| Source-to-artifact traceability | the artifact names its commit, tree and generator version |
| Hash and size manifest | per-file SHA-256 and byte size, recomputed from bytes, never typed |
| Dependency inventory | recorded inventory when governing sources require it, with licence per entry |
| Licence inventory | every dependency carries a recorded licence and a refusal path if absent |
| Provenance attestation | the artifact is bound to its source and builder identity |
| Signing policy | signing is deferred and operator-only; no key exists at P0 |
| Clean-build verification | builds run only from a clean checkout |
| Two-build comparison | two independent builds are compared byte-wise; any difference refuses release |
| Secret scan | no credential, token or key in any artifact or log |
| Vulnerability review | recorded review before any publication decision |
| Release immutability | a released artifact is never rewritten |
| Rollback and yank | yank is recorded; history is never rewritten |

## 2. Manifest rules

A manifest row is `path`, `sha256`, `size`, `kind`. The validator recomputes every row; a row
that disagrees with the bytes blocks the packet. No wildcard, no directory digest substituting
for per-file rows, no excluded file without a recorded reason.

## 3. Provenance rules

Every future artifact records: source commit and tree, generator version, dependency inventory
digest, build environment identity, and the exact command that produced it. A provenance claim
without a resolvable source identity is treated as absent, not as probable.

## 4. Cost and providers

Reproducibility must not depend on an external service. No registry client, no hosted cache, no
signing service and no recurring cost is introduced by Book 6 planning. If a later stage needs
one, it stops for an operator decision rather than provisioning it.

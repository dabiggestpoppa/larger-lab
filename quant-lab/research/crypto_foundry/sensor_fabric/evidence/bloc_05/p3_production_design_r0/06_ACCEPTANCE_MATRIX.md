# ACCEPTANCE MATRIX

## 1. Result semantics — separate claims, never one badge

Four things are routinely confused. Production must keep them apart in the type system and in every docstring.

| Claim | Field(s) | Owner | Means | Does **not** mean |
|---|---|---|---|---|
| **Field binding** | `decision = ACCEPT_FIELD_BINDING`, `verified_field_allowlist` | verifier derives, consumer reports | the named canonical fields were re-derived from the approved row and their transformations re-executed | that the record is authentic, complete, or operator-authorized |
| **Synthetic / non-authoritative** | *(absent from production)* | — | — | in the harness, `SYNTHETIC_TEST_ONLY` marks a capability that certifies nothing; production removes the state entirely rather than shipping a weakened one |
| **Authorization** | `custody_source_authorized: bool`, `custody_source_authorization_status ∈ {AUTHORIZED, INTEGRATION_REQUIRED, UNAUTHORIZED}` | policy derives from pinned manifest bytes | an approved operator-authority record covers *this* artifact, approval, registry, record kind, provider and cutoff | that the evidence was intact (`custody_verified`) or that the fields bound (`ACCEPT_FIELD_BINDING`) |
| **Downstream trust** | `RecordVerification.downstream_trusted` + `unverified_dimensions` | verifier sets under its own laws | the in-scope prerequisites held and the non-scope dimensions are enumerated | whole-record authentication; `LINEAGE`, `INSTRUMENT_IDENTITY`, `SOURCE_REVISION` stay unverified unless separately proven |

**Law:** `ACCEPT_FIELD_BINDING` with `custody_source_authorized=False` is a valid, expected outcome (today it is the *only* reachable one). `AUTHORIZED` never appears without `custody_verified=True`. Neither implies `downstream_trusted`.

## 2. Decision table

| trust_scope | unverified_dims | evidence bytes | fields | PIT | replay | custody verified | custody authority | Decision |
|---|---|---|---|---|---|---|---|---|
| ≠ ECO | — | — | — | — | — | — | — | REFUSE `FORGED_TRUST_SCOPE` |
| ECO | empty | — | — | — | — | — | — | REFUSE `EMPTY_UNVERIFIED_DIMENSIONS` |
| ECO | ok | missing | — | — | — | — | — | REFUSE `EVIDENCE_BYTES_MISSING` |
| ECO | ok | mismatch | — | — | — | — | — | REFUSE `EVIDENCE_BYTES_MISMATCH` |
| ECO | ok | ok | missing | — | — | — | — | REFUSE `FIELD_NOT_IN_ALLOWLIST` |
| ECO | ok | ok | ok | inadmissible | — | — | — | REFUSE `PIT_INADMISSIBLE` |
| ECO | ok | ok | ok | ok | blocked | — | — | REFUSE `REPLAY_BLOCKED` |
| ECO | ok | ok | ok | ok | ok | **False** | any | REFUSE `VERIFICATION_FAILED` (custody is a prerequisite of acceptance) |
| ECO | ok | ok | ok | ok | ok | True | INTEGRATION_REQUIRED | **INTEGRATION_REQUIRED** (no refusal — nothing was violated; authority is absent) |
| ECO | ok | ok | ok | ok | ok | True | UNAUTHORIZED | REFUSE `UNAUTHORIZED_CUSTODY_SOURCE` |
| ECO | ok | ok | ok | ok | ok | True | AUTHORIZED | **ACCEPT_FIELD_BINDING**, `custody_source_authorized=True` |

**Order is part of the contract.** PIT and replay are adjudicated **before** authority, so an inadmissible record is refused whatever the custody source claims. The table above is the normative order.

## 3. Exception handling — fail closed, bounded diagnostics

| Situation | Behaviour |
|---|---|
| `RecordVerificationError` (typed refusal from the verifier) | REFUSE with the mapped reason; detail = the verifier's own message, bounded |
| `SemanticAuthorityRefusal` / `AuthorityRefusal` | REFUSE `VERIFICATION_FAILED` with mapped refusal; under the empty manifest this is the *expected* path |
| Naive/bare-date cutoff | REFUSE `NAIVE_CUTOFF` |
| Unexpected exception (bug, `MemoryError`, third-party) | REFUSE `VERIFIER_CRASH`; detail = exception class + first 200 chars; **no traceback, no repr of payloads**, never an accept |
| Store read raises | REFUSE `EVIDENCE_BYTES_MISSING` with reference name only |
| Everything else | REFUSE |

**Diagnostics bound.** Detail strings are truncated, never include artifact bytes, manifests, or evidence content, and never include a digest the caller did not already supply. Rationale: a trust boundary that leaks payload in an error string is an exfiltration channel.

**Never** does a `try/except` in the consumer convert an error into acceptance, and never does it swallow `KeyboardInterrupt`/`SystemExit` (those propagate).

## 4. Conformance mapping — harness attack IDs to production requirements

| Harness evidence | Production requirement | Rung |
|---|---|---|
| AT43/AT53–AT57 capability forging | spec E, §5; A3.2–A3.3 | 3 |
| CAP01 direct mint / CAP02 marker copy / CAP08b provider / CAP12 record kind | §5, spec I | 3 |
| RG08 forged replay evaluation | spec H; A4.2 | 4 |
| P2B-11 digest-only custody | spec G; A4.1 | 4 |
| F-R1-01 custody object's own report | preserved via `_custody_verified` | 2 |
| §4 cached/deserialized divergence | spec F; A2.4 | 2 |
| §6 PIT/replay before authority | §2 decision table; A4.3 | 4 |
| §7 evidence rebinding | spec G | 4 |
| three-outcome decision taxonomy | A1.2 | 1 |

## 5. Definition of done for the *design* (this checkpoint)

- [x] Architecture, boundary spec, threat model, rungs, acceptance matrix, risk register, code paths published.
- [x] Existing production ownership identified and marked REUSE; no duplication proposed.
- [x] `rederive` callback rejected as a provenance guarantee, with the replacement argument.
- [x] Capability-marker model replaced by derivable authorization, with the out-of-scope claim stated plainly.
- [x] Empty-manifest `INTEGRATION_REQUIRED` treated as a fact, not a defect.
- [ ] No production code written (deliberate).

## 6. Definition of done for *authorization to consume* (not this checkpoint)

Requires an approved operator-authority artifact in the manifest, a custody provider under independent control, and Rung 7 acceptance — none of which exists. A passing test never grants this.

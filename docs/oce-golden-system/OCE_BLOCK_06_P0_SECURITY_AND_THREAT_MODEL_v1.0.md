# OCE Golden System — Block 6 P0 Security and Threat Model — v1.0

**Document ID:** OCE-B6-P0-THREAT-001
**Version:** 1.0
**Stage:** `AUTHORIZED_STAGE=BOOK_6-P0-PLANNING_ONLY`
**Machine copy:** `OCE_BLOCK_06_P0_FAILURE_AND_THREAT_REGISTRY_v1.0.json`

No mitigation in this document is implemented. Each row names the asset, what an attacker can
do, where the trust boundary sits, the refusal required, the planned proof and the evidence
that would later be produced. `mitigation_state` is `PLANNED_NOT_IMPLEMENTED` for all twenty.

## 1. Threats

| ID | Threat | Asset | Trust boundary | Required refusal |
|---|---|---|---|---|
| T01 | Path traversal | filesystem | archive boundary | reject escaping entry |
| T02 | Symlink escape | filesystem | archive boundary | reject escaping link |
| T03 | Malicious archive | build host | archive boundary | reject hostile archive |
| T04 | Dependency confusion | install set | resolution boundary | pin and verify source |
| T05 | Namespace collision | symbol space | publish boundary | refuse duplicate name |
| T06 | Package substitution | artifact identity | retrieval boundary | refuse digest mismatch |
| T07 | Manifest tampering | evidence | evidence boundary | refuse mismatched row |
| T08 | Provenance forgery | provenance | attestation boundary | refuse unbound attestation |
| T09 | Secret leakage | credentials | publication boundary | refuse and rotate |
| T10 | Unsafe deserialization | runtime | input boundary | refuse untyped decode |
| T11 | Dynamic imports | runtime | code boundary | refuse undeclared import |
| T12 | Plugin injection | runtime | plugin boundary | refuse uncertified plugin |
| T13 | Arbitrary code execution | host | execution boundary | refuse execution surface |
| T14 | Environment-variable authority | configuration | config boundary | refuse implicit authority |
| T15 | Unbounded inputs | resources | resource boundary | refuse over limit |
| T16 | Denial of service | availability | resource boundary | bound and quarantine |
| T17 | Nondeterministic outputs | evidence | determinism boundary | refuse differing rebuild |
| T18 | Stale compatibility metadata | compatibility | compatibility boundary | refuse unsupported claim |
| T19 | Unauthorized publication | release | release boundary | refuse publication |
| T20 | Authority-bearing extraction | governance | authority boundary | refuse extraction |

## 2. Trust boundaries

Six boundaries carry the model: the archive boundary (F13, F14, F21), the resolution boundary
(F06–F08, F20), the artifact and evidence boundary (F11, F12, T07, T08), the runtime boundary
(T10–T13, F18), the resource boundary (T15, T16), and the governance boundary (F01–F04, F22,
F23, T20). A control that sits on the wrong boundary is not a mitigation; it is a bypass with
extra steps.

## 3. Refusal law

Refusal is explicit and named. The system never degrades a security refusal into a warning, a
retry with relaxed parameters, or an environment-dependent fallback. Unknown identity, unknown
version, absent evidence and ambiguous target all fail closed, consistent with the
constitution's deny-by-default article.

## 4. What is deliberately absent

No network service, no registry client, no signing key, no plugin loader and no dynamic import
surface is designed at P0. Those are exactly the surfaces that would create a new authority or
a recurring cost, and the authority map forbids both. Book 6 may later add a local-only,
operator-release-gated publication path, and that decision belongs to the operator, not to a
builder agent.

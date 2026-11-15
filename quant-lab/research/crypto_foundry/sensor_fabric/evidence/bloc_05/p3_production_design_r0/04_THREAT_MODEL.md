# PRODUCTION THREAT MODEL

## 1. Principals

| Principal | Capabilities | Trusted for |
|---|---|---|
| **T1 Untrusted data** | record payloads, artifact bytes, evidence blobs, manifest bytes arriving with a record | nothing |
| **T2 Public API caller** | builds requests, chooses fields, supplies replay evidence objects, may hold cached verdicts | nothing; its claims are inputs to be checked |
| **T3 Trusted application code** | loads the policy, holds the pinned root, owns the custody provider, calls `evaluate` | the *composition* it performs: which verifier, which root, which store |
| **T4 Privileged in-process code** | arbitrary Python under the same interpreter: `model_construct`, `object.__setattr__`, monkeypatching, importing internals | nothing, and **cannot be constrained** by a data boundary |

The distinction that matters: **T2 is adversarial; T3 is trusted only in its wiring, and even T3's claims about individual records are re-derived; T4 is out of scope.**

## 2. Enumerated attacks

### Prevented (must refuse, and refusal is testable)

| ID | Attack | Principal | Control |
|---|---|---|---|
| A01 | Forged verdict via factory callback (`rederive` returns `model_copy`) | T2 | no callback exists; policy derives (spec C) |
| A02 | `RecordVerification.model_construct(...)` handed in as `candidate` | T2 | candidate is compared, never used; divergence refuses |
| A03 | `assert_trustworthy()` bypass / contradictory verdict | T2 | policy calls `assert_trustworthy()` on the derived verdict, which is verifier-produced and passes |
| A04 | Caller supplies manifest bytes so approval follows the record | T2/T1 | policy uses its own pinned bytes; claimed bytes only compared (spec A) |
| A05 | Direct `_issue()` capability minting | T2 | no capability object in production (spec §5) |
| A06 | Copying the issuance marker (`object.__setattr__`, `dataclasses.replace`) | T2 | nothing to copy; authorization recomputed from pinned bytes |
| A07 | Cross-record authority reuse (same evidence, different record kind/provider) | T2 | identity tuple bound into derivation (spec I) |
| A08 | Cross-cutoff authority inheritance | T2 | cutoff bound; change ⇒ `INTEGRATION_REQUIRED` |
| A09 | `SYNTHETIC_TEST_ONLY` promoted to authorized | T2/T1 | basis does not exist in `src/` (spec E) |
| A10 | Trust-scope laundering (`trust_scope` ≠ `ECONOMIC_FIELD_BINDING`) | T1 | inspection 1 refuses `FORGED_TRUST_SCOPE` |
| A11 | Empty `unverified_dimensions` read as whole-record authentication | T1 | inspection 2 refuses |
| A12 | Field not actually verified but demanded by caller | T2 | `FIELD_NOT_IN_ALLOWLIST` |
| A13 | Evidence bytes swapped after verification | T1/T2 | rebinding (spec G) |
| A14 | Digest-only "custody" (no bytes held) | T1 | rebinding requires readable bytes; missing ⇒ refuse |
| A15 | Forged replay evaluation object | T2 | flattened to `NOT_POLICY_DERIVED`, blocked (spec H) |
| A16 | Stale cached verdict after revocation / cutoff move | T2 | re-derivation each call; cache never authoritative |
| A17 | PIT-inadmissible record consumed because custody looked fine | T1 | PIT and replay adjudicated **before** authority |
| A18 | Verifier raises; consumer degrades open | any | `_fail_closed` maps to REFUSE with bounded detail (spec §3 of 06) |
| A19 | Silent provenance gap (`authority_provenance is None`) | T1 | verifier refuses `PROVENANCE_MISSING` |
| A20 | Empty manifest treated as "no restrictions" | T3 misdesign | `INTEGRATION_REQUIRED` is the computed result, not a default |

### Out of scope (documented, not defended)

| ID | Condition | Why out of scope |
|---|---|---|
| X01 | T4 constructs a policy with a rooted context over its own manifest bytes | The pin is a compile-time constant; T4 can rewrite constants. Application security cannot survive arbitrary code execution in-process. |
| X02 | T4 monkeypatches `evidence_digest`, `assess_replay_eligibility`, or the verifier | Same. Mitigation is process isolation and code review, not a Python sentinel. |
| X03 | T4 replaces the `TrustedCustodyProvider` instance | The store is T3-supplied wiring; a hostile wiring is a compromised process. |
| X04 | Side-channel/DoS via huge records or pathological evidence counts | Availability, not integrity. Bound inputs at the API edge; separate checkpoint. |
| X05 | Physical/host compromise, key theft, supply-chain compromise of dependencies | Outside the application boundary. |
| X06 | Semantics of a *future* approved operator authority (how an operator becomes approved) | Governance, not code. This repository ships an empty manifest; minting authority is a custody process. |

**Bounded claim to state plainly in the code docstring:** *this is a data boundary inside one process. It resists a hostile caller and hostile data. It does not resist code running with the application's privileges, and no in-process Python mechanism can.*

## 3. What the current harness does not prevent but production does

| Class | Harness behaviour | Production |
|---|---|---|
| Callback provenance | `rederive()` trusted after the fact; `assert_trustworthy` catches some forgeries | verification is derived; no intake of verdicts |
| Capability minting | private `_issue` + module marker; explicitly bounded | no capability object; recomputation is the only path |
| Marker copying | marker is a module-private `object()`; copy ⇒ `is_issued` True if the marker object is reachable | nothing to copy |
| Cross-cutoff reuse | checked by comparing `capability.knowledge_cutoff != knowledge_cutoff` | cutoff is an input to the derivation, not a field to compare |
| Manifest substitution | context pin refuses foreign bytes (good) | same, plus claimed bytes are never adopted |

## 4. Residual risk after R0

1. **Empty-manifest deadlock.** With no approved operator artifact, every production consumption returns `INTEGRATION_REQUIRED`. That is correct and is also the reason this design cannot be "finished" by code alone (`07_RISK_REGISTER.md` R-04).
2. **Harness/production semantic drift.** Two implementations of the same policy invite divergence (`R-06`). Mitigation: the acceptance matrix runs the *same* attack fixtures against both, and the harness is later re-pointed at the production policy as its oracle.
3. **T4.** Unchanged and unavoidable; must be stated, not hidden (`R-03`).

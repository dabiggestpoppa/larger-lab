# P3 PRODUCTION TRUST CONSUMER — DESIGN R0

**Checkpoint:** SENSOR-B5-P3-PRODUCTION-TRUST-CONSUMER-DESIGN-R0
**Base:** `6de26be9130eb99e0a9b53b340fc5bfaafa4a684` (consolidated candidate)
**Branch:** `agent/crypto-sensor-fabric-p3-production-design-r0`
**Nature:** documentation only. Zero production source changes.

| # | Document | Answers |
|---|---|---|
| 01 | `01_ARCHITECTURE.md` | What exists, what the gap is, the target shape and its four rules |
| 02 | `02_RESPONSIBILITY_MATRIX.md` | Which module owns each of D01–D20, and what must not be duplicated |
| 03 | `03_TRUST_BOUNDARY_SPEC.md` | Boundaries A–J, the `rederive` decision, and the capability replacement |
| 04 | `04_THREAT_MODEL.md` | Principals, attacks A01–A20, out-of-scope X01–X06, residual risk |
| 05 | `05_IMPLEMENTATION_RUNGS.md` | Rungs 1–7 with entry criteria, acceptance and stop conditions |
| 06 | `06_ACCEPTANCE_MATRIX.md` | Result semantics, the normative decision table, exception policy |
| 07 | `07_RISK_REGISTER.md` | R-01…R-14, residual risks, accounting for this checkpoint |
| 08 | `08_PROPOSED_CODE_PATHS.md` | Three new modules, full component plan, interface sketches, reuse ledger, effort |

## Reference lock

| Artefact | SHA |
|---|---|
| Consolidated candidate | `6de26be9130eb99e0a9b53b340fc5bfaafa4a684` |
| Canonical evidence | `5c38d0d6396e7cd9b70d5970272475fa975e16e7` |
| Historical producer verification | `b76ba80683b12072c22ab0b379a2204a99dc64b1` |
| R6 implementation | `9d289500fd7bdd4145d2b9d5e052b93e471cd1f1` |
| R6 boundary audit | `ced44a1a9e27ffff1da2f1afc164e3442abd2a35` |
| Production baseline | `f199a7e3f7d92ce555fb436343d24bd42907c3a8` |

## The three findings that drive the design

1. **The `rederive` callback is not a provenance guarantee.** Production replaces it with derivation: the consumer calls the verifier itself and never accepts a verdict object.
2. **An in-process issuance marker cannot be protected.** Production removes the object entirely and recomputes authorization from pinned manifest bytes, so a forged capability is worth exactly nothing.
3. **`SYNTHETIC_TEST_ONLY` must not ship.** It is a harness affordance; in production the only outcomes are `AUTHORIZED`, `INTEGRATION_REQUIRED`, `UNAUTHORIZED`.

## Status

Design complete, implementation **not** started. Under the shipped empty approval manifest every consumption resolves to `INTEGRATION_REQUIRED` — a custody fact, not a defect, and not something code in this repository can resolve.

No production merge, no provider approval, no custody authorization, no trust promotion, no program-gate advancement, no self-ratification. This checkpoint does not close the independent R6 security audit.

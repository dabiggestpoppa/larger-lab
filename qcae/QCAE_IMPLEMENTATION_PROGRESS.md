# QCAE Implementation Progress Ledger

**Branch:** `qcae-capability-acquisition-engine`
**Canon:** QCAE v0.1 (Blocks 0–18, COMPLETE / FROZEN) under `qcae/books/`
**Build mode:** BUILD MODE per master prompt; phases P0→P12 strictly sequential.

---

## Current Phase

**P0 — Skeleton + Domain Schemas**

Governing canon for this phase:

- Book I, Block 0 — Constitution (lifecycle 0.5, evidence doctrine 0.4, authority 0.3)
- Book I, Block 1 — Capability Model (1.1 contracts, 1.2 atoms, 1.3 graph)
- Book V, Block 15 — 15.1 package topology, 15.2 core domain boundaries
- Book VI, Block 18 — 18.1 phase sequencing, 18.2 entry/exit criteria, 18.3 evidence matrix

### P0 Checklist

- [x] P0-I0 progress ledger + implementation decision records
- [ ] P0-C01 package skeleton per Book V 15.1 + test wiring
- [ ] P0-C02 base error taxonomy + schema-versioned serialization base
- [ ] P0-C03 LifecycleState machine + transition guards (canon 0.5)
- [ ] P0-C04 CapabilityContract (canon 1.1.4 fields, versioning, req/pref/forbidden)
- [ ] P0-C05 CapabilityAtom (1.2.22), CompositeCapability (1.2.10–11), Candidate
- [ ] P0-C06 Relationship (1.3.4), EntityRef (1.3.3/1.3.16), EvidenceRef (0.4.2/0.4.3)
- [ ] P0-C07 AcquisitionDecision (0.5.12), Authority primitives (0.3), Job/Step identity
- [ ] P0-T01 architecture/dependency guard tests (canon 15.2 forbidden deps)
- [ ] P0-FREEZE freeze manifest + full suite green + ledger current

### P0 Exit Gate (canon 18.2 + master prompt §28)

- core package structure exists
- canonical domain objects exist and are schema-versioned
- lifecycle rules explicit and centrally testable
- serialization round trips work (including schema-version rejection)
- all P0 tests pass
- no external provider implementation leaked into core (guard-tested)
- progress ledger current
- deviations from canon: zero or explicitly approved (see below)
- coherent enough for P1 (Evidence + Registry Spine) to build directly on top

---

## Commit Log

| Commit | Phase-Intent | Purpose |
| --- | --- | --- |
| (pending) | P0-I0 | progress ledger + ADR-0001/0002 |
| (pending) | P0-C01 | package skeleton + test wiring |
| (pending) | P0-C02 | error taxonomy + serialization base |
| (pending) | P0-C03 | lifecycle machine + transition guards |
| (pending) | P0-C04 | capability contract domain |
| (pending) | P0-C05 | atoms + composites + candidates |
| (pending) | P0-C06 | relationships + evidence refs |
| (pending) | P0-C07 | acquisition decisions + authority + job/step |
| (pending) | P0-T01 | architecture dependency guards |
| (pending) | P0-FREEZE | phase freeze manifest |

---

## Test Ledger

| Suite | Tests | Passed | Failed | Skipped | Commit |
| --- | --- | --- | --- | --- | --- |
| (pending first run) | | | | | |

Important adversarial tests to include:

- illegal lifecycle transition rejected (every non-adjacent jump)
- waivable gate (DOMAIN_VERIFIED only) rejected without policy justification
- contract with behavior listed both required and forbidden rejected
- contract with empty required behaviors rejected
- atom identity independent of implementation (same atom, different candidates)
- composite with single-member alternative group rejected
- composite with required atom inside alternative group rejected
- relationship with type outside controlled vocabulary rejected
- evidence ref with malformed artifact hash rejected
- schema-version mismatch / unknown object type rejected on deserialize
- core importing a forbidden provider module fails the architecture guard

---

## Evidence Artifacts (canon 18.3 Phase 0 matrix)

- [ ] schema snapshots (serialized form of each domain object, in freeze manifest)
- [ ] lifecycle transition test evidence
- [ ] architecture/dependency guard test evidence
- [ ] serialization round-trip evidence
- [ ] P0 freeze manifest (machine-readable: test run, SHAs, deferred items)

---

## Implementation Decision Records

- ADR-0001 — core domain uses stdlib dataclasses + explicit validation; no pydantic/dataclass-library dependency in `qcae/core`
- ADR-0002 — `qcae` package importable from repo root; tests under `qcae/tests/`; wired into root `pyproject.toml` pytest config

Location: `qcae/implementation/decisions/`

---

## Unresolved Questions / Derived Points (for operator review)

1. **Lifecycle branches derived from canon 0.5.** The canonical state machine in 0.5.1 is linear with branches at ACQUISITION_CANDIDATE → {APPROVED, REJECTED, DEFERRED} and MONITORED → {REVIEW_REQUIRED, SUPERSEDED, RETIRED}. P0 derives the additional edges: rejection/deferral permitted from CANDIDATE…ACQUISITION_CANDIDATE (canon 0.5.14–0.5.15 describe candidate rejection/deferral), REVIEW_REQUIRED → MONITORED return after revalidation (canon 0.5.17), and REJECTED/SUPERSEDED/RETIRED as terminal. Terminal-ness of REJECTED and SUPERSEDED is inferred (negative knowledge must not be silently overwritten; supersession preserves history per 0.5.18). If the operator wants different branch legality, this is a localized change in `core/lifecycle`.
2. **Waivable gate set = {DOMAIN_VERIFIED}** per canon 0.5.10 ("may be marked NOT_APPLICABLE with policy justification"). All other gates hard-required in sequence.
3. **VerificationLevel enum** uses Book I 1.3.13 (DISCOVERED…DOMAIN_VERIFIED). The master prompt §8 lists a slightly different illustrative set (CLAIMED/SOURCE_SUPPORTED/…); canon 1.3.13 wins per §0 of the master prompt.
4. **AtomStatus enum** (PROPOSED/ACTIVE/DEPRECATED/RETIRED) is a P0 derivation — canon 1.2.22 lists a `status` field without values. To be revisited at P5 (forensics) without schema break (field is versioned).
5. **Job/Step status vocabularies are minimal P0 identity contracts** (PENDING/RUNNING/SUCCEEDED/FAILED/CANCELLED; steps +SKIPPED). Block 12/13 chapters will be read before P2 job runtime; job/step schemas may then be extended (additive, versioned).
6. **NegativeKnowledge, Evaluation, CapabilityReceipt, MonitoringRecord** are intentionally NOT in P0 (P1/P5/P8 scope per 18.1); their evidence-ref and relationship substrates exist from P0.

## Deviations from Canon

None so far.

## Blockers

None.

## Next Action

P0-C01: create Book V package skeleton and pytest wiring.

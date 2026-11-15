# IMPLEMENTATION RUNGS

Seven rungs. Each has entry criteria (what must be true before work starts), acceptance tests (what proves it), and a **stop condition** (what makes the rung halt rather than improvise). Rungs 1–2 and 5 can be developed independently of each other; 3–4 depend on 2; 6–7 are strictly sequential.

Nothing here authorizes implementation. This is the sequence a later directive would approve.

---

## Rung 1 — Contract and interface definitions

**Scope.** `consumer/models.py` only: `ConsumerRequest`, `ConsumerVerdict`, `ConsumerDecision`, `ConsumerRefusalReason`, `CustodyAuthorityBasis`. Types and laws, no I/O, no verifier call.

**Entry.** This design accepted; no production consumer exists (true today).

**Acceptance.**
- A1.1 `ConsumerRequest` contains **no** field typed `RecordVerification`, `ConsumerVerdict`, `SemanticAuthority`, `TrustedAuthorityContext`, or any callable returning a verdict.
- A1.2 `ConsumerDecision` has exactly `ACCEPT_FIELD_BINDING`, `REFUSE`, `INTEGRATION_REQUIRED` — no `ACCEPT`, no `AUTHORIZED` as a decision.
- A1.3 `CustodyAuthorityBasis` has exactly `AUTHORIZED`, `INTEGRATION_REQUIRED`, `UNAUTHORIZED` — **no** `SYNTHETIC_TEST_ONLY`.
- A1.4 Model laws: frozen, `extra="forbid"`, naive-datetime-refusing, mirroring `NormalizationModelBase`.
- A1.5 Import graph: `consumer.models` imports nothing from `sensors/verification.py` at runtime (types only via `TYPE_CHECKING`) so the contract cannot become a second source of truth.

**Stop.** If any of A1.1–A1.3 requires an exception "for tests", stop: the test seam is wrong, not the model.

---

## Rung 2 — Production-owned verification derivation

**Scope.** `consumer/policy.py::TrustConsumerPolicy.derive` plus the policy-owned root/registry/custody handles. Adoption of `verify_trade_record` / `verify_liquidation_record`.

**Entry.** Rung 1 merged.

**Acceptance.**
- A2.1 A caller cannot inject a verdict: no parameter or attribute of that type exists on the intake path (grep-level assertion in a test).
- A2.2 Two records differing only in provider/approval/registry digest/cutoff produce different derivations, and any claimed-bytes mismatch refuses `TRUSTED_CONTEXT_MISMATCH`.
- A2.3 `assert_trustworthy()` is called on every derived verdict before inspection.
- A2.4 A `model_construct`-forged candidate is rejected as divergence, never accepted.
- A2.5 Derivation cost is measured and recorded (one invocation per consumption; no hidden re-derivation loops).

**Stop.** If any acceptance case can only pass by accepting a caller-supplied verdict, stop and re-open spec C.

---

## Rung 3 — Authority and custody policy integration

**Scope.** `consumer/custody_authority.py`: derived basis from pinned manifest bytes; `INTEGRATION_REQUIRED` under the shipped empty manifest.

**Entry.** Rung 2 merged.

**Acceptance.**
- A3.1 Under the shipped manifest (`"artifacts": {}`), **no input can produce `AUTHORIZED`** — property test over fixture families, not a single example.
- A3.2 No public symbol in `src/` constructs an authorized authority value; the derivation function is the only producer.
- A3.3 Changing any bound element (artifact, approval, registry digest, record kind, provider, cutoff) flips `AUTHORIZED` → `INTEGRATION_REQUIRED` in the fixture manifest.
- A3.4 `custody_verified` and `custody_source_authorized` remain independent in the verdict; a test asserts all four combinations are reachable *as values* and that only the authorized-and-verified case accepts.
- A3.5 `INTEGRATION_STATE` string unchanged; approval manifest byte-identical.

**Stop.** If satisfying A3.1 requires a flag, an env var, or a test-only basis, stop: that is the exact regression this design exists to prevent.

---

## Rung 4 — Replay, PIT and evidence rebinding

**Scope.** `consumer/rebinding.py`; replay flattening; inspection order with PIT/replay **before** authority.

**Entry.** Rungs 2–3 merged.

**Acceptance.**
- A4.1 Bytes replaced between derive and inspect ⇒ `EVIDENCE_BYTES_MISMATCH`; bytes removed ⇒ `EVIDENCE_BYTES_MISSING`; digest-only ⇒ refusal.
- A4.2 Forged `.eligibility="ELIGIBLE"` object ⇒ `REPLAY_BLOCKED` with `NOT_POLICY_DERIVED`.
- A4.3 PIT-inadmissible or replay-blocked records refuse **even when** custody authority would have been granted.
- A4.4 Naive cutoff / bare date ⇒ refusal, never UTC-midnight assumption.
- A4.5 Rebinding reads each referenced blob exactly once per consumption (no unbounded reads).

**Stop.** If inspection order cannot place PIT/replay before authority without duplicating verdict logic, stop and reconcile with §3 of the architecture.

---

## Rung 5 — Negative security testing

**Scope.** `tests/.../test_b5_p3_consumer_security.py`: the A01–A20 attack list from `04_THREAT_MODEL.md`, run against the **production** policy.

**Entry.** Rungs 1–4 merged (or developed in parallel against a stub policy that satisfies Rung 1).

**Acceptance.**
- A5.1 Every prevented attack has at least one test that fails if the control is removed (mutation-checked, not merely green).
- A5.2 Every out-of-scope condition is asserted to be *documented*, not silently absent: the test file cites X01–X06 explicitly.
- A5.3 No test constructs authority by patching internals (`object.__setattr__` on module state) — that would prove the harness, not the boundary.
- A5.4 The same fixtures are run against the harness policy and the production policy; disagreements are enumerated.

**Stop.** If an attack passes only because a test monkeypatched production internals, the control is unproven — stop and redesign the control.

---

## Rung 6 — Canonical regression and independent audit

**Scope.** Full collection (expected 4,733 nodes, re-measured, not inherited), canonical runner execution, independent reconciliation, plus an independent reviewer who did not write the code.

**Entry.** Rung 5 merged; governance suite green.

**Acceptance.**
- A6.1 Universe collected and executed with `collected == executed`, 0 missing / extra / duplicate / unmapped, digests equal to the independently measured anchor.
- A6.2 `ANCHORED_COMPLETE` with `GREEN` — a self-consistent result alone is insufficient.
- A6.3 Independent review produces findings; each is either repaired or explicitly accepted with rationale.
- A6.4 Zero unauthorized `src` changes relative to the rung's declared scope.

**Stop.** Any RED, timeout, or unexplained node ⇒ stop; do not re-run hoping for green.

---

## Rung 7 — Governance reconciliation and acceptance review

**Scope.** Ledger entry (new number, no renumbering), progress file update, acceptance review.

**Entry.** Rung 6 green and audited.

**Acceptance.**
- A7.1 Inventory 1,102 / 1,102 (or the then-current pinned count, measured), I11R2 pin consistent.
- A7.2 Approval manifest still empty; `INTEGRATION_REQUIRED` still the state; no trust promotion.
- A7.3 Frozen I05/I09/I10 constraints unchanged; no audit branch merged.
- A7.4 Acceptance review explicitly records that the consumer is *implemented and bounded*, not *authorized to consume production custody*.

**Stop.** If any governance artefact must move to make the rung pass, stop: the rung is not the authority.

---

## Independence and critical path

```
R1 ──▶ R2 ──▶ R3 ──▶ R4 ──▶ R6 ──▶ R7
        └────▶ R5 ──────────┘  (R5 can start with R1, driven by the threat model)
```

- **Independent:** R1 and R5 (R5 against stubs), and R4's rebinding module (pure function over a custody protocol).
- **Serial:** R2 → R3 (authority binds to derivation identity), R6 → R7.
- **Parallel-safe:** R5 fixtures can be authored from `04_THREAT_MODEL.md` before any production code exists, which is the cheapest way to keep the tests adversarial rather than descriptive.

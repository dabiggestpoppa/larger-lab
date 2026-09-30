# CSIA Book 5 Hardening R4 — Registry / Derived-Ref Authority Decay Seal

> **Status:** COMPLETE — all gates PASS, failure-first demonstrated, operator acceptance pending
> **Base:** `2a455bcb01f8a2958913380b8164ba7c602c18a9` (R3 final)
> **Branch:** `agent/crypto-systems-intelligence-atlas-book5-build`
> **Date:** 2026-09-30

---

## 1. Trigger — newly demonstrated concrete defect (operator-reported, reproduced)

`Book5CanonicalRecordRegistry.resolve` checked only dict membership and record
kind. Registration validated the underlying Book 2 claims **once**, at
registration time. Therefore:

1. register a valid position / flow / fact / liability / transformation while
   its Book 2 claim is OBSERVED;
2. later transition that claim to CONTESTED / STALE / REJECTED / SUPERSEDED
   through the accepted Book 2 transition engine (`promotion.ClaimStateEngine`);
3. call `compose_path()` or `topology_view()` (or `registry.resolve()` directly);
4. `registry.resolve()` still accepted the old registry entry;
5. 5G emitted a new `derived=True` artifact pointing at data whose Book 2
   authority was no longer current.

**Failure-first demonstration** (pre-seal, at base `2a455bcb`): the E-matrix
ran **40 failed / 11 passed** — every decay row failed with the defect live
(the stale entry resolved; `compose_path`/`topology_view` minted derived
artifacts over decayed authority).

## 2. Scope discipline

Narrow fix, per the R3 exit directive:

- **Changed:** `Book5CanonicalRecordRegistry.resolve` (live Book 2
  revalidation, provenance-required), `compose_path` / `topology_view`
  (forward the engine's provenance into every resolution).
- **Unchanged:** R2 context-binding family, R3 context seal and binding
  construction, `registered_record` / `registered_refs` (documented
  structural, non-authoritative — pinned by E17/E20), no-second-engine
  doctrine, registry-never-mints, `compose_snapshot` / `observed_value_display`
  live validation (pinned by E10/E11/E8 — they were already sealed).

## 3. The seal

`resolve(ref, *, expected_kind=None, provenance=None)` — resolution is now a
**live Book 2 authority boundary**:

| order | rejection | meaning |
|-------|-----------|---------|
| 1 | UNKNOWN | ref never registered |
| 2 | WRONG-KIND | registered, but the API requires a different kind (precedence preserved — E12) |
| 3 | NO-AUTHORITY-CONTEXT | `provenance` is None (explicit None fails closed — R2 mandatory-authority pattern) |
| 4 | STALE-AUTHORITY | entry's Book 2 claims no longer resolve as canonical, current, evidenced (`resolve_claim_refs` → `resolve_claim` → `can_promote_to_graph`); for flow/liability/observed-fact kinds the R3 quantitative context seal re-runs live too |

Central R4 invariant: **NO STALE AUTHORITY THROUGH THE REGISTRY.** The record
itself is immutable, so its entry is never "fixed": resolution rejects while
Book 2 authority is non-current and restores the moment Book 2 restores it
(E13 STALE→OBSERVED; E14 CONTESTED→CORROBORATED via the accepted P-4 engine).

`compose_path` / `topology_view` forward `self.provenance` into every stage /
node / edge / endpoint resolution, closing the derived-views decay surface.

## 4. Verification

- R4-focused: **51/51 PASS** (`test_book5_hardening_r4.py`, E1–E20).
- Full CSIA: **784 passed** — Book1=107, Book2=108, Book3=83, Book4=230
  (all unchanged), Book5 **205 → 256** (+51 R4 rows), Total **733 → 784**.
- ruff PASS (src + tests); mypy **44 files clean**.
- R1/R2/R3 suites green: hardening_r1 37, hardening_r2 44, hardening_r3 46,
  core 22, adversarial 31, blocs 25.

## 5. Attack matrix (Phases 1–3)

- **E1–E3, E5–E7, E9, E9b** — decay × {CONTESTED, STALE, REJECTED,
  SUPERSEDED} × surface {resolve, compose_path, topology node, topology edge,
  fact resolve, liability, transformation}; SUPERSEDED driven through the
  canonical transition engine (mandatory replacement + reason).
- **E4** — two-claim entry: only the second ref decays → whole entry rejects.
- **E12** — WRONG-KIND precedence over stale-authority.
- **E13/E14** — resurrection/recovery (decay is live, not a tombstone).
- **E15/E18** — fresh-claim rebind; decay is per-claim, not per-registry.
- **E16** — endpoint isolation: healthy flow edge over decayed endpoint
  position rejects.
- **E10/E11** — single-engine controls (register / compose_snapshot already
  live-revalidate; pinned).
- **E17/E20** — `registered_record` / `registered_refs` stay structural,
  never authority.
- **E19** — explicit-None provenance fails closed at resolve.

## 6. Doctrine preservation

- No second epistemic engine: the seal re-uses the accepted Book 2 engines
  (`resolve_claim_refs` / `can_promote_to_graph` / `validate_quantitative_record`);
  no DB, no graph DB, no global state, no default resolver.
- Registry never mints: unchanged; `SynthesisWriteLedger` write count stays 0
  by construction.
- Epistemic honesty: `NO STALE AUTHORITY THROUGH THE REGISTRY` mirrors the R3
  `NO BINDING != CONTEXT VERIFIED` family — authority is verified at decision
  time against live state, never remembered from a construction.

## 7. Exit state

```text
BOOK_5_HARDENING_R4 = PASS
BOOK_5_IMPLEMENTATION = COMPLETE_HARDENED (R4)
BOOK_5_ACCEPTANCE = NOT_SELF_ACCEPTED
STATUS = READY_FOR_OPERATOR_ACCEPTANCE
BOOK_6 = NOT_STARTED
LIVE_ACQUISITION_AUTHORITY = FALSE
```

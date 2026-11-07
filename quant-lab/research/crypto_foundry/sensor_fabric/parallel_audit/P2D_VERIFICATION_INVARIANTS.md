# P2D Verification Invariants — Parallel Audit (SENSOR-B5-PARALLEL-R1)

**Base:** `0f0b3195b43a47b88896ef8d1cfa49e2568a581e` · **Status:** research / red-team, not ratified

Each invariant is machine-checkable. Violations at base are marked. Invariants I-1..I-8 are the gate for closing F-R1-01..04.

## Invariants

### I-1 — Custody identity, not shape (F-R1-01)
**Predicate:** `verify_*` accepts custody only if `type(custody) is BlobStoreCustody` (or an equivalent sealed capability) bound to a store whose `verify_blob` re-hashes bytes. A structural `held_digest` return never suffices.
**Base violation:** `TrustedCustodyProvider` Protocol (`verification.py:159`) + `_custody_verified` (`verification.py:416`) accept any shape-conforming object. Confirmed: counterfeit accepted, `downstream_trusted=True`.
**Check:** PA-R1-01 must go green; negative control PA-R1-06 must refuse.

### I-2 — Scoped verdict (F-R1-02)
**Predicate:** `downstream_trusted=True ⟹` all of `semantic_mapping_approved`, `record_transformation_verified`, `custody_verified`, `source_lineage_verified`, `instrument_authenticated`, `source_revision_authenticated`, `pit_admissible` are True.
**Base violation:** `verify_trade_record` sets `downstream_trusted=custody_ok` (`verification.py:589`) with lineage/instrument/revision False. Liquidation path already enforces `False` (`verification.py:837`).
**Check:** PA-R1-02.

### I-3 — Model-level consistency (F-R1-03)
**Predicate:** `RecordVerification` carries a `model_validator(mode="after")` enforcing I-2's implication plus `custody_verified ⟹ fields_verified` non-empty (or custody false ⇒ fields empty) and `pit_admissible ⟹ available_at` present.
**Base violation:** No validator (`verification.py:252`); contradictory instances serialize. Confirmed by harness PA-R1-03.
**Check:** Construction of both contradictory variants raises.

### I-4 — Availability is mandatory for PIT (F-R1-04)
**Predicate:** `_assert_intraday_pit` never returns admissibility when `available_date is None`; it raises `RecordVerificationError`. The `if available_date is None: return` branch (`verification.py:403`) is deleted, and approval manifests require `available_at` + `available_at_instant`.
**Base violation:** PIT-absent approval passes cutoff `2026-01-02` with `pit_admissible=True`. Confirmed PA-R1-04.
**Check:** PA-R1-04 refuses; any future availability field removal breaks the approval schema.

### I-5 — Fail-closed custody (defense in depth)
**Predicate:** Wrong hash, `None`, exception, or unknown ref ⇒ `RecordVerificationError`; never a verdict object.
**Base status:** Untested in this harness — gap flagged as PA-R1-06; must be green before merge.
**Check:** PA-R1-06.

### I-6 — Liquidation conservatism (regression guard)
**Predicate:** `verify_liquidation_record` always returns `downstream_trusted=False` until lineage/instrument/revision dimensions gain authenticated checks.
**Base status:** Holds (`verification.py:690,837`).
**Check:** PA-R1-05.

### I-7 — No mock-as-evidence
**Predicate:** `FakeCustody` / test doubles appear only in test code; production paths never import test modules. The P2c test file (`test_b5_i09p2c_record_verification.py`) is scaffolding for pinning manifests, not evidence of custody.
**Base status:** Holds in source; risk is interpretive, not code.
**Check:** `grep -rn FakeCustody quant-lab/src` empty.

### I-8 — Replay gate separation
**Predicate:** PIT admissibility (`verification.py`) and strict replay eligibility (`normalization/time/availability.py`, `replay_gate.py`) are distinct predicates; neither implies the other. Commands/observation rows must not be promoted across the gate without the replay check.
**Base status:** Unchanged; noted because `derive_market_available_at` documents a different availability concept.
**Check:** Code review on any P2d change touching time contracts.

## Minimal remediation (mirrors P2cR1 §15, no ratification)
1. Seal custody (I-1) — identity or capability, not Protocol shape.
2. Scope the verdict + add validator (I-2, I-3).
3. Close the availability gap (I-4) — require fields at approval time, fail closed at verify time.
4. Add PA-R1-06 negatives (I-5) before merge.

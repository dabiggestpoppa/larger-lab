# CR-RISK-BLOCK-IV-D1.2-INSTRUMENT-SPEC-AND-QUANTITY-REPRESENTABILITY-PLAN — PROGRESS

**Status:** PASS — committed, pushed, other checkout synced.

## What was planned

Lane B (quantity representability) preregistration — PLAN ONLY, no empirical
quantity study, no broker, no orders:

- **Question:** given a frozen account/product contract, can each sealed
  EconomicTarget be represented by broker-native quantity without materially
  altering exposure?  EconomicTarget != broker quantity.
- **Truth hierarchy:** ACTUAL_OBSERVED → BROKER_DOCUMENTED → PROFILE_FROZEN →
  USER_SPECIFIED_SCENARIO (new) → HYPOTHETICAL_DIAGNOSTIC → UNKNOWN; user
  assumptions (25k USD, 1:50/1:100/1:500 prop, OX up to 1:1000) labeled
  USER_SPECIFIED_SCENARIO, never actual/documented.
- **Profiles:** PROP_25K_L50 / L100 / L500 / OX_SMALL_L1000 — research labels
  only, registry CSV, instrument fields UNKNOWN until frozen.
- **Quantity pipeline:** EconomicTarget → account-currency notional → native
  exposure → raw quantity → feasibility gate → faithful rounded quantity →
  represented notional → exposure error.
- **Rounding:** primary ROUND_DOWN_TOWARD_ZERO; upward default false; min →
  MIN_QUANTITY_BLOCKED, max → MAX_QUANTITY_BLOCKED; clipping false; multi-
  ticket split false; nearest = comparator only.
- **Fidelity:** exposure ratio / relative / signed error; materiality
  tolerance preregistered at 1% (matches D1 frozen band; risk-unit rationale
  documented; never chosen from PF/EV).
- **Lane B vs Lane C:** margin/buying-power/leverage excluded (D1.3);
  QUANTITY_REPRESENTABLE can still be MARGIN_BLOCKED later.
- **Account sizes:** 5k/10k/25k/50k/100k diagnostic + actual intended when
  frozen; leverage recorded as metadata only (does not drive Lane B unless
  broker volume rules depend on tier).
- **Currency:** USDJPY/USD quantity semantics not assumed trivial; causal
  conversion price(s) at translation time; long/short symmetry checked, not
  assumed.
- **Distortion plans:** family / pos / quantile (reuses D1.1 RANK_BIN_EDGE
  boundaries, NOT recomputed) / subperiod-regime (sealed fields only).
- **Counterfactuals:** ALTERED_BOOK_ROUND_UP / NEAREST / CLIPPED / SPLIT —
  diagnostic only, never faithful.
- **Runtime handoff:** InstrumentPhysicalSpec + AccountPhysicalProfile schemas
  consumed from execution-runtime-foundation (`62e6d040` QL-EXEC-R4.1
  recorded read-only); Capital Routing builds no broker client.
- **Missing truth:** 18 unresolved fields, all UNKNOWN, all blocking —
  empirical D1.2 BLOCKED until quantity fields frozen (D1.2A).
- **Sequence:** D1.2A physical-profile-truth-ingest-and-seal → D1.2B
  quantity-representability-surface → D1.3 margin → ...

## Evidence

- 26 artifacts in `research/capital_routing/risk/block4_quantity_representability_d1_2_plan/`
  (start with `CR_BLOCK4_D1_2_QUANTITY_PIPELINE.md`,
  `CR_BLOCK4_D1_2_ROUNDING_POLICY.md`, `CR_BLOCK4_D1_2_PROFILE_REGISTRY.csv`,
  `CR_BLOCK4_D1_2_INSTRUMENT_SPEC_SCHEMA.json`, `CR_BLOCK4_D1_2_DECISION.json`)
- tests: `tests/test_quantity_representability_d1_2_plan.py` — 36 tests
- combined: 318/318 across 10 suites; determinism byte-identical; offline

## Decision

`d1_2_plan_pass = true` · `d1_2_empirical_ready = false` ·
`d1_2_empirical_authorized = false` · `d1_3_authorized = false` ·
`production_authorized = false` · `human_review_required = true`

Next: CR-RISK-BLOCK-IV-D1.2A-PHYSICAL-PROFILE-TRUTH-INGEST-AND-SEAL (then
D1.2B surface) — not started.

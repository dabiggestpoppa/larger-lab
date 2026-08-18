# CR-RISK-BLOCK-IV-D1.2A-PHYSICAL-PROFILE-TRUTH-INGEST-AND-SEAL — PROGRESS

**Status:** PARTIAL_PASS_WAITING_PHYSICAL_TRUTH — committed, pushed, other
checkout synced.

## What was ingested (evidence-based, read-only inspection after git fetch)

Cross-workstream heads recorded: execution-runtime-foundation `62e6d040`
(QL-EXEC-R4.1), tb-forward-engine `b48fd352` (TB-R6.1D), main `9f612886`
(OCE Block 0), capital-routing `aaf3e054` (D1.2).

Truth source inventory (10 sources) and findings:

- **execution-runtime-foundation**: `SymbolInfo` contract SHAPE exists
  (quant-lab/execution_runtime/types.py — symbol, digits, point,
  contract_size, volume_min/max/step, trade_mode, trade_tick_size/value) but
  is populated ONLY at runtime from a live MT5 session. NO committed
  USDJPY/account observation snapshots exist. InstrumentPhysicalSpec /
  AccountPhysicalProfile absent under those exact names.
- **FakeMT5 / SimBroker fixtures** hardcode the generic FX convention
  (contract_size=100000, volume_min=0.01, volume_step=0.01, volume_max=100)
  — TEST FIXTURES, explicitly NOT truth; never accepted as actual.
- **capital-routing**: USDJPY MT5 price-data session evidence
  (mt5_session_schedule_by_symbol.csv) — session/data only, no contract rules.
- **tb-forward-engine**: TB_P5_BROKER_LOT_CONSTRAINTS.csv + TB execution
  contracts — TB strategy/account artifacts for a DIFFERENT book; NOT CR
  USDJPY account truth.
- **User-specified scenarios**: 4 profiles with equity + leverage only;
  instrument fields NOT supplied.

## Conclusion (honest, no manufactured PASS)

NO actual/documented USDJPY quantity truth exists in the repository. All
executable quantity fields (broker_symbol, product_type, contract_size,
volume min/step/max, account currency, base/quote/margin currency,
trade_calc_mode, hedging/netting, quantity conversion rule) are UNKNOWN.
Every scenario profile is PARTIAL_PROFILE (equity + leverage only) → 0
profiles quantity-complete → **PARTIAL_PASS_WAITING_PHYSICAL_TRUTH**.

`d1_2a_pass = true` (ingest + seal executed correctly) · `d1_2b_ready =
false` · `d1_2b_authorized = false` · `d1_3_authorized = false` ·
`production_authorized = false` · `human_review_required = true`

Next: CR-RISK-BLOCK-IV-D1.2A1-PHYSICAL-TRUTH-COLLECTION.

## Sealed contracts

- QUANTITY_MINIMUM_COMPLETE / MARGIN_COMPLETE rules frozen (11 / 16 fields).
- Quantity conversion contract defined but UNRESOLVED: broker "1.0 volume"
  semantics NOT inferred from FX convention; native base-USD notional mapping
  undetermined until product observed; causal entry-side conversion required.
- Long/short symmetry: UNKNOWN, not assumed symmetric.
- Field-level provenance (value / truth_class / source / observed_at /
  source_hash / status) per field; profile truth = weakest required field.
- Profile generation hashes: deterministic canonical hash; any contract-field
  change → new generation.
- Source conflicts: none found (no actual/documented evidence to conflict);
  conflict state machine tested (blocking conflict → BLOCKED, never PASS).
- Security: no secrets in artifacts; account IDs pseudonymous (SCENARIO-*).
- No quantity surface (D1.2B), no margin study (D1.3), no broker client, no
  MT5 import, no order API, no performance-based selection.

## Evidence

- 22 artifacts in `research/capital_routing/risk/block4_physical_profile_truth_d1_2a/`
  (start with `CR_BLOCK4_D1_2A_TRUTH_SOURCE_INVENTORY.csv`,
  `CR_BLOCK4_D1_2A_INSTRUMENT_TRUTH.csv`,
  `CR_BLOCK4_D1_2A_EXECUTION_RUNTIME_HANDOFF_AUDIT.md`,
  `CR_BLOCK4_D1_2A_PROFILE_GENERATION_MANIFEST.json`, `CR_BLOCK4_D1_2A_DECISION.json`)
- tests: `tests/test_physical_profile_truth_d1_2a.py` — 40 tests
- combined: 358/358 across 11 suites; determinism byte-identical; offline

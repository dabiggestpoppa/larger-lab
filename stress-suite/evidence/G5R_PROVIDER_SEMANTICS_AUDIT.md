# G5R PROVIDER SEMANTICS AUDIT — S17 source-layer diagnosis integrity

Scope: G5R-10 (semantics key = provider + metric), G5R-11 (adapter version must match the
contract), G5R-12 (missing normalized value stays UNKNOWN), G5R-13 (time / quality /
contract semantics), G5R-14 (NO_DISAGREEMENT invariant), G5R-15 (explicit tolerance
contract). Core law: a fixture cannot declare source semantics into existence.

## 1. (provider, metric) keying — fail closed (G5R-10)

`run_s17` indexes `ProviderSemanticsRecord` by `(provider, metric)`. A provider publishing
several metrics resolves each observation to ITS metric's contract
(`test_same_provider_multiple_metrics_resolve_correct_contract` — the OTHER_METRIC
contract is provably not consulted). A missing contract fails closed:
`diagnose_provider_disagreement` returns step `provider_semantics` FAILED with cause
`SEMANTIC_CONTRACT_MISSING`, terminal `DATA_INSUFFICIENT`; the runner EMITS the fail-closed
diagnostic per pair (disposition `SOURCE_DIAGNOSTIC_REQUIRED`) and never compares, never
averages (`test_missing_metric_semantics_fails_closed`).

*Note (§29): the original draft asserted `diagnoses == []` for the no-contract runner case.
A silent skip IS the G5R-10 defect, so the assertion was corrected to require the
fail-closed diagnostics; the change is documented in the test docstring.*

## 2. Adapter version equality (G5R-11)

`observation.adapter_version == semantic_contract.adapter_version` unless the contract's
explicit `compatible_adapter_versions` list admits it; blank versions fail. Detected at the
adapter layer BEFORE normalization: CASE E (obs v2 vs contract v1) → `ADAPTER_MISMATCH` /
`REPAIRABLE_SOURCE_MISMATCH` (`test_wrong_observation_adapter_version_detected`,
`test_blank_observation_adapter_version_detected`, `test_matching_adapter_passes`).

## 3. Missing normalized value (G5R-12)

`ProviderObservation.normalized_value` is `Optional[float]`; `from_fixture` no longer
coerces an absent value to 0.0. Missing ⇒ step `normalization` FAILED with cause
`NORMALIZATION_MISSING`, terminal `DATA_INSUFFICIENT` — it can never become a real zero
that manufactures or hides disagreement (`test_missing_normalized_value_not_zero` — CASE F,
`test_missing_normalized_value_blocks_disagreement_comparison`).

## 4. Time / quality / contract / instrument semantics (G5R-13)

Each declared dimension is validated at its diagnosis layer, none silently skipped:

- observation `time_window` must equal the semantic contract's window (both sides) →
  `TIME_WINDOW_MISMATCH`;
- observation `quality_state` must meet the contract's required quality state →
  `QUALITY_FAILURE`;
- `contract_type` compatibility is BOTH per-provider (obs vs own contract) AND pairwise
  (obs A vs obs B) — a SPOT and a PERP_LINEAR reading of the same metric are not
  comparable → `CONTRACT_TYPE_MISMATCH`
  (`test_spot_vs_perp_contract_type_mismatch_detected`);
- canonical instrument identity checked against the registered `canonical_instrument`
  (S17 semantics fixture now registers `BTC_USDT_PERP` + `PERP_LINEAR` on every contract).

## 5. NO_DISAGREEMENT invariant (G5R-14)

Terminals: `REPAIRABLE_SOURCE_MISMATCH | GENUINE_SOURCE_DISAGREEMENT | NO_DISAGREEMENT |
DATA_INSUFFICIENT`. Equal clean normalized values terminate `NO_DISAGREEMENT` /
`NO_DISAGREEMENT` — never GENUINE
(`test_equal_clean_normalized_values_no_disagreement`). Genuine disagreement (340 vs 212
liquidations across clean semantics) remains preserved, never averaged.

## 6. Explicit tolerance contract (G5R-15)

`DisagreementToleranceContract` (provisional, versioned data; values NOT
constitutionalized) supports absolute / relative / basis-point tolerance per metric+units.
`disagreement_is_material()` replaces raw float inequality as the universal test: a
340.0 vs 340.0001 difference under `absolute_tolerance=0.001` is NOT material;
340 vs 212 IS. Wired into the diagnosis (`test_tolerance_wired_into_diagnosis`). The S17
runner resolves tolerances from the scenario's `disagreement_tolerances` fixture by
(metric, units).

## 7. Diagnosis order invariant

Canonical order enforced end-to-end (`test_diagnosis_order_invariant`):
provider semantics → instrument identity → adapter → normalization → time semantics →
quality → disagreement surface. A failure at layer k blocks all later layers.

## 8. Result

`S17 PROVIDER SEMANTICS: PASS — (provider, metric) contracts, adapter equality, missing-normalization preservation, full semantic dimensions, NO_DISAGREEMENT invariant, explicit provisional tolerance.`

# G5R TRANSFER VALIDATION AUDIT — S19 map / protocol / target-data integrity

Scope: G5R-20 (structural map must validate ALL required axes), G5R-21 (target protocol
must be a real frozen object), G5R-22 (target data must pass governed sensor adequacy),
G5R-23 (source evidence refs must resolve; source evidence != target validation).
Core laws: **ANALOGY != TRANSFER** and **SOURCE EVIDENCE != TARGET VALIDATION.**

## 1. Full-axis map validation (G5R-20)

The G5 contract requires the map to carry: source_domain, target_domain,
source_definition, target_candidate_definition, source_observables, target_observables,
units/scales, state_semantics, market-structure assumptions, mechanism invariants, known
broken assumptions, required sensors, falsifiers.

`validate_transfer_map(tmap) -> TransferMapValidationResult` checks all 13 axes
(`TRANSFER_MAP_AXES`) and preserves per-axis status. Blank mandatory axes can never
produce STRUCTURALLY_SOUND; declared `known_broken_assumptions` invalidate soundness (they
are preserved, not hidden). No verbosity requirement — presence is the bar.

Regressions: `test_missing_units_scale_not_sound`, `test_missing_state_semantics_not_sound`,
`test_missing_market_structure_assumption_not_sound`, `test_missing_falsifiers_not_sound`,
`test_missing_required_sensor_definition_not_sound`, `test_complete_map_sound`,
`test_incomplete_transfer_map_runner_analogy` (CASE J → map unsound → ANALOGY_ONLY).

## 2. Real frozen target protocol (G5R-21)

`resolve_frozen_target_protocol(hypothesis, protocols)`:

- `frozen_target_protocol_ref` must be non-empty AND resolve to a registered
  `FrozenExperimentProtocol` (`protocol_frozen=true` alone authorizes nothing — CASE I);
- the protocol's `target_domain` must EQUAL the hypothesis's target domain (a protocol
  frozen for CRYPTO cannot authorize an FX validation — `test_wrong_target_domain_protocol_rejected`);
- the protocol fingerprint must be present/valid; frozen-before-result is carried by the
  protocol object.

The S19 scenario now registers `PROTO_TC1_FX_VALIDATION` (target_domain FX, dataset
lineage, features, metrics, falsification criteria, holdout ref, cost/execution
assumptions) and the hypothesis carries `frozen_target_protocol_ref` pointing at it.
Result: `valid_registered_frozen_protocol_allows_domain_validation_required`.

*AMB-G5R-02 (documented): claim↔hypothesis linkage is asserted via `claim_ref` fields in
tests; a hard field-level comparison inside the resolver is future work.*

## 3. Governed target data (G5R-22)

S19 target data runs the same `SensorRequirement` / `DataAvailabilityRecord` /
`SensorAdequacyResult` semantics as S18: every required target sensor must satisfy its
full vector (`rec.adequate_history(r)`). The caller boolean
`target_data_available=True` is recorded as `NON_AUTHORITATIVE_TEST_CONVENIENCE` and can
NEVER change the primary governed result — on the primary (inadequate) pack the
disposition stays DATA_BLOCKED even with the boolean set
(`test_boolean_override_cannot_bypass_target_sensor_adequacy`,
`test_without_frozen_protocol_transfer_stays_hypothesis` — old boolean-flip assertions
documented and replaced in tests/test_g5.py).

## 4. Source evidence firewall (G5R-23)

`resolve_source_evidence_refs(hypothesis, registry)` returns unresolved refs; any unknown
ref fails closed: `source_evidence_refs_resolved=false`, and the disposition can never be
DOMAIN_VALIDATION_REQUIRED (`test_phantom_source_evidence_ref_rejected` — PHANTOM_99).
Registered crypto evidence (FAM_A, lineage `CRYPTO_FOUNDRY_FAM_A`) resolves and is
preserved as CRYPTO-domain evidence
(`test_registered_crypto_evidence_preserved`). Crypto evidence — however strong — counts
as target validation in no path: the FX route to DOMAIN_VALIDATION_REQUIRED requires
governed TARGET adequacy + a registered FX-frozen protocol, and
`source_validation_as_target_validation=false` plus `!= DOMAIN_VALIDATED` are asserted
(`test_crypto_evidence_cannot_satisfy_target_validation`,
`test_source_validation_cannot_be_target_validation`).

## 5. Preserved firewall behaviors

Broken structural assumption → TRANSFER_REJECTED; name-only mapping → ANALOGY_ONLY;
missing target observables → DATA_BLOCKED; CEREBUS FX doctrine never overridden by
analogy; no FX strategy generated (`fx_strategy_generated=false`,
`cerebus_doctrine_overridden=false` asserted on every run).

## 6. Result

`S19 TRANSFER VALIDATION: PASS — all 13 map axes validated; target protocol a registered frozen object; target data governed by sensor adequacy; source evidence resolves but never validates the target.`

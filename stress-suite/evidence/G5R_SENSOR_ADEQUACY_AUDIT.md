# G5R SENSOR ADEQUACY AUDIT — S18 full-vector adequacy + evidenced capability change

Scope: G5R-16 (full requirement vector), G5R-17 (provenance), G5R-18 (sensor arrival is an
evidenced event), G5R-19 (SearchDemand acceptable-source semantics).
Core law: **AVAILABLE != ADEQUATE.**

## 1. The defect (pre-G5R)

`DataAvailabilityRecord.adequate_history()` primarily checked `status` + `history_depth`.
`SensorRequirement` defines a full vector — required_observable, resolution, history_depth,
instrument_coverage, time_semantics, quality_minimum — most of which went unchecked. The
S18 `sensor_available_later=True` boolean flipped availability in runner code, letting a
caller assert a sensor into existence.

## 2. Full-vector adequacy (G5R-16)

`DataAvailabilityRecord.adequacy` fields added: `resolution`, `time_semantics`,
`quality_state`, `certification`. `adequate_history(requirement)` now requires, under the
provisional contract, ALL of:

1. observable matches the requirement;
2. `status == AVAILABLE`;
3. `verified`;
4. known provenance: non-empty `source` + non-empty `certification` that is not `UNKNOWN`;
5. resolution equal to the requirement's resolution;
6. history depth sufficient via the structured **`HistorySpan`** representation —
   `12m` == 12 months, `2021-06-01..` == months-since the fixed provisional
   HISTORY_ANCHOR — never naive string equality;
7. required instrument coverage satisfied (subset check);
8. time semantics compatible;
9. quality minimum met (`VERIFIED` or exact state match).

The full-vector verdict is also exposed per requirement via
`assess_sensor_adequacy(requirement, record) -> SensorAdequacyResult` with every dimension
individually reported (`missing` tuple), so nothing fails silently.

Regressions: `test_available_but_unverified_not_adequate` (CASE G),
`test_available_wrong_resolution_not_adequate` (CASE H, runner-level DATA_BLOCKED too),
`test_available_wrong_instrument_not_adequate`,
`test_available_wrong_time_semantics_not_adequate`,
`test_available_insufficient_history_not_adequate`,
`test_full_requirement_match_adequate`, `test_structured_history_not_naive_string_equality`,
`test_sensor_arrival_does_not_retroactively_validate_history`.

## 3. Governed policy backstop

The shared policy gained two generic availability rules so an AVAILABLE-but-inadequate
record can never silently POLICY_HOLD:
`g5.availability.blocked_insufficient_vector` (AVAILABLE + sensor_resolution
INSUFFICIENT → DATA_BLOCKED) and `g5.availability.blocked_unverified_sensor`
(AVAILABLE + sensor_verified false → DATA_BLOCKED). The runner feeds adequacy results
(available/insufficient, verified) — not the raw boolean — into the policy.

## 4. Provenance (G5R-17)

`certification` distinguishes `AUTHORITATIVE_SYNTHETIC_SENSOR_FIXTURE` (primary G5
synthetic use) from `CRYPTO_SENSOR_FABRIC_CERTIFICATION` (future real use).
UNKNOWN/absent provenance ⇒ not adequate (`test_unknown_provenance_not_adequate`).

## 5. Sensor arrival as an evidenced event (G5R-18)

`SensorCapabilityChangeRecord`: observable, old state, new state, source, evidence refs,
certification, effective epoch, history coverage.

- The legacy boolean (`sensor_available_later=True`) may flip a status field for test
  plumbing only — it CANNOT set verified/certification, so the requirement vector still
  fails and the record is reported `NON_AUTHORITATIVE`
  (`test_boolean_alone_cannot_make_sensor_verified`).
- A REGISTERED, evidence-backed, certified change can genuinely make the requirement
  adequate and reopen eligibility via the governed reopen evaluator
  (`test_registered_sensor_change_can_reopen` → REOPEN_CANDIDATE).
- Arrival never retroactively validates history: a later-arriving sensor cannot satisfy a
  longer history requirement than the change's coverage.

## 6. SearchDemand semantics (G5R-19)

`SearchDemand.required_instruments` (what must be observable, e.g.
`BTC_USDT_PERP`, `ETH_USDT_PERP`) is SEPARATE from
`SearchDemand.acceptable_source_classes` (who may supply it, e.g.
`CRYPTO_SENSOR_FABRIC`). An instrument id is never stored as a provider
(`test_search_demand_separates_instruments_from_source_classes`). The pre-G5R field
`acceptable_sources` (which held instrument ids) survives only as a marked LEGACY DISPLAY
field for old-call compatibility; decision semantics use the new pair.
SearchDemand remains NOT claim validation (`test_search_demand_is_not_claim_validation`).

## 7. Result

`S18 SENSOR ADEQUACY: PASS — full requirement vector + provenance; boolean override non-authoritative; capability change evidenced; instruments separated from source classes.`

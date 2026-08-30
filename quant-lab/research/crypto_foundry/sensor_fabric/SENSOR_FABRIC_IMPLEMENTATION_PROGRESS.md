# SENSOR FABRIC — IMPLEMENTATION PROGRESS LEDGER

Human-readable execution ledger for the Crypto Mechanical Sensor Fabric build.
This ledger is NOT a substitute for Git history; it is an operator-facing summary
that is updated at every staged checkpoint.

---

## Current state

| Field | Value |
|---|---|
| Current Bloc | 2 — HISTORICAL CAPABILITY PROBE HARNESS |
| Current checkpoint | SENSOR-B2-I05 DONE; SENSOR-B2-I06 (binance probe) pending |
| Bloc 1 verdict | PASS_BLOC_01_CONTRACTS_FROZEN — operator_ratified = TRUE (see evidence/bloc_01/BLOC_01_DECISION.md) |
| Operator review state | RATIFIED — Bloc 2 implementation_authorized = TRUE |
| human_review_required | TRUE |
| Bloc 2 implementation_authorized | TRUE |
| Last successful commit SHA | (see commit log below) |
| Branch | `agent/crypto-sensor-fabric-build` |
| Base planning commit | `4bb677f9e0266f4dc48405181696019f359ae49f` |
| Planning head (frozen) | `agent/crypto-sensor-fabric-plan` @ `4bb677f9e0266f4dc48405181696019f359ae49f` |
| Operator review state | IN PROGRESS — Bloc 1 |
| human_review_required | TRUE |
| next_bloc_authorized | FALSE (waiting on operator after Bloc 1 report) |

## Test counts (cumulative)

| Checkpoint | Added | Passed | Failed |
|---|---|---|---|
| SENSOR-B1-01 | 46 | 46 | 0 |
| SENSOR-B1-02 | 40 | 40 | 0 |
| SENSOR-B1-03 | 23 | 23 | 0 |
| SENSOR-B1-04 | 25 | 25 | 0 |
| SENSOR-B1-05 | 14 | 14 | 0 |
| SENSOR-B1-06 | 0 (evidence only) | — | — |
| SENSOR-B1-R01 | 6 | 6 | 0 |
| SENSOR-B1-R02 | 7 | 7 | 0 |
| SENSOR-B1-R03 | 8 | 8 | 0 |
| SENSOR-B1-R04 | 8 | 8 | 0 |
| SENSOR-B1-R06 | 0 (ratification record) | — | — |
| SENSOR-B2-I01 | 32 | 32 | 0 |
| SENSOR-B2-I02 | 21 | 21 | 0 |
| SENSOR-B2-I03 | 61 | 61 | 0 |
| SENSOR-B2-I04 | 23 | 23 | 0 |
| SENSOR-B2-I05 | 24 | 24 | 0 |
| cumulative | 338 | 338 | 0 |

## External / provider blockers

- None yet — Bloc 1 makes no external calls by design.

## Data blockers

- None yet — no data acquisition in Bloc 1.

## Disk / storage status

- Bloc 1 stores only code, schemas, configs, tests and evidence in Git.
- No market data written. Actual T0/T1/T2 data lives outside Git (later blocs).

## Live probe status

- NOT STARTED — Bloc 2 owns capability probes.

## Unresolved contradictions / plan observations

- BLOC5_SCHEMA_REFINEMENT_PENDING (informational, not a blocker): the frozen
  Bloc 1 SensorFamily has no MECHANICAL_ORDER_FLOW member — order flow is a
  T2-derived state family (master prompt §20), not a T1 sensor.  Provider
  aggressor/order-flow probing therefore rides on MECHANICAL_TRADE (trades /
  taker-side flags); Gate's `taker_side` and Kraken's trade `side`/`type`
  semantics are characterized on the trade sensor for later T2 derivation.

## Next checkpoint

- SENSOR-B2-I06: binance-capability-probe
  - REST/archive characterization, fixtures + tests; preserve the ratified
    isBuyerMaker contract: true -> SELL aggressor, false -> BUY
  - gate: binance probe suite green, offline

## Staged commit plan (Bloc 1, from `bloc_01/03`)

1. `SENSOR-B1-01: establish sensor-fabric contract and enum foundation`
2. `SENSOR-B1-02: add canonical mechanical observation schemas`
3. `SENSOR-B1-03: add free-only provider and sensor-priority registries`
4. `SENSOR-B1-04: add semantic equivalence and methodology contracts`
5. `SENSOR-B1-05: freeze JSON schemas and compatibility tests`
6. `SENSOR-B1-06: record contract-freeze evidence and Bloc 1 decision`

## Commit log

| Checkpoint | SHA | Files changed | Tests | Result | Blockers |
|---|---|---|---|---|---|
| SENSOR-B1-01 | 695d0288 | contracts layer, enums, base, access/quality/identity/missingness, test tree, ledger, pyproject/.gitignore | 46 passed / 0 failed | PASS | none |
| SENSOR-B1-02 | 957cfc85 | 8 canonical sensor schemas + ProviderEnvelope + PriceLevel, 15 committed fixtures, schema test suite | 86 passed / 0 failed | PASS | none |
| SENSOR-B1-03 | 3de4cdda | provider_registry.yaml + sensor_priority.yaml, registry loaders, F9 required-runtime validation | 109 passed / 0 failed | PASS | none |
| SENSOR-B1-04 | 8b2162a1 | semantic_equivalence.yaml + methodology_registry.yaml, equivalence/methodology loaders, pooling rule | 134 passed / 0 failed | PASS | none |
| SENSOR-B1-05 | daf9257a | JSON-schema snapshot export (14 snapshots), versioning/compat suite, regeneration script | 148 passed / 0 failed | PASS | none |
| SENSOR-B1-06 | ec8d1821 / eaf7a543 | evidence package: schema inventory, provider snapshot, equivalence matrix, test evidence, decision | 148 passed / 0 failed (re-run) | PASS | none |
| SENSOR-B1-R01 | 3f4b97da | methodology/equivalence yaml, aggressor contract fixture + tests | +6 | 6 passed / 0 failed (narrow) | PASS | none |
| SENSOR-B1-R02 | 381b224b | capability vocabulary, provider_registry.yaml, tests, provider snapshot | +7 | 61 passed / 0 failed (registry suite) | PASS | none |
| SENSOR-B1-R03 | 12750cf1 | quality.py + blocking-state tests | +8 | 13 passed / 0 failed (quality suite) | PASS | none |
| SENSOR-B1-R04 | bc179d53 | schema pin validators + mismatch tests | +8 | 62 passed / 0 failed (schemas+versioning) | PASS | none |
| SENSOR-B1-R05 | e6124031 | revalidation + evidence/ledger update | 177 passed / 0 failed (full re-run) | PASS | none |
| SENSOR-B1-R06 | 961bdcc8 | operator ratification recorded in ledger + decision evidence | — | PASS | none |
| SENSOR-B2-I01 | f5254f5a | probes package: enums, core models, failures, redaction + test suite | 209 passed / 0 failed | PASS | none |
| SENSOR-B2-I02 | 7065a211 | planner + runner + historical_checkpoints.yaml, deterministic planning, recent-control-first suppression | 230 passed / 0 failed | PASS | none |
| SENSOR-B2-I03 | 23364591 | evidence.py + coverage.py + scoring.py: immutable evidence, evidence ladder, coverage vector, redundancy, promotion gate | 291 passed / 0 failed | PASS | none |
| SENSOR-B2-I04 | a19db8a3 | kraken probe module + payload characterization helpers + endpoint registry + 10 fixtures + tests | 314 passed / 0 failed | PASS | none |
| SENSOR-B2-I05 | (pending) | shared REST probe base (rest.py) + kraken refactor onto it + gate probe module + 12 fixtures + tests | 338 passed / 0 failed | PASS | none |

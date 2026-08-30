# SENSOR FABRIC — IMPLEMENTATION PROGRESS LEDGER

Human-readable execution ledger for the Crypto Mechanical Sensor Fabric build.
This ledger is NOT a substitute for Git history; it is an operator-facing summary
that is updated at every staged checkpoint.

---

## Current state

| Field | Value |
|---|---|
| Current Bloc | 2 — HISTORICAL CAPABILITY PROBE HARNESS |
| Current checkpoint | SENSOR-B2-I12R1 (A–D) DONE (pre-live contract audit, repairs, regenerated packet); I13 live probing NOT YET AUTHORIZED — awaiting operator review |
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
| SENSOR-B2-I06 | 24 | 24 | 0 |
| SENSOR-B2-I07 | 20 | 20 | 0 |
| SENSOR-B2-I08 | 18 | 18 | 0 |
| SENSOR-B2-I09 | 15 | 15 | 0 |
| SENSOR-B2-I10 | 12 | 12 | 0 |
| SENSOR-B2-I11 | 20 | 20 | 0 |
| SENSOR-B2-I11R1 | 21 | 21 | 0 |
| SENSOR-B2-I12 | 16 | 16 | 0 |
| SENSOR-B2-I12R1A | 6 | 6 | 0 |
| SENSOR-B2-I12R1B | 7 | 7 | 0 |
| SENSOR-B2-I12R1C | 14 | 14 | 0 |
| cumulative | 491 | 491 | 0 |

## External / provider blockers

- None yet — Bloc 1 makes no external calls by design.

## Data blockers

- None yet — no data acquisition in Bloc 1.

## Disk / storage status

- Bloc 1 stores only code, schemas, configs, tests and evidence in Git.
- No market data written. Actual T0/T1/T2 data lives outside Git (later blocs).

## Live probe status

- NOT STARTED — Bloc 2 owns capability probes.

## Source-contract repairs

- SENSOR-B2-I12R1 (A–D): PRE-LIVE CONTRACT AUDIT — correct provider endpoint/
  query contracts before I13.  Kraken historical OI now targets Market Analytics
  `/api/charts/v1/analytics/{symbol}/open-interest` (epoch-SECOND since/to + explicit
  interval; analytics also routed for funding/future-basis/long-short-ratio/orderbook;
  trade-level /history anatomy retained; precomputed analytics never marked
  EXACT_EQUIVALENT).  Gate market-wide positioning uses the PUBLIC
  `/api/v4/futures/{settle}/contract_stats` (from in Unix SECONDS, interval/limit,
  no invented `to`); user /positions is PRIVATE_ACCOUNT_DATA / OUT_OF_SCOPE.  Binance
  OI uses the ABSOLUTE https://fapi.binance.com/futures/data/openInterestHist (NOT
  /fapi/v1/...); REST retention recorded separately from archive capability.  Bybit OI
  units are CONTRACT-TYPE dependent (linear = base asset); funding interval not frozen
  to 8h; funding pagination validated independently of OI.  OKX funding uses
  /api/v5/public/funding-rate-history (not /market) with fundingTime-keyed pagination
  and fields fundingRate/realizedRate/fundingTime/formulaType/method preserved.
  Coinalyze missing local free key classifies CREDENTIAL_NOT_CONFIGURED (run
  prerequisite, never AUTH_BLOCKED).  New machine-readable manifest
  config/crypto_sensor_fabric/live_probe_contracts.yaml freezes every planned I13
  contract; pre-live evidence/bloc_02 packet regenerated (still all UNATTEMPTED / E0 /
  REFERENCE_ONLY).

- SENSOR-B2-I11R1: Bitfinex community probe re-aligned with the ACTUAL frozen
  source — the public GitHub repo `tradingstrategy-ai/bitfinex-liquidations`,
  a single Git-LFS DuckDB dump (`bitfinex_liquidations.duckdb`).  Removed the
  invented daily-CSV `liquidations/{YYYY-MM-DD}.csv` tree and the fictitious
  `checksums.txt`.  Integrity evidence is now the Git LFS OID (SHA-256) +
  upstream commit SHA + declared size.  Evidence class stays COMMUNITY_ARCHIVE;
  mixed spot/margin + perpetual market types stay explicit (never whole-db
  PERPETUAL_LIQUIDATIONS).  No automatic multi-hundred-MB download; the DuckDB
  fixture is the small LFS pointer text.  ProbeFailureClass grew
  F_REQUIRED_ARTIFACT_MISSING (license / methodology missing) — confirms-at
  `test_probe_enum_member_sets_are_frozen` snapshot.

## Unresolved contradictions / plan observations

- BLOC5_SCHEMA_REFINEMENT_PENDING (informational, not a blocker): the frozen
  Bloc 1 SensorFamily has no MECHANICAL_ORDER_FLOW member — order flow is a
  T2-derived state family (master prompt §20), not a T1 sensor.  Provider
  aggressor/order-flow probing therefore rides on MECHANICAL_TRADE (trades /
  taker-side flags); Gate's `taker_side` and Kraken's trade `side`/`type`
  semantics are characterized on the trade sensor for later T2 derivation.

## Next checkpoint

- STOP GATE after SENSOR-B2-I12 (I13 live probing NOT authorized):
  - I13: approved low-rate live capability matrix — MUST NOT start until the
    operator reviews the generated pre-live packet (probe matrix, source URLs,
    expected requests, free-only classifications, network plan).
  - I14: provider-role-decision-packet (freezes claims, roles, exclusions).
  - Generated evidence packet: `evidence/bloc_02/` (01-11; all cells
    UNATTEMPTED / E0 / NOT_PIT_READY — nothing verified prior to live probing).

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
| SENSOR-B2-I05 | 22714a17 | shared REST probe base (rest.py) + kraken refactor onto it + gate probe module + 12 fixtures + tests | 338 passed / 0 failed | PASS | none |
| SENSOR-B2-I06 | d3df21a9 | binance REST + archive probe module, ratified isBuyerMaker aggressor function, 11 fixtures + tests | 362 passed / 0 failed | PASS | none |
| SENSOR-B2-I07 | 36263167 | bybit probe module: cursor-paginated OI/funding, numeric-string timestamps, csv.gz trade archive, 9 fixtures + tests | 382 passed / 0 failed | PASS | none |
| SENSOR-B2-I08 | 122e985a | okx probe module: data envelope, after/before cursor, /books current-only, traderecords archive, 8 fixtures + tests | 400 passed / 0 failed | PASS | none |
| SENSOR-B2-I09 | d8de59e9 | deribit probe module: trade-level liquidation anatomy, has_more sequence pagination, include_old, narrow universe, 8 fixtures + tests | 415 passed / 0 failed | PASS | none |
| SENSOR-B2-I10 | 46686270 | coinalyze probe module: venue-attributed aggregator symbols, free-key, corroboration semantics, 9 fixtures + tests | 427 passed / 0 failed | PASS | none |
| SENSOR-B2-I11 | 2c6b9dcd | bitfinex community archive probe module: license/checksum semantics, archive-hole detection, COMMUNITY_ARCHIVE evidence class, 6 fixtures + tests | 447 passed / 0 failed | PASS | none |
| SENSOR-B2-I11R1 | 3662b644 | realign Bitfinex probe with tradingstrategy-ai/bitfinex-liquidations Git-LFS DuckDB source; drop daily-CSV+checksums assumptions; LFS OID revision identity; F_REQUIRED_ARTIFACT_MISSING; tests A-J | 448 passed / 0 failed | PASS | none |
| SENSOR-B2-I12 | c6952503 | reports.py offline evidence-packet generator + 16 tests; generate_bloc_02_packet.py; pre-live evidence/bloc_02 packet (01-11) all UNATTEMPTED/E0 | 464 passed / 0 failed | PASS | none |
| SENSOR-B2-I12R1A | 4173e980 | Kraken Market Analytics repair + Gate public contract_stats positioning / seconds `from`; per-sensor absolute URLs; golden + negative tests | 470 passed / 0 failed | PASS | none |
| SENSOR-B2-I12R1B | 414afca3 | Binance OI absolute route / Bybit OI units + funding pagination / OKX funding /public route; golden + negative tests | 477 passed / 0 failed | PASS | none |
| SENSOR-B2-I12R1C | 40b5cd02 | Deribit/Coinalyze/Bitfinex audit, CREDENTIAL_NOT_CONFIGURED, live_probe_contracts.yaml manifest + validation tests | 491 passed / 0 failed | PASS | none |
| SENSOR-B2-I12R1D | (head) | regenerated pre-live evidence packet from corrected registry + full revalidation | 491 passed / 0 failed | PASS | none |

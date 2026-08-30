# SENSOR FABRIC — IMPLEMENTATION PROGRESS LEDGER

Human-readable execution ledger for the Crypto Mechanical Sensor Fabric build.
This ledger is NOT a substitute for Git history; it is an operator-facing summary
that is updated at every staged checkpoint.

---

## Current state

| Field | Value |
|---|---|
| Current Bloc | 3 — PRODUCTION PROVIDER ADAPTER ARCHITECTURE (common foundation) |
| Current checkpoint | SENSOR-B3-I05 COMPLETE — KRAKEN_FUTURES ADAPTER OFFLINE (PASS_SENSOR_B3_I05_KRAKEN_ADAPTER_OFFLINE, pending operator review) |
| Bloc 2 verdict | PASS_BLOC_02_WITH_SENSOR_GAPS (co-earned PASS_BLOC_02_FREE_ONLY_REDUNDANCY) — IMPLEMENTATION COMPLETE, OPERATOR RATIFIED (SENSOR-B2-RATIFY) |
| Bloc 1 verdict | PASS_BLOC_01_CONTRACTS_FROZEN — operator_ratified = TRUE (see evidence/bloc_01/BLOC_01_DECISION.md) |
| Operator review state | RATIFIED — Bloc 2 ratified; Bloc 3 common foundation OPERATOR REVIEWED / ACCEPTED FOR FIRST PROVIDER (I04R2-RATIFY); SENSOR-B3-I05 (Kraken) IMPLEMENTED OFFLINE — awaiting operator review of PASS_SENSOR_B3_I05_KRAKEN_ADAPTER_OFFLINE |
| human_review_required | TRUE |
| Bloc 2 implementation_authorized | TRUE (COMPLETE — ratified) |
| Bloc 3 implementation_authorized | TRUE — common foundation complete/hardened/behaviorally closed (SENSOR-B3-I01..I04 + I04R1 + I04R2); provider_adapter_implementation_authorized = KRAKEN_FUTURES ONLY |
| Common foundation status | COMMON_FRAMEWORK_READY=TRUE · BEHAVIORAL_CONFORMANCE_READY=TRUE · REAL_PROVIDER_ADAPTERS=1 (KRAKEN_FUTURES, offline) · PROVIDER_PARSER_CONFORMANCE=OFFLINE_PASS (Kraken; PRODUCTION_CANDIDATE mode) · NETWORK_VALIDATION=NOT_YET_RUN |
| Bloc 3 adapter status | kraken_adapter_implemented = TRUE · kraken_network_smoke = NOT_RUN · bloc_03_common_foundation_complete = TRUE |
| Last successful commit SHA | (see commit log below) |
| Branch | `agent/crypto-sensor-fabric-build` |
| Base planning commit | `4bb677f9e0266f4dc48405181696019f359ae49f` |
| Planning head (frozen) | `agent/crypto-sensor-fabric-plan` @ `4bb677f9e0266f4dc48405181696019f359ae49f` |
| next_provider_authorized | FALSE beyond Kraken (I05 Kraken ONLY; I06 Gate NOT authorized) |
| next_checkpoint_authorized | FALSE (I05 complete offline; I06 Gate recommended but NOT authorized — await operator review) |

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
| SENSOR-B2-I13R1A | 21 | 21 | 0 |
| SENSOR-B2-I13R1B | 4 | 4 | 0 |
| SENSOR-B2-I13R1C | 2 | 2 | 0 |
| SENSOR-B2-I14A | 7 | 7 | 0 |
| SENSOR-B3-I01 | 19 | 19 | 0 |
| SENSOR-B3-I02 | 25 | 25 | 0 |
| SENSOR-B3-I03 | 25 | 25 | 0 |
| SENSOR-B3-I04 | 14 | 14 | 0 |
| SENSOR-B3-I04R1 | f929ae6f | 28 | 0 |
| SENSOR-B3-I04R2 | 48c639ed | 30 | 0 |
| SENSOR-B3-I04R2-RATIFY | 0 (governance) | — | — |
| SENSOR-B3-I05A | dc9b71af | 18 | 0 |
| SENSOR-B3-I05B | 490cd111 | 78 | 0 |
| SENSOR-B3-I05C | (evidence only) | — | — |
| cumulative | 762 | 762 | 0 |

## External / provider blockers

- BINANCE_USDM REST (`fapi.binance.com`): F_ACCESS_GEO from this region (HTTP 451 with "Service unavailable from a restricted location … Eligibility" on all four /fapi/v1 sensors). The public data.binance.vision archive is REACHABLE from the same region (OI + aggTrades history verified at 2022) — proves REST_BLOCKED ≠ ARCHIVE_BLOCKED.
- BYBIT_LINEAR (`bybit.com` via CloudFront): F_ACCESS_GEO from this region (403 hard block on all four sensors). No bypass attempted.
- GATE_FUTURES `contract_stats`: no GEO/AUTH issue on the public surface; but historical `from` beyond 180 days is rejected (`INVALID_PARAM_VALUE: from time exceeds 180-day limit`) — recent-only (rolling 180-day boundary, proven live at the 2022 checkpoint; older dates synthesized HISTORY_BLOCKED_BY_VERIFIED_RETENTION_BOUNDARY). Funding/trades contract corrected in I13R1: single GET /funding_rate + GET /trades use Unix SECONDS from/to (the earlier INVALID_CREDENTIALS on the plural POST /funding_rates was a REQUEST_CONTRACT_INVALID, not provider auth); rows {r,t} / signed-size trades verified.
- KRAKEN_FUTURES Market Analytics: reachable; historical reach is RAGGED by sensor/instrument (I13R1): liquidation-volume verified 2021-2026; OI verified 2024/2026 (EMPTY_VALID 2021/2022, BTC+ETH); basis verified 2022+; book-metric 2024+; funding EMPTY_VALID at 2021/2022/2024 but VERIFIED 2026+recent. `/history` trade and `/orderbook` snapshots return F_SCHEMA_CHANGED on the current API surface (analytics family is the healthy path).
- COINALYZE: no local free API key configured — recorded CREDENTIAL_NOT_CONFIGURED (4 scopes NOT_ATTEMPTED), never AUTH_BLOCKED.

## Data blockers

- None yet — no data acquisition in Bloc 1.

## Disk / storage status

- Bloc 1 stores only code, schemas, configs, tests and evidence in Git.
- No market data written. Actual T0/T1/T2 data lives outside Git (later blocs).

## Live probe status

- SENSOR-B2-I13 COMPLETE — first controlled live capability evidence run executed
  (probe_run_id `bloc02_i13_...`, 47 attempts, 23 verified samples / 14 failed / 6
  empty-valid / 4 not-attempted). Live probe runner: `scripts/bloc_02_i13_live.py`
  (sequential, bounded retry, low concurrency, gitignored raw evidence under
  `quant-lab/data/`, sanitized packet under `evidence/bloc_02/`). Followed by
  SENSOR-B2-I13R1 repair and SENSOR-B2-I14 role freeze.
- SENSOR-B2-I13R1 COMPLETE — evidence integrity/completion repair. 113 attempts
  (78 verified / 18 empty-valid / 13 failed / 4 not-attempted), 34/34 canonical
  scopes in reports (registry-driven universe, no scope drops), full frozen
  checkpoint matrix per scope with short-circuits (CURRENT_ONLY,
  HISTORY_BLOCKED_BY_VERIFIED_RETENTION_BOUNDARY, surface geo/auth), E2+ claims
  carry resolving evidence_ids, PIT fail-closed, verified-only redundancy,
  per-instrument history boundaries, Bitfinex = SOURCE_AVAILABILITY_VERIFIED only,
  Gate funding/trades corrected to Unix SECONDS (GET /funding_rate verified
  recent+2026; /trades verified recent). Merge-on-resume runner stays idempotent.
- Live contract corrections from observed evidence: Gate `contract_stats`
  `interval` is a STRING bucket ("1h"), not seconds; Deribit funding `get_funding_rate_history`
  result is a raw LIST (not `{data:[...]}`); Bybit CloudFront country block is F_ACCESS_GEO,
  not auth; Kraken analytics `data` may be a dict-of-lists for some types. Each recorded in
  the probe module + contradiction files.

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

- SENSOR-B3-I04R2-RATIFY COMPLETE — operator ACCEPTED the hardened Bloc 3
  common foundation for first-provider implementation.  provider_adapter
  implementation authorized = KRAKEN_FUTURES ONLY.  current checkpoint =
  SENSOR-B3-I05.  next_provider_authorized = FALSE beyond Kraken.  I06 Gate
  NOT authorized.
- SENSOR-B3-I05 COMPLETE (OFFLINE) — KRAKEN_FUTURES production adapter
  implemented on the common foundation with evidence-backed native acquisition
  modes (Market Analytics REST_RANGE / TIME_RANGE, epoch-second since/to,
  interval in seconds, result.more resume) grounded in the I14 promotion set
  and Bloc 2 I13R1 evidence.  Exactly six promoted paths ADAPTER_READY;
  MECHANICAL_TRADE + MECHANICAL_BOOK_SNAPSHOT stay typed unsupported.
  PRODUCTION_CANDIDATE conformance 0 failed; 762 passed / 0 failed; ruff
  clean; FAKE TRANSPORT ONLY — zero network calls; no Bloc 4 code.
  Evidence: `evidence/bloc_03/BLOC_03_I05_KRAKEN_IMPLEMENTATION_EVIDENCE.md`.
- Recommended next checkpoint: **SENSOR-B3-I06 — GATE_FUTURES**, but it is
  NOT authorized (`next_checkpoint_authorized = FALSE`); stop and await
  operator review of PASS_SENSOR_B3_I05_KRAKEN_ADAPTER_OFFLINE.

## Prior next-checkpoint history

- SENSOR-B2-RATIFY COMPLETE — operator RATIFIED the Bloc 2 provider-role
  decision (PASS_BLOC_02_WITH_SENSOR_GAPS, co-earned
  PASS_BLOC_02_FREE_ONLY_REDUNDANCY).  Bloc 2 = IMPLEMENTATION COMPLETE /
  OPERATOR RATIFIED.
- SENSOR-B3-I01..I04 COMPLETE — BLOC 3 COMMON FOUNDATION: base models +
  provider protocol, free-only access gate, request fingerprinting + raw
  envelope integrity, retry/rate-limit/pagination/resume mechanics, and the
  common provider conformance suite (fake adapter passes; degraded adapters
  fail the exact invariant).  I14 promotion-file capability binding in place
  (source_promotion_candidates.yaml is the ONLY input list).  Status =
  COMMON_FRAMEWORK_READY; PROVIDER_ADAPTER_READY = NO (zero adapters built).
  Bloc 3 implementation evidence: `evidence/bloc_03/`.
- SENSOR-B3-I04R1 COMPLETE — COMMON CONFORMANCE HARDENING: strict full-I14
  promotion-bound enforcement (sensor/role/history/PIT/pin/redundancy/access/
  hazards/evidence), fail-closed PRODUCTION_CANDIDATE vs FRAMEWORK_TEST mode,
  live-vs-historical mode separation (CURRENT_ONLY -> live, no auto-granted
  live from historical; HISTORICAL -> live NONE), strict promotion-file
  parsing (unknown/missing required values fail closed), real behavioral
  empty-valid vs unsupported + schema-drift fail-closed + retry-classifier
  conformance via the I03 classifier, valid-typed adversarial fixtures.
  636 passed / 0 failed, ruff clean, zero network calls, zero provider
  adapters built.  Evidence: `evidence/bloc_03/BLOC_03_I04R1_HARDENING.md`.
- SENSOR-B3-I04R2 COMPLETE — FINAL COMMON-FOUNDATION CONFORMANCE CLOSURE:
  empty-valid vs unsupported and provider method dispatch are now BEHAVIORAL
  (the suite invokes the real adapter's `fetch_*` methods via a new
  provider-independent `dispatch_fetch` — Issues 1/2); every adversarial
  fixture is a VALID typed model (model_dump + model_validate, enum members —
  Issue 3); promotion bounds now bind live_mode/archive_mode/access_path/auth/
  free_access_status/history_scope and forbid manufacturing an exact native
  historical_mode from a coarse I14 history label (Issues 4/8/9); the probe
  evidence ref must RESOLVE (provider+sensor+id all match I14 lineage —
  Issue 5); promotion-file structure is strict (root/schema_version/candidates
  shape, provider+sensor required, duplicates fail — Issue 6); the I14
  access_path is authoritative — `auth_mode_override` removed (Issue 7);
  geo/access/payment never retried even with budget (Issue 7); schema
  fail-closed is proven against a fake parser (Issue 10).  666 passed / 0
  failed, ruff clean, zero network calls, zero provider adapters built,
  zero Bloc 4 code.  Evidence:
  `evidence/bloc_03/BLOC_03_I04R2_CONFORMANCE_CLOSURE.md`.
- `next_checkpoint_authorized = FALSE` — SENSOR-B3-I05 (Kraken) and any
  provider adapter await OPERATOR REVIEW of the hardened, behaviorally closed
  common foundation.
  - Full evidence packet: `evidence/bloc_02/` (01-11 evidence; 12-16 decision).
  - Bloc 3 implementation evidence: `evidence/bloc_03/` (added by I01-I04 + I04R1).

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
| SENSOR-B2-I12R1D | 0b5d6143 | regenerated pre-live evidence packet from corrected registry + full revalidation | 491 passed / 0 failed | PASS | none |
| SENSOR-B2-I13 | be8ba89b | first controlled live capability evidence run: live probe runner, probe contract fixes from live observation, sanitized evidence packet (01-11) with real CAPABILITY_CLAIMS / FAILURES / contradictions, progress ledger | 491 passed / 0 failed (offline suite unaffected) | PASS_WITH_LIMITATIONS | Binance REST + Bybit geo-blocked; Gate contract_stats 180-day limit; Kraken /history + /orderbook schema drift; Coinalyze no key |
| SENSOR-B2-I13R1A | 6abd5d66 | evidence lineage (E2+ requires resolving evidence_ids) + PIT fail-closed invariants + verified-only redundancy + per-instrument history boundaries + report synthesis fixes + tests | 512 passed / 0 failed | PASS | none |
| SENSOR-B2-I13R1B | 65d3934d | Gate funding/trades contract correction: single GET /funding_rate + /trades with Unix SECONDS (ms was REQUEST_CONTRACT_INVALID), rows {r,t}/signed-size, 180-day boundary; golden tests; manifest updates | 516 passed / 0 failed | PASS | none |
| SENSOR-B2-I13R1C | 022ed7bb | restore 34-scope universe + full frozen checkpoint matrix (2021/2022/2024/2026) with short-circuits + Kraken liquidation via analytics + archive merge idempotency + enum members + targeted live probes | 518 passed / 0 failed | PASS | none |
| SENSOR-B2-I13R1D | 9709335b | regenerated I13R1 evidence packet from corrected contracts (34 scopes, 113 attempts) + ledger + full revalidation | 518 passed / 0 failed | PASS | none |
| SENSOR-B2-I14A | 7d5b4372 | decision.py final-role/redundancy/exclusion/contradiction/promotion adjudication + promote-candidate render + tests | 525 passed / 0 failed | PASS | none |
| SENSOR-B2-I14B | b149e3e2 | I14 decision generator script + final packet artifacts (12 decision md, 13-16 matrices, source_promotion_candidates.yaml; decision head pinned to I14A) | 525 passed / 0 failed | PASS | none |
| SENSOR-B2-RATIFY | a0181a92 | operator ratification of Bloc 2 provider-role decision recorded in ledger (governance only) | 525 passed / 0 failed | PASS | none |
| SENSOR-B3-I01 | 6ce9fb5d | base adapter package (providers/base/): controlled vocabularies, FetchRequest/FetchBatch/RawPayloadEnvelope/ResumeToken models, typed error taxonomy, MechanicalProviderAdapter protocol; Bloc 2 probe base renamed base.py -> probe_base.py; tests | 544 passed / 0 failed | PASS | none |
| SENSOR-B3-I02 | 28a20272 | free-only access gate (Bloc 1 F9 policy + Bloc 3 auth vocabulary, fail closed, runs before transport), deterministic request fingerprint + raw payload integrity hash; tests | 569 passed / 0 failed | PASS | none |
| SENSOR-B3-I03 | 45b1683a | retry classification + bounded exponential backoff (no geo/access retries), normalized rate-limit snapshots (UNKNOWN valid), cursor-loop/non-monotonic protection, deterministic resume-token round-trip, provider-semantics completion; tests | 594 passed / 0 failed | PASS | none |
| SENSOR-B3-I04 | 41296e1c | common provider conformance suite (Q0 contract/Q1 parser/Q2 mechanics) + I14 promotion-file capability binding (allowed_role/history_mode/verified_history/PIT bounds); fake adapter passes, degraded adapters fail exact invariants; bloc_03 evidence area; tests | 608 passed / 0 failed | PASS | none |
| SENSOR-B3-I04R1A | f929ae6f | conformance hardening: full I14 promotion-bound enforcement, PRODUCTION_CANDIDATE/FRAMEWORK_TEST modes (fail closed by default), live-vs-historical mode separation, strict promotion-file parsing, schema-drift classifier (no zero coercion), behavioral empty-valid/schema/retry conformance, valid-typed adversarial fixtures, declared_capabilities removed; tests | 636 passed / 0 failed | PASS | none |
| SENSOR-B3-I04R1B | (see below) | I04R1 hardening evidence + full ledger reconciliation (current-state, test counts, I04 SHA, I04R1 narrative, next-checkpoint flags) | 636 passed / 0 failed (re-run) | PASS | none |
| SENSOR-B3-I04R2A | 48c639ed | behavioral dispatch + empty-valid/unsupported (Issue 1/2), valid-typed adversarial fixtures (Issue 3/11), full live/archive/access/auth + history-scope surface binding (Issue 4/9), resolving evidence refs (Issue 5), strict promotion-file structure (Issue 6), auth override removed (Issue 7), HistoryScope/no manufactured native mode (Issue 8), geo/access/payment never retried (Issue 7); tests | 666 passed / 0 failed | PASS | none |
| SENSOR-B3-I04R2B | 7011c544 | I04R2 closure evidence + full ledger reconciliation (current-state, test counts, commit log) | 666 passed / 0 failed (re-run) | PASS | none |
| SENSOR-B3-I04R2-RATIFY | 9fb266fd | governance only: operator accepts common foundation for Kraken implementation (I05 authorized, KRAKEN_FUTURES ONLY; I06 Gate NOT authorized) | — | PASS | none |
| SENSOR-B3-I05A | dc9b71af | base native-evidence seam (ProviderNativeCapabilityEvidence) + q0_native_mode_evidence conformance gate + adversarial tests | 684 passed / 0 failed | PASS | none |
| SENSOR-B3-I05B | 490cd111 | Kraken package: request builders, provider-native parsers, typed error mapping, KrakenAdapter + fake-transport tests | 762 passed / 0 failed | PASS | none |
| SENSOR-B3-I05C | (see reconciliation) | Kraken fixtures/manifest, README, implementation evidence, readiness matrix, ledger | 762 passed / 0 failed (re-run) | PASS | none |

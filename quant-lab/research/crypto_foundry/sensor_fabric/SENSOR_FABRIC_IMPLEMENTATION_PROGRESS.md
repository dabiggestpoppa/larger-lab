# SENSOR FABRIC — IMPLEMENTATION PROGRESS LEDGER

Human-readable execution ledger for the Crypto Mechanical Sensor Fabric build.
This ledger is NOT a substitute for Git history; it is an operator-facing summary
that is updated at every staged checkpoint.

---

## Current state

| Field | Value |
|---|---|
| Current Bloc | 4 — IMMUTABLE T0 RAW EVIDENCE LAKE |
| Current checkpoint | SENSOR-B4-I01 — STORAGE MODELS + ENUMS (proposed PASS_SENSOR_B4_I01_STORAGE_CONTRACTS_FROZEN; BLOC_03_IMPLEMENTATION = OPERATOR_ACCEPTED / FROZEN via SENSOR-B3-I11R1-RATIFY; BLOC_04_PLAN = PASS_BLOC_04_PLAN_FROZEN; typed storage vocabulary only — NO persistence, NO backend, NO network) |
| Bloc 2 verdict | PASS_BLOC_02_WITH_SENSOR_GAPS (co-earned PASS_BLOC_02_FREE_ONLY_REDUNDANCY) — IMPLEMENTATION COMPLETE, OPERATOR RATIFIED (SENSOR-B2-RATIFY) |
| Bloc 1 verdict | PASS_BLOC_01_CONTRACTS_FROZEN — operator_ratified = TRUE (see evidence/bloc_01/BLOC_01_DECISION.md) |
| Operator review state | RATIFIED — Bloc 2 ratified; Bloc 3 COMPLETE + OPERATOR_ACCEPTED + FROZEN (SENSOR-B3-I11R1-RATIFY: PASS_SENSOR_B3_I11R1_HANDOFF_CONSISTENCY_SEALED = OPERATOR_ACCEPTED, PASS_BLOC_03_IMPLEMENTATION = OPERATOR_ACCEPTED, BLOC_03_IMPLEMENTATION_COMPLETE=TRUE, BLOC_03_FROZEN=TRUE, NETWORK_VALIDATION=PASS, REAL_PROVIDER_ADAPTERS=4, PRODUCTION_PATHS=17/17, PHYSICAL_PRODUCTION_SYMBOL_CHECKS=18/18; authorized SENSOR-B4-I01 STORAGE MODELS + ENUMS ONLY); BLOC_04_PLAN = PASS_BLOC_04_PLAN_FROZEN; Bloc 4 I01 in progress — typed storage vocabulary only, no persistence yet |
| human_review_required | TRUE |
| Bloc 2 implementation_authorized | TRUE (COMPLETE — ratified) |
| Bloc 3 implementation_authorized | TRUE — common foundation complete/hardened/behaviorally closed (SENSOR-B3-I01..I04 + I04R1 + I04R2); provider_adapter_implementation_authorized = NONE beyond I08 (Kraken + Gate + OKX + Deribit implemented offline; next step requires operator authorization) |
| Common foundation status | COMMON_FRAMEWORK_READY=TRUE · BEHAVIORAL_CONFORMANCE_READY=TRUE · REAL_PROVIDER_ADAPTERS=4 (KRAKEN_FUTURES + GATE_FUTURES + OKX_SWAP + DERIBIT, offline) · PROVIDER_PARSER_CONFORMANCE=OFFLINE_PASS (Kraken + Gate + OKX + Deribit; PRODUCTION_CANDIDATE mode, 0 failed each) · I14 PRODUCTION-ADAPTER INVENTORY = 17/17 provider×sensor candidates implemented OFFLINE (4 providers × I14 sets) · CROSS_PROVIDER_OFFLINE_CLOSURE=TRUE (SENSOR-B3-I09; deterministic PRODUCTION_ADAPTER_MATRIX.csv/.json derived from I14 + adapter code; exact-set 3-level equality proven) · AUTHORITY_DUPLICATE_GUARD=TRUE (I09R1: duplicate I14 promotion + duplicate human readiness keys fail closed) · VERIFICATION_COVERAGE_GUARD=TRUE (I09R1: explicit complete verification required; missing != explicit False; ADAPTER_READY cannot coexist with failed validation; network smoke locked NOT_RUN in the immutable I09 matrix) · NETWORK_VALIDATION=PASS (I10 run i10-live + I10R1 run i10r1-recheck overlay + I10R2 run i10r2-recheck seal: 17/17 logical paths, 18/18 physical production-symbol checks; I09 matrix untouched) · BLOC_03_IMPLEMENTATION_COMPLETE=TRUE · BLOC_03_FROZEN=TRUE (SENSOR-B3-I11 final validation + handoff; G1–G8 gates PASS / PASS_WITH_LIMITED; handoff package + integrity tests green; provider implementation code unchanged; zero network in I11) |
| Bloc 3 adapter status | kraken_adapter_implemented = TRUE · kraken_offline_implementation_frozen = TRUE · kraken_network_smoke = NOT_RUN · gate_adapter_implemented = TRUE · gate_offline_implementation_frozen = TRUE · gate_network_smoke = NOT_RUN · okx_adapter_implemented = TRUE · okx_offline_sealed = TRUE · okx_implementation_frozen = TRUE · okx_network_smoke = NOT_RUN · deribit_adapter_implemented = TRUE (I08) · deribit_completion_truth_sealed = TRUE (I08R1) · deribit_offline_sealed = TRUE (I08R1) · deribit_offline_implementation_frozen = TRUE (I08R1-RATIFY) · deribit_network_smoke = NOT_RUN · bloc_03_common_foundation_complete = TRUE · cross_provider_offline_closure = TRUE (SENSOR-B3-I09 COMPLETE; deterministic 17-path production inventory + exact-set equality + evidence-ref/scope/role audits; matrix generated, NOT hand-declared) · cross_provider_authority_sealed = TRUE (SENSOR-B3-I09R1; duplicate authority + verification-coverage guards; matrix regeneration byte-identical) · network_validation = PASS (SENSOR-B3-I10 run i10-live + SENSOR-B3-I10R1 run i10r1-recheck overlay + SENSOR-B3-I10R2 run i10r2-recheck semantic seal; 17/17 logical, 18/18 physical; the immutable I09 matrix keeps network_smoke_status = NOT_RUN) · gate_completion_truth_sealed = TRUE (I10R2B: runtime is_complete=False matches frozen LIMITED/LIMITED authority; no invented resume token) · kraken_additive_firewall_sealed = TRUE (I10R2C: unknown additive metrics preserved raw, never projected) · adapter_semantic_versions = gate-adapter-v2, kraken-adapter-v2 (I10R2C; OKX/Deribit v1 unchanged) |
| Last successful commit SHA | (see commit log below) |
| Branch | `agent/crypto-sensor-fabric-build` |
| Base planning commit | `4bb677f9e0266f4dc48405181696019f359ae49f` |
| Planning head (frozen) | `agent/crypto-sensor-fabric-plan` @ `4bb677f9e0266f4dc48405181696019f359ae49f` |
| next_provider_authorized | FALSE (all four I14 production providers implemented offline; no further provider without operator authorization) |
| next_checkpoint_authorized | FALSE — Bloc 4 I01 in progress; recommended next (after operator acceptance of I01): SENSOR-B4-I02 CONTENT ADDRESSING + PATHS + CHECKSUMS (NOT started) |

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
| SENSOR-B3-I05R1A | 17e70035 | 31 | 0 |
| SENSOR-B3-I05R1B | a1e191ea | 14 | 0 |
| SENSOR-B3-I05R2A | a737d9e6 | 22 | 0 |
| SENSOR-B3-I05R2-RATIFY | (governance) | — | — |
| SENSOR-B3-I06A | b30ab5d6 | 15 | 0 |
| SENSOR-B3-I06B | 4f0ee81b | 88 | 0 |
| SENSOR-B3-I06C | (evidence only) | — | — |
| SENSOR-B3-I06-RATIFY | (governance) | — | — |
| SENSOR-B3-I07A | be075378 | 17 | 0 |
| SENSOR-B3-I07B+C | 699a2ede | 89 | 0 |
| SENSOR-B3-I07C | (evidence only) | — | — |
| SENSOR-B3-I07R1A | ffbdfdfd | 8 | 0 |
| SENSOR-B3-I07R1B | 820feca4 | 21 | 0 |
| SENSOR-B3-I07R1C | (evidence/readiness/ledger) | — | — |
| SENSOR-B3-I07R2A | cf269288 | 7 | 0 |
| SENSOR-B3-I07R2B | (evidence/ledger) | — | — |
| SENSOR-B3-I07R2-RATIFY | (governance) | — | — |
| SENSOR-B3-I08A | f6acec7e | 20 | 0 |
| SENSOR-B3-I08B+C | 82e23c52 | 148 | 0 |
| SENSOR-B3-I08R1A | 3b6f8c39 | 0 (code) | — |
| SENSOR-B3-I08R1B | d44831c7 | 10 | 0 |
| SENSOR-B3-I08R1-RATIFY | (governance) | — | — |
| SENSOR-B3-I09A | dffe18f6 | 0 (code) | — |
| SENSOR-B3-I09B | d299cdd2 | 42 | 0 |
| SENSOR-B3-I09C | 08559207 | 0 (generated matrix) | — |
| SENSOR-B3-I09R1A | b3e26cef | 0 (code) | — |
| SENSOR-B3-I09R1B | 17636a78 | 15 | 0 |
| SENSOR-B3-I09R1C | 1dd03835 | 0 (evidence/ledger) | — |
| SENSOR-B3-I09R1-RATIFY | (governance) | — | — |
| SENSOR-B3-I10A | f92d6bd9 | 29 | 0 |
| SENSOR-B3-I10B | c4bc5c3e | 0 (live evidence) | — |
| SENSOR-B3-I10C | (this commit) | 0 (evidence/ledger) | — |
| SENSOR-B3-I10R1A | 37542be5 | 0 (evidence only) | — |
| SENSOR-B3-I10R1B | c773aaac | (gate repair tests; full-suite cumulative first at I10R1D) | — |
| SENSOR-B3-I10R1C | fb8c4d48 | (kraken repair tests; full-suite cumulative first at I10R1D) | — |
| SENSOR-B3-I10R1D | 6081b88a | 15 (cumulative 1353) | 0 |
| SENSOR-B3-I10R1E | e6b67d37 | 1 (cumulative 1354) | 0 |
| SENSOR-B3-I10R1F | (this commit) | 0 (ledger) | — |
| SENSOR-B3-I10R2A | da4123b2 | 0 (evidence/adjudication) | — |
| SENSOR-B3-I10R2B | d7c49225 | 5 (cumulative 1359) | 0 |
| SENSOR-B3-I10R2C | cb3bff61 | 1 (cumulative 1360) | 0 |
| SENSOR-B3-I10R2D | 6fc1551d | 0 (live evidence) | — |
| SENSOR-B3-I10R2E | 55eb5a2d | 0 (evidence/ledger) | — |
| SENSOR-B3-I10R2-RATIFY | 8478eeb5 | 0 (governance) | — |
| SENSOR-B3-I11A | 61821aac | 0 (audit machinery + Deribit README docs audit fix) | — |
| SENSOR-B3-I11A-fix | 583a777a | 0 (generator mypy/ruff hygiene, artifacts byte-identical) | — |
| SENSOR-B3-I11B | 9651479f | 0 (generated handoff artifacts) | — |
| SENSOR-B3-I11C | 8ee37b3d | 0 (reports) | — |
| SENSOR-B3-I11D | 8f5f18ad | 7 (handoff integrity tests) | 0 |
| SENSOR-B3-I11E | 34bcc0fe | 0 (ledger/freeze) | — |
| SENSOR-B3-I11E-fix | 5f510974 | 0 (ledger row fix) | — |
| SENSOR-B3-I11R1A | (this commit) | 0 (handoff role/limitations repair + generator fix) | — |
| SENSOR-B3-I11R1B | (next commit) | 12 (cross-surface semantic consistency tests) | 0 |
| SENSOR-B3-I11R1C | (next commit) | 0 (test-truth reconciliation) | — |
| SENSOR-B3-I11R1D | (next commit) | 0 (seal evidence/ledger) | — |
| cumulative | 1379 | 1379 | 0 |

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

- SENSOR-B3-I11R1 COMPLETE — FINAL HANDOFF CONSISTENCY + TEST-TRUTH SEAL
  (proposed `PASS_SENSOR_B3_I11R1_HANDOFF_CONSISTENCY_SEALED`).  Operator
  review held `PASS_BLOC_03_IMPLEMENTATION` pending three handoff-truth
  repairs, all closed:
  - **OKX role truth (A).**  `PROVIDER_IMPLEMENTATION_REPORT.md` mislabeled
    OKX FUNDING/TRADE as SECONDARY; authoritative I14 + final matrix say
    PRIMARY.  Human report corrected; a regression test now validates the
    report role table against the final machine matrix (no second truth
    surface), and the OKX adversarial assertion locks BOOK_SNAPSHOT =
    CURRENT_ONLY / FUNDING = PRIMARY / TRADE = PRIMARY.
  - **Test-truth (B).**  `OFFLINE_TEST_REPORT` claimed 1360 final, but the
    I11D handoff-integrity tests (7) had already raised the true final to
    1367.  After I11R1 the ENTIRE ordinary suite (including handoff integrity
    + the new semantic-consistency tests) is **1379 passed / 0 failed / 1
    skipped** (env-gated live smoke, fail-closed); report + ledger now carry
    the same actual count; historical 1360/1367 executions preserved as
    history.
  - **Path-specific Deribit limitations (C).**  Generator fixed
    (`generate_bloc_03_i11_handoff.py`): FUNDING carries only funding
    continuation LIMITED prose; LIQUIDATION only the trade-level microscope +
    source-page coverage; TRADE only the native trade-event surface.  All
    generated surfaces regenerated (overlay/capability/final matrix/
    fixture report) and byte-identical on double run (SHA-256 recorded in
    the seal evidence).
  Cross-surface semantic-equality tests added (I11R1B, +12): exact-set 17
  across I14/I09/capability/overlay/final; role == I14 allowed_role; symbol
  scope, history scope, PIT, methodology pin, resume/completion equal across
  surfaces; current adapter versions agree (v2/v2/v1/v1) while I09 keeps v1
  provenance and NOT_RUN network state (chronology-aware, not naive
  equality).  Provider implementation code UNCHANGED; I09 matrix and all
  I10/I10R1/I10R2 artifacts untouched; I11R1 network calls = 0.  Proposed
  verdict: `PASS_SENSOR_B3_I11R1_HANDOFF_CONSISTENCY_SEALED` then
  `PASS_BLOC_03_IMPLEMENTATION` (BLOC_03_IMPLEMENTATION_COMPLETE=TRUE,
  BLOC_03_FROZEN=TRUE, NETWORK_VALIDATION=PASS).  Evidence:
  `evidence/bloc_03/BLOC_03_I11R1_HANDOFF_CONSISTENCY_SEAL.md`.
- SENSOR-B3-I11 COMPLETE — FINAL BLOC 3 VALIDATION + HANDOFF (proposed
  `PASS_BLOC_03_IMPLEMENTATION`).  Numbering note (§2): I11 fulfills BOTH the
  frozen planning responsibilities I15 (final validation) AND I16 (handoff);
  old plan history is not rewritten.  Final authority order honored
  (Bloc 1 contracts -> Bloc 2 evidence -> I14 promotions -> frozen Bloc 3
  architecture -> adapter code -> I09 matrix -> I10/I10R1/I10R2 live evidence
  -> runtime overlay -> derived handoff artifacts).  Final inventory:
  registry exactly 4 (KRAKEN_FUTURES/GATE_FUTURES/OKX_SWAP/DERIBIT),
  production paths 17/17, physical symbols 18/18, roles PRIMARY=7 /
  SECONDARY=6 / CURRENT_ONLY=2 / MECHANISM_MICROSCOPE=2, adapter versions
  kraken-adapter-v2 / gate-adapter-v2 / okx-adapter-v1 / deribit-adapter-v1.
  Acceptance gates: G1 PASS, G2 PASS, G3 PASS, G4 PASS_WITH_LIMITED,
  G5 PASS, G6 PASS, G7 PASS, G8 PASS.  Audits: exact-set equality (17) across
  I14/adapter/I09/overlay/final matrix; evidence refs all resolve; fixture
  coverage 17/17 paths; docs audit 4/4 READMEs; typed-failure + free-only
  adversarial suites green; current-only paths explicitly current-only;
  runtime overlay regenerated path-specific (no provider-wide prose).  Final
  full suite 1367 passed / 0 failed (1 skipped live, fail-closed); normal
  suite makes ZERO network calls; I11 network calls = 0.  Handoff package:
  `FINAL_ADAPTER_READINESS_MATRIX.csv/.json`,
  `PROVIDER_CAPABILITY_RUNTIME.json`, `PROVIDER_IMPLEMENTATION_REPORT.md`,
  `KNOWN_FAILURES.md`, `ACCESS_CLASS_REPORT.md`, `OFFLINE_TEST_REPORT.json`,
  `NETWORK_SMOKE_EVIDENCE_INDEX.md`, `BLOC_04_INPUT_MANIFEST.md`,
  `BLOC_03_HANDOFF_INDEX.md` + `test_handoff_integrity.py` (7 tests).
  Machine artifacts deterministic (run twice, byte-identical).  Provider
  implementation code UNCHANGED; I09 matrix and all I10/I10R1/I10R2
  artifacts untouched.  BLOC_03_IMPLEMENTATION_COMPLETE=TRUE,
  BLOC_03_FROZEN=TRUE, NETWORK_VALIDATION=PASS.  next_checkpoint_authorized
  = FALSE; recommended next: **SENSOR-B4-I01 IMMUTABLE T0 RAW EVIDENCE LAKE
  FOUNDATION** — NOT begun; Bloc 4 must not be incepted here.  Evidence:
  `evidence/bloc_03/` (PROVIDER_IMPLEMENTATION_REPORT.md + handoff index).
- SENSOR-B3-I10R2 COMPLETE — SEMANTIC CONSISTENCY SEAL (proposed
  `PASS_SENSOR_B3_I10R2_SEMANTIC_CONSISTENCY_SEALED`).  Three closure issues
  from operator review of I10R1 were closed:
  - **Gate adjudication reconciled (I10R2A).**  I10R1A's provisional
    `B_PROVIDER_SEMANTIC_DRIFT` is SUPERSEDED: the ONLY committed ms evidence
    was the I05-era SYNTHETIC_SCHEMA_FIXTURE (proves tests, not provider
    history); I13 datetimes were unit-masked; therefore the real historical
    provider unit is **UNIDENTIFIED** and the ms assumption was a
    **PRIOR_CHARACTERIZATION / SYNTHETIC-FIXTURE ERROR** (final
    `A_PRIOR_CHARACTERIZATION_ERROR_WITH_UNIDENTIFIED_HISTORICAL_UNIT`).
    Current contract = epoch seconds (live-proven); no provider drift is
    claimed; all current Gate docs/code carry this one canonical diagnosis.
    `BLOC_03_I10R2_SEMANTIC_RECONCILIATION.json` records the supersession;
    the I10R1A artifact remains immutable history.
  - **Gate completion truth sealed (I10R2B).**  Runtime no longer
    manufactures `is_complete=True`: all four Gate paths report
    `is_complete=False`, `next_resume_token=None`, with truthful
    PARTIAL_INTERVAL / GAP_DETECTED / EMPTY_VALID flags — matching the frozen
    I09 LIMITED/LIMITED matrix authority.  contract_stats deep traversal
    remains UNRESOLVED; funding from/to coverage is not proven exhaustive.
  - **Provenance versioned + Kraken firewall (I10R2C).**  Gate/Kraken
    adapters bumped to `gate-adapter-v2` / `kraken-adapter-v2` (OKX/Deribit
    untouched; I09 matrix keeps v1 as history).  Kraken `_build_dict_rows`
    now projects ONLY the evidence-backed required metric set — an unknown
    additive key is preserved raw and flagged, never silently promoted.
    `relativeRate` classification reconciled to REQUIRED (both keys in every
    observed response; earlier KNOWN_OPTIONAL wording superseded).
  - **Literal Kraken timestamp evidence (I10R2D).**  The I10R1 walker-capture
    gap is closed: the recheck captured native funding `timestamp` members
    `[1788170400000 … 1788253200000]` — 13-digit epoch MILLISECONDS decoding
    to 2026-08-31T10:00Z … 2026-09-01T09:00Z (hour grid, matches window).
  Targeted recheck (`i10r2-recheck`, manifest `ddb4dccdcdd4429b`): 5
  sequential GET calls (Gate FUNDING/LIQUIDATION/OI/POSITIONING BTC_USDT +
  Kraken funding PI_XBTUSD), 0 retries, 0 credentials → **5/5
  LIVE_PASS_NONEMPTY, KNOWN_SCHEMA**, v2 adapters, no 1970 artifact, Gate
  truthfully LIMITED (PARTIAL_INTERVAL), Kraken funding `more`-terminal
  complete.  Full suite 1360 passed / 0 failed pre and post; ruff clean;
  changed-scope mypy clean (pre-existing 10 baseline).  Combined I10 baseline
  + I10R1 overlay + I10R2 seal: physical production-symbol checks 18/18,
  logical paths 17/17 → `PASS_SENSOR_B3_I10_PRODUCTION_ADAPTER_NETWORK_SMOKE`
  = OPERATOR_ACCEPTABLE.  `BLOC_03_CURRENT_RUNTIME_ADAPTER_OVERLAY.json`
  (17 paths) is the current-runtime overlay for I11.  I09 matrix and all
  original I10/I10R1 artifacts UNTOUCHED.  `next_checkpoint_authorized =
  FALSE`; recommended next: **SENSOR-B3-I11 FINAL BLOC 3 VALIDATION +
  HANDOFF** — NOT begun; validators must not incept it.
  Evidence: `evidence/bloc_03/BLOC_03_I10R2_SEMANTIC_RECONCILIATION.json`,
  `BLOC_03_I10R2_TARGETED_RECHECK_PLAN.json`, `_RESULTS.json`,
  `BLOC_03_I10R2_SEMANTIC_SEAL_EVIDENCE.md`,
  `BLOC_03_CURRENT_RUNTIME_ADAPTER_OVERLAY.json`.
- SENSOR-B3-I10R1 COMPLETE — TARGETED REPAIR RECHECK (GATE/KRAKEN LIVE
  SEMANTIC REPAIR + TARGETED RECHECK).  Operator review of I10 returned
  `BLOCK_SENSOR_B3_I10_MIXED` (b51c3883): the narrow original diagnosis was
  overruled — 3 Gate contract_stats paths (LIQUIDATION / OPEN_INTEREST /
  POSITIONING, BTC_USDT) carried 1970 convenience timestamps for a 2026
  request (unit contradiction), and Kraken funding had null timestamps +
  additive flag.  I10R1 adjudicated against ALL committed evidence + 2
  sanitized characterization calls:
  - **Gate = PRIOR_CHARACTERIZATION_ERROR (A)** — live `time` is 10-digit
    epoch SECONDS (seconds interpretation → 2026 grid matching the request
    window; ms → 1970).  The I05-era ms fixture was a label/parser error,
    not provider drift; repaired to seconds with adversarial unit tests;
    native integers preserved; no magnitude heuristic.
  - **Kraken funding = sensor-specific epoch MILLISECONDS (B)** — NULL
    conveniences on 24 nonempty rows only occur on year-9999 overflow, i.e.
    13-digit ms; `result.data` metric set is EXACTLY {rate, relativeRate} —
    the I10 ADDITIVE was a parser-policy mislabel, not a new field.  Funding
    converts ms (other analytics stay seconds); known metric set widened;
    genuinely-new keys still classify ADDITIVE and are never promoted.
  - Fail-closed smoke temporal-plausibility guard added (I10R1D): nonempty
    historical/event batches need BOTH convenience timestamps inside a
    365-day envelope; 1970 cannot LIVE_PASS (TEMPORAL_SEMANTIC_REVIEW);
    CURRENT_ONLY books exempt; truthful LIMITED pages stay PARTIAL;
    empty-valid needs no fabricated timestamp.
  Targeted recheck (`i10r1-recheck`, manifest `e77646fd4c5202e4`, anchor
  2026-09-01T02:06:52Z): exactly the four affected paths, 4 sequential GET
  calls, 0 retries, 0 credentials → **4/4 LIVE_PASS_NONEMPTY, KNOWN_SCHEMA**,
  plausible 2026 timestamps, request fingerprints + raw hashes present, no
  1970 artifact, no null timestamps.  Total I10R1 live budget 2 + 4 = 6
  calls (max 6).  Combined with the immutable I10 baseline: physical
  production-symbol checks 18/18, logical paths 17/17 →
  **PASS_SENSOR_B3_I10R1_TARGETED_REPAIR_RECHECK** and
  **PASS_SENSOR_B3_I10_PRODUCTION_ADAPTER_NETWORK_SMOKE** (evidence overlay;
  the I09 matrix and all three original I10 artifacts remain untouched).
  `next_checkpoint_authorized = FALSE`; recommended next: **SENSOR-B3-I11
  FINAL BLOC 3 VALIDATION + HANDOFF** — NOT begun; validators must not
  incept it.
  Evidence: `evidence/bloc_03/BLOC_03_I10R1_STRUCTURAL_ADJUDICATION.json`,
  `BLOC_03_I10R1_TARGETED_RECHECK_PLAN.json`, `_RESULTS.json`,
  `_EVIDENCE.md`.  Full suite pre/post 1354 passed / 0 failed; ruff clean;
  changed-scope mypy clean (pre-existing 10 baseline).  I11 NOT started.
- SENSOR-B3-I10 EXECUTED (historical baseline — see evidence/bloc_03/): the
  FIRST authorized live-network checkpoint ran the full bounded 17-path /
  18-request plan once (run `i10-live`, manifest hash `2c2e791bfad10fb4`,
  anchor 2026-09-01T01:23:57Z, 18 calls, 0 retries).  Original automated
  classification: 17/18 LIVE_PASS (16 NONEMPTY + 1 EMPTY_VALID — Deribit
  liquidation genuinely empty in window) + 1 SCHEMA_ADDITIVE_REVIEW
  (Kraken funding PI_XBTUSD).  Operator review overruled this narrow
  diagnosis (BLOCK_SENSOR_B3_I10_MIXED) and the I10R1 overlay adds 4/4
  repaired recheck passes; the ORIGINAL I10 artifacts and hashes are
  immutable and were NOT rewritten.
- SENSOR-B3-I09R1-RATIFY COMPLETE (governance) — operator ACCEPTED
  `PASS_SENSOR_B3_I09R1_CROSS_PROVIDER_OFFLINE_CLOSURE_SEALED` and authorized
  SENSOR-B3-I10 (CONTROLLED PRODUCTION-ADAPTER NETWORK SMOKE) ONLY — the FIRST
  authorized live-network checkpoint.  KRAKEN_FUTURES, GATE_FUTURES, OKX_SWAP
  and DERIBIT remain OFFLINE_FROZEN; the offline production inventory (17
  provider×sensor paths) stays `network_smoke_status = NOT_RUN` (I10 writes
  NEW smoke evidence; it never rewrites the immutable I09 matrix).  NOT
  authorized: provider repairs, schema changes, history expansion, new
  providers, Bloc 4, MECH21, LF14, capital field, alpha.
- SENSOR-B3-I09R1 COMPLETE — CROSS-PROVIDER AUTHORITY BOUNDARY MICROSEAL
  (operator RATIFIED via SENSOR-B3-I09R1-RATIFY; NOT `PASS_BLOC_03`).  Three fail-closed authority
  seams repaired in `providers/readiness.py` + `test_production_matrix.py`
  (+15 tests; cumulative 1309):  (A) I14 promotion authority is validated
  structurally unique by `validate_promotion_candidate_uniqueness`
  (raw=17, unique=17, duplicates=0) BEFORE any set/dict conversion, wired into
  every authority consumer — `build_readiness_records`, `compute_exact_sets`,
  `evidence_ref_audit`, `validate_record_bound`; an exact OR conflicting
  duplicate row fails closed on every path.  (B) `load_human_readiness_matrix`
  rejects duplicate nonempty (provider, sensor) rows — identical or
  conflicting, no last-write-wins.  (C) `build_readiness_records` requires
  explicit, COMPLETE verification coverage for every I14 key (verbatim
  `verification` dict or complete `conformance_pass`+`schema_pass` maps);
  missing != explicit False; explicit False with a truthful non-ready status is
  allowed as data; `ADAPTER_READY` cannot coexist with a failed
  conformance/schema flag; `network_smoke_status` is hard-locked to `NOT_RUN`
  pre-I10.  Canonical `PRODUCTION_ADAPTER_MATRIX.csv/.json` regenerated
  byte-for-byte identical (17 rows; semantic content unchanged).  Exact
  17-path equality, roles, symbols, LIMITED states, CURRENT_ONLY and Deribit
  mechanism-microscope semantics all preserved.  Full suite green
  (1309 passed / 0 failed); ruff clean; changed-scope mypy clean; ZERO network;
  Kraken/Gate/OKX/Deribit regressions green; frozen provider code untouched;
  no I10 (network smoke); no Bloc 4.  Evidence:
  `evidence/bloc_03/BLOC_03_I09R1_AUTHORITY_SEAL_EVIDENCE.md`.
- SENSOR-B3-I09 COMPLETE — CROSS-PROVIDER ADAPTER MATRIX / OFFLINE CLOSURE
  (proposed `PASS_SENSOR_B3_I09_CROSS_PROVIDER_OFFLINE_CLOSURE`, awaiting
  operator review; NOT `PASS_BLOC_03`).  Proves the four production adapters
  form ONE coherent, evidence-bounded acquisition fabric.  New
  `crypto_sensor_fabric/providers/readiness.py`: 4-provider production
  registry + deterministic `AdapterReadinessRecord` inventory generator whose
  readiness is DERIVED from I14 (source_promotion_candidates.yaml) + real
  adapter `capabilities()` + resolved evidence refs + supplied conformance
  results (no self-attestation loop).  Canonical
  `evidence/bloc_03/PRODUCTION_ADAPTER_MATRIX.csv/.json` generated (17 rows).
  Exact-set equality proven at all three levels (I14 == adapter-supported ==
  matrix, each 17); provider counts 6/4/3/4; role counts 7/6/2/2; per-sensor
  source counts match; evidence refs all resolve to committed bloc_02
  artifacts; symbol scopes evidence-backed (probe instruments never leak);
  CURRENT_ONLY/resume LIMITED/mechanism-microscope preserved; all network
  smoke NOT_RUN; byte-for-byte deterministic; human
  ADAPTER_READINESS_MATRIX.csv reconciled (never an authority input).
  Cross-provider 42-test closure suite 0 failed; full suite green; ruff/mypy
  clean on changed modules; ZERO network; Kraken/Gate/OKX/Deribit regressions
  green; no provider code altered; no I10 (network smoke); no Bloc 4.
  Evidence: `evidence/bloc_03/BLOC_03_I09_CROSS_PROVIDER_OFFLINE_CLOSURE.md`.
- SENSOR-B3-I08R1-RATIFY COMPLETE (governance) — operator ACCEPTED
  PASS_SENSOR_B3_I08R1_DERIBIT_SEALED.  All four current production adapters
  recorded OFFLINE_FROZEN (KRAKEN_FUTURES, GATE_FUTURES, OKX_SWAP, DERIBIT)
  with network_smoke = NOT_RUN each.  Authorization = SENSOR-B3-I09
  CROSS-PROVIDER ADAPTER MATRIX / OFFLINE CLOSURE ONLY.  NOT authorized:
  production-adapter network smoke, Bloc 4, any other provider, adapter
  matrix, source expansion.  REAL_PROVIDER_ADAPTERS = 4;
  I14_PRODUCTION_PATHS_IMPLEMENTED_OFFLINE = 17 / 17.  No provider
  implementation code was modified in this governance commit.
- SENSOR-B3-I08R1 COMPLETE — DERIBIT COMPLETION + QUALITY SEMANTICS SEAL
  (repair after HOLD_PASS_SENSOR_B3_I08_DERIBIT_ADAPTER_OFFLINE_PENDING_
  I08R1_COMPLETION_SEAL).  Three defects fixed: (A) COMPLETE never carries
  PARTIAL_INTERVAL — completion is decided BEFORE quality flags (PARTIAL/GAP
  mutually exclusive; empty = EMPTY_VALID only); (B) funding terminal proof
  DEMOTED — the "short page under the count cap is exhaustive" rule is only a
  characterization heuristic and no committed artifact proves
  get_funding_rate_history returns ALL window records whenever
  len(result) < count, so funding is NEVER certified complete
  (completion_proof = LIMITED); (C) liquidation completion now uses the FULL
  schema-validated SOURCE-page coverage (new ParsedDeribit.coverage_timestamps
  seam), so a filtered projection cannot manufacture completeness — proven by
  the liquidation filter trap (ordinary trade outside window + liquidation
  inside + has_more=false → semantic output 1 row, is_complete=FALSE).
  Trade/liquidation keep has_more=false as the current-window terminal flag.
  PRODUCTION_CANDIDATE conformance 0 failed; 1252 passed / 0 failed; ruff
  clean; mypy clean on changed modules; Kraken + Gate + OKX regression green
  (frozen); zero network calls; no I09; no Bloc 4.  Evidence:
  `evidence/bloc_03/BLOC_03_I08R1_DERIBIT_COMPLETION_SEAL_EVIDENCE.md`.
- SENSOR-B3-I08 COMPLETE (OFFLINE) — DERIBIT PRODUCTION ADAPTER on the
  hardened common foundation.  Exactly four I14-promoted paths ADAPTER_READY:
  BOOK_SNAPSHOT CURRENT_ONLY, FUNDING SECONDARY historical, LIQUIDATION +
  TRADE MECHANISM_MICROSCOPE historical.  Production symbol scope
  evidence-derived (BTC-PERPETUAL only; probe keeps ETH/SOL).  Trade +
  liquidation share get_last_trades_by_instrument (start/end epoch-ms,
  count<=1000, include_old=true); funding result is a RAW LIST (observed
  LIVE); book is the current-only get_order_book snapshot (depth=25).
  JSON-RPC errors typed (40400 invalid instrument, 10001 rate limit, 10000/
  10002 auth, -32601/-32602 semantic; HTTP200 errors never EMPTY_VALID).
  Parser seal per 09 fingerprints (trade 13-field closed record, funding
  5-field closed record with funding_rate/1h/8h unverified-additive, book
  core timestamp/instrument_name/bids/asks); epoch-ms INT timestamps strict
  (bool rejected).  Liquidation microscope projects ONLY rows flagged
  "liquidation" (never interval totals; zero events -> EMPTY_VALID with raw
  preserved).  Completion truth: single window complete only when non-empty,
  all rows in-window and terminal (funding under count cap; trade/liq
  has_more=false); no invented resume token (continuation LIMITED).
  PRODUCTION_CANDIDATE conformance 0 failed; 1242 passed / 0 failed; ruff
  clean; mypy clean on changed modules; FAKE TRANSPORT ONLY — zero network
  calls; Kraken + Gate + OKX regression green (frozen); no Bloc 4; no other
  provider.  Evidence:
  `evidence/bloc_03/BLOC_03_I08_DERIBIT_IMPLEMENTATION_EVIDENCE.md`.
- SENSOR-B3-I07R2-RATIFY COMPLETE (governance) — operator ACCEPTED
  PASS_SENSOR_B3_I07R2_OKX_SEALED; OKX recorded OFFLINE_FROZEN
  (adapter_implemented = boundary_hardened = offline_sealed =
  implementation_frozen = TRUE, network_smoke = NOT_RUN) and may not be
  modified again before SENSOR-B3-I14 network smoke unless a regression,
  evidence contradiction, or explicit operator reopening.  Kraken + Gate stay
  OFFLINE_FROZEN.  Authorization = DERIBIT / SENSOR-B3-I08 ONLY.  No adapter
  matrix, no network smoke, no Bloc 4, no other provider.  REAL_PROVIDER_-
  ADAPTERS = 3 (Kraken + Gate + OKX).  No Kraken/Gate/OKX provider code was
  modified.
- SENSOR-B3-I08 (DERIBIT) is the CURRENT checkpoint — production adapter on
  the hardened common foundation; Deribit is the mechanism microscope
  (trade-level liquidation anatomy, never interval totals).  NOT yet started
  at this governance commit.
- SENSOR-B3-I07R2 COMPLETE — OKX WINDOW-OVERLAP TRUTH MICROSEAL (repair
  after HOLD_PASS_SENSOR_B3_I07R1_OKX_SEALED_PENDING_I07R2_MICROSEAL).
  Residual defect: PARTIAL/GAP overlap was decided from first/last RETURNED
  rows (assumes ascending order); OKX history can be returned descending, so a
  page with a valid in-window row could be misclassified GAP_DETECTED.  Fixed:
  overlap truth from ANY schema-validated row timestamp inside the requested
  [start, end) window (order-invariant); invariant violation fails closed;
  PARTIAL/GAP mutually exclusive; actual_first/last keep returned-row-order
  meaning (not min/max); historical stays is_complete=False with no invented
  resume; book CURRENT_ONLY unchanged.  Descending oldest/newest/middle,
  scrambled-page, true-gap and ascending-funding tests added.  Conformance
  0 failed; 1074 passed / 0 failed; ruff clean; mypy clean on changed module;
  Kraken + Gate regression green (frozen); zero network calls; no Deribit;
  no Bloc 4.  Evidence:
  `evidence/bloc_03/BLOC_03_I07R2_OKX_MICROSEAL_EVIDENCE.md`.
- SENSOR-B3-I07R1 COMPLETE — OKX ACQUISITION-TRUTH + SCHEMA-BOUNDARY SEAL
  (repair after HOLD_PASS_SENSOR_B3_I07_OKX_ADAPTER_OFFLINE_PENDING_I07R1).
  I14 sensor set, roles, BTC-USDT-SWAP scope, access, PIT, methodology pins,
  history bounds and CURRENT_ONLY book classification UNCHANGED.  Repairs:
  (1) window truth — historical funding/trade fetches are NEVER certified
  complete (continuation direction UNRESOLVED; single page returned with
  is_complete=False, no invented resume token, PARTIAL_INTERVAL / GAP_DETECTED
  flag; requested vs actual boundaries separate); book snapshot stays complete
  per unit; (2) parser required fields sealed to the closed 09 fingerprints
  (funding 7, trade 7, book 4 — every structural field required);
  (3) seqId exact-int typing (bool rejected); (4) book levels require at least
  [price, size]; (5) markPrice reconciled to optional/unverified additive
  (probe fixture only, NOT in the committed runtime fingerprint).
  PRODUCTION_CANDIDATE conformance 0 failed; 1067 passed / 0 failed; ruff
  clean; FAKE TRANSPORT ONLY — zero network calls; Kraken + Gate regression
  green (frozen, unchanged); no Deribit; no Bloc 4.  Evidence:
  `evidence/bloc_03/BLOC_03_I07R1_OKX_SEAL_EVIDENCE.md`.
- SENSOR-B3-I07 COMPLETE (OFFLINE) — OKX_SWAP production adapter on the
  hardened common foundation.  Exactly three I14-promoted paths (BOOK_SNAPSHOT
  CURRENT_ONLY, FUNDING + TRADE PRIMARY historical) ADAPTER_READY, production
  symbol scope evidence-derived (BTC-USDT-SWAP; probe keeps ETH/SOL/DOGE).
  Funding uses the PUBLIC /api/v5/public/funding-rate-history (never /market);
  trade uses /api/v5/market/history-trades; book is the current-only /books
  snapshot (sz=400, no historical cursor).  ms-epoch STRING timestamps validated
  strictly (no silent coercion).  Nonzero OKX v5 codes stay typed (never
  EMPTY_VALID).  Funding/trade after/before continuation direction UNRESOLVED
  by I13 evidence -> single evidence-backed request window (no invented
  continuation cursor).  PRODUCTION_CANDIDATE conformance 0 failed; 1038
  passed / 0 failed; ruff clean; FAKE TRANSPORT ONLY — zero network calls; no
  Deribit; no Bloc 4.  Kraken + Gate regression green (unchanged, still frozen).
  Evidence: `evidence/bloc_03/BLOC_03_I07_OKX_IMPLEMENTATION_EVIDENCE.md`.
- SENSOR-B3-I06-RATIFY COMPLETE (governance) — operator ACCEPTED
  PASS_SENSOR_B3_I06_GATE_ADAPTER_OFFLINE; recorded Gate OFFLINE
  implementation FROZEN (may not be modified before SENSOR-B3-I14 network
  smoke), repaired the stale `provider_adapter_implementation_authorized =
  KRAKEN_FUTURES ONLY` text, recorded Kraken = frozen, and authorization =
  OKX_SWAP ONLY for the next provider.  DERIBIT = NOT AUTHORIZED YET.
  next_checkpoint_authorized = OKX I07 ONLY.  No Kraken/Gate provider code
  was modified.
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
- SENSOR-B3-I05R1 COMPLETE (BOUNDARY HARDENING) — production/probe instrument
  separation (production `{PI_XBTUSD, PI_ETHUSD}`; probe keeps SOL/DOGE),
  sensor-specific symbol scopes proven by native-evidence grant instruments,
  request provider-identity guard + named-method/sensor identity guards,
  granularity fail-closed (explicit unsupported → typed
  `UnsupportedGranularity`), no-transport failure names the requested sensor,
  SchemaDrift now carries the preserved RawPayloadEnvelope (materialized
  before the parse decision), and list/dict analytics cardinality mismatch is
  BREAKING in both directions.  807 passed / 0 failed; ruff clean; FAKE
  TRANSPORT ONLY — zero network calls; no Bloc 4 code; I14 bounds unchanged.
  Verdict proposed: `PASS_SENSOR_B3_I05R1_KRAKEN_BOUNDARY_HARDENED`.
- SENSOR-B3-I05R2 COMPLETE (FINAL PRODUCTION SEAL, intentionally small) —
  closes the review seams: foreign `FetchRequest` errors now report the
  ACTUAL requested sensor (instrument-list mismatch uses the documented
  neutral provider-level placeholder, never a scientific sensor);
  `fetch_trades`/`fetch_book` check method/sensor identity FIRST so a
  mismatched request is a typed `ProviderSemanticError`, never a false
  "surface unsupported"; Kraken Market Analytics bucket timestamps FAIL
  CLOSED to evidence-backed `list[int]` epoch seconds (string/float/bool/
  None/mixed → SchemaDrift with parsed output blocked, no silent coercion),
  an empty list stays EMPTY_VALID, and the invalid-timestamp SchemaDrift
  preserves the exact raw envelope; resume `since` + non-monotonic now derive
  only from schema-validated int timestamps (silent `int()` rescue removed).
  829 passed / 0 failed; ruff clean; FAKE TRANSPORT ONLY — zero network
  calls; no Bloc 4 code; I14 bounds unchanged.  Verdict proposed: `PASS_SENSOR_B3_I05R2_KRAKEN_SEALED`; Kraken OFFLINE implementation FROZEN
  until SENSOR-B3-I14 network smoke.
- SENSOR-B3-I05R2-RATIFY COMPLETE (governance) — operator ACCEPTED
  PASS_SENSOR_B3_I05R2_KRAKEN_SEALED; Kraken OFFLINE implementation FROZEN
  (may not be modified again before SENSOR-B3-I14 network smoke).  provider
  adapter implementation authorized = GATE_FUTURES ONLY.  current checkpoint =
  SENSOR-B3-I06.  next_provider_authorized = FALSE beyond Gate.
- SENSOR-B3-I06 COMPLETE (OFFLINE) — GATE_FUTURES production adapter build on
  the hardened common foundation.  Exactly four I14-promoted paths (FUNDING /
  LIQUIDATION / OPEN_INTEREST / POSITIONING) ADAPTER_READY, all SECONDARY,
  production symbol scope evidence-derived (BTC_USDT; probe keeps ETH/SOL/DOGE).
  contract_stats native mechanics frozen (from=sec, interval STRING "1h", no
  invented `to`); funding = single-contract GET /funding_rate (from/to=sec,
  rows {r,t}).  Request/response timestamp units kept distinct (contract_stats
  `time` ms, funding `t` sec).  No private /positions, no plural /funding_rates.
  180-day retention -> HistoricalRangeUnavailable.  PRODUCTION_CANDIDATE
  conformance 0 failed; 932 passed / 0 failed; ruff clean; FAKE TRANSPORT ONLY
  — zero network calls; no Bloc 4; no OKX/Deribit production code.  Kraken
  regression green (unchanged, still frozen).  Evidence:
  `evidence/bloc_03/BLOC_03_I06_GATE_IMPLEMENTATION_EVIDENCE.md`.
- STOPS: after I06 the operator reviews `PASS_SENSOR_B3_I06_GATE_ADAPTER_OFFLINE`.
- Recommended next checkpoint: the next production provider MUST be replanned
  against I14.  The old staged plan listed I07 Binance / I08 Bybit / I09 OKX:
  that sequence is superseded — Binance/Bybit/Coinalyze/Bitfinex are NOT current
  Bloc 3 production candidates.  Remaining production candidates are **OKX_SWAP**
  and **DERIBIT**; OKX is the natural next provider, but it is NOT authorized
  (`next_checkpoint_authorized = FALSE`) — stop and await operator review.

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
| SENSOR-B3-I05C | f5295a8e | Kraken fixtures/manifest, README, implementation evidence, readiness matrix, ledger | 762 passed / 0 failed (re-run) | PASS | none |
| SENSOR-B3-I05R | 254716bd | record I05C SHA in ledger + evidence | 762 passed / 0 failed (re-run) | PASS | none |
| SENSOR-B3-I05R1A | 17e70035 | production/probe scope separation + sensor symbol_scope from evidence + grant-instruments proof in conformance + request provider-identity guard + granularity fail-closed + named-method/sensor identity + no-transport sensor identity; tests | 793 passed / 0 failed | PASS | none |
| SENSOR-B3-I05R1B | a1e191ea | AcquisitionError.raw_payload_envelope (provider-independent) + adapter materializes raw envelope before parse decision + SchemaDrift carries it + list/dict cardinality BREAKING both directions + per-sensor drift envelope proofs; tests | 807 passed / 0 failed | PASS | none |
| SENSOR-B3-I05R1C | (this commit) | evidence/README/readiness/ledger reconciliation for I05R1 | 807 passed / 0 failed (re-run) | PASS | none |
| SENSOR-B3-I05R2A | a737d9e6 | foreign-provider error carries requested sensor + neutral instrument-list placeholder + unsupported named-method identity guards + timestamp fail-closed to int epoch seconds + resume/no-int-rescue; tests | 829 passed / 0 failed | PASS | none |
| SENSOR-B3-I05R2C | (this commit) | evidence/README/ledger seal (I05R2 FINAL SEAL) | 829 passed / 0 failed (re-run) | PASS | none |
| SENSOR-B3-I05R2-RATIFY | (governance) | operator freezes Kraken offline implementation and authorizes Gate implementation (ledger only) | 829 passed / 0 failed (re-run) | PASS | none |
| SENSOR-B3-I06A | b30ab5d6 | Gate capability + native acquisition contract (4 paths, SECONDARY, BTC_USDT scope, contract_stats + funding_rate grants), exact-set tests | 844 passed / 0 failed | PASS | none |
| SENSOR-B3-I06B | 4f0ee81b | Gate requests/errors/parsers/adapter + fake transport + request/error/parser/adapter tests incl. PRODUCTION_CANDIDATE conformance | 932 passed / 0 failed | PASS | none |
| SENSOR-B3-I06C | (this commit) | Gate README, implementation evidence, readiness matrix, ledger | 932 passed / 0 failed (re-run) | PASS | none |
| SENSOR-B3-I06-RATIFY | (governance) | operator accepts Gate I06 (PASS_SENSOR_B3_I06_GATE_ADAPTER_OFFLINE), freezes Gate offline implementation, repairs stale provider-authorization ledger text, authorizes OKX I07 only (Deribit NOT AUTHORIZED YET) | 932 passed / 0 failed (re-run) | PASS | none |
| SENSOR-B3-I07A | be075378 | OKX capability + native acquisition contract (3 paths, roles, BTC-USDT-SWAP scope, REST_CURSOR grants, exact-set test) | 949 passed / 0 failed | PASS | none |
| SENSOR-B3-I07B+C | 699a2ede | OKX requests/errors/parsers/adapter + fixtures + tests (funding PUBLIC namespace, trade history-trades, book current-only, ms-string timestamps, raw envelope dry schema drift, typed errors, PRODUCTION_CANDIDATE conformance) | 1038 passed / 0 failed | PASS | none |
| SENSOR-B3-I07C | (this commit) | OKX README, implementation evidence, readiness matrix, ledger | 1038 passed / 0 failed (re-run) | PASS | none |
| SENSOR-B3-I07R1A | ffbdfdfd | OKX window-truth: historical funding/trade never certified complete (is_complete=False, no invented resume, PARTIAL_INTERVAL/GAP_DETECTED flags, requested vs actual boundaries separate; book CURRENT_ONLY unchanged) + window-truth tests | 1067 passed / 0 failed | PASS | none |
| SENSOR-B3-I07R1B | 820feca4 | OKX parser seal: required fields to closed fingerprints (funding 7, trade 7, book 4), exact-int seqId (bool rejected), book level >= [price, size], markPrice additive-only; per-field/seqId/level/markPrice tests | 1067 passed / 0 failed | PASS | none |
| SENSOR-B3-I07R1C | (this commit) | OKX seal evidence (BLOC_03_I07R1_OKX_SEAL_EVIDENCE.md), README completion-truth, I07 evidence corrections, ledger | 1067 passed / 0 failed (re-run) | PASS | none |
| SENSOR-B3-I07R2A | cf269288 | OKX order-invariant overlap: PARTIAL/GAP from ANY validated row timestamp in window (descending/scrambled pages can no longer cause false GAP); invariant violation fails closed; PARTIAL/GAP exclusive; descending + scrambled + true-gap + funding regression tests | 1074 passed / 0 failed | PASS | none |
| SENSOR-B3-I07R2B | (this commit) | OKX microseal evidence (BLOC_03_I07R2_OKX_MICROSEAL_EVIDENCE.md), ledger | 1074 passed / 0 failed (re-run) | PASS | none |
| SENSOR-B3-I07R2-RATIFY | (governance) | operator accepts PASS_SENSOR_B3_I07R2_OKX_SEALED, freezes OKX offline implementation, authorizes Deribit I08 only (no adapter matrix / network smoke / other providers / Bloc 4) | 1074 passed / 0 failed (re-run) | PASS | none |
| SENSOR-B3-I08A | f6acec7e | Deribit capability + native acquisition contract (4 paths, roles, BTC-PERPETUAL scope, REST_RANGE/TIME_RANGE grants, exact-set tests) | 1094 passed / 0 failed | PASS | none |
| SENSOR-B3-I08B+C | 82e23c52 | Deribit requests/errors/parsers/adapter + fixtures + tests (trade/liq shared surface, funding raw-list envelope, book current-only, epoch-ms INT timestamps, liquidation microscope filter, typed JSON-RPC errors, completion truth, PRODUCTION_CANDIDATE conformance) | 1242 passed / 0 failed | PASS | none |
| SENSOR-B3-I08R1A | 3b6f8c39 | parsers coverage seam (ParsedDeribit.coverage_timestamps = full source-page validated timestamps) + adapter completion block (COMPLETE never PARTIAL; funding completion_proof LIMITED; liquidation completion from source coverage; trade/liq terminal = has_more=false) | 1242 passed / 0 failed | PASS | none |
| SENSOR-B3-I08R1B | d44831c7 | quality-matrix A-G tests (complete trade/liq clean, partial/gap exclusive, liquidation filter trap, no ordinary leakage, empty liquidation conservative), funding never-complete under-cap + count-cap tests, LIQ_TRAP fixture | 1252 passed / 0 failed | PASS | none |
| SENSOR-B3-I08R1-RATIFY | 889d5f6c | governance: operator accepts PASS_SENSOR_B3_I08R1_DERIBIT_SEALED; all four providers OFFLINE_FROZEN; authorizes SENSOR-B3-I09 only | 1252 passed / 0 failed | PASS | none |
| SENSOR-B3-I09A | dffe18f6 | production adapter registry + deterministic inventory generator (readiness.py): AdapterReadinessRecord, exact-set/collision audits, symbol/evidence/role audits, resume LIMITED preservation, deterministic CSV/JSON | 1252 passed / 0 failed | PASS | none |
| SENSOR-B3-I09A-fix | 97450123 | type-cast evidence_basis iteration in readiness.py (mypy clean) | 1294 passed / 0 failed | PASS | none |
| SENSOR-B3-I09B | d299cdd2 | cross-provider closure tests (42): registry topology, 17-path exact-set equality, evidence-ref resolution, symbol scope, bound-drift, semantic firewall, determinism, human-matrix reconcile, real-adapter protocol coherence | 1294 passed / 0 failed | PASS | none |
| SENSOR-B3-I09C | 08559207 | generate canonical PRODUCTION_ADAPTER_MATRIX.csv/.json (17 rows) + reconcile human readiness matrix | 1294 passed / 0 failed (re-run) | PASS | none |
| SENSOR-B3-I09D | 4d4c62a4 | closure evidence + ledger reconciliation for I09 | 1294 passed / 0 failed (re-run) | PASS | none |
| SENSOR-B3-I09R1A | b3e26cef | fail closed on duplicate I14 promotion + duplicate human readiness rows; require explicit complete verification coverage (missing != explicit False; ADAPTER_READY cannot coexist with failed validation; network smoke locked NOT_RUN pre-I10) | 1294 passed / 0 failed | PASS | none |
| SENSOR-B3-I09R1B | 17636a78 | authority-seal adversarial tests (15): duplicate I14 exact + conflicting, every-consumer reject, human duplicate identical + conflicting, missing conformance/schema/verification, explicit-False-vs-missing, ADAPTER_READY+failed-flag rejected, network upgrade rejected, raw/unique I14 counts | 1309 passed / 0 failed | PASS | none |
| SENSOR-B3-I09R1C | 1dd03835 | authority-seal evidence + ledger reconciliation for I09R1; matrix regeneration byte-identical | 1309 passed / 0 failed (re-run) | PASS | none |
| SENSOR-B3-I09R1-RATIFY | (this commit) | governance: operator ACCEPTS PASS_SENSOR_B3_I09R1_CROSS_PROVIDER_OFFLINE_CLOSURE_SEALED; all four adapters stay OFFLINE_FROZEN with network_smoke_status NOT_RUN; authorizes SENSOR-B3-I10 controlled production-adapter network smoke ONLY (no repairs / schema changes / history expansion / new providers / Bloc 4 / MECH21 / LF14 / capital / alpha) | 1309 passed / 0 failed (re-run) | PASS | none |
| SENSOR-B3-I10A | f92d6bd9 | fail-closed network-smoke harness (network_smoke.py): opt-in env gate SENSOR_NETWORK_SMOKE=1 + @pytest.mark.sensor_network_smoke, 17-logical/18-physical target derivation from canonical matrix, HTTPS-only allowlist, GET-only, no credential headers, <=15s timeout, 2 MiB cap, zero retries, frozen+hashed manifest, sanitized artifacts; 29 offline tests | 1338 passed / 0 failed (1 skipped live) | PASS | none |
| SENSOR-B3-I10B | c4bc5c3e | execute bounded live smoke (SENSOR_NETWORK_SMOKE=1): 18/18 requests once, 0 retries; 17 LIVE_PASS (16 nonempty + 1 empty-valid), 1 SCHEMA_ADDITIVE_REVIEW (KRAKEN funding PI_XBTUSD); immutable plan+results JSON | 1338 passed / 0 failed (post-run) | HOLD | additive funding drift — human review |
| SENSOR-B3-I10C | (this commit) | reconcile I10 smoke evidence (EVIDENCE.md), ledger; harness records endpoint/version/evidence-ref per request (I10 §27) + LF-deterministic artifacts | 1338 passed / 0 failed (re-run) | HOLD | HOLD_SENSOR_B3_I10_SCHEMA_ADDITIVE_REVIEW |
| SENSOR-B3-I10-REVIEW | b51c3883 | operator governance-only review: bounded I10 execution accepted as valid evidence; 1970 Gate contract_stats timestamps (3 paths) + Kraken funding null timestamps/additive override the narrow original diagnosis -> BLOCK_SENSOR_B3_I10_MIXED; authorizes I10R1 ONLY | — | BLOCK | BLOCK_SENSOR_B3_I10_MIXED |
| SENSOR-B3-I10R1A | 37542be5 | sanitized structural adjudication: Gate contract_stats live `time` = 10-digit epoch SECONDS (2022-era fixture was ms) -> PRIOR_CHARACTERIZATION_ERROR; Kraken funding `result.timestamp` list[int] len 24, metric set EXACTLY {rate, relativeRate} -> B_FUNDING_SPECIFIC_EPOCH_MILLISECONDS | — (evidence only; 2 characterization calls) | PASS | none |
| SENSOR-B3-I10R1B | c773aaac | repair Gate contract_stats `time` semantics to epoch seconds (native integer preserved; no magnitude heuristic; adversarial unit tests for all 3 affected sensors); probe pagination: contract_stats seconds, /trades ms like-for-like | gate suite 104 passed / 0 failed | PASS | none |
| SENSOR-B3-I10R1C | fb8c4d48 | repair Kraken funding timestamp unit (sensor-specific epoch ms; other analytics paths stay seconds) + funding known metric set {rate, relativeRate}; genuinely-new metric keys remain SCHEMA_ADDITIVE (never promoted to semantics) | kraken suite 134 passed / 0 failed | PASS | none |
| SENSOR-B3-I10R1D | 6081b88a | fail-closed smoke temporal-plausibility guard (TEMPORAL_SEMANTIC_REVIEW: nonempty historical batches need both convenience timestamps inside a 365-day envelope; 1970 cannot LIVE_PASS; CURRENT_ONLY books exempt; truthful LIMITED stays PARTIAL) + native integer timestamp sample capture + adversarial tests | 1353 passed / 0 failed (1 skipped live) | PASS | none |
| SENSOR-B3-I10R1E | e6b67d37 | execute 4-path targeted live recheck (i10r1-recheck, manifest e77646fd4c5202e4): Gate liquidation/OI/positioning BTC_USDT + Kraken funding PI_XBTUSD = 4/4 LIVE_PASS_NONEMPTY, KNOWN_SCHEMA, 2026 timestamps, 0 retries; freeze plan + results + evidence; list-typed native timestamp sample capture | 1354 passed / 0 failed (post-run) | PASS | none |
| SENSOR-B3-I10R1F | (this commit) | reconcile ledger: I10R1 COMPLETE; combined I10 verdict PASS_SENSOR_B3_I10_PRODUCTION_ADAPTER_NETWORK_SMOKE via immutable I10 baseline + I10R1 overlay; next_checkpoint_authorized = FALSE | — | PASS | none |
| SENSOR-B3-I10R2A | da4123b2 | reconcile Gate historical-unit adjudication: I10R1A provisional B_PROVIDER_SEMANTIC_DRIFT SUPERSEDED -> final A_PRIOR_CHARACTERIZATION_ERROR_WITH_UNIDENTIFIED_HISTORICAL_UNIT (only ms evidence = synthetic fixture; real historical unit UNIDENTIFIED; provider drift NOT established); BLOC_03_I10R2_SEMANTIC_RECONCILIATION.json + current docs canonicalized | — (evidence) | PASS | none |
| SENSOR-B3-I10R2B | d7c49225 | seal Gate runtime completion semantics against LIMITED readiness: is_complete always False, no resume token, PARTIAL_INTERVAL/GAP_DETECTED/EMPTY_VALID; tests for overlap/out-of-window/empty/funding/no-invented-token | gate suite 109 passed / 0 failed | PASS | none |
| SENSOR-B3-I10R2C | cb3bff61 | version repaired contracts gate-adapter-v2 / kraken-adapter-v2 (OKX/Deribit untouched); Kraken additive firewall (_build_dict_rows projects only required metrics; unknown additive preserved raw, never projected); relativeRate reconciled to REQUIRED (KNOWN_OPTIONAL superseded); missing-relativeRate BREAKING test | 1360 passed / 0 failed (pre-run; 1 skipped live) | PASS | none |
| SENSOR-B3-I10R2D | 6fc1551d | execute 5-path targeted live recheck (i10r2-recheck, manifest ddb4dccdcdd4429b): Gate funding/liquidation/OI/positioning BTC_USDT + Kraken funding PI_XBTUSD = 5/5 LIVE_PASS_NONEMPTY, KNOWN_SCHEMA, v2 adapters, Gate LIMITED (is_complete=False, PARTIAL_INTERVAL), Kraken funding literal ms sample [1788170400000..1788253200000]; freeze plan + results + BLOC_03_CURRENT_RUNTIME_ADAPTER_OVERLAY.json | 1360 passed / 0 failed (post-run) | PASS | none |
| SENSOR-B3-I10R2E | 55eb5a2d | final evidence / ledger reconciliation: BLOC_03_I10R2_SEMANTIC_SEAL_EVIDENCE.md + ledger (Current state, operator review, network-validation rows, test counts 1360 cumulative, Next checkpoint entry, commit log) | 1360 passed / 0 failed (re-run) | PASS | none |
| SENSOR-B3-I10R2-RATIFY | 8478eeb5 | governance: operator ACCEPTS PASS_SENSOR_B3_I10R2_SEMANTIC_CONSISTENCY_SEALED and PASS_SENSOR_B3_I10_PRODUCTION_ADAPTER_NETWORK_SMOKE (17/17 logical, 18/18 physical; kraken-adapter-v2 / gate-adapter-v2 / okx-adapter-v1 / deribit-adapter-v1); authorizes SENSOR-B3-I11 FINAL BLOC 3 VALIDATION + HANDOFF ONLY (no Bloc 4 implementation) | 1360 passed / 0 failed (re-run) | PASS | none |
| SENSOR-B3-I11A | 61821aac | final audit machinery: deterministic handoff generator (exact-set 17, provider/role/sensor counts, evidence-ref audit, docs audit, AST fixture coverage); Deribit README docs-audit fix (Known Issues + current live-validated truth) | 1360 passed / 0 failed | PASS | none |
| SENSOR-B3-I11A-fix | 583a777a | generator mypy/ruff hygiene (no artifact changes; regeneration byte-identical) | 1360 passed / 0 failed | PASS | none |
| SENSOR-B3-I11B | 9651479f | generate final runtime artifacts: BLOC_03_CURRENT_RUNTIME_ADAPTER_OVERLAY.json v2 (path-specific completion), PROVIDER_CAPABILITY_RUNTIME.json, FINAL_ADAPTER_READINESS_MATRIX.csv/.json (joined baseline+overlay), FIXTURE_COVERAGE_REPORT.json (17/17 paths) | 1360 passed / 0 failed | PASS | none |
| SENSOR-B3-I11C | 8ee37b3d | implementation report, known failures, access class report, offline test report | 1360 passed / 0 failed | PASS | none |
| SENSOR-B3-I11D | 8f5f18ad | Bloc 4 input manifest + handoff index + network evidence index + handoff integrity tests (7) | 1367 passed / 0 failed | PASS | none |
| SENSOR-B3-I11E | (this commit) | final evidence / ledger / freeze reconciliation: BLOC_03_IMPLEMENTATION_COMPLETE=TRUE, BLOC_03_FROZEN=TRUE; proposed PASS_BLOC_03_IMPLEMENTATION; next_checkpoint_authorized=FALSE; recommended next SENSOR-B4-I01 (NOT begun) | 1367 passed / 0 failed (re-run) | PASS | none |

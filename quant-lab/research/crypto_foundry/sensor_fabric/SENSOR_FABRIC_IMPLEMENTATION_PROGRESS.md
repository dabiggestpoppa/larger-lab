# SENSOR FABRIC — IMPLEMENTATION PROGRESS LEDGER

Human-readable execution ledger for the Crypto Mechanical Sensor Fabric build.
This ledger is NOT a substitute for Git history; it is an operator-facing summary
that is updated at every staged checkpoint.

---

## Current state

| Field | Value |
|---|---|
| Current Bloc | 4 — IMMUTABLE T0 RAW EVIDENCE LAKE |
| Current checkpoint | SENSOR-B4-I11R2-RATIFY: operator acceptance of the complete PostgreSQL operational metadata chain. The operator reviewed and ACCEPTED I11 -> I11R1 -> I11R2A -> I11R2B -> I11R2C at ratified head fa6df668ca3351eb910b0450d1151c67482b2b24, having confirmed: the commit chain is append-only and linear with zero merge commits and no rebase, reset, amend, squash or force push; the G4-10 contract holds in committed code (schema crypto_sensor_fabric_ops, repository role operational_metadata_non_raw, forbidden raw and secret columns and secret-shaped values refused, resume tokens absent, PostgreSQL authoritative for no prior subsystem); the real PostgreSQL 16.15 evidence records the 18-row 9-table populated reconstruction, exact schema, drop/reinstall/rebuild parity, idempotence, failed-refresh rollback, concurrent-refresh serialisation, the I07/I08/I09 tamper firewalls, preserved operational state and unchanged T0 evidence; both historical governance tests are bound to immutable evidence rather than the mutable dashboard; and production diff is ZERO with historical evidence diff ZERO. This checkpoint is GOVERNANCE ONLY: no production source, no historical evidence artifact, no provider code, no DuckDB I10 code, no frozen Bloc-4 plan and no main branch change. external_ci = NONE_OBSERVED. next_checkpoint_authorized=TRUE for SENSOR-B4-I12 RAW EVIDENCE QUERY / REPLAY API, authorized_scope = I12 ONLY; I13+ unauthorized; research frozen. I12 is AUTHORIZED but NOT STARTED. |
| Bloc 2 verdict | PASS_BLOC_02_WITH_SENSOR_GAPS (co-earned PASS_BLOC_02_FREE_ONLY_REDUNDANCY) — IMPLEMENTATION COMPLETE, OPERATOR RATIFIED (SENSOR-B2-RATIFY) |
| Bloc 1 verdict | PASS_BLOC_01_CONTRACTS_FROZEN — operator_ratified = TRUE (see evidence/bloc_01/BLOC_01_DECISION.md) |
| Operator review state | I11 chain OPERATOR_ACCEPTED by the operator at ratified head fa6df668ca3351eb910b0450d1151c67482b2b24. PASS_SENSOR_B4_I11_POSTGRES_OPERATIONAL_METADATA_SEALED=OPERATOR_ACCEPTED; PASS_SENSOR_B4_I11R1_RUNTIME_CORRECTNESS_SEALED=OPERATOR_ACCEPTED; PASS_SENSOR_B4_I11R2_GOVERNANCE_REGRESSION_SEALED=OPERATOR_ACCEPTED; G4-10_OPERATIONAL_METADATA_GATE=IMPLEMENTATION_PASS; next_checkpoint_authorized=TRUE; next_checkpoint=SENSOR-B4-I12 RAW EVIDENCE QUERY / REPLAY API; authorized_scope=I12 ONLY; I13+ unauthorized; research frozen. recommended_next=SENSOR-B4-I12 IMPLEMENTATION. This ratification is operator authority, not self-ratification: no checkpoint in the I11 chain ever ratified itself. The ratification record is the append-only BLOC_04_I11_CHAIN_OPERATOR_RATIFICATION.md. |
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
| next_checkpoint_authorized | TRUE - the operator accepted the complete I11 -> I11R1 -> I11R2 chain at ratified head fa6df668ca3351eb910b0450d1151c67482b2b24 and G4-10 is IMPLEMENTATION_PASS. next_checkpoint=SENSOR-B4-I12 RAW EVIDENCE QUERY / REPLAY API; authorized_scope=I12 ONLY; I13+ unauthorized; research remains frozen. I12 is AUTHORIZED but NOT STARTED as of this commit. |

## Append-only SENSOR-B4-I10R1 / I10R2 checkpoint history

- **SENSOR-B4-I10R1** — append-only implementation chain `343873a1` → `08edabea` → `ac1c6db6` → `9dfbf85f` → `51e23b10`. R1 repaired schema inference and strict row shape, metadata-only T0A discovery cost, storage-usage dimensions, recovery gross-malformed refusal, wholly orphaned lineage, and measured rather than static evidence builders. The checkpoint remains `OPERATOR_HOLD`; no self-ratification occurred.
- **SENSOR-B4-I10R2** — append-only relation-governance parity repair. Projection discovery now reuses the frozen typed lineage models and ordering/bounds/artifact-list helpers against the already-loaded blob and acquisition metadata truth, with no T0A payload verify/decode path. Recovery discovery validates the complete durable `RecoveryJournal` envelope before projecting the narrow quarantine view. R2 evidence measures actual DuckDB counts for all eight views and preserves historical I10/I10R1 evidence byte-for-byte. Current verdict is `PENDING_OPERATOR_REVIEW`; I11 and I12+ remain unauthorized; research remains frozen.
- **SENSOR-B4-I10R2-RATIFY** — operator accepted the complete I10 -> I10R1 -> I10R2 chain and accepted G4-09 as `IMPLEMENTATION_PASS`. I11 PostgreSQL operational metadata repository work is authorized but was not started; I12+ remain unauthorized and research remains frozen.

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
| SENSOR-B3-I11R1D | 34a8130a | 0 (seal evidence/ledger) | — |
| SENSOR-B3-I11R1-RATIFY | 049baf52 | 0 (governance) | — |
| SENSOR-B4-I01A | (this commit) | 18 (storage enums) | 0 |
| SENSOR-B4-I01B | (next commit) | 48 (storage models validation) | 0 |
| SENSOR-B4-I01C | (next commit) | 12 (deterministic serialization + Bloc 3 handoff) | 0 |
| SENSOR-B4-I01D | 6d0f23d9 | 0 (evidence/ledger) | — |
| SENSOR-B4-I01R1A | (this commit) | (semver + lineage contract seal; full-suite cumulative first at I01R1C) | — |
| SENSOR-B4-I01R1B | (next commit) | 37 (date-basis/hash-ref/timestamp adversarial tests) | 0 |
| SENSOR-B4-I01R1C | (next commit) | 0 (seal evidence/ledger) | — |
| SENSOR-B4-I02A | (this commit) | 0 (checksums primitives + ChecksumAlgorithm + models shared-rule refactor) | — |
| SENSOR-B4-I02B | (next commit) | 0 (paths/object-key derivation + public exports) | — |
| SENSOR-B4-I02C | (next commit) | 122 (storage tests: test_checksums 35 + test_paths 87; storage 115 -> 237) | 0 |
| SENSOR-B4-I02D | (next commit) | 0 (evidence/ledger) | — |
| SENSOR-B4-I02E | d11895bd | 0 (ruff hygiene: DTZ001 noqa on intentional naive-datetime tests) | — |
| SENSOR-B4-I02F | 7b6926c3 | 0 (empty CI re-trigger) | — |
| SENSOR-B4-I02R1A | 8fbe5500 | 35 (canonical decoding + bijection both directions) | 0 |
| SENSOR-B4-I02R1B | 94922be3 | 0 (full-SHA projection key; collision + full-hash tests folded into R1A batch) | 0 |
| SENSOR-B4-I02R1C | d7a4f6c6 | 0 (canonical-path seal evidence) | — |
| cumulative | 1638 | 1638 | 0 |
| SENSOR-B4-I03A | fa95b771 | 56 (compression 34 + atomic 22; storage 259 → 315) | 0 |
| SENSOR-B4-I03B | fa41aa43 | 51 (blob store core; storage 315 → 366) | 0 |
| SENSOR-B4-I03C | 95b21b26 | 24 (adversarial seal; storage 366 → 390; full-suite cumulative 1768 passed / 0 failed / 2 skipped) | 0 |
| cumulative | 1768 | 1768 | 0 (2 env-skips: live smoke + POSIX-only permission on Windows) |
| SENSOR-B4-I03R1A | d19e9d13 | 9 (reuse-durability seal: 5 adversarial + 4 reuse-order contract; storage 390 → 399) | 0 |
| SENSOR-B4-I03R1B | 9225acb6 | 21 (durable directory chain + fail-closed NAME_MAX probe + nonce validation; storage 399 → 420, +1 POSIX-only probe skip on Windows) | 0 |
| SENSOR-B4-I03R1C | 9363143e | 6 (namespace/crash/race supplemental matrix + machine evidence; storage 420 → 426) | 0 |
| cumulative | 1806 | 1803 | 0 (3 env-skips: live smoke + 2 POSIX-only probe tests on Windows; full collect 1806) |
| SENSOR-B4-I04A | a8a56c04 | 6 (AcquisitionRecord handoff-preservation tests; storage 426 → 432) | 0 |
| SENSOR-B4-I04B | 0a160108 | 0 (immutable blob + acquisition Parquet catalog repository) | — |
| SENSOR-B4-I04C | 06e1b80d | 0 (append-only partition manifests + transactional current pointer + locks/CAS) | — |
| SENSOR-B4-I04D | c4bfb33f | 58 (catalog 25 + manifests 27 + concurrency 4 + machine evidence 2; storage 432 → 490) | 0 |
| cumulative | 1870 | 1867 | 0 (3 env-skips: live smoke + 2 POSIX-only probe tests on Windows; full collect 1870) |
| SENSOR-B4-I04R1A | efde5fea | 9 (acquisition provenance gate; storage 490 → 499) | 0 |
| SENSOR-B4-I04R1B | df0d28ca | 11 (H3 recomputation + provider-integrity claims; storage 499 → 510) | 0 |
| SENSOR-B4-I04R1C | 0a112ccf | 10 (blobless outcomes + non-secret metadata; storage 510 → 520) | 0 |
| SENSOR-B4-I04R1D | cdef2ab3 | 13 (closed pointer schema + partition/ancestry binding; storage 520 → 534) | 0 |
| SENSOR-B4-I04R1E | (this commit) | 2 (deterministic machine evidence: PROVENANCE_MATRIX + POINTER_SCHEMA; storage 534 → 536) | 0 |
| cumulative | 1916 | 1913 | 0 (3 env-skips: live smoke + 2 POSIX-only probe tests on Windows; full collect 1916) |

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

- SENSOR-B4-I07R1F (this commit) — FINAL MICROSEAL of the I07 job/resume ledger. Two remaining
transport/truth seams closed: (A) an already-committed checkpoint is retried and re-proved under the
floor PERSISTED IN ITS OWN PROOF (constructor configuration governs NEW checkpoints only, so a
restart with a different `min_durable_status` can no longer reject or reinterpret durable history);
(B) the shared `DurableJsonCatalog` cache is internally synchronized by one REENTRANT lock, so
concurrent per-job writers can never race `refresh`/`commit` into a false vanished-record corruption.
Also reconciles the operator-facing top-level ledger, which still named I06R1-RATIFY as current truth.
Proposed: `PASS_SENSOR_B4_I07R1F_PERSISTED_FLOOR_CATALOG_CONCURRENCY_LEDGER_SEALED`, then operator may
accept `PASS_SENSOR_B4_I07R1_GATE_IDENTITY_REPLAY_SEALED` and
`PASS_SENSOR_B4_I07_DURABLE_JOB_STATE_RESUME_SEALED`. `DURABLE_RESUME_IMPLEMENTED = PENDING_OPERATOR_ACCEPTANCE`;
`next_checkpoint_authorized = FALSE`. I08 (RECOVERY / QUARANTINE) NOT authorized, NOT started.

- SENSOR-B4-I06R1-RATIFY — operator accepts I06R1 + I06 (G4-04_REVISION_GATE =
  IMPLEMENTATION_PASS); ledger current state reconciled: stale top-level I04/I05 current-state text
  replaced with the I07-authorized truth; agent/crypto-sensor-fabric-build fast-forwarded to main
  d09941e7 (no content change, no force); historical checkpoint entries/evidence untouched.
  AUTHORIZED: SENSOR-B4-I07 DURABLE JOB STATE + RESUME COUPLING ONLY — I08+ NOT authorized, NOT started.

- SENSOR-B4-I04R2 COMPLETE — USABLE-ACQUISITION PROVENANCE + STREAMING H3 SEAL (proposed
  `PASS_SENSOR_B4_I04R2_USABLE_PROVENANCE_SEALED`; then proposed `PASS_SENSOR_B4_I04R1_PROVENANCE_INTEGRITY_SEALED`
  then proposed `PASS_SENSOR_B4_I04_ACQUISITION_MANIFEST_REPOSITORY`).  Operator review found ONE remaining
  provenance contradiction: durable failed-acquisition history could satisfy a LOCAL_HASH_VERIFIED manifest
  provenance gate because find_matching_acquisitions() did not distinguish durable acquisition history from
  usable manifest provenance.  I04R2A-D added 48 tests; deterministic machine evidence
  BLOC_04_I04R2_USABLE_PROVENANCE_MATRIX.json (byte-stable).  Storage 582 nodes (+48); full suite 1961 passed /
  0 failed / 3 skipped; network 0; provider code unchanged; T0A_EVIDENCE_PIPELINE_COMPLETE=TRUE;
  BLOC3_T0A_INTEGRATION_COMPLETE=FALSE (I14); no T0B / DuckDB / PostgreSQL / SourceRevision / active resume /
  provider integration.  I05 NOT started.

- SENSOR-B4-I04R1 COMPLETE — ACQUISITION-PROVENANCE + H3-INTEGRITY +
  POINTER-TRUTH SEAL (proposed
  `PASS_SENSOR_B4_I04R1_PROVENANCE_INTEGRITY_SEALED`, then proposed
  operator acceptance `PASS_SENSOR_B4_I04_ACQUISITION_MANIFEST_REPOSITORY`).
  The operator hold `HOLD_PASS_SENSOR_B4_I04_ACQUISITION_MANIFEST_REPOSITORY_PENDING_I04R1_PROVENANCE_INTEGRITY_SEAL`
  closed four truth seams: A) acquisition-before-manifest provenance (every
  non-empty blob_ref needs >=1 durable matching acquisition; byte identity
  never transfers provider/sensor identity); B) H3 recomputation over the
  exact decoded source bytes (verified=True earned, never caller-trusted;
  fake claims and unearned PROVIDER_HASH_VERIFIED metadata/manifests fail
  typed); C) closed blobless failure evidence ("OK"/"SUCCESS" never
  masquerade) + a narrow non-secret acquisition metadata boundary (reject,
  never redact; keys not values in error text); D) closed strictly-typed
  current-pointer JSON (schema_version=1), partition-key read binding and
  pointer-ancestry binding.  Historical I04 evidence untouched; I04R1
  supersedes the affected claims chronologically.  I04R1A-D added 46 tests;
  deterministic machine evidence BLOC_04_I04R1_PROVENANCE_MATRIX.json +
  BLOC_04_I04R1_POINTER_SCHEMA.json (byte-stable).  Storage 536 nodes
  (+46); full suite 1913 passed / 0 failed / 3 skipped; network 0; provider
  code unchanged; T0A_EVIDENCE_PIPELINE_COMPLETE=TRUE;
  BLOC3_T0A_INTEGRATION_COMPLETE=FALSE (I14); no T0B / DuckDB / PostgreSQL /
  SourceRevision / active resume / provider integration.  I05 NOT started.
- SENSOR-B4-I04 COMPLETE — ACQUISITION + MANIFEST REPOSITORY (proposed
  `PASS_SENSOR_B4_I04_ACQUISITION_MANIFEST_REPOSITORY`).  The durable local
  metadata/catalog layer over the accepted T0A bytes: I04A reconciled the
  AcquisitionRecord persistence schema with the frozen Bloc-3 handoff (no
  raw acquisition context lost — adapter version, endpoint host/path +
  request family, requested vs actual range kept separate, schema state,
  evidence ref, provider checksum triple, retrieval/observation/ingestion
  timestamps distinct; no secrets).  I04B: append-only EvidenceBlob
  metadata + AcquisitionRecord immutable Parquet catalog fragments with
  stable explicit Arrow schemas and the I03R1 durability doctrine
  (stage/flush/fsync/verify/no-clobber publish/parent fsync); blob metadata
  requires a present + verified physical blob; empty body is valid
  zero-byte evidence; repeated acquisitions may share a blob; conflicting
  immutable metadata fails typed.  I04C: append-only PartitionManifest
  complete-snapshot versions (v1/vN rules, supersedes-current, no gaps,
  projection_refs fail-closed pre-I05, referentially verified blob_refs,
  integrity never exceeds referenced evidence, coverage separate from
  integrity) + partition-scoped atomic-mkdir lock + expected-current CAS
  (stale writers fail, never auto-rebase; no stale-lock auto-delete) +
  transactional current pointer (old-or-new, P1-P5 crash matrix, orphan
  fragments never auto-deleted, retry re-establishes pointer durability
  before success).  I04D sealed with 58 tests including the 8-writer
  same-base race (exactly one current v2) and the pointer crash matrix;
  deterministic machine evidence BLOC_04_I04_CATALOG_SCHEMAS.json +
  BLOC_04_I04_MANIFEST_CONCURRENCY.json (byte-stable).  Storage 490 nodes
  (+64); full suite 1867 passed / 0 failed / 3 skipped; network 0; provider
  code unchanged; T0A_EVIDENCE_PIPELINE_COMPLETE=TRUE (storage-layer
  pipeline); BLOC3_T0A_INTEGRATION_COMPLETE=FALSE (I14); no T0B /
  DuckDB / PostgreSQL / SourceRevision / active resume / provider
  integration.  I05 NOT started.
- SENSOR-B4-I03R1 COMPLETE — DURABILITY NAMESPACE SEAL (proposed
  `PASS_SENSOR_B4_I03R1_DURABILITY_NAMESPACE_SEALED`, then proposed operator
  acceptance `PASS_SENSOR_B4_I03_ATOMIC_FILESYSTEM_BACKEND`).  Operator
  review HOLD found three NARROW durability seams on the accepted I03
  architecture; all sealed without redesign:
  (A) ORPHAN RETRY — every REUSED_EXISTING path (ordinary dedupe,
  publish-race loser, retry after crash-E orphan, retry after crash-F) now
  re-establishes CURRENT parent-directory durability BEFORE success, frozen
  as EXISTING_FINAL_VERIFY < PARENT_DIR_FSYNC < STAGING_CLEANUP <
  SUCCESS_RETURN via is_canonical_reuse_order(); a crash-E orphan that
  verifies byte-perfectly is no longer silently promoted to durable success;
  (B) DIRECTORY CHAIN — new ensure_durable_directory_chain() /
  ensure_durable_directory() in atomic.py create each missing namespace
  component with DIR_CREATE < DIR_FSYNC < PARENT_NAMESPACE_FSYNC from the
  deepest existing ancestor BEFORE any final link; blind os.makedirs() is
  gone from the commit path; concurrent mkdir races tolerated
  (confirm-and-continue); existing file/symlink components FAIL CLOSED
  (never removed/replaced); staging namespace created under the same
  contract; root policy explicit: configured root must pre-exist as a
  directory (InvalidStorageRoot otherwise); final publication remains
  no-clobber os.link with post-link final-parent fsync — both concerns
  separately tagged (FINAL_LINK / FINAL_PARENT_FSYNC);
  (C) TRUE COMPONENT LIMIT — default_name_max() probes PC_NAME_MAX only on
  an EXISTING directory; a nonexistent target or failing probe raises
  DurabilityUnsupported instead of silently assuming 255 (Windows 255
  recorded as explicit platform policy, not dynamic proof); the store probes
  from the deepest existing ancestor and validates the generated staging
  <nonce>.partial component BEFORE open — typed ComponentTooLong; no
  truncation/normalization/native-id hashing anywhere.  Historical I03
  evidence untouched: the crash-matrix generator now regenerates rows in
  memory and asserts byte-equality with the frozen
  BLOC_04_I03_CRASH_MATRIX.json; the atomic-order generator seals the
  supplemental BLOC_04_I03R1_ATOMIC_ORDER.json instead.  Machine evidence:
  BLOC_04_I03R1_NAMESPACE_DURABILITY.json (fresh_namespace_commit /
  reuse_existing / retry_after_crash_E / retry_after_crash_F /
  publish_race_loser).  No recovery scanner, no acquisition records, no
  manifests, no resume, no T0B (I08 owns recovery; I04 owns metadata).
  Storage tests 426 nodes (+36); full suite 1803 passed / 0 failed / 3
  skipped (floor >=1768); ruff clean; changed-scope mypy clean; network 0;
  provider code UNCHANGED.  Flags: ATOMIC_FILESYSTEM_BACKEND_READY=TRUE,
  T0A_BLOB_BACKEND_IMPLEMENTED=TRUE, T0A_EVIDENCE_PIPELINE_COMPLETE=FALSE,
  MANIFEST_REPOSITORY_IMPLEMENTED=FALSE, T0B_STORAGE_IMPLEMENTED=FALSE.
  Evidence:
  `evidence/bloc_04/BLOC_04_I03R1_DURABILITY_NAMESPACE_SEAL_EVIDENCE.md`.
- SENSOR-B4-I03 COMPLETE — ATOMIC FILESYSTEM BACKEND (proposed
  `PASS_SENSOR_B4_I03_ATOMIC_FILESYSTEM_BACKEND`).  New storage modules
  `compression.py` (streaming NONE/ZSTD wrapper: `encode_source_stream` +
  `iter_decode_stored`; H1 = exact-source SHA-256 BEFORE wrapper compression,
  H2 = stored-object SHA-256, H1==H2 only for NONE; bounded reads,
  non-seekable sources, caller stream ownership preserved, no full-object
  materialization; zstandard>=0.23.0 per dependency policy — no
  gzip/bz2/lzma substitute), `atomic.py` (generic no-clobber durability
  primitives reusable by I05: component-length guard via PC_NAME_MAX / NTFS
  255 failing closed typed ComponentTooLong BEFORE any artifact write —
  closes I02R1's LONG_COMPONENT_CHECK_REQUIRED_IN_I03; st_dev
  same-filesystem enforcement, cross-device denied with NO copy+delete
  fallback; os.link-based publish_no_replace — final name appears only for
  a fully-fsynced inode, existing final never overwritten;
  platform-truthful directory fsync (POSIX O_RDONLY fsync / Windows
  FILE_FLAG_BACKUP_SEMANTICS + FlushFileBuffers) or typed
  DurabilityUnsupported; deterministic FaultPoint hooks A-F + ListOpRecorder
  canonical seven-operation durable-order contract) and `blob_store.py`
  (LocalBlobStore on an EXPLICIT configurable root — runtime configuration,
  never evidence identity, storage_uri = backend-neutral object key;
  commit sequence THROUGH step 6: staging under
  staging/<escaped job_id>/<nonce>.partial O_EXCL 0o600 → streaming write →
  flush → fsync(fd while open) → staged verification (re-opened: stored H2,
  decoded H1, length, optional explicit-algorithm H3 against decoded source
  bytes; mismatch refuses the commit with staged evidence preserved) →
  no-clobber publication → parent-directory fsync → success; steps 7-8 NOT
  here).  Public API: put/put_bytes/blob_exists (presence only)/open_blob
  (decoded source stream; missing = typed BlobMissing, distinct from
  empty)/verify_blob (recomputed H1 vs content identity; corruption =
  QUARANTINED_INTEGRITY_FAILURE, no repair; recovery = I08);
  BlobPutResult disposition COMMITTED_NEW | REUSED_EXISTING (disposition !=
  integrity state); EvidenceBlob LOCAL_HASH_VERIFIED only, created_at via
  injected clock (metadata, never identity); NO public overwrite operation —
  committed T0A is immutable.  Duplicate put idempotent (final mtime/content
  untouched); 8-thread same-hash race → exactly one COMMITTED_NEW / one
  final / all verify; corrupt existing final = ExistingBlobIntegrityConflict,
  never overwritten/deleted/repaired.  Crash matrix A-F test-frozen +
  generated BLOC_04_I03_CRASH_MATRIX.json (UNCOMMITTED_STAGING x4 /
  ORPHAN_DURABLE_BLOB / DURABLE_COMMITTED) + BLOC_04_I03_ATOMIC_ORDER.json;
  no auto-recovery, no stale-partial scanning (I08).  Storage tests 390
  (+131: compression 34 + atomic 22 + blob-store core 51 + adversarial 24);
  full suite 1768 passed / 0 failed / 2 skipped (1 env-gated live smoke + 1
  POSIX-only permission assertion skipped on Windows; floor was >=1638);
  ruff clean on changed scope; changed-scope mypy clean (remaining 4 =
  documented pre-existing yaml/planner baseline in untouched Bloc 2/3
  modules); network 0; provider code UNCHANGED; no acquisition repository,
  no manifests, no resume advancement, no T0B, no DuckDB, no Postgres.
  Flags: ATOMIC_FILESYSTEM_BACKEND_READY=TRUE, T0A_BLOB_BACKEND_IMPLEMENTED=
  TRUE, T0A_EVIDENCE_PIPELINE_COMPLETE=FALSE (AcquisitionRecord +
  PartitionManifest persistence = I04), MANIFEST_REPOSITORY_IMPLEMENTED=
  FALSE, T0B_STORAGE_IMPLEMENTED=FALSE.  Evidence:
  `evidence/bloc_04/BLOC_04_I03_ATOMIC_FILESYSTEM_EVIDENCE.md`.
- SENSOR-B4-I02 COMPLETE — CONTENT ADDRESSING + PATHS + CHECKSUMS (proposed
  `PASS_SENSOR_B4_I02_CONTENT_ADDRESSING_PATHS_CHECKSUMS`).  New storage
  modules `checksums.py` + `paths.py`; I01 models rewire SHA-256 syntax
  validation onto ONE shared rule (`checksums.validate_sha256_hex`); new
  `ChecksumAlgorithm` enum (SHA256 | MD5 | CRC32).  Exact-byte SHA-256 identity
  primitives (H1 source / H2 stored-object / H3 provider layers kept separate;
  bytes-only hashing, no implicit decoding; empty payload valid; bounded
  streaming, non-seekable, caller-owned, 1 GiB-equivalent large-stream proof);
  provider checksums explicit-algorithm only, never inferred from length,
  never promoted to T0 identity.  Content-addressed T0A blob keys
  (`blobs/sha256/h0h1/h2h3/<full>.blob[.zst]`, content ID immune to
  provider/sensor/instrument/date) and deterministic T0B projection keys
  (explicit caller-adjudicated logical date, no date-basis inference, no
  schema-hash doctrine — I05 owns that).  Reversible UTF-8-preserving segment
  escaping (narrow literal alphabet, uppercase %HH, no Unicode normalization,
  native identity escaped never normalized, empty coordinates fail closed) +
  lexical-only `resolve_under_root` containment (zero filesystem mutation;
  symlink hardening deferred to I15).  Storage tests 237 (122 new); full
  suite 1616 passed / 0 failed / 1 skipped; ruff clean on changed files
  (pre-existing test_models.py DTZ/I001 baseline documented); changed-scope
  mypy clean (only the known yaml/planner baseline in untouched Bloc 2
  modules remains); network 0; filesystem mutation 0; provider code
  unchanged; I01 + I01R1 evidence preserved.  Evidence:
  `evidence/bloc_04/BLOC_04_I02_CONTENT_ADDRESSING_EVIDENCE.md`.
- SENSOR-B4-I01R1 COMPLETE — PROJECTION VERSION + T0 LINEAGE + DATE-BASIS SEAL
  (proposed `PASS_SENSOR_B4_I01R1_STORAGE_CONTRACTS_SEALED`, then operator
  acceptance of `PASS_SENSOR_B4_I01_STORAGE_CONTRACTS_FROZEN`).  Five narrow
  contract defects sealed BEFORE hashes/paths/IDs depend on them:
  - **(A) semver:** `projection_schema_version` int -> strict
    `MAJOR.MINOR.PATCH` string (1.0.0/1.1.0/2.0.0 accepted; 1, v1, 1.0,
    prerelease, leading zeros, negatives rejected) on BOTH
    RawProjectionArtifact and RawNormalizationBatch; canonical JSON
    serializes the version as a string; no auto-bump logic.
  - **(B) T0 lineage:** RawProjectionArtifact.source_blob_sha256 requires
    >=1 unique T0A hash (`[]` rejected); RawNormalizationBatch requires
    >=1 source blob AND >=1 acquisition ref (no source-less normalization
    batch).
  - **(C) date basis:** PartitionManifest.date_basis default EVENT_TIME ->
    UNKNOWN; caller must explicitly assert EVENT_TIME/PROVIDER_FILE_DATE/
    SNAPSHOT_TIME; no inference from dates/provider/sensor.
  - **(D) hash refs:** 64-lowercase-hex syntax + duplicate rejection on all
    T0A SHA surfaces (blob, acquisition, projection source, lineage, manifest
    blob_refs, result blob_refs, batch source refs, source revision, job
    last-committed); non-SHA refs untouched.
  - **(E) timestamp order:** projection min/max_provider_time and manifest
    min/max_time fail closed when inverted; one-sided bounds remain valid
    (absent side never fabricated).
  Schema version != parser version != adapter version preserved.  All 16
  model names retained; no public API expansion.  Storage tests 115 (37
  new); full suite 1494 passed / 0 failed / 1 skipped; ruff clean;
  changed-scope mypy clean; network 0; storage writes 0; provider code
  unchanged; original I01 evidence preserved (chronology: I01 -> operator
  review -> I01R1).  Evidence:
  `evidence/bloc_04/BLOC_04_I01R1_LINEAGE_SCHEMA_SEAL_EVIDENCE.md`.
- SENSOR-B4-I01 COMPLETE — STORAGE MODELS + ENUMS (proposed
  `PASS_SENSOR_B4_I01_STORAGE_CONTRACTS_FROZEN`).  Bloc 3 ratified + frozen
  (SENSOR-B3-I11R1-RATIFY: I11R1 seal + Bloc 3 implementation OPERATOR_ACCEPTED;
  BLOC_04_PLAN = PASS_BLOC_04_PLAN_FROZEN).  New `crypto_sensor_fabric/storage/`
  package: 16 frozen models (EvidenceBlob, AcquisitionRecord, RawProjectionArtifact,
  ProjectionLineage, PartitionManifest, StorageJobState, StorageJobTransition,
  SourceRevision, IntegrityCheck, StorageQuotaState, BackupState, RawEvidenceQuery,
  RawEvidenceResult, RawNormalizationBatch, RecoveryAction, ExportManifest) + 12
  exact frozen enum vocabularies (integrity/coverage/revision-policy/revision-state/
  projection/encoding/date-basis/priority/disk-pressure/backup/job-status/object-type).
  Revision-policy reconciliation: FIRST_SEEN/LATEST_SEEN final vocabulary ONLY;
  obsolete FIRST_ACQUIRED/LATEST_ACQUIRED NOT introduced; query default =
  ERROR_ON_AMBIGUITY.  Fail-closed: extra=forbid, UTC-normalized datetimes (naive
  rejected), SHA-256 format-only validation, nonnegative counts, end>=start windows,
  no canonical asset/unit fields, no secret-bearing fields.  Deterministic
  serialization helper + tests.  Bloc 3 bridge: storage imports only frozen
  provider/base shared contracts; provider adapters do not import storage; no
  circular dependency.  NO persistence/backend/hashing/compression/paths/manifest
  repository/DuckDB/Postgres/Parquet; network calls = 0; provider code UNCHANGED.
  Full suite 1457 passed / 0 failed (1 skipped live, fail-closed); ruff clean;
  changed-scope mypy clean.  Readiness: STORAGE_MODEL_CONTRACTS_READY=TRUE,
  T0A/T0B_STORAGE_IMPLEMENTED=FALSE, ATOMIC_BACKEND_IMPLEMENTED=FALSE,
  MANIFEST_REPOSITORY_IMPLEMENTED=FALSE.  next_checkpoint_authorized=FALSE;
  recommended next: **SENSOR-B4-I02 CONTENT ADDRESSING + PATHS + CHECKSUMS**
  (NOT started).  Evidence: `evidence/bloc_04/BLOC_04_I01_STORAGE_CONTRACTS_EVIDENCE.md`.
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

## BLOC 4 — I05 CHAIN RATIFICATION + I06 SOURCE REVISION / MUTATION REGISTRY

| Commit | Stage | Tests | Verdict | Notes |
|---|---|---|---|---|
| SENSOR-B4-I05R4-RATIFY | ce4d8412 | governance only | PASS (operator) | operator ACCEPTS the complete I05 chain: PASS_SENSOR_B4_I05R4_EVIDENCE_INTERFACE_RETRY_SEALED, PASS_SENSOR_B4_I05R3_LINEAGE_IDENTITY_TIME_SEALED, PASS_SENSOR_B4_I05R2_FAIL_CLOSED_PUBLIC_API_SEALED, PASS_SENSOR_B4_I05R1_DURABLE_END_TO_END_LINEAGE_SEALED, PASS_SENSOR_B4_I05_RAW_PROJECTION_LINEAGE; I05R4 evidence-hash wording chronologically corrected (new files added, historical bytes untouched); authorizes SENSOR-B4-I06 ONLY |
| SENSOR-B4-I06A | c5c90c3e | RevisionSourceIdentityV1 identity contract (14 identity/construction/tamper tests) | PASS | source_revision_key = SHA256(canonical_json({identity_version:1, fields})); REQUEST semantics only (11 fields); content/observation fields + source_locator structurally excluded; descriptor persisted and recomputed on reload (§14); sealed dependency protocols at construction (§16) |
| SENSOR-B4-I06B | b43b35f5 | registry semantics/locks/idempotence/crash (23 tests) | PASS | physical T0A verification gates registration; blobless never segments; forensic usable_provenance=false via single I04R2 predicate; rev1 STABLE / IDENTICAL_REFETCH / SOURCE_MUTATION / A→B→A / PROVIDER_DECLARED_REVISION with explicit evidence; out-of-order + same-time-ambiguity fail closed; per-source locks, never auto-deleted; idempotent re-registration re-proves durable truth; crash completion keeps segment's own classification |
| SENSOR-B4-I06C | e2e98331 | declarations + six resolution modes (17 tests) + invocation-robust sibling imports | PASS | canonical declarations require evidence_ref + existing revision; unique/duplicate/zero/multiple canonical semantics per §36/§60; ERROR_ON_AMBIGUITY never picks latest; ALL no-dedupe; FIRST/LATEST explicit; EXACT strict; strictens reload chronology validation; closes the I05R4 audit invocation-sensitivity defect via _sibling_import loader |
| SENSOR-B4-I06D | e0e6466d | restart/corruption/concurrency/T0B-preservation (9 tests) | PASS | restart preserves chains; per-family corruption fails closed with frozen-vocabulary reload validation; concurrent different-byte mutations cannot fork numbering; rev1 bytes byte-identical across later revisions; rev1 T0B chain stays resolver-valid + manifest untouched after rev2 (§63/§64) |
| SENSOR-B4-I06E | 80cfbcfe + (this commit) | 3 deterministic matrices (identity/mutation/resolution) published once, pytest READ-ONLY vs committed bytes; evidence MD + ledger | 939 storage / 2318 full, 0 failed | proposed PASS_SENSOR_B4_I06_SOURCE_REVISION_MUTATION_REGISTRY; G4-04_REVISION_GATE = IMPLEMENTATION_PASS; SOURCE_REVISION_REGISTRY_IMPLEMENTED=TRUE, SOURCE_MUTATION_EXPLICIT=TRUE, REVISION_RESOLUTION_READY=TRUE; DURABLE_RESUME_IMPLEMENTED=FALSE; next_checkpoint_authorized=FALSE; recommended next SENSOR-B4-I07 DURABLE JOB STATE + RESUME COUPLING (NOT started) |

Current state: SOURCE_REVISION_REGISTRY_IMPLEMENTED=TRUE. I05→I06 chain
complete and pending operator review. next_checkpoint_authorized=FALSE —
SENSOR-B4-I07 (DURABLE JOB STATE + RESUME COUPLING) NOT authorized, NOT
started. Research NOT resumed.

## BLOC 4 — I06R1 CANONICAL REVISION CONTRACT MICROSEAL

| Commit | Stage | Tests | Verdict | Notes |
|---|---|---|---|---|
| SENSOR-B4-I06R1A/R1B | 2c4ad0b1 | canonical vocabulary + durable-acquisition identity binding (10 R1A/R1B tests incl. coordinated-tamper) | PASS | RevisionState/Policy imported from storage.enums only — RevisionResolutionMode is RevisionPolicy (object alias, §4); shadow SourceRevision deleted, get/list return frozen models.SourceRevision with aware-UTC datetimes + canonical enum (§5-§7); identity_version Literal[1] on identity AND segment records, V2 construction AND persisted-V2 rejected (§9/§10); restart re-derives identity from durable birth acquisition for EVERY segment — descriptor AND key must match (§11); observation source keys bound to durable acquisitions (§12); coordinated descriptor+key+filename tamper, same-blob wrong-source observation, duplicate birth acquisition all fail closed (§13-§15) |
| SENSOR-B4-I06R1C | 444e2ad1 | typed declarations + crash-safe ordering + collision-free ids (declaration tests updated) | PASS | ProviderRevisionDeclaration typed input replaces dict semantics (§24); declaration committed BEFORE segment (§25 option A) — pending evidence alone is safe, never unsupported truth; restart segment-driven proof that every PROVIDER_DECLARED_REVISION has supporting evidence (§26); default declaration ID = full SHA256 over source-namespaced semantics, no wall clock (§35); cross-source collisions impossible (§36); idempotent exact repeat adopts, semantic divergence → RevisionDeclarationConflict (§37); declared_at/registered_at typed aware-UTC datetimes, no str(datetime) path (§31/§32); evidence_ref nonempty everywhere (§30) |
| SENSOR-B4-I06R1D | 3f142288 | birth idempotence + declaration crash-boundary adversarial proof (17 tests) | PASS | birth re-registration returns ORIGINAL classification (FIRST_REGISTRATION/SOURCE_MUTATION/PROVIDER_DECLARED_REVISION — never IDENTICAL_REFETCH), identical same-process vs restart (§19-§21); IDENTICAL_REFETCH requires distinct acquisition event (§22); crash matrix: before declaration / after declaration before segment / retry-completes / divergent-evidence conflict / missing-evidence restart all fail safe (§26-§28); same-bytes declaration preserves evidence without minting a revision (§29) |
| SENSOR-B4-I06R1E | (this commit) | 3 deterministic R1 matrices (canonical-contract / identity-binding / declaration-durability) published once, pytest READ-ONLY vs committed bytes; evidence MD + ledger | 960 storage / 2339 full, 0 failed (fresh baseline 939/2318 re-measured at 295a8af5) | proposed PASS_SENSOR_B4_I06R1_CANONICAL_CONTRACT_DECLARATION_SEALED; then operator may accept PASS_SENSOR_B4_I06_SOURCE_REVISION_MUTATION_REGISTRY and G4-04_REVISION_GATE = IMPLEMENTATION_PASS; REVISION_CANONICAL_CONTRACT_SEALED=TRUE, PROVIDER_DECLARATION_DURABILITY_SEALED=TRUE; frozen enums.py/models.py byte-identical (reconciliation by import, not edit); historical I06 evidence untouched; DURABLE_RESUME_IMPLEMENTED=FALSE; next_checkpoint_authorized=FALSE; recommended next SENSOR-B4-I07 (NOT started) |

I06R1 current state: operator findings A-E sealed (canonical vocabulary,
durable-acquisition identity binding, evidence-before-classification,
declaration contract, birth idempotence). Historical I06 evidence remains
chronological truth for the pre-I06R1 implementation. I05→I06→I06R1 chain
complete and pending operator review. next_checkpoint_authorized=FALSE —
SENSOR-B4-I07 (DURABLE JOB STATE + RESUME COUPLING) NOT authorized, NOT
started. Research NOT resumed.

## BLOC 4 — I06R1 RATIFICATION (OPERATOR)

| Commit | Stage | Tests | Verdict | Notes |
|---|---|---|---|---|
| SENSOR-B4-I06R1-RATIFY | (this commit) | governance only (no test delta) | PASS (operator) | operator ACCEPTS PASS_SENSOR_B4_I06R1_CANONICAL_CONTRACT_DECLARATION_SEALED + PASS_SENSOR_B4_I06_SOURCE_REVISION_MUTATION_REGISTRY; G4-04_REVISION_GATE = IMPLEMENTATION_PASS; SOURCE_REVISION_REGISTRY_IMPLEMENTED=TRUE, SOURCE_MUTATION_EXPLICIT=TRUE, REVISION_RESOLUTION_READY=TRUE, REVISION_CANONICAL_CONTRACT_SEALED=TRUE, PROVIDER_DECLARATION_DURABILITY_SEALED=TRUE; DURABLE_RESUME_IMPLEMENTED=FALSE, RECOVERY_SCANNER_IMPLEMENTED=FALSE; branch agent/crypto-sensor-fabric-build fast-forwarded to main d09941e7 (no force, no content change); stale top-level I05/I04 current-state text reconciled; historical checkpoint entries/evidence NOT rewritten; AUTHORIZED: SENSOR-B4-I07 DURABLE JOB STATE + RESUME COUPLING ONLY — I08+ NOT authorized, NOT started |

I06R1-RATIFY current state: I05→I06→I06R1 chain OPERATOR_ACCEPTED;
G4-04_REVISION_GATE=IMPLEMENTATION_PASS. next_checkpoint_authorized=TRUE —
SENSOR-B4-I07 DURABLE JOB STATE + RESUME COUPLING ONLY. I08+ NOT authorized,
NOT started. Research NOT resumed.

## BLOC 4 — I07 DURABLE JOB STATE + RESUME COUPLING

| Commit | Stage | Tests | Verdict | Notes |
|---|---|---|---|---|
| SENSOR-B4-I07A | 37a54678 | DurableJobStateRepository (storage/jobs.py): append-only birth+event chain on the FROZEN StorageJobState/StorageJobTransition models; single-step forward state machine, no silent backward moves, annotated retry/continuation edges, terminal states, CAS guard; §16 resume gate (advance_checkpoint resolves acquisition + physical-verify + manifest-committed proof from durable truth; weaker explicit RAW_COMMITTED floor); CHECKPOINT_ADVANCED reachable ONLY via the gate; re-entrant per-job file+process locks, never auto-deleted; restart validation fail-closed incl. durable re-anchoring of committed checkpoint pointers | 29 tests | PASS |
| SENSOR-B4-I07B | 00a47ccd | job↔evidence coupling adversarial proof: two-batch resume cycle; cursor-never-advances-past-unindexed-evidence attack; §20 crash tests 6/7 (crash-before-advancement retry completes; crash-after-publication adopts exactly once with durable proof re-resolved — idempotence is not stale trust); divergent-retry typed conflicts visible after restart; manifest-anchor parquet tamper + stale/cross-process lock fail closed | 11 tests (storage 1000 passed / 0 failed / 3 skipped) | PASS |
| SENSOR-B4-I07C | (this commit) | 2 deterministic matrices (job-state §15 / resume-coupling §16+§20) published once, pytest READ-ONLY vs committed bytes; evidence MD + ledger | — | proposed PASS_SENSOR_B4_I07_DURABLE_JOB_STATE_RESUME_SEALED; DURABLE_RESUME_IMPLEMENTED=TRUE; RECOVERY_SCANNER_IMPLEMENTED=FALSE; recommended next SENSOR-B4-I08 RECOVERY / QUARANTINE (NOT authorized, NOT started) |

I07 current state: durable job state + resume coupling sealed per 03 doc §15/§16
with the frozen I01 vocabulary. next_checkpoint_authorized=FALSE pending operator
review of PASS_SENSOR_B4_I07_DURABLE_JOB_STATE_RESUME_SEALED. I08+ NOT authorized,
NOT started. Research NOT resumed.

## BLOC 4 — I07R1 RESUME-TRUTH HARDENING SEAL

Operator review set PASS_SENSOR_B4_I07_DURABLE_JOB_STATE_RESUME_SEALED =
OPERATOR_HOLD pending I07R1 (gates/identity/replay/coordination seams A-H).
Historical I07 evidence remains chronological truth for the pre-I07R1
implementation; its baseline wording ("storage 939 / full 2318") used the older
pre-I06R1 counts — the authoritative fresh baseline at exact head 42cdfe09 was
storage 1000 / full 2318 (I07R1E evidence §9).

| Commit | Stage | Tests | Verdict | Notes |
|---|---|---|---|---|
| SENSOR-B4-I07R1A/B/C/D | cbb93b15 | Sealed checkpoint API + identity-bound proof + replay=writer + safe locks + post-lock refresh: public advance_status narrowed to (job_id, *, to_status, reason, evidence_ref, expected_from); CHECKPOINT_ADVANCED reachable ONLY via private _append_checkpoint_event (no caller-settable flag); ordinary transitions preserve all four pointers exactly; states fully re-validated pre-durability; checkpoint proof resolves durable acquisition with EXACT job identity (provider/sensor/request_fingerprint) + authoritative I04R2 is_usable_manifest_provenance + MANIFEST-floor exact manifest↔acquisition binding (provider/venue/sensor/instrument/granularity); RAW floor requires manifest_id=None (no dummy anchors); exact blob anchor sealed; durable V1 checkpoint_proof persisted and re-proved under the floor persisted in each proof; ONE pure transition graph drives write path AND restart replay (forward skips, ungated checkpoints, bad retry edges, reason-less failures = corruption); birth identity / ordinary-event pointers / canonical event ids / result-time binding replay-validated; lock key = sha256(utf8(job_id)).lock (raw IDs never become paths; traversal/Unicode/long-ID safe); DurableJsonCatalog.refresh() validated read-only reload at OUTERMOST lock acquisition (two-repo refresh / sequence race / external checkpoint retry proven, no chain fork, no raw-JSON bypass) | 53 new I07R1 tests (storage 1056 passed / 0 failed / 3 skipped) | PASS |
| SENSOR-B4-I07R1E | (this commit) | 4 deterministic matrices (public API / checkpoint identity / restart replay / coordination — 39 cases) published once, pytest READ-ONLY vs committed bytes; evidence MD BLOC_04_I07R1_GATE_IDENTITY_REPLAY_EVIDENCE.md incl. historical I07 baseline correction + fresh exact-head baseline; ledger reconciliation | — | proposed PASS_SENSOR_B4_I07R1_GATE_IDENTITY_REPLAY_SEALED, then PASS_SENSOR_B4_I07_DURABLE_JOB_STATE_RESUME_SEALED for operator acceptance; DURABLE_RESUME_IMPLEMENTED=PENDING_OPERATOR_ACCEPTANCE; RECOVERY_SCANNER_IMPLEMENTED=FALSE; next_checkpoint_authorized=FALSE; recommended next SENSOR-B4-I08 RECOVERY / QUARANTINE ONLY after operator acceptance (NOT authorized, NOT started) |

I07R1 current state: PASS_SENSOR_B4_I07_DURABLE_JOB_STATE_RESUME_SEALED =
OPERATOR_HOLD (hardening executed). Proposed verdicts await operator review.
next_checkpoint_authorized=FALSE. I08 (RECOVERY / QUARANTINE) NOT authorized,
NOT started. Research NOT resumed.

---

## BLOC 4 — I07R1F FINAL MICROSEAL (PERSISTED FLOOR + CATALOG CONCURRENCY + LEDGER TRUTH)

Operator review of I07R1 confirmed the accepted architecture and found two remaining technical
seams plus one governance-state miss. I07R1F closes exactly those; no module split, no fixture
cleanup, no typed-event refactor, no I08 work.

### Governance reconciliation note (I07R1F §16)

I07R1E appended the correct HOLD state chronologically at the bottom of this ledger but did NOT
advance the operator-facing **Current state** table, so the top of the ledger still named
`SENSOR-B4-I06R1-RATIFY` as current truth — two checkpoints stale. That defect is corrected in
this commit (Current checkpoint / Operator review state / next_checkpoint_authorized rows now
carry the I07R1F truth). Historical checkpoint entries and evidence in this ledger are NOT
rewritten; the previous top-level text is retained below as an explicitly labeled historical
governance record.

### Commit-chain deviation record (I07R1F §17) — recorded, NOT repaired

The I07R1 prompt requested staged commits `I07R1A` → `I07R1B` → `I07R1C` → `I07R1D` → `I07R1E`.
The implementation delivered A/B/C/D together as one content commit `cbb93b15` (`SENSOR-B4-I07R1A/B/C/D`)
with `I07R1E` as `dd4db197`. This is a process/staging deviation only: the content is accepted
work, and no history has been rewritten, rebased, squashed or force-pushed to repair it. The
I07R1F prompt's two-commit plan (`I07R1F-A`, `I07R1F-B`) is followed exactly.

| Commit | Stage | Tests | Verdict | Notes |
|---|---|---|---|---|
| SENSOR-B4-I07R1F-A | 619cbaf0 | Persisted-floor exact retry + catalog cache concurrency sealed. `advance_checkpoint` detects an existing `CHECKPOINT_ADVANCED` head FIRST and re-proves it via `_retry_committed_checkpoint` under the floor persisted in that checkpoint's own proof (`_require_checkpoint_shape` now applies to NEW checkpoints only, so the current constructor floor can no longer reject or reinterpret durable history); divergent historical retries remain `JobTransitionConflict`. `DurableJsonCatalog` gains one internal `RLock` guarding the complete `_cache` critical sections of `refresh` / `commit` / `get` / `has` / `list_ids` / `__len__` (12 new adversarial proofs, each verified load-bearing against the pre-fix sources) | storage 1073 passed / 0 failed / 3 skipped (fresh exact-head baseline 1061 / 0 / 3 at dd4db197 + 12 new) | PASS |
| SENSOR-B4-I07R1F-B | (this commit) | 2 deterministic matrices (persisted floor — 5 cases; catalog concurrency — 5 cases) published once, pytest READ-ONLY vs committed bytes; evidence MD `BLOC_04_I07R1F_PERSISTED_FLOOR_CONCURRENCY_LEDGER_EVIDENCE.md`; top-level operator ledger reconciled to current truth | storage 1076 passed / 0 failed / 3 skipped (1079 collected); full 2455 passed / 0 failed / 4 skipped (2459 collected) — fresh exact-head baseline re-measured at dd4db197 in a clean worktree: storage 1061/0/3, full 2440/0/4; delta +15 tests, 0 failures | proposed `PASS_SENSOR_B4_I07R1F_PERSISTED_FLOOR_CATALOG_CONCURRENCY_LEDGER_SEALED`; then operator may accept `PASS_SENSOR_B4_I07R1_GATE_IDENTITY_REPLAY_SEALED` and `PASS_SENSOR_B4_I07_DURABLE_JOB_STATE_RESUME_SEALED`; `DURABLE_RESUME_IMPLEMENTED = PENDING_OPERATOR_ACCEPTANCE`; `RECOVERY_SCANNER_IMPLEMENTED = FALSE`; `next_checkpoint_authorized = FALSE`; recommended next SENSOR-B4-I08 RECOVERY / QUARANTINE ONLY AFTER operator acceptance (NOT authorized, NOT started) |

I07R1F current state: implementation COMPLETE and machine-proven; proposed verdict awaits operator
review. PASS_SENSOR_B4_I07_DURABLE_JOB_STATE_RESUME_SEALED = OPERATOR_HOLD.
PASS_SENSOR_B4_I07R1_GATE_IDENTITY_REPLAY_SEALED = PENDING_OPERATOR_REVIEW.
SENSOR-B4-I07R1F = PENDING_OPERATOR_REVIEW. DURABLE_RESUME_IMPLEMENTED =
PENDING_OPERATOR_ACCEPTANCE. RECOVERY_SCANNER_IMPLEMENTED = FALSE.
next_checkpoint_authorized = FALSE. I08 (RECOVERY / QUARANTINE) NOT authorized, NOT started.
No quota, no DuckDB, no Postgres, no provider integration, network = 0. Research NOT resumed.

---

## BLOC 4 — I07R1G RUNTIME-PROOF SCHEMA + REPLAY-PARITY MICROSEAL

Prompt: `SENSOR-B4-I07R1G` (runtime checkpoint-proof schema + replay-parity seal), starting at
`d10f2a5ee9e249b0e70b2f745a0b44aa64777e40` (I07R1F missing-proof runtime adversarial proof),
branch `agent/crypto-sensor-fabric-build`, clean tree. Required lineage `619cbaf0` → `7fa51ada`
→ `91294f10` → `d10f2a5e` verified before any edit. No reset, no rebase, no force push, no
history rewrite.

### Operator finding → seam closed

One seam remained: the runtime exact-retry path validated that a committed checkpoint's
`checkpoint_proof` EXISTED, not that it was VALID, while restart validated the full contract —
so runtime truth and restart truth had two owners and disagreed. Proof existence is not proof
validity: a malformed but present proof was an adoptable success at runtime and a corruption at
restart.

Closure is one authority used by both paths: the pure module-level `validate_checkpoint_proof`
owns the closed V1 field set, the version guard, the floor contract and the floor↔manifest rule;
the repository method `_validate_checkpoint_proof` adds the proof↔resulting-state anchor binding
and the durable batch re-proof under the floor PERSISTED in the proof itself. Both the runtime
path (before any adoption) and restart replay call that single method; the old restart-only
`_reprove_checkpoint` is deleted rather than paralleled, so reader and writer cannot drift.

### Machine-measured parity (before → after)

The attack path is a chain-VALID later checkpoint head (`ACQUIRING -> CHECKPOINT_ADVANCED`,
canonical event id, `resulting_state.updated_at == transition.transitioned_at`) published at its
correct hashed physical key while the repository is constructed BEFORE the forgery, so the
outermost-lock validated refresh ADOPTS it and the runtime retry path is what must refuse it.
An intact-proof control is accepted on both paths, which makes every rejection specific to proof
VALIDITY rather than the forgery's shape.

| Forged proof | runtime before | runtime after | restart after |
|---|---|---|---|
| proof missing | JobCatalogCorrupt | JobCatalogCorrupt | JobCatalogCorrupt |
| proof_version = 2 | **NO_ERROR (adopted)** | JobCatalogCorrupt | JobCatalogCorrupt |
| proof_version missing | **NO_ERROR (adopted)** | JobCatalogCorrupt | JobCatalogCorrupt |
| floor missing | **KeyError** | JobCatalogCorrupt | JobCatalogCorrupt |
| floor unknown | **ValueError** | JobCatalogCorrupt | JobCatalogCorrupt |
| acquisition anchor mismatch | **NO_ERROR (adopted)** | JobCatalogCorrupt | JobCatalogCorrupt |
| blob anchor mismatch | **NO_ERROR (adopted)** | JobCatalogCorrupt | JobCatalogCorrupt |
| manifest anchor mismatch | **NO_ERROR (adopted)** | JobCatalogCorrupt | JobCatalogCorrupt |
| RAW floor + manifest anchor | **JobTransitionConflict** | JobCatalogCorrupt | JobCatalogCorrupt |
| MANIFEST floor + no manifest | **JobTransitionConflict** | JobCatalogCorrupt | JobCatalogCorrupt |
| proof = `[]` | JobCatalogCorrupt | JobCatalogCorrupt | JobCatalogCorrupt |
| proof = `{}` | JobCatalogCorrupt | JobCatalogCorrupt | JobCatalogCorrupt |
| proof = `"proof"` / `1` / `True` | **TypeError** | JobCatalogCorrupt | JobCatalogCorrupt |
| proof + unexpected extra field | **NO_ERROR (adopted)** | JobCatalogCorrupt | JobCatalogCorrupt |
| same blob, wrong acquisition | **JobTransitionConflict** | JobCatalogCorrupt | JobCatalogCorrupt |
| intact control (not an attack) | accepted | accepted | accepted |

Both paths were also attacked with the same-bytes wrong-anchor case (two durable acquisitions,
identical blob SHA, different request identity, internally consistent forged anchors →
corruption), and the valid-history regressions were re-proven: RAW-persisted retry under a
MANIFEST constructor and MANIFEST-persisted retry under a RAW constructor both still succeed and
adopt exactly, while a divergent caller batch stays `JobTransitionConflict` (a valid record with
a divergent request is not corruption, because the validator re-proves the PERSISTED anchors,
never the caller's).

### Load-bearing proof

`jobs.py` (md5 `41531a946a4c76277316707e2612a730`) was backed up, ONLY the runtime call to the new
authority was neutralised back to the pre-I07R1G shape, and the new suite re-run: 15 of 19 tests
failed with exactly the predicted modes above (six silent adoptions, KeyError, ValueError, three
TypeErrors, three JobTransitionConflict). Restored from the backup and re-verified byte-identical
(md5 `41531a94…`), then green again (19/19).

### Commit chain (no squash)

| Commit | Stage | Tests | Verdict | Notes |
|---|---|---|---|---|
| SENSOR-B4-I07R1G-A | 3c838e4d | Runtime and restart checkpoint-proof validation unified in one authority (`validate_checkpoint_proof` + `_validate_checkpoint_proof`); `_reprove_checkpoint` deleted; replay calls the same authority. New adversarial surface `test_job_state_r1g.py` (17 forged cases + intact-proof control + same-bytes premise test) and evidence builder `test_i07r1g_evidence.py` | storage 1098 passed / 0 failed / 3 skipped (1101 collected) — fresh exact-head baseline measured in a clean worktree at d10f2a5e: storage 1077/0/3 (1080), full 2456/0/4 (2460) | PASS |
| SENSOR-B4-I07R1G-B | b24ef884 | 1 deterministic matrix (`BLOC_04_I07R1G_RUNTIME_PROOF_PARITY_MATRIX.json`, 14 cases) published once, pytest READ-ONLY vs committed bytes; evidence MD `BLOC_04_I07R1G_RUNTIME_PROOF_PARITY_EVIDENCE.md`; top-level operator ledger advanced to I07R1G truth | storage 1098 passed / 0 failed / 3 skipped (1101 collected); full 2477 passed / 0 failed / 4 skipped (2481 collected); delta +21 tests, 0 failures | proposed `PASS_SENSOR_B4_I07R1G_RUNTIME_PROOF_SCHEMA_REPLAY_PARITY_SEALED`; then operator may accept `PASS_SENSOR_B4_I07R1F_PERSISTED_FLOOR_CATALOG_CONCURRENCY_LEDGER_SEALED`, `PASS_SENSOR_B4_I07R1_GATE_IDENTITY_REPLAY_SEALED` and `PASS_SENSOR_B4_I07_DURABLE_JOB_STATE_RESUME_SEALED`; `DURABLE_RESUME_IMPLEMENTED = PENDING_OPERATOR_ACCEPTANCE`; `RECOVERY_SCANNER_IMPLEMENTED = FALSE`; `next_checkpoint_authorized = FALSE`; recommended next SENSOR-B4-I08 RECOVERY / QUARANTINE ONLY AFTER operator acceptance (NOT authorized, NOT started) |
| SENSOR-B4-I07R1G post-audit repair | (this commit) | Two audit findings INSIDE this checkpoint's own lines closed, nothing else: (1) the replay loop once again runs the CHEAP pure `validate_transition` check BEFORE the durable re-proof, restoring cheap-check-first order (unifying the proof contract had inverted it); (2) the per-event loop now calls the existing module-level `is_checkpoint_event(payload)` predicate instead of recomputing `is_checkpoint` inline, so the predicate has one owner. Both are ordering/ownership refactors — every rejection still classifies as `JobCatalogCorrupt`, the 17 forged cases still fail closed on both paths, the intact-proof control is still accepted, and the committed matrix regenerates byte-identically (no evidence change required). The record also now states plainly (evidence MD §12) that the closed field-set check is stricter than §11's enumerated attack list while no legitimate writer path can emit an extra proof field, and that two extra test/matrix variants (a bool proof and an extra-field proof) were not requested — flagged for the operator to veto. mypy is recorded precisely: `jobs.py` clean apart from the pre-existing `probes/planner.py:79` baseline, new test modules carrying the same `import-not-found`/`arg-type` noise the pre-existing r1f modules produce | storage/full re-measured at the final tree — see evidence MD §12 | **NO VERDICT CHANGE** — every proposed PASS in this section remains `PENDING_OPERATOR_REVIEW`; `OPERATOR_HOLD` states unchanged; I08 NOT authorized, NOT started |

### Governance reconciliation note (I07R1G §18)

The operator-facing **Current state** table is advanced in this commit to `SENSOR-B4-I07R1G` with
`PASS_SENSOR_B4_I07R1F… = OPERATOR_HOLD`, `PASS_SENSOR_B4_I07R1_GATE_IDENTITY_REPLAY_SEALED =
OPERATOR_HOLD` and `PASS_SENSOR_B4_I07_DURABLE_JOB_STATE_RESUME_SEALED = OPERATOR_HOLD`,
`DURABLE_RESUME_IMPLEMENTED = PENDING_OPERATOR_ACCEPTANCE`, `RECOVERY_SCANNER_IMPLEMENTED = FALSE`
and `next_checkpoint_authorized = FALSE`. No self-acceptance: every verdict this checkpoint
proposes stays `PENDING_OPERATOR_REVIEW`. Historical checkpoint entries and evidence in this
ledger are NOT rewritten; the superseded I07R1F text is retained in the same row, explicitly
labeled a historical governance record.

### Read-only governance and environment notes

Historical I07/I07R1/I07R1F evidence and matrices are untouched (`git diff d10f2a5e..HEAD` under
`evidence/` shows only the single ADDED I07R1G matrix, zero modifications). The new matrix is
generated in `tmp_path` and byte-compared by pytest; publication happened once as an explicit
operator invocation. Re-running the suites again re-dirtied the same seven I03R1/I04-era legacy
evidence files with pure line-ending changes (identical insert/delete counts, byte-identical
content); they were restored with `git checkout HEAD --` before committing, so this commit
carries zero historical-evidence changes. Per the prompt this is recorded, not counted as an
I07R1G behavioural failure.

I07R1G current state: implementation COMPLETE and machine-proven; proposed verdict awaits operator
review. `PASS_SENSOR_B4_I07R1G_RUNTIME_PROOF_SCHEMA_REPLAY_PARITY_SEALED = PENDING_OPERATOR_REVIEW`.
`PASS_SENSOR_B4_I07R1F_PERSISTED_FLOOR_CATALOG_CONCURRENCY_LEDGER_SEALED = OPERATOR_HOLD`.
`PASS_SENSOR_B4_I07R1_GATE_IDENTITY_REPLAY_SEALED = OPERATOR_HOLD`.
`PASS_SENSOR_B4_I07_DURABLE_JOB_STATE_RESUME_SEALED = OPERATOR_HOLD`.
`DURABLE_RESUME_IMPLEMENTED = PENDING_OPERATOR_ACCEPTANCE`. `RECOVERY_SCANNER_IMPLEMENTED = FALSE`.
`next_checkpoint_authorized = FALSE`. Recommended next: **SENSOR-B4-I08 RECOVERY / QUARANTINE**,
ONLY AFTER operator acceptance.

**STOP GATE honored:** I08 (recovery / quarantine) NOT started. Research NOT resumed.

---

## SENSOR-B4-I07R1H — runtime refreshed-chain + restart validation parity

Prompt: `SENSOR-B4-I07R1H` (runtime refreshed-event chain + restart
validation parity), starting at `7a7d576c056693a49cf261753af886a5b4df4e0c`
on `agent/crypto-sensor-fabric-build` (clean tree; lineage
`3c838e4d` → `b24ef884` → `7a7d576c` verified).

Operator finding closed: the outermost per-job lock refreshed the
birth/event catalogs and then materialized the newest `resulting_state`
directly — but `DurableJsonCatalog.refresh()` proves fragment parse and
physical-key binding only, NOT that an adopted event satisfies the
job-state contract (canonical event identity, transition/result binding,
immutable birth identity, time binding, the frozen transition graph,
contiguity/linkage/chronology, ordinary pointer immutability).  A
long-lived repository could therefore consume as runtime state an event a
fresh restart would reject.  ONE per-job chain authority
(`_validate_job_chain`) now serves BOTH callers: the outer lock runs it
for the LOCKED job after both refreshes complete (targeted, never a
global all-job rescan), and restart (`_validate_cross_constraints`)
reuses it per job plus the global unknown-job check — no rule duplicated,
same `validate_transition` graph, same `is_checkpoint_event` predicate,
same I07R1G proof authority.

| Commit | SHA | Content | Tests | Verdict |
|---|---|---|---|---|
| SENSOR-B4-I07R1H-A | 765ed1a2 | Shared per-job chain authority (`_validate_job_chain`) wired into outer-lock refresh (job-targeted, post-refresh) and restart replay; monolithic `_validate_cross_constraints` reduced to the global unknown-job check + per-job sweep. New adversarial surface `test_job_state_r1h.py` (13 chain-corrupt cases + intact control + job-local proof) | see SENSOR-B4-I07R1H-B row for final counts | proposed |
| SENSOR-B4-I07R1H-B | (this commit) | Machine matrix `BLOC_04_I07R1H_REFRESHED_CHAIN_PARITY_MATRIX.json` (16 cases, all PASS) published once, pytest READ-ONLY vs committed bytes; evidence MD `BLOC_04_I07R1H_REFRESHED_CHAIN_VALIDATION_PARITY_EVIDENCE.md`; top-level operator ledger advanced to I07R1H truth | fresh exact-head baseline at 7a7d576c: storage 1098/0/3 (1101 collected), full 2477/0/4 (2481 collected); final: storage 1115 passed / 0 failed / 3 skipped (1118 collected), full 2494 passed / 0 failed / 4 skipped (2498 collected); delta +17, zero failures | proposed `PASS_SENSOR_B4_I07R1H_REFRESHED_CHAIN_VALIDATION_PARITY_SEALED`; then operator may accept `PASS_SENSOR_B4_I07R1G_RUNTIME_PROOF_SCHEMA_REPLAY_PARITY_SEALED`, `PASS_SENSOR_B4_I07R1F_PERSISTED_FLOOR_CATALOG_CONCURRENCY_LEDGER_SEALED`, `PASS_SENSOR_B4_I07R1_GATE_IDENTITY_REPLAY_SEALED` and `PASS_SENSOR_B4_I07_DURABLE_JOB_STATE_RESUME_SEALED`; `DURABLE_RESUME_IMPLEMENTED = PENDING_OPERATOR_ACCEPTANCE`; `RECOVERY_SCANNER_IMPLEMENTED = FALSE`; `next_checkpoint_authorized = FALSE`; recommended next SENSOR-B4-I08 RECOVERY / QUARANTINE ONLY AFTER operator acceptance (NOT authorized, NOT started) |

Adversarial outcome (13 chain-corrupt heads, each published at its CORRECT
hashed physical key so catalog refresh adopts it, each with a fully valid
proof where present — only chain semantics corrupted): `from_status_chain_break`,
`transition_job_id_mismatch`, `result_status_mismatch`,
`provider_identity_mismatch`, `sensor_identity_mismatch`,
`request_identity_mismatch`, `updated_at_transition_mismatch`,
`backward_chronology`, `sequence_gap`, `event_identity_mismatch`,
`ordinary_resume_pointer_mutation`, `ordinary_anchor_mutation`,
`proof_on_ordinary_event` — ALL rejected `JobCatalogCorrupt` on BOTH the
runtime refresh path and fresh restart, chain unchanged (corruption never
writes).  Intact refreshed control ADOPTED at runtime (adoption proven by
the probe's own +1 event) and accepted at restart.  Load-bearing proof:
neutralizing only the runtime gate (`_validate_job_chain` removed from
`_refresh_durable_truth`) failed 14 of 15 r1h tests with the predicted
mode (corrupt heads adopted at runtime, restart still refusing), then the
source was restored byte-identically and re-verified green.  I07R1G
forged-proof parity (17 cases + control) remains green and its committed
matrix regenerates byte-identically; RAW/MANIFEST persisted-floor
cross-config retries remain green; catalog RLock unchanged;
constructor-floor authority for NEW checkpoints unchanged.

Precision notes: ruff clean on all changed scope.  mypy stated precisely
per §31: `jobs.py` introduces no new error beyond the documented
pre-existing `probes/planner.py:79` baseline; the repository defines no
`[tool.mypy]` policy, and the two new test modules were type-checked with
the source root configured (`MYPYPATH="quant-lab/src;
quant-lab/tests/crypto_sensor_fabric/storage"`) and are fully clean (zero
errors, no `import-not-found`, no arg-type notes).  Network = 0; provider
source unchanged.  One earlier full-suite run observed a single failure in
the pre-existing `test_blob_store_adversarial.py` concurrency test
(threading, code untouched by this checkpoint); it passes in isolation and
in the recorded final run.  Historical I07/I07R1/I07R1F/I07R1G evidence
and the historical ledger sections untouched.

### Governance reconciliation note (I07R1H §32)

The operator-facing **Current state** table is advanced in this commit to
`SENSOR-B4-I07R1H` with
`PASS_SENSOR_B4_I07R1G_RUNTIME_PROOF_SCHEMA_REPLAY_PARITY_SEALED = OPERATOR_HOLD`,
`PASS_SENSOR_B4_I07R1F_PERSISTED_FLOOR_CATALOG_CONCURRENCY_LEDGER_SEALED = OPERATOR_HOLD`,
`PASS_SENSOR_B4_I07R1_GATE_IDENTITY_REPLAY_SEALED = OPERATOR_HOLD`,
`PASS_SENSOR_B4_I07_DURABLE_JOB_STATE_RESUME_SEALED = OPERATOR_HOLD`,
`DURABLE_RESUME_IMPLEMENTED = PENDING_OPERATOR_ACCEPTANCE`,
`RECOVERY_SCANNER_IMPLEMENTED = FALSE` and
`next_checkpoint_authorized = FALSE`.  No self-ratification: every verdict
this checkpoint proposes stays `PENDING_OPERATOR_REVIEW`.  Historical
checkpoint entries and evidence in this ledger are NOT rewritten; the
superseded I07R1G top-level text is retained in the same rows, explicitly
labeled a historical governance record.

**STOP GATE honored:** I08 (recovery / quarantine) NOT started.  Research
NOT resumed.

## SENSOR-B4-I07R1I — failed-gate atomicity + validated public reads + ledger structure

Prompt: `SENSOR-B4-I07R1I` (failed outer-entry rollback + validated public
read + ledger structure seal), starting at
`940c25097774a11c3e3b5282c41f1428fb5f10cf` on
`agent/crypto-sensor-fabric-build` (lineage `765ed1a2` → `940c2509`
verified; the worktree opened with a preserved partial attempt at this
checkpoint — a crashed session had left the implementation and both test
modules on disk but no verification runs, no evidence MD and no commits;
that state was verified against the spec and adopted, then completed —
recorded as a process note, NOT a history rewrite).

Operator finding closed (§3–§21): `_NestedFileLock.__enter__` acquired the
per-job physical lock, installed `_lock_owners[job_id]` and THEN ran
`_refresh_durable_truth` (both catalog refreshes + the shared
`_validate_job_chain` authority).  When that gate raised, `__exit__` never
ran: the bare `except` released only the in-process RLock, so the owner
record and the physical lock survived — the NEXT same-thread operation on
that job classified itself as NESTED and skipped acquire/refresh/validate
entirely.  A rejected gate became a live reentrant context and validation
failure weakened the next validation attempt.  Separately, the PUBLIC reads
`get_job` / `list_transitions` read the catalogs directly, so
durable-but-invalid state a long-lived repository had just adopted from
disk by refresh was readable as validated runtime truth.

| Commit | SHA | Content | Tests | Verdict |
|---|---|---|---|---|
| SENSOR-B4-I07R1I-A | ee7777d8 | Failed outer-entry rollback + validated public reads: `_NestedFileLock.__enter__` wraps `_refresh_durable_truth` so ANY post-acquisition failure rolls back THIS attempt's owner entry, physical lock handle and lock file before the ORIGINAL error escapes (§5); `_acquire_file_lock` failure installs nothing, so a pre-existing foreign/stale lock is never auto-deleted and remains I08 recovery evidence (§6); cleanup faults never replace the corruption diagnosis (§7); public `get_job` / `list_transitions` now cross the SAME per-job gate as the writers (`with self._job_lock(...)` → refresh + `_validate_job_chain` → unlocked internal helpers `_get_job_unlocked` / `_list_transitions_unlocked`, §14–§16), with successful nested reentrancy preserved (§17) and the legitimate `create_job` empty path untouched (§18). New adversarial surface `test_job_state_r1i.py` (§25 cases A–P) | see SENSOR-B4-I07R1I-B row for final counts | proposed |
| SENSOR-B4-I07R1I-B | (this commit) | 2 deterministic matrices (`BLOC_04_I07R1I_FAILED_GATE_ATOMICITY_MATRIX.json` 17 cases: all 15 required + the §21 rollback-disabled counterfactual + the I07R1H intact control; `BLOC_04_I07R1I_LEDGER_STRUCTURE_MATRIX.json` 6 cases) published once, pytest READ-ONLY vs committed bytes; evidence MD `BLOC_04_I07R1I_FAILED_GATE_ATOMICITY_VALIDATED_READ_EVIDENCE.md`; top-level Current checkpoint row repaired from three logical cells to two (§22) with the ledger structure test (§23) | fresh exact-head baseline at 940c2509 (clean worktree): storage 1115 passed / 0 failed / 3 skipped (1118 collected), full 2494 passed / 0 failed / 4 skipped (2498 collected); final: storage 1142 passed / 0 failed / 3 skipped (1145 collected), full 2521 passed / 0 failed / 4 skipped (2525 collected); delta +27, zero failures | proposed `PASS_SENSOR_B4_I07R1I_FAILED_GATE_ATOMICITY_VALIDATED_READ_SEALED`; then operator may accept `PASS_SENSOR_B4_I07R1H_REFRESHED_CHAIN_VALIDATION_PARITY_SEALED`, `PASS_SENSOR_B4_I07R1G_RUNTIME_PROOF_SCHEMA_REPLAY_PARITY_SEALED`, `PASS_SENSOR_B4_I07R1F_PERSISTED_FLOOR_CATALOG_CONCURRENCY_LEDGER_SEALED`, `PASS_SENSOR_B4_I07R1_GATE_IDENTITY_REPLAY_SEALED` and `PASS_SENSOR_B4_I07_DURABLE_JOB_STATE_RESUME_SEALED`; `DURABLE_RESUME_IMPLEMENTED = PENDING_OPERATOR_ACCEPTANCE`; `RECOVERY_SCANNER_IMPLEMENTED = FALSE`; `next_checkpoint_authorized = FALSE`; recommended next SENSOR-B4-I08 RECOVERY / QUARANTINE ONLY AFTER operator acceptance (NOT authorized, NOT started) |

Adversarial outcome (§25 A–P, every case on the proven repository-FIRST
forged-head shape): first corrupt operation `JobCatalogCorrupt` (A); the
immediate SAME-THREAD retry also `JobCatalogCorrupt` with the validation
and refresh counters at 2 — two real gate passes, the nested shortcut never
taken (B/C); owner map clean after failure (D); the owned lock file absent
(E); a second thread acquires the lock normally and fails closed —
`JobCatalogCorrupt`, never `JobLockHeld` (F); `_births.refresh` and
`_events.refresh` failures roll back identically with the typed ORIGINAL
catalog error and a genuine fresh outer entry afterwards (G/H);
direct `get_job` and `list_transitions` after a corrupt external
publication both `JobCatalogCorrupt` with no prior write, the forged head
already present in the cache when refused — cache state is forensic, never
runtime truth (I/J, §13/§20); valid public reads and cross-repository
refreshed reads green (K–N); successful nested entry refreshes exactly once
and one write entry refreshes exactly once (§17); the `create_job` empty
path and its idempotent re-create stay green (O); the I07R1H intact
refreshed control remains adopted (P) and every rejected gate leaves the
durable chain byte-count unchanged.  Load-bearing proof: the §21
counterfactual (rollback neutralized IN the evidence builder, no production
edit) shows the second same-thread attempt skipping validation on the
leaked owner record and ADOPTING the forged head (`second_attempt_adopted_forged_head
= true`), plus the owner/lock leak fields — the exact defect sealed; the
§23 structure test was additionally proven content-red against the
committed 940c2509 ledger blob and green after repair.  Regressions:
I07R1H 13 chain-corruption cases + intact control, I07R1G 17 forged-proof
cases + control (committed matrices regenerate byte-identically), I07R1F
RAW↔MANIFEST persisted-floor cross-config retries, two-repository
refresh/serialization, external exact checkpoint retry, catalog RLock,
safe hashed lock paths — all green (107 upstream tests re-run in one
command).

Ledger structure repair (§22): the top-level Current checkpoint row at
940c2509 carried the intended I07R1H cell followed by a duplicated trailing
segment beginning `| — closed V1 schema`; the row now carries EXACTLY two
logical cells (the governance test proves every ordinary row is
`Field | Value`).  §24: `Current checkpoint = SENSOR-B4-I07R1I`; all five
upstream I07 approvals stay `OPERATOR_HOLD`;
`DURABLE_RESUME_IMPLEMENTED = PENDING_OPERATOR_ACCEPTANCE`;
`RECOVERY_SCANNER_IMPLEMENTED = FALSE`; `next_checkpoint_authorized =
FALSE`; no self-ratification — every verdict this checkpoint proposes
stays `PENDING_OPERATOR_REVIEW`.  Historical checkpoint entries and
evidence NOT rewritten.

Precision notes: ruff clean on all changed scope.  mypy stated precisely
per §32: `jobs.py` introduces no new error beyond the documented
pre-existing `probes/planner.py:79` baseline; the repository defines no
`[tool.mypy]` policy, so the two new test modules were type-checked with
the source root configured (`MYPYPATH="src;
tests/crypto_sensor_fabric/storage"`) and are fully clean apart from that
same single pre-existing baseline (the evidence module's two deliberate
rollback-neutralization assignments carry explicit `method-assign`
suppressions).  External CI truth (§31): at operator review of 940c2509
the combined commit statuses and workflow runs were NONE — all evidence
here is local/repository evidence; no CI success is claimed.  Network = 0;
provider source unchanged; historical I07/I07R1/I07R1F/I07R1G/I07R1H
evidence untouched (the seven pre-I05-era evidence JSONs showed their
documented CRLF-only churn during pytest and were restored before commit —
zero content delta, recorded per §29).

**STOP GATE honored:** I08 (recovery / quarantine) NOT started.  Research
NOT resumed.

## SENSOR-B4-I07R1I-RATIFY — operator accepts the complete I07 chain, authorizes I08

Prompt: `SENSOR-B4-I07R1I-RATIFY`, starting at
`fd96160485ad44763022f6a1f07f80e5ffb5d794` on
`agent/crypto-sensor-fabric-build` (clean tree; lineage `ee7777d8` →
`fd961604` verified; main intentionally NOT merged/rebased — it is on a
divergent lineage and this branch remains implementation truth).

Operator decision: the complete I07 chain is ACCEPTED —
PASS_SENSOR_B4_I07_DURABLE_JOB_STATE_RESUME_SEALED,
PASS_SENSOR_B4_I07R1_GATE_IDENTITY_REPLAY_SEALED,
PASS_SENSOR_B4_I07R1F_PERSISTED_FLOOR_CATALOG_CONCURRENCY_LEDGER_SEALED,
PASS_SENSOR_B4_I07R1G_RUNTIME_PROOF_SCHEMA_REPLAY_PARITY_SEALED,
PASS_SENSOR_B4_I07R1H_REFRESHED_CHAIN_VALIDATION_PARITY_SEALED and
PASS_SENSOR_B4_I07R1I_FAILED_GATE_ATOMICITY_VALIDATED_READ_SEALED =
OPERATOR_ACCEPTED.  DURABLE_RESUME_IMPLEMENTED = TRUE;
RECOVERY_SCANNER_IMPLEMENTED = FALSE; next_checkpoint_authorized = TRUE
authorizing SENSOR-B4-I08 RECOVERY / QUARANTINE ONLY; I09+ NOT
authorized.

| Commit | SHA | Content | Tests | Verdict |
|---|---|---|---|---|
| SENSOR-B4-I07R1I-RATIFY | (this commit) | governance-only top-level ledger truth: Current checkpoint = SENSOR-B4-I07R1I-RATIFY, all six I07-chain verdicts OPERATOR_ACCEPTED, DURABLE_RESUME_IMPLEMENTED=TRUE, RECOVERY_SCANNER_IMPLEMENTED=FALSE, next_checkpoint_authorized=TRUE (I08 ONLY) | no test delta (no source/test/evidence change) | operator verdict (ratification) |

Historical checkpoint entries and evidence NOT rewritten.  The historical
I07R1I/I07R1H/I07R1G cells in the Current checkpoint row retain their
checkpoint-time states, explicitly labeled.

**STOP GATE honored:** this is a ratification commit only — I08
implementation begins in the next commit under the newly authorized
state.

## SENSOR-B4-I08 — recovery / quarantine (scan != apply, no silent repair)

Prompt: `SENSOR-B4-I08 RECOVERY / QUARANTINE`, starting at
`fd96160485ad44763022f6a1f07f80e5ffb5d794` on
`agent/crypto-sensor-fabric-build` (clean tree; I07R1I lineage `ee7777d8`
→ `fd961604` verified; main intentionally NOT merged/rebased — divergent
lineage; this branch remains implementation truth).

**Commit-staging deviation (recorded, not repaired):** the prompt's
preferred five-stage I08A–I08E chain was delivered as THREE commits
(I08A module, I08B adversarial proof, I08C evidence/ledger freeze) —
the engine matured as one module, so the A/B/C/D stage boundaries
collapsed into the module commit.  Each commit carries independent
content; nothing was squashed and no history was rewritten.

First commit `abcc1b40` SENSOR-B4-I07R1I-RATIFY (governance-only — see
the section above), then a fresh post-ratification baseline at
`abcc1b40`: storage 1142 passed / 0 failed / 3 skipped (1145 collected);
full 2521 passed / 0 failed / 4 skipped (2525 collected).

Implementation: `quant-lab/src/crypto_sensor_fabric/storage/recovery.py`
— ONE focused module (no jobs.py refactor, no module split, no fixture
cleanup, no event-model redesign): a two-phase `RecoveryEngine` with a
READ-ONLY deterministic `scan()` (byte-census proven; findings sorted;
same tree + inputs ⇒ identical result) producing a typed finding
vocabulary (UNCOMMITTED_STAGING, ORPHAN_DURABLE_BLOB, ORPHAN_PROJECTION,
ORPHAN_MANIFEST, CORRUPT_BLOB, MISSING_MANIFEST_TARGET,
ACQUISITION_SOURCE_QUARANTINED, JOB_DURABILITY_DIVERGENCE,
LOCK_PRESENT_OWNER_UNPROVEN, UNKNOWN_CONTEXT), and an `apply_plan()`
that is the ONLY mutating path: every action revalidates its target
against the scanned before-state first (typed RecoveryPlanConflict on
drift).  The append-only RecoveryAction journal lives under
`<t0_root>/catalogs/recovery/actions/` through the shared
DurableJsonCatalog primitive; the logical action id is SHA-256 over the
canonical §7 field set with registration time excluded — exact retry
adopts the existing durable record (idempotent), genuinely divergent
semantics raise typed conflicts and the catalog refuses overwrite.  The
frozen RecoveryAction model is used verbatim for the seven frozen
StorageObjectType members; staging artifacts and job locks (no frozen
member) use an internal durable envelope instead of altering frozen
fields.  Quarantine is `<t0_root>/quarantine/{integrity,malformed,
unknown_context}` with no-clobber deterministic locators (content hash
decides byte identity; different bytes behind the same locator raise a
typed conflict) and byte preservation; corrupt blobs are quarantined,
never overwritten, and the canonical location fails closed; orphan
reconciliation goes only through existing public repository APIs when
context proves identity, otherwise unknown-context quarantine —
provenance never manufactured; manifests reconcile only with exact
ancestry, verified refs and CAS attestation (crash-5: current pointer
stays old valid truth — no latest-wins); job durability divergence is
detected through the public gated read and the runtime gate refuses the
QUARANTINED transition, which is journaled UNRESOLVED (frozen
permission); checkpoint events are never mutated; job locks are never
auto-deleted (LOCK_PRESENT_OWNER_UNPROVEN; explicit operator clear
requires the exact expected job fingerprint and no in-process owner);
path-traversal and symlink escapes are rejected (typed), destinations
are hash-based — no raw logical id ever becomes a path component; no
quota engine, no DuckDB, no Postgres, no RawEvidenceQuery (I09+ scope).

| Commit | SHA | Content | Tests | Verdict |
|---|---|---|---|---|
| SENSOR-B4-I08A | `efde153e` | recovery findings vocabulary + append-only RecoveryAction journal + read-only deterministic scanner (`recovery.py`, `test_recovery.py`) | +24 storage | implementation |
| SENSOR-B4-I08B | `ae348941` | quarantine + explicit reconciliation actions + crash/idempotence/TOCTOU/path-safety proof (`test_recovery_crash_matrix.py`) | +21 storage | implementation |
| SENSOR-B4-I08C | (this commit) | freeze I08 machine evidence (4 matrices) + evidence MD + ledger truth (`test_i08_evidence.py`) | +4 storage (+1 skip on Windows) | evidence freeze; verdict PENDING_OPERATOR_REVIEW |

Machine evidence: BLOC_04_I08_RECOVERY_SCAN_MATRIX.json (11 cases),
BLOC_04_I08_QUARANTINE_MATRIX.json (9 cases: 8 OK + 1 SKIPPED_ON_WINDOWS
for the POSIX-only symlink attack), BLOC_04_I08_CRASH_MATRIX.json
(12/12 frozen scenarios), BLOC_04_I08_RECOVERY_IDEMPOTENCE_MATRIX.json
(6 cases) — generated in tmp by pure builders and compared
byte-for-byte against the committed files; normal pytest NEVER writes
the evidence tree; evidence tree clean at freeze.

All 12 frozen crash scenarios green (staging, orphan blob, orphan
projection, orphan manifest, missing manifest target, corrupted blob,
acquisition/quarantine dependency, job durability divergence, unproven
lock, refetch/revision semantics, concurrent CAS writers).

Final at the I08 tree: storage 1191 passed / 0 failed / 4 skipped;
full 2570 passed / 0 failed / 5 skipped (+49 over baseline, zero
failures).  Ruff clean on the complete changed scope; mypy: recovery.py
and the three new test modules fully clean with the source root
explicitly configured (I07R1G/I07R1H convention), the only error in
each run being the documented pre-existing probes/planner.py:79
baseline; network=0; provider source unchanged; historical I07 evidence
untouched; the documented legacy CRLF-churn files restored before
commit (zero content delta).

PASS_SENSOR_B4_I08_RECOVERY_QUARANTINE_SEALED =
PENDING_OPERATOR_REVIEW (proposed PASS after implementation).
RECOVERY_SCANNER_IMPLEMENTED = PENDING_OPERATOR_ACCEPTANCE.
recommended_next = SENSOR-B4-I09 QUOTA / STORAGE ESTIMATOR.
next_checkpoint_authorized = FALSE.  DURABLE_RESUME_IMPLEMENTED = TRUE.

**STOP GATE honored:** I09/I10/I11/I12/I13/I14/I15/I16/I17 NOT started;
research NOT resumed.

## SENSOR-B4-I08R1 - RECOVERY TRUTH HARDENING (effect atomicity + crash truth + lock authority + run identity)

Starting SHA 00898d666fa4a595af02321e1eedbf543717a455 (I08 head, clean tree,
lineage abcc1b40 RATIFY / efde153e I08A / ae348941 I08B / 00898d66 I08C
verified). Operator review found FOUR load-bearing defects (A: recovery
effects mutated durable truth before the RecoveryAction was durable; B: the
committed crash matrix did not faithfully instantiate several frozen
boundaries; C: clear_job_lock could delete without proving owner absence;
D: generated run ids derived from id(self)+counter) plus TWO hardening
seams (E: quarantine copies buffered whole files via read_bytes; F:
_scan_jobs labeled every exception JOB_DURABILITY_DIVERGENCE). All six
sealed in I08R1; no I08 architecture change; historical I08/I07 evidence
untouched.

DELIVERED in the preferred four-commit chain (no squash):

- b83d65ef SENSOR-B4-I08R1A: journal-first replayable effects + streamed quarantine.
  New RecoveryOperationJournal at catalogs/recovery/operations/ over the
  shared DurableJsonCatalog primitive: phases INTENT / EFFECT_COMMITTED /
  COMPLETED / UNRESOLVED; operation identity = SHA-256 over the canonical
  semantic set (run id, action kind, object, problem, resolution, before/
  after states) with registration time EXCLUDED; each phase its own
  append-only physical row (phase-qualified key, EFFECT rows detail-
  qualified because one operation may commit several effects); exact retry
  idempotent, divergent retry typed RecoveryActionConflict, rows never
  mutated in place. Every mutating handler resequences: revalidate (I08 28)
  -> durable INTENT -> irreversible effect -> EFFECT row -> COMPLETED/
  UNRESOLVED outcome -> frozen RecoveryAction; if INTENT publication fails
  nothing was mutated. apply_plan first FINALIZES open operations: a landed
  effect under an open operation is ADOPTED on restart (quarantine kinds by
  canonical-absence under a prior durable record; reconciliation kinds by
  exact committed metadata/acquisition/manifest), so a post-commit crash
  converges instead of becoming a false stale-plan conflict. Orphan-blob
  reconciliation is a replayable two-step operation (metadata EFFECT row ->
  acquisition EFFECT row -> COMPLETED) with a typed mid-reconciliation
  ORPHAN_BLOB_CONTINUATION scan finding that completes step 2 after a
  crash; metadata conflict/acquisition conflict stay typed. Manifest
  reconciliation: post-commit-crash retry recognizes the committed exact
  manifest (CAS + exact ancestry authoritative, no latest-wins).
  Quarantine copy: _quar_copy_stream - bounded 1 MiB chunks, SHA-256 in
  the same pass, staged file fsync, publish_no_replace, directory fsync,
  source unlinked ONLY after durable destination (parent fsync); exact
  retry adopts identical destination; different destination bytes typed
  RecoveryQuarantineConflict. Run ids: new_run_id = recovery-<uuid4.hex>
  (128 bits cryptographic; no id(self), no counter, no wall clock, no temp
  paths); explicit deterministic ids preserved for evidence runs.

- 906ae137 SENSOR-B4-I08R1B: true frozen crash boundaries. New authoritative
  BLOC_04_I08R1_CRASH_TRUTH_MATRIX.json (13 rows: frozen 1-12 + crash-2b)
  built by test_i08r1_crash_truth.py on the real stack with typed injected
  faults and fresh-repository restart probes. Crash 2 proven in BOTH
  branches (no context -> unknown_context quarantine; registered context
  -> replayable metadata+acquisition reconciliation, crash BETWEEN the two
  appends surfaces as a typed continuation finding and completes on
  retry). Crash 4 constructs a real CATALOGED projection (physical
  artifact + catalog row + T0A lineage) with NO manifest reference and
  proves a catalog row alone is NOT health (cataloged_yet_finding=True;
  record-only action; artifact never moved). Crash 5 publishes a VALID v2
  fragment (supersedes == durable v1, refs verify) before the pointer
  update, reconciled through the public CAS API; a separate invalid-
  ancestry case stays UNRESOLVED (no latest-wins). Crash 6 occurs BEFORE
  advance_checkpoint: job stays MANIFEST_COMMITTED with anchors
  (None, None); recovery neither advances the cursor nor mints anchors.
  Crash 7 uses the accepted I06 registry: same source identity + same
  exact bytes -> IDENTICAL_REFETCH (not blob-store dedupe). Crash 8 uses
  I06 SOURCE_MUTATION with genuinely DIFFERENT bytes (distinct sha) at a
  strictly later response_observed_at (I06 40: same-seen_at mutation
  fails closed) - the mutated acquisition is appended ONCE with final
  facts (I04 28 first-append-wins). Crash 9 keeps the corruption path and
  adds restart-convergent phases. Crash 10 adds the target-reappears
  stale-plan conflict (bytes restored to the ORIGINAL content sha - a
  mutated restore would be a different blob, not staleness). Crash 11
  reports the MEASURED contract gap: no public projection-invalidation API
  exists in src/ (asserted; test fails if an API appears, forcing a real
  INVALID_PARSER upgrade) - T0A retained, projection still cataloged,
  rebuildable, source never rewritten; no junk file disguised as parser
  invalidation. Crash 12: typed ManifestCASConflict for the CAS loser,
  exactly one winner, no silent branch. Historical honesty (I08R1 33):
  BLOC_04_I08_CRASH_MATRIX.json is untouched on disk but is now
  documented as a first-pass approximation - several rows (4, 5, 6, 7, 8,
  11) did not instantiate the frozen boundary and must not be read as
  12/12 authoritative after I08R1.

- 077494be SENSOR-B4-I08R1C: lock-clear authority, run identity, typed job scan.
  clear_job_lock owner repository is MANDATORY (omission = TypeError,
  None or owner without _lock_owners truth = typed
  RecoveryConfigurationError; fingerprint mismatch refused; live owner
  record refused; same-thread RLock reentrancy CANNOT bypass the owner-map
  check - probe-alone is insufficient because the owning thread can always
  re-acquire an RLock; unowned matching lock succeeds with RecoveryAction
  + INTENT journaled BEFORE the unlink). apply_plan never clears locks; no
  TTL; no process-death inference; foreign locks never auto-deleted
  (scan/apply record lock_present=True, cleared=False). _scan_jobs catches
  ONLY typed job failures: JobLockHeld (healthy-writer contention) is
  skipped and the physical lock classifies separately; genuine durable-
  chain failures classify JOB_DURABILITY_DIVERGENCE; unexpected I/O or
  programming errors PROPAGATE (never mislabeled). Proven: healthy job +
  held lock -> no divergence finding; forged chain -> divergence finding;
  injected OSError -> propagates typed.

- SENSOR-B4-I08R1D: evidence freeze + ledger. Four deterministic matrices
  (BLOC_04_I08R1_EFFECT_ATOMICITY_MATRIX.json 8 cases,
  BLOC_04_I08R1_CRASH_TRUTH_MATRIX.json 13 cases,
  BLOC_04_I08R1_LOCK_RUN_ID_MATRIX.json 7 cases,
  BLOC_04_I08R1_STREAMING_QUARANTINE_MATRIX.json 6 cases - all cases OK,
  byte-stable regeneration under test_generated_matches_committed), the
  chronological evidence MD
  BLOC_04_I08R1_RECOVERY_TRUTH_ATOMICITY_EVIDENCE.md, and this ledger row.

Evidence governance: builders pure; normal pytest generates to tmp and
byte-compares; pytest never writes the committed evidence tree; the
documented legacy CRLF-churn evidence files were restored after the final
suites (zero content delta).

Fresh baseline at 00898d66 (measured): storage 1191/0/4, full 2570/0/5.
Final recorded runs at the I08R1 tree: storage 1235 passed / 0 failed /
4 skipped (+44); full 2614 passed / 0 failed / 5 skipped (+44); zero
failures; the documented unrelated blob-store concurrency flake did not
reproduce. Ruff: All checks passed! on the full changed scope. Mypy:
production recovery.py carries ONLY the documented pre-existing
probes/planner.py:79 baseline; the three new test modules (source root
configured via MYPYPATH + --explicit-package-bases, the established
convention) carry the same method-assign class as the pre-existing
injected-fault tests and no import-not-found/arg-type residue - tests are
not part of a repo mypy gate policy (no [tool.mypy] exists); stated
precisely, not claimed clean. network=0; provider source unchanged; no
I09; no quota; no DuckDB; no Postgres; no RawEvidenceQuery; research NOT
resumed.

PASS_SENSOR_B4_I08R1_CRASH_TRUTH_EFFECT_ATOMICITY_LOCK_AUTHORITY_SEALED =
PENDING_OPERATOR_REVIEW (proposed PASS; NOT self-ratified).
PASS_SENSOR_B4_I08_RECOVERY_QUARANTINE_SEALED = OPERATOR_HOLD.
RECOVERY_SCANNER_IMPLEMENTED = PENDING_OPERATOR_ACCEPTANCE.
recommended_next = SENSOR-B4-I09 QUOTA / STORAGE ESTIMATOR.
next_checkpoint_authorized = FALSE.  DURABLE_RESUME_IMPLEMENTED = TRUE.

**STOP GATE honored:** I09/I10/I11/I12/I13/I14/I15/I16/I17 NOT started;
research NOT resumed.

## SENSOR-B4-I08R2 - RECOVERY OPERATION TERMINALITY + FINAL-EVIDENCE CONSISTENCY

Prompt: `SENSOR-B4-I08R2`, mandatory start
`3e6d86142c1bbf26f6dfc8732a6961f255f2a3bc` on
`agent/crypto-sensor-fabric-build`; main remains on its separate lineage.
The operator found that the I08R1 advisory finalizer did not finalize an
interrupted landed operation. The immutable I08R1 effect-atomicity matrix
proves the historical false-green (`operation_completed=false` and
`completed_operations=0` while result=`OK`); I08R2 preserves those bytes and
repairs semantics prospectively.

| Commit | SHA | Content | Verdict |
|---|---|---|---|
| SENSOR-B4-I08R2A | `79f48d07` | One authoritative `_replay_open_operations` consumes durable replay work under the ORIGINAL operation/run; canonical operation-record validation; full SHA-256 effect keys; all-fields exact retry; terminal rows name the final action; I08R1 false-green matrix frozen as historical evidence | implementation |
| SENSOR-B4-I08R2B | `4b53fffc` | Real crash ordering for quarantine/terminal reconciliation; action-without-terminal adopts the exact action; lock clear uses INTENT -> immediate live owner revalidation -> unlink/fsync -> EFFECT -> action -> COMPLETED and replays the original run | implementation |
| SENSOR-B4-I08R2C | `df5754b8` | Three byte-stable executable matrices: terminality 15, record integrity tamper 14, lock-clear atomicity 9; all OK; immutable I08R1 counterfactual cited; historical I07R1I ledger matrix decoupled from the live ledger | evidence |
| SENSOR-B4-I08R2D | (this commit) | Evidence MD freeze + chronological ledger reconciliation | proposed evidence seal |

Implementation: open operations are grouped by original `operation_id`; every
row is canonically validated; operation identity is recomputed from semantic
payload; phase-qualified ids are checked; malformed/tampered/unknown-schema
records fail closed. Landed quarantine/orphan/manifest/job/lock effects are
recognized from the INTENT fingerprint plus current storage truth, never from
a possibly absent RecoveryAction. Replay appends/adopts EFFECT as needed,
adopts one existing final action when only the terminal phase was lost,
otherwise writes one final action, then appends COMPLETED under the original
`recovery_run_id`. Source+destination both absent never completes; a different
destination conflicts. Orphan manifest pointer-unreadable refusals retain a
pre-effect INTENT. Contradictory terminals, effect-without-intent,
terminal-without-action, action ownership mismatch, ambiguous actions, and
truncated effect keys are typed corruption.

Explicit lock clear never auto-runs. It validates fingerprint and owner
authority, writes INTENT, revalidates owner map and RLock immediately before
unlink, unlinks/fsyncs, then records EFFECT, the actual-after-state action,
and COMPLETED. Restart recognizes the effect only from exact INTENT path +
fingerprint + expected job id. Repeated restart is stable.

Machine evidence: `BLOC_04_I08R2_OPERATION_TERMINALITY_MATRIX.json` 15/15 OK;
`BLOC_04_I08R2_OPERATION_RECORD_INTEGRITY_MATRIX.json` 14/14 tamper shapes
fail closed; `BLOC_04_I08R2_LOCK_CLEAR_ATOMICITY_MATRIX.json` 9/9 OK. The
byte-stable evidence tree is read-only under pytest. The I07R1I ledger matrix
is frozen to the normalized fd961604 Current-state section SHA-256
`412da2f97b5d9627101e35ad6ebd68be6bd4aa1e8b643cc4400858feb26cb824`, so a
chronological live ledger no longer falsifies historical evidence. Historical
I08R1 effect-atomicity bytes remain untouched.

Verification: storage **1246 passed / 0 failed / 4 skipped** (two existing
Windows manifest-visibility warnings; test passed); complete project test root
**2625 passed / 0 failed / 5 skipped**; focused I08R2 11 passed; ledger repair
3 passed. Ruff clean. Mypy: only the pre-existing
`src/crypto_sensor_fabric/probes/planner.py:79 [call-overload]` dependency
error, no new recovery.py error. Unscoped repository-root pytest is not a
valid gate because an existing research script invokes `sys.exit(0)` during
import (91 passed / 0 failed before collection stopped); the project gate is
`pytest tests/ -q`. The seven known pre-I05-era evidence files showed CRLF-only
churn and were restored. No external CI success claimed. network=0; provider
source unchanged.

`PASS_SENSOR_B4_I08R2_OPERATION_TERMINALITY_EVIDENCE_CONSISTENCY_SEALED =
PENDING_OPERATOR_REVIEW` (proposed; not self-ratified).
`PASS_SENSOR_B4_I08R1_CRASH_TRUTH_EFFECT_ATOMICITY_LOCK_AUTHORITY_SEALED =
PENDING_OPERATOR_REVIEW`.
`PASS_SENSOR_B4_I08_RECOVERY_QUARANTINE_SEALED = OPERATOR_HOLD`.
`RECOVERY_SCANNER_IMPLEMENTED = PENDING_OPERATOR_ACCEPTANCE`.
`DURABLE_RESUME_IMPLEMENTED = TRUE`; `next_checkpoint_authorized = FALSE`;
recommended next after acceptance is SENSOR-B4-I09 QUOTA / STORAGE ESTIMATOR.

**STOP GATE honored:** I09 quota/storage estimator, DuckDB, Postgres,
RawEvidenceQuery, provider integration, quota thresholds, and research were
NOT started. I09 remains NOT authorized.

## SENSOR-B4-I08R2R1 - EVIDENCE TRUTH + LOCK-CLEAR RACE + CANONICAL RECORD MICROSEAL

Mandatory start: `cc97de4709407cad2d3204db6e184c42254b13fe` on
`agent/crypto-sensor-fabric-build`; main remains unchanged at
`7c7816f382947bbc8a1f2154435fc436f2428fa8`.

| Commit | SHA | Content | Verdict |
|---|---|---|---|
| SENSOR-B4-I08R2R1A | `d0b0360e` | Repair evidence truth derivation; use `last_replay_report`; isolate open operations with an empty plan; required-invariant evaluator plus forced-false counterfactual | implementation/evidence |
| SENSOR-B4-I08R2R1B | `79469d4e` | Hold per-job RLock continuously through final validation, unlink, and fsync; canonical zero-offset UTC; typed malformed state; exact operation/action outcome binding | implementation |
| SENSOR-B4-I08R2R1C | `3ee122ab` | Publish deterministic evidence-truth (5), lock-race (3), and canonical-record (7) matrices; prove 11 historical I08/I08R1/I08R2 matrix hashes unchanged | evidence |
| SENSOR-B4-I08R2R1D | (this commit) | Microseal narrative, governance reconciliation, final gates, push | proposed seal |

The two immutable I08R2 false-green rows remain historical evidence:
`crash_after_unlink_replays_original` had `replay_closed=false` with `OK`,
and `present_lock_intent_not_false_completed` had `no_action=false` and
`report_left_open=false` with `OK`. R2R1 repairs the executable builders and
publishes new matrices rather than rewriting those bytes.

R2R1 matrix rows: evidence truth 5 (4 `OK`, one deliberate counterfactual
`FAIL`); lock-clear race 3/3 `OK`; canonical record 7/7 `OK`. Every committed
row is re-evaluated from explicit `required_invariants` under pytest. The
successful clear order is `INTENT -> UNLINK -> FSYNC -> EFFECT ->
RecoveryAction -> COMPLETED`; a separate contender cannot acquire the job
authority at the unlink or fsync boundary.

Final local gates: focused R2R1 17 passed; I08R2/I08R1/I07 focused regression
66 passed; storage 1263 passed / 0 failed / 4 skipped; final
`pytest tests/ -q` 2642 passed / 0 failed / 5 skipped. An initial full run
reproduced the documented unrelated blob-store concurrency flake (2641 pass,
1 fail, 5 skip); the isolated test passed on rerun and the final full run was
green. Ruff and compileall passed. Mypy reports only the pre-existing
`src/crypto_sensor_fabric/probes/planner.py:79 [call-overload]` dependency
error, with no new `recovery.py` error. Unscoped root pytest remains invalid
because research import executes `sys.exit(0)`; no root-level pass is claimed.
Provider source diff = 0; I09/quota/storage-estimator diff = 0; network = 0.
The seven known CRLF-churn evidence files were restored.

`PASS_SENSOR_B4_I08R2R1_EVIDENCE_TRUTH_LOCK_RACE_CANONICAL_SEALED =
PENDING_OPERATOR_REVIEW` (proposed; not self-ratified).
`PASS_SENSOR_B4_I08R2_OPERATION_TERMINALITY_EVIDENCE_CONSISTENCY_SEALED =
OPERATOR_HOLD`.
`PASS_SENSOR_B4_I08R1_CRASH_TRUTH_EFFECT_ATOMICITY_LOCK_AUTHORITY_SEALED =
OPERATOR_HOLD`.
`PASS_SENSOR_B4_I08_RECOVERY_QUARANTINE_SEALED = OPERATOR_HOLD`.
`RECOVERY_SCANNER_IMPLEMENTED = PENDING_OPERATOR_ACCEPTANCE`.
`DURABLE_RESUME_IMPLEMENTED = TRUE`; `next_checkpoint_authorized = FALSE`.
Recommended next: operator review of the complete I08 -> I08R1 -> I08R2 ->
I08R2R1 chain. I09 may begin only after explicit operator acceptance.

**STOP after push. I09 was not begun.**

## SENSOR-B4-I08R2R1-RATIFY — COMPLETE RECOVERY CHAIN OPERATOR ACCEPTANCE

Mandatory start: `311fd52b75298e181d5c20f796bff130e8b16770` on
`agent/crypto-sensor-fabric-build`; main remains unchanged at
`7c7816f382947bbc8a1f2154435fc436f2428fa8`.

The operator accepts the complete technical chain: I08 recovery/quarantine,
I08R1 effect atomicity and lock authority, I08R2 operation terminality, and
I08R2R1 evidence truth/lock-race/canonical-record closure. Acceptance applies
to the superseding live implementation and its new evidence. Historical
false-green I08/I08R1/I08R2 matrices remain immutable counterfactuals; no
historical matrix was regenerated or rewritten.

| Accepted stage | Freeze / ratification SHA | State |
|---|---|---|
| I08 | `00898d66` | `PASS_SENSOR_B4_I08_RECOVERY_QUARANTINE_SEALED = OPERATOR_ACCEPTED` |
| I08R1 | `3e6d8614` | `PASS_SENSOR_B4_I08R1_CRASH_TRUTH_EFFECT_ATOMICITY_LOCK_AUTHORITY_SEALED = OPERATOR_ACCEPTED` |
| I08R2 | `cc97de47` | `PASS_SENSOR_B4_I08R2_OPERATION_TERMINALITY_EVIDENCE_CONSISTENCY_SEALED = OPERATOR_ACCEPTED` |
| I08R2R1 | `311fd52b` | `PASS_SENSOR_B4_I08R2R1_EVIDENCE_TRUTH_LOCK_RACE_CANONICAL_SEALED = OPERATOR_ACCEPTED` |
| I08R2R1-DOC | `a349d874` | Lock-clear docstring aligned to sealed INTENT -> unlink/fsync -> EFFECT -> action -> terminal ordering |

Governance transition:

- `RECOVERY_SCANNER_IMPLEMENTED = TRUE`
- `DURABLE_RESUME_IMPLEMENTED = TRUE`
- `G4-02_ATOMIC_DURABILITY_GATE = IMPLEMENTATION_PASS`
- `next_checkpoint_authorized = TRUE`
- `next_checkpoint = SENSOR-B4-I09 QUOTA / STORAGE ESTIMATOR`
- `authorized_scope = I09 ONLY`
- I10+ remain unauthorized; research remains frozen.

Ratification gate results: focused recovery/resume gate **54 passed**;
storage **1263 passed / 0 failed / 4 skipped**; project `pytest tests/ -q`
**2642 passed / 0 failed / 5 skipped**. The existing Windows manifest
visibility warning was recorded as a warning, not a failure. Ruff on the
changed recovery scope passed; py_compile/compileall passed. Mypy reports only
the pre-existing `src/crypto_sensor_fabric/probes/planner.py:79 [call-overload]`
dependency error. Historical hash gates passed. Provider-source diff and
I09/quota/storage-estimator diff from `311fd52b` are zero; network = 0.

This is a governance-only ratification checkpoint. I09 was not begun in this
prompt; its authorization begins only after this commit is pushed.

## SENSOR-B4-I09 - QUOTA / STORAGE ESTIMATOR

Mandatory start: `0fcf0d954295cfd9bb07649f819e44e59ea76cc9` on
`agent/crypto-sensor-fabric-build`; remote main remains
`7c7816f382947bbc8a1f2154435fc436f2428fa8`.

| Commit | Content | Verdict |
|---|---|---|
| `9da63026` | SENSOR-B4-I09A: config-driven quota classification, integer watermarks, hard absolute floor, typed side-effect-free write decisions | implementation |
| `8b4a5065` | SENSOR-B4-I09B: integer-byte estimator, coverage confidence labels, U0/U1/U2 policy, T0A non-deletion | implementation |
| `f3bdfdcc` | SENSOR-B4-I09C: adversarial matrices, required-invariant evaluator, deliberate counterfactuals, deterministic byte comparison | evidence builders/tests |
| `632cc339` | SENSOR-B4-I09C-R1: repair priority evidence to derive verdicts from measured booleans | repair |
| `054f5b64` | SENSOR-B4-I09C-R2: align watermark invariant name and floor scenario inputs | repair |
| `a2588179` | SENSOR-B4-I09C-R3: target exactly-floor and one-byte-below boundary | repair |
| `457f596e` | SENSOR-B4-I09B-R1: reject configuration that enables automatic T0A destruction | safety repair |
| D (this commit) | Publish five deterministic JSON artifacts, evidence narrative, and governance reconciliation | proposed seal |

Frozen `StorageQuotaState`, `DiskPressure`, `StoragePriority`, and `SensorFamily`
are reused. Watermarks remain config-driven: `<70% NORMAL`, `>=70% WATCH`,
`>=85% CONSTRAINED`, `>=95% CRITICAL`, with equality in the higher state.
A write is safe iff `free - projected >= absolute_free_floor_bytes`; exactly at
the floor is allowed, one byte below blocks, and P0 has no bypass. P2 defers and
P3 pauses under constrained pressure; all non-essential writes block at
critical pressure; actual filesystem safety always wins.

The estimator uses separate integer ceiling division for raw and projection
components, then exact total reconciliation. Confidence is an evidence-coverage
label based on measured sample duration and empty samples, not an invented
statistical interval. U2 full-depth books remain off by default and no storage
policy changes evidence semantics. T0A is never automatically destroyed; an
unsafe config override is rejected.

Machine evidence: watermark 7/7 OK; priority pause 14 OK plus one deliberate
FAIL; estimator 7 OK plus one deliberate FAIL; non-destructive retention 9/9 OK;
quota simulation contains six side-effect-free scenarios. Every measured row
declares `required_invariants`, and `OK` iff all named predicates are boolean
true. Normal pytest regenerates and byte-compares without writing committed
evidence.

Final local gates: focused I09 52 passed; required I07/I08 regression slice 241
passed / 1 skipped; storage 1315 passed / 4 skipped / one known Windows
pointer-visibility warning; complete project `pytest tests/ -q --maxfail=1`
2694 passed / 5 skipped. Ruff and compileall passed. Mypy reports only the
pre-existing `src/crypto_sensor_fabric/probes/planner.py:79 [call-overload]`
dependency error and no I09 error. Historical I08 hash/read-only gates passed.
Provider source diff = 0; I10 DuckDB, I11 PostgreSQL, and I12 RawEvidenceQuery
implementation diffs = 0; network = 0. Seven known CRLF-only evidence files were
restored. Unscoped root pytest is not claimed because of the known research
`sys.exit(0)` import.

`PASS_SENSOR_B4_I09_QUOTA_STORAGE_ESTIMATOR_SEALED = PENDING_OPERATOR_REVIEW`.
`G4-08_STORAGE_PRESSURE_GATE = IMPLEMENTATION_PASS_PENDING_OPERATOR_REVIEW`.
`next_checkpoint_authorized = FALSE`; `recommended_next = OPERATOR REVIEW OF
SENSOR-B4-I09`. I10 remains unauthorized and research remains frozen.

## SENSOR-B4-I09R1 - EVIDENCE TRUTH + QUOTA ADMISSION + FAIL-CLOSED POLICY MICROSEAL

Mandatory start: `71ccb0c7fbd110edf6d431140009254f90c37722` on
`agent/crypto-sensor-fabric-build`; remote main remains
`7c7816f382947bbc8a1f2154435fc436f2428fa8`.

| Commit | Content | Verdict |
|---|---|---|
| `683f5d7a` | SENSOR-B4-I09R1A: remove essential bypass; reconcile and rederive untrusted quota state | repair |
| `fa38e779` | SENSOR-B4-I09R1B: explicit estimate admission; strict retention boolean and schema types | repair |
| `ed2a7569` | SENSOR-B4-I09R1A-R1: require explicit config and matching floor authority | repair |
| `fe7cd0d3` | SENSOR-B4-I09R1C: adversarial tests and deterministic required-invariant builders | evidence builders/tests |
| `ec1eff5f` | SENSOR-B4-I09R1B-R1: require explicit admission config authority | repair |
| D (this commit) | Publish four R1 matrices, microseal, and operator-hold reconciliation | proposed seal |

The historical I09 quota simulation incorrectly named a row
`floor_breach_p0_blocked` although it left 8,000 bytes free against a 20-byte
floor and therefore correctly returned `PROCEED`. Its bytes remain immutable.
R1 publishes a real exactly-at-floor permitted case and a real one-byte-below
blocked case. The old test skipped simulation truth; every R1 row now declares
`required_invariants` and derives `OK` iff all are boolean true. The deliberate
`counterfactual_one_byte_below_floor_permitted` row is `FAIL`.

Pre-repair, non-P0 `essential=True` converted CRITICAL to `WARN`, and a forged
NORMAL state at 95% bytes incorrectly returned `PROCEED` for P2. R1 removes the
caller flag entirely, requires explicit `QuotaConfig`, reconciles byte facts,
rederives pressure under that config, and rejects stale/forged pressure,
ratio, capacity, or floor truth. P0 alone continues at CRITICAL while
floor-safe; P1/P2/P3 block.

R1 adds a pure admission boundary. Over-budget plans block before execution;
budget-safe plans pass their full estimate through the same quota/floor policy.
Constrained P2 defers, constrained P3 pauses, critical P1/P2/P3 block, and P0
cannot bypass the floor. Retention config now requires exact booleans and an
exact nonempty string schema version; no string or numeric coercion is allowed.
T0A refusal is measured independently for P0/P1/P2/P3 including P3+T0A.
`HIGH` remains only a >=24-hour duration label, not a calibrated probability,
confidence interval, or proof of representative activity.

R1 evidence: simulation truth 9 rows (8 OK, one deliberate FAIL); priority
authority 14/14 OK; backfill admission 9/9 OK; retention config safety 23/23 OK.
All six historical I09 evidence hashes remain unchanged. Historical I08
hash/read-only gates pass.

Final gates: focused I09 + I09R1 126 passed; required I07/I08 regression slice
241 passed / 1 skipped; storage 1389 passed / 4 skipped; project
`pytest tests/ -q` 2768 passed / 5 skipped. Ruff, py_compile, and compileall
passed. Mypy has no I09/I09R1 error and reports only the pre-existing
`src/crypto_sensor_fabric/probes/planner.py:79 [call-overload]` dependency
error. Provider, frozen-contract, I10 DuckDB, I11 PostgreSQL, and I12
RawEvidenceQuery diffs are zero; product/test network calls are zero. Seven
known CRLF-only evidence files were restored. Unscoped root pytest is not
claimed because of the known research `sys.exit(0)` import.

`PASS_SENSOR_B4_I09_QUOTA_STORAGE_ESTIMATOR_SEALED = OPERATOR_HOLD`.
`PASS_SENSOR_B4_I09R1_EVIDENCE_TRUTH_ADMISSION_POLICY_SEALED =
PENDING_OPERATOR_REVIEW`.
`G4-08_STORAGE_PRESSURE_GATE = IMPLEMENTATION_PASS_PENDING_OPERATOR_REVIEW`.
`next_checkpoint_authorized = FALSE`; `recommended_next = OPERATOR REVIEW OF
COMPLETE I09 -> I09R1 CHAIN`. I10 and I11+ remain unauthorized; research remains
frozen.

## SENSOR-B4-I09R1-RATIFY — COMPLETE QUOTA / STORAGE-PRESSURE CHAIN ACCEPTANCE

Mandatory start: `0dc51fb39a492542b13536c333d1886b7f6ae2ee` on
`agent/crypto-sensor-fabric-build`; remote main remains
`7c7816f382947bbc8a1f2154435fc436f2428fa8`.

The operator accepts the complete technical chain SENSOR-B4-I09 ->
SENSOR-B4-I09R1. Acceptance applies to the superseding implementation and R1
evidence. The original I09 quota-simulation mislabel remains immutable
historical counterevidence and was not rewritten. The R1 chronology-only
documentation correction is recorded separately as `b2665897`.

Ratification truth: `<70% NORMAL`, `>=70% WATCH`, `>=85% CONSTRAINED`, and
`>=95% CRITICAL`, with equality in the higher state. A write is safe only when
`free - projected >= absolute_free_floor_bytes`; exactly at the floor is
allowed, one byte below blocks with `STORAGE_CAPACITY_BLOCKED`, and no priority
bypasses it. NORMAL proceeds for floor-safe P0/P1/P2/P3; WATCH warns;
CONSTRAINED proceeds P0/P1, defers P2, and pauses P3; CRITICAL warns only for
floor-safe P0 and blocks P1/P2/P3.

Caller-controlled `essential` authority is removed. Public safe-write decisions
require explicit config, reconcile bytes, check utilization, rederive pressure,
and reject stale pressure or mismatched floor authority. Oversized planned work
blocks before execution. Automatic destructive T0A retention remains forbidden
for every priority including P3+T0A. `HIGH` confidence means >=24-hour sample
duration coverage only, not calibrated probability, a statistical interval, or
proof of representative activity.

Final gates: focused I09 + I09R1 126 passed; required I07/I08 regression slice
241 passed / 1 skipped; storage 1389 passed / 4 skipped; project
`pytest tests/ -q` 2768 passed / 5 skipped. Ruff and compile checks passed.
Mypy reports only the pre-existing
`src/crypto_sensor_fabric/probes/planner.py:79 [call-overload]` dependency
error and no I09/I09R1 error. Historical I08 and historical I09 six-file hash
gates passed. All four R1 matrices regenerate byte-identically and every row
satisfies required-invariant truth. Provider, I10, I11, I12, and frozen-contract
implementation diffs are zero; product/test network calls are zero.

`PASS_SENSOR_B4_I09_QUOTA_STORAGE_ESTIMATOR_SEALED = OPERATOR_ACCEPTED`.
`PASS_SENSOR_B4_I09R1_EVIDENCE_TRUTH_ADMISSION_POLICY_SEALED =
OPERATOR_ACCEPTED`.
`G4-08_STORAGE_PRESSURE_GATE = IMPLEMENTATION_PASS`.
`next_checkpoint_authorized = TRUE`; `next_checkpoint = SENSOR-B4-I10 DUCKDB
DISCOVERY CATALOG`; `authorized_scope = I10 ONLY`. I11+ remain unauthorized;
research remains frozen. I10 implementation did not begin in this ratification
checkpoint.
## SENSOR-B4-I11 — POSTGRESQL OPERATIONAL METADATA REPOSITORY (BLOCKED RUNTIME)

I11 implementation adds the fixed `crypto_sensor_fabric_ops` PostgreSQL metadata
boundary, the direct `psycopg[binary] >=3.2,<4` dependency, public-source
reconstruction adapters, raw/secret firewalls, deterministic canonical rows,
transaction rollback/advisory-lock code, offline tests, and five append-only
matrices. No I12 or research work was started.

Runtime validation is blocked by the environment: no PostgreSQL server binaries,
Docker runtime, WSL distro, local listener, or `SENSOR_POSTGRES_TEST_DSN` were
available. The two real integration tests therefore skipped. The evidence pack
records `POSTGRES_RUNTIME_VALIDATION=BLOCKED_ENVIRONMENT` and does not claim
a G4-10 implementation pass.

- `PASS_SENSOR_B4_I11_POSTGRES_OPERATIONAL_METADATA_SEALED=BLOCKED_RUNTIME_VALIDATION`
- `G4-10_OPERATIONAL_METADATA_GATE=PENDING_REAL_POSTGRES_RUNTIME`
- `dependency_resolution_network=YES` (psycopg 3.3.6 and psycopg-binary resolved/downloaded)
- `product/provider/test external network=ZERO`
- `local PostgreSQL loopback traffic=ZERO`
- `next_checkpoint_authorized=FALSE`
- `recommended_next=SUPPLY REAL LOCAL POSTGRESQL RUNTIME AND OPERATOR REVIEW`
- I12+ remain unauthorized; research remains frozen.

Evidence artifacts are under `evidence/bloc_04/`:
`BLOC_04_I11_POSTGRES_SCHEMA_MATRIX.json`,
`BLOC_04_I11_RECONSTRUCTION_MATRIX.json`,
`BLOC_04_I11_AUTHORITY_FIREWALL_MATRIX.json`,
`BLOC_04_I11_TRANSACTION_ATOMICITY_MATRIX.json`,
`BLOC_04_I11_RUNTIME_INTEGRATION_MATRIX.json`, and
`BLOC_04_I11_POSTGRES_OPERATIONAL_METADATA_EVIDENCE.md`.

## SENSOR-B4-I11R1 - POSTGRES RUNTIME TRUTH + SCHEMA / OPERATIONAL API CORRECTNESS MICROSEAL

Six operator-reported I11 defects were reproduced against a real PostgreSQL
16.15 runtime before any repair, then fixed:

- **A** the forbidden-column vocabulary contained `token`, so every acquisition
  row self-refused because the contract also declared `resume_token_before` /
  `resume_token_after`. Both columns are removed from the PostgreSQL
  acquisitions DDL and row contract. PostgreSQL is not the I07 resume
  authority; the frozen `AcquisitionRecord` is unchanged.
- **B** `canonical_rows` built its `ORDER BY` by character-joining an already
  rendered SQL string. Replaced with an explicit per-table `CANONICAL_ORDER`
  sort-key map.
- **C** the generic operational writer used `ON CONFLICT (singleton)` for every
  operational table, which cannot work for `integrity_checks` (primary key
  `check_id`, no singleton column). Replaced with `record_integrity_check`
  (idempotent by `check_id`, divergent same-id raises `PostgresConflict`),
  `set_quota_state`, and `set_backup_state`.
- **D** acquisition DDL mapped almost every non-time field to `text`.
  `TABLE_SCHEMAS` is now the single authority for DDL, insert order, nullability,
  primary keys, foreign keys, introspection and tests. `provider_checksum_verified`
  is `boolean`; temporal fields are `timestamptz`.
- **E** `install_schema` used `CREATE ... IF NOT EXISTS` without proving the
  installed structure. `validate_installed_schema()` now proves the exact table
  set, column order/types/nullability, PK shape, the single
  `storage_job_transitions.job_id -> storage_jobs.job_id` foreign key, and
  exactly one `schema_metadata` row with the exact version/role. It fails
  closed; there is no auto-migration and no DROP of unexpected user state.
- **F** one substring tuple conflated column vocabulary with value detection.
  Split into `_FORBIDDEN_COLUMN_TERMS` (payload/body/content/raw/trade_row/
  book_level/market_row/event_array/bytea), `_SECRET_COLUMN_TERMS`
  (password/cookie/authorization/api_key/apikey/secret), and `_SECRET_VALUE_RE`.

Reconstruction completeness is an explicit caller contract: `MetadataInventory`
requires `complete=True` and the complete id/key set. Readiness import reuses
the accepted `providers.readiness.load_human_readiness_matrix` loader and
provider registry import reuses the accepted `registry.provider_registry`
loader, so there is no duplicate parser ontology. No accepted I04/I05/I06/I07/
I08/I09/I10 module was modified.

### Measured against real PostgreSQL 16.15

- focused I11 + I11R1 tests: **38 passed** (real DSN, loopback `127.0.0.1:55432`)
- storage suite: **1502 passed, 4 skipped, 2 failed**
- project suite outside storage: **1379 passed, 1 skipped, 0 failed**
- exact schema: 13 tables (`schema_metadata` + 12 frozen I11 tables), 12
  canonical sort-key entries; 8 parametrized schema attacks refused
- populated reconstruction: 18 rows across 9 reconstructible tables
  (2 provider_registry, 2 adapter_readiness, 2 blobs_current_metadata,
  2 acquisitions, 2 storage_jobs, 3 storage_job_transitions,
  2 partition_manifest_current, 2 source_revisions, 1 recovery_runs)
- drop/reinstall/rebuild parity exact; repeated refresh idempotent
- zero `LocalBlobStore.verify_blob` / `open_blob` / `_decode_stats` calls
- failed refresh rolls back; concurrent refresh serialized on a
  transaction-scoped advisory lock with no committed hybrid snapshot
- I07, I08 and I09 tamper firewalls hold; operational-only state preserved
- Ruff: at the accepted baseline (only the pre-existing I08 `F401`/`F811`)
- mypy: **15 pre-existing errors only**, unchanged

### Section 23 CRLF diagnostic (verified, not assumed)

The prior 59-failure attribution was proven rather than accepted. The
machine-wide `core.autocrlf=true` comes from `C:/Program Files/Git/etc/gitconfig`,
not from this repository, and it rewrote **3236** committed LF blobs to CRLF in
the worktree at checkout. Evidence builders emit LF, so byte comparison against
CRLF worktree files failed. This worktree is now `core.autocrlf=false`
(worktree-scoped) and all 3236 files are byte-identical to their committed
blobs; **no committed byte was rewritten** and `git diff --cached` stayed empty.

A separate pre-existing mutation remains: `test_catalog_evidence.py` and
`test_i04r1_evidence.py` write seven `BLOC_04_I0*` evidence files with
`Path.write_text`, which translates LF to CRLF on Windows, so those files are
re-CRLF'd on every test run. Their content is unchanged modulo line endings and
no test asserts on their bytes. Fixing an accepted I04 test is outside the
I11R1 scope.

### The two remaining failures are NOT I11R1 regressions

`test_i10r2_evidence.py::test_i10r2_evidence_is_measured_and_committed` and
`test_job_state_r1i.py::test_ledger_operator_state_is_truthful` both assert
against the top-level `## Current state` ledger table. The I11 commit
`09fc62f6` rewrote that table and dropped the anchor text they require. Both
test files and the ledger are byte-identical to `09fc62f6`, so I11R1 did not
cause this. At `7f4e753b` the Current state row carried explicitly labelled
*historical, superseded* proposal snapshots next to the live verdict, which is
what satisfied both tests. Restoring that text, or relaxing the two accepted
frozen tests, is an operator decision and was not taken unilaterally.

Because the full regression suite is not green, the G4-10 success law is NOT
satisfied and the gate is not claimed.

- `PASS_SENSOR_B4_I11R1_RUNTIME_CORRECTNESS_SEALED=PENDING_OPERATOR_REVIEW`
- `G4-10_OPERATIONAL_METADATA_GATE=NOT_PASSED_REGRESSION_BLOCKED`
- `PASS_SENSOR_B4_I11_POSTGRES_OPERATIONAL_METADATA_SEALED=BLOCKED_RUNTIME_VALIDATION` (unchanged)
- `next_checkpoint_authorized=FALSE`
- `recommended_next=OPERATOR REVIEW OF COMPLETE I11 -> I11R1 CHAIN AND A DECISION ON THE TWO PRE-EXISTING GOVERNANCE-LEDGER TEST FAILURES`
- I12+ remain unauthorized; research remains frozen. No self-ratification.

Runtime truth: PostgreSQL 16.15 on loopback `127.0.0.1:55432`;
`postgres_runtime_provision_network=YES` (official package acquisition only);
`dependency_resolution_network=NO`; provider/product network `ZERO`;
cloud databases and provider APIs were not contacted. No credentials were
persisted into Git; the disposable cluster was destroyed.

New R1 evidence under `evidence/bloc_04/`: `BLOC_04_I11R1_SCHEMA_RUNTIME_MATRIX.json`
(5 rows), `BLOC_04_I11R1_POPULATED_RECONSTRUCTION_MATRIX.json` (5),
`BLOC_04_I11R1_AUTHORITY_FIREWALL_MATRIX.json` (3),
`BLOC_04_I11R1_TRANSACTION_CONCURRENCY_MATRIX.json` (3),
`BLOC_04_I11R1_OPERATIONAL_STATE_MATRIX.json` (5),
`BLOC_04_I11R1_EVIDENCE_TRUTH_MATRIX.json` (3), and
`BLOC_04_I11R1_POSTGRES_RUNTIME_MICROSEAL.md`. Every non-counterfactual row is
measured `OK`; every `counterfactual_*` row is synthetic `FAIL`. The six
original I11 blocked-runtime artifacts are byte-unchanged.
## SENSOR-B4-I11R2 - HISTORICAL GOVERNANCE TEST DECOUPLING + GREEN REGRESSION CLOSURE

Prompt: `SENSOR-B4-I11R2`, starting at
`ccc6a7264fcf5ff560777c9c9a685f1877746987` on
`agent/crypto-sensor-fabric-build`.  I12+ unauthorized; research frozen.

Accepted operator finding: the two remaining failures are governance-TEST
architecture failures, not PostgreSQL implementation failures.  Two accepted
historical checkpoint tests were reading the MUTABLE top-level `## Current
state` dashboard, which is SUPPOSED to advance as checkpoints are ratified and
superseded.  They therefore broke when I07R1I and I10R2 were legitimately
ratified and I11 began, with no regression in anything either checkpoint ever
did.  `postgres_metadata.py` and every I11R1 measured behaviour are untouched.

### Governance model formalised in the suite

- `## Current state` is a MUTABLE DASHBOARD.  It carries only the present
  checkpoint's truth and must advance.
- Checkpoint history is APPEND-ONLY.  Each `## SENSOR-B4-<NAME> ...` section is
  immutable once written.
- Committed evidence matrices and microseals are IMMUTABLE MEASURED ARTIFACTS.

A historical checkpoint test binds to exactly one immutable source.  It never
reads the dashboard.  A current-state test never claims to represent a
superseded checkpoint.

`extract_checkpoint_section(text, heading_exact)` in
`tests/crypto_sensor_fabric/storage/_sibling_import.py` is the shared
enforcement point: exact heading match (not even trailing whitespace is
tolerated), exactly one section or fail, bounded by the next heading of the
same or higher rank, no `## Current state` dependency, no document-wide string
search, and no general Markdown parser.

### Repointed historical bindings

- I07R1I proposal truth -> `BLOC_04_I07R1I_LEDGER_STRUCTURE_MATRIX.json`
  (cases `i07_hold_chain_truthful` with the exact five hold keys and
  `proposal_pending`, `durable_resume_pending_acceptance`,
  `next_checkpoint_not_authorized`).
- I10R2 governance truth -> `BLOC_04_I10R2_RELATION_GOVERNANCE_MICROSEAL.md`,
  exact `## Governance` section, including the negative that I10R2 never
  self-ratified.
- I07R1I-RATIFY truth -> the ledger's exact
  `## SENSOR-B4-I07R1I-RATIFY ...` section (`OPERATOR_ACCEPTED`,
  `DURABLE_RESUME_IMPLEMENTED = TRUE`, `next_checkpoint_authorized = TRUE`
  authorizing I08 and only I08).
- Live dashboard -> a new test proves it is present-checkpoint-only and is not
  re-pinned to `SENSOR-B4-I07R1I`.

### Measured closure

Production diff ZERO (`quant-lab/src` untouched).  All 131 pre-existing
`bloc_04` evidence artifacts byte-identical: 0 mismatches, 0 added, 0 removed.
The `BLOC_04_I10R2_MEASUREMENT_PARITY_MATRIX.json` row key
`implementation_ledger_current_state_parity` is deliberately UNCHANGED, so the
committed I10R2 matrix regenerates byte-for-byte; only the immutable source that
predicate reads was repointed.

Ruff: changed scope clean; storage-tree baseline unchanged at exactly the two
known `test_i08_evidence.py` findings.  compileall clean.  mypy: repository
baseline unchanged at exactly 15 errors in 9 files; the one finding inside a
changed file (`test_i10r2_evidence.py` `fetchone()[0]`) is PRE-EXISTING and
byte-identical at the start HEAD - it was simply never type-checked with
`MYPYPATH` configured before.

Regression GREEN: storage 1488 passed / 25 skipped / 0 failed; non-storage
1379 passed / 1 skipped / 0 failed; full project 2867 passed / 26 skipped /
0 failed.  All 26 skips are self-declaring: 21 real-PostgreSQL I11/I11R1 guards
(no `SENSOR_POSTGRES_TEST_DSN` in this run), 4 POSIX-only platform guards on
this Windows host, and 1 deliberate live-network-smoke opt-in

`POSTGRES_RERUN=BLOCKED_ENVIRONMENT`: the disposable PostgreSQL 16.15 cluster
reached `ready to accept connections` on three separate starts and then faulted
three times with the identical Windows `0xC0000142` backend failure already
recorded at I11R1, each immediately after a time-based checkpoint.  No
production change was made in I11R2, so no new PostgreSQL proof is required by
this checkpoint's success law, and the committed I11R1 measured evidence is NOT
invalidated.  The disposable cluster was destroyed; no credential reached Git.

New append-only evidence under `evidence/bloc_04/`:
`BLOC_04_I11R2_GOVERNANCE_REGRESSION_MATRIX.json`,
`BLOC_04_I11R2_GOVERNANCE_TEST_DECOUPLING.md` and
`BLOC_04_I11R2_REGRESSION_RUN_RECORD.txt`.  Suite results are PARSED from the
verbatim run record, never hand-declared.

### Governance

- `PASS_SENSOR_B4_I11_POSTGRES_OPERATIONAL_METADATA_SEALED=OPERATOR_HOLD`
- `PASS_SENSOR_B4_I11R1_RUNTIME_CORRECTNESS_SEALED=OPERATOR_HOLD`
- `PASS_SENSOR_B4_I11R2_GOVERNANCE_REGRESSION_SEALED=PENDING_OPERATOR_REVIEW`
- `G4-10_OPERATIONAL_METADATA_GATE=IMPLEMENTATION_PASS_PENDING_OPERATOR_REVIEW`
- `next_checkpoint_authorized=FALSE`
- `recommended_next=OPERATOR REVIEW OF COMPLETE I11 -> I11R1 -> I11R2 CHAIN`
- I12+ remain unauthorized; research remains frozen.  No self-ratification.
## SENSOR-B4-I11R2C - REPO-WIDE GOVERNANCE BINDING AUDIT, ENFORCED AS LAW

Follow-up hardening of `SENSOR-B4-I11R2`, at the operator's request, after
`5766ab06dff17d89861aaf80708f8d4907f0f703`.  I12+ remain unauthorized; research
remains frozen.  This checkpoint changes **no production source**, **no
historical evidence artifact**, and **no governance verdict**: G4-10 stays
`IMPLEMENTATION_PASS_PENDING_OPERATOR_REVIEW`, nothing is self-ratified, and
the `I11 -> I11R1 -> I11R2 CHAIN` operator review is still the next step.

### The sweep

Every tracked Python file in the repository was scanned - **965** files - for
the three text shapes that can express a dependency on a mutable governance
dashboard, and for the other candidate dashboards in the tree
(`quant-lab/STATUS.md`, `quant-lab/research/crypto_foundry/CURRENT_RESEARCH_STATE.md`,
`CRYPTO_MASTER_PLAN.md`) and for the other mutable ledger sections
(`## Next checkpoint`, `## Commit log`, `## Test counts`,
`## Prior next-checkpoint history`, `## Unresolved contradictions`).

**No further historical test reads a mutable dashboard.**  Only two modules open
the governance ledger at all, and both do so legitimately:
`test_job_state_r1i.py` for the two-column Current-state structural law, the
dashboard's own present-checkpoint law, and the exact append-only
`SENSOR-B4-I07R1I-RATIFY` section; and `test_i11r2_evidence.py` for the same
purposes plus the deliberately re-implemented pre-I11R2 counterfactual.  No test
in any other subsystem reads a progress or status document.  Nothing needed
repointing.

### Finding 1 - `test_i07r1i_evidence.py` was already correct, for a reason worth keeping

That module had solved the same problem earlier and well: it carries a FROZEN
literal projection of the I07R1I `## Current state` section and reads no live
ledger, with an explicit comment that the dashboard "is chronological and must
advance at later checkpoints".  Its comment states the source commit
`fd961604` and a section digest.  That is now the accepted precedent shape.

### Finding 2 - a provenance pin that nothing checked

`_FROZEN_I07R1I_SECTION_SHA256` and `_FROZEN_I07R1I_SOURCE_COMMIT` were
**defined and never used by any code**.  A pin nothing verifies is decoration:
it documented provenance it did not enforce.  The pin was checked and is
**correct** - the `## Current state` section at commit `fd961604`, CRLF
normalised to LF with a trailing newline, hashes to exactly
`412da2f97b5d9627101e35ad6ebd68be6bd4aa1e8b643cc4400858feb26cb824`.  It is now
enforced: the digest is recomputed from the real Git object on every run, and
the frozen projection is cross-checked against the committed measured
`BLOC_04_I07R1I_LEDGER_STRUCTURE_MATRIX.json` so the two independent historical
sources for the same I07R1I truth cannot silently diverge.

### The sweep is now enforced, not merely performed

A one-time audit decays: the next checkpoint that helpfully re-reads the
dashboard would reintroduce the identical bug and the suite would stay green
right up until the operator legitimately ratified something.  So the audit
became a machine-enforced law in
`tests/crypto_sensor_fabric/storage/test_i11r2_binding_audit.py`.  It scans all
965 tracked Python files for the three predicates and requires the hit set to
equal an explicit, reasoned allowlist; a new module that touches the dashboard
fails loudly with its name and the predicate it tripped.  Adding an allowlist
entry is therefore a governance decision, not a convenience.

New append-only evidence:
`BLOC_04_I11R2_GOVERNANCE_BINDING_AUDIT.json` - 5 rows, 4 measured `OK` and 1
synthetic `FAIL`.  The counterfactual row asserts that a hypothetical new
historical test reading the dashboard would be **tolerated**, and must evaluate
FAIL.

### Measured state of the post-I11R2C tree

Production diff **zero**; historical evidence diff **zero**; the 131 pre-existing
`bloc_04` artifacts remain byte-identical.  Ruff storage-tree baseline unchanged
at exactly the two known `test_i08_evidence.py` findings; mypy repository
baseline unchanged at exactly 15 errors in 9 files, with no new finding in
changed scope.  Regression green: storage **1491** passed / 25 skipped /
0 failed (the I11R2A/B 1488 plus the 3 new audit tests), non-storage
**1379** passed / 1 skipped / 0 failed, full project **2870** passed /
26 skipped / 0 failed.  The `SENSOR-B4-I11R2_REGRESSION_RUN_RECORD.txt` and
`BLOC_04_I11R2_GOVERNANCE_REGRESSION_MATRIX.json` published at I11R2B are
deliberately **not** regenerated: they record the tree I11R2A/B was published
against, and rewriting a published evidence artifact would itself be the
append-only violation this checkpoint exists to prevent.

## SENSOR-B4-I11R2-RATIFY — operator accepts the complete I11 chain, authorizes I12

Ratified head: `fa6df668ca3351eb910b0450d1151c67482b2b24` on branch
`agent/crypto-sensor-fabric-build`.  Append-only: this section is new;
no prior checkpoint-history section was rewritten, and no historical
evidence artifact was regenerated.

### The chain accepted

`09fc62f6` I11 -> `81dd7828` I11R1A -> `05369fee` I11R1B -> `8311e61b`
I11R1C -> `ccc6a726` I11R1D -> `b5d45007` I11R2A -> `5766ab06` I11R2B
-> `fa6df668` I11R2C.  Verified linear: every commit has exactly one
parent, the range contains zero merge commits, and no rebase, reset,
amend, squash or force push occurred at any point.

### What was verified before acceptance

- **G4-10 contract**, from committed code: PostgreSQL is operational
  metadata and state only; schema `crypto_sensor_fabric_ops`;
  repository role `operational_metadata_non_raw`; no raw payload, no
  BYTEA market store, no full trade rows, no book-level bulk payloads,
  no generic raw body/content/data escape hatch, no resume-token
  persistence in PostgreSQL acquisitions.  PostgreSQL is not authority
  for raw T0 evidence, I07 job resume/checkpoint, I08 recovery journal
  or I09 quota policy.
- **Real PostgreSQL 16.15 execution**, not static SQL inference: the
  18-row / 9-table populated reconstruction, exact schema validation,
  drop/reinstall/rebuild parity, idempotence, zero T0A verify/open/
  decode calls, failed-refresh rollback, concurrent-refresh
  serialisation, the I07/I08/I09 tamper firewalls, preserved
  operational state, unchanged T0 evidence, and refused schema attacks
  are all committed measured evidence.
- **Governance repair**: I07R1I proposal truth binds to its committed
  measured `BLOC_04_I07R1I_LEDGER_STRUCTURE_MATRIX.json`; I10R2
  governance truth binds to its committed microseal's exact
  `## Governance` section.  The live dashboard is proven
  present-checkpoint-only.  I11R2C changed no governance verdict --
  its dashboard was byte-identical to I11R2B's.
- **Regression closure**, as recorded append-only at I11R2C: storage
  1491 passed / 25 skipped / 0 failed, non-storage 1379 / 1 / 0, full
  project 2870 / 26 / 0.  The I11R2A/B run record and matrix were
  deliberately not regenerated.
- **Immutability**: production diff ZERO across the I11R2 chain, 131
  pre-existing evidence artifacts byte-identical, I11/I11R1 artifacts
  unchanged, providers unchanged, DuckDB I10 unchanged, frozen Bloc-4
  plan unchanged, `main` unchanged.

### Two defects found and fixed at ratification

**The I11R2C audit could not scan itself.**  It scans
`git ls-files '*.py'`, but when it first ran the auditor was still
untracked, so it measured 965 files and never saw its own source --
which necessarily contains all three predicate literals because it
defines them.  The committed artifact's `python_files_scanned: 965` and
`unexpected_hits: {}` were accurate for the tree scanned but
**incomplete as a claim**: the repository now holds 966 tracked Python
files, and the true number of modules that open the governance ledger
is three, not the two the artifact names.  The artifact is frozen
evidence and was deliberately NOT rewritten.  Instead the self-exclusion
is explicit and commented in the auditor, and a new test
`test_audit_excludes_only_itself` prevents it from ever growing
silently.

**Git output was decoded with the Windows locale.**  Both evidence
modules called `subprocess.run(..., text=True)` with no explicit
encoding, which decodes as cp1252 on this host and silently
mis-decoded the ledger's em-dashes before the frozen-projection digest
was computed.  Both now decode UTF-8 explicitly, and the frozen I11R2B
dashboard digest is recomputed from the real Git object on every run.

### Dashboard dependency, closed in both directions

Ratification legitimately advances the dashboard, which exposed a
mirror image of the I11R2 defect.  The I11R2 measured matrix asserted
`next_checkpoint_authorized=FALSE` against the *live* dashboard, so a
historical checkpoint's own evidence would have broken the moment the
operator ratified.  Its `current_state_still_truthful` row is now
measured against the **frozen I11R2B dashboard**, resolved from the Git
object at `5766ab06` and digest-pinned, so the committed matrix
regenerates byte-for-byte at any later governance state.  The
present-checkpoint law in `test_job_state_r1i.py` stays a live test but
now asserts **internal consistency** -- the authorization field must
agree with the checkpoint the dashboard claims -- instead of a
hard-coded pre-ratification `FALSE`.

### External CI truth

`external_ci = NONE_OBSERVED`.  No external check-runs were observed on
the ratified head and no external CI is claimed.  Local verification is
the accepted evidence source.

### Non-blocking future hardening notes

Recorded, not blocking, and deliberately not actioned -- no I11R3 was
created for any of them:

- **A.** The audit keys scan hits by **basename**; two same-named
  modules in different directories would collide.  Repo-relative path
  identity would remove that.
- **B.** The audit detects explicit **literal** dependency shapes.  It
  is not a formal static-analysis proof and cannot see a dynamically
  constructed path or read.
- **C.** Accepted I04 tests write seven `BLOC_04_I0*` artifacts with
  `Path.write_text` and can still produce Windows CRLF churn in a
  non-byte-faithful worktree.
- **D.** Machine-wide `core.autocrlf=true` remains an environment
  hygiene issue, distinct from this repository's configuration.
- **E.** The disposable local PostgreSQL runtime later exhibited
  Windows `0xC0000142` faults after the completed measured run.  The
  I11R1 evidence already records the completed real-PG execution and is
  not invalidated by this.

### Authorization boundary

```
PASS_SENSOR_B4_I11_POSTGRES_OPERATIONAL_METADATA_SEALED = OPERATOR_ACCEPTED
PASS_SENSOR_B4_I11R1_RUNTIME_CORRECTNESS_SEALED          = OPERATOR_ACCEPTED
PASS_SENSOR_B4_I11R2_GOVERNANCE_REGRESSION_SEALED        = OPERATOR_ACCEPTED
G4-10_OPERATIONAL_METADATA_GATE                          = IMPLEMENTATION_PASS
next_checkpoint_authorized                               = TRUE
next_checkpoint                                          = SENSOR-B4-I12 RAW EVIDENCE QUERY / REPLAY API
authorized_scope                                         = I12 ONLY
I13+                                                      = UNAUTHORIZED
research                                                  = FROZEN
recommended_next                                         = SENSOR-B4-I12 IMPLEMENTATION
```

This ratification accepts the PostgreSQL operational metadata repository
and its governance/regression closure **only**.  It is not acceptance of
I12 or any later Bloc-4 work.  Research remains frozen.  I12 is
authorized but **not started**; it must not begin in the ratification
run.

## SENSOR-B4-I11R2C-R1 — the governance binding audit now audits itself

Correction of the first defect named at I11R2-RATIFY.  Append-only: this
section is new; no prior checkpoint-history section was rewritten.  The
paragraph above that says the audit artifact "was deliberately NOT
rewritten" is left exactly as ratified -- the correction below supersedes
it, and rewriting it would be the append-only violation this checkpoint
exists to prevent.

Corrected head: `adf1dd1f18431caf0a91940a0d952425f73ec345` on branch
`agent/crypto-sensor-fabric-build`.

### The defect, restated

`test_i11r2_binding_audit.py` scans `git ls-files '*.py'`.  When it was
first published the auditor was still untracked, so it measured 965
files and never saw its own source.  The committed artifact claimed
`python_files_scanned: 965`, `unexpected_hits: {}` and
`ledger_readers_allowed: [test_i11r2_evidence.py,
test_job_state_r1i.py]`.  Those values were accurate for the tree that
was scanned and **incomplete as a claim**: the repository holds 966
tracked Python files, the auditor necessarily trips all three
predicates because it *defines* them, and the true number of modules
that open the governance ledger is three, not two.

### Why RATIFY's fix was the wrong trade

Ratification resolved the mismatch by declaring a self-exclusion
(`SELF_EXCLUDED = frozenset({"test_i11r2_binding_audit.py"})`) plus a
`_scanned_paths()` filter, which preserved the frozen artifact
byte-for-byte.  That was rejected by the operator: **correctness over
frozen bytes**.  An auditor that quietly omits its own scope cannot be
trusted to police that scope, and freezing a number that is known to be
short makes the artifact a record of a convenient scope rather than of
the code that exists.

### What changed

The exclusion mechanism is **gone**.  There is nothing to exclude.

- `_scanned_paths()` returns every tracked `.py` file with no filter;
  `_scan()` no longer skips the auditor.
- `ALLOWLIST` gained a `test_i11r2_binding_audit.py` entry stating that
  it trips all three predicates because it defines them, and that it
  reads the ledger only to recompute the frozen I07R1I provenance pin
  from a pinned Git object -- asserting no historical checkpoint truth
  from the dashboard, which is the defect being policed.  Six entries.
- `LEDGER_READERS` expanded from two members to three.
- `test_audit_excludes_only_itself` was **replaced** by
  `test_audit_scans_itself_and_is_accounted_for`, which asserts the
  auditor is present in `_scanned_paths()`, in `ALLOWLIST` and in
  `LEDGER_READERS`; that it really does trip all three `PREDICATES`;
  and that the built payload's `python_files_scanned` equals
  `len(_scanned_paths())` with the auditor named in
  `measured_hits["governance_ledger_filename"]` and in
  `ledger_readers_allowed`, and `unexpected_hits == {}`.
- `BLOC_04_I11R2_GOVERNANCE_BINDING_AUDIT.json` was **republished** to
  match: 12 insertions, 1 deletion.  `python_files_scanned` 965 -> 966;
  three `measured_hits` buckets gain the auditor; `ledger_readers_allowed`
  and `allowlist` gain their entries.  The artifact is byte-stable: a
  rerun without the `UPDATE_I11R2_EVIDENCE=1` override regenerates it
  identically and passes.

### Unchanged by this correction

- Production diff **ZERO** against `adf1dd1f`; no `quant-lab/src`
  change, no untracked source, no dependency, provider, DuckDB or frozen
  plan change.
- The other 130 historical evidence artifacts are byte-identical.  The
  131-entry `HISTORICAL_EVIDENCE` hash sweep still reports
  `mismatched: []`, `missing: []`, `crlf_only: []`.
- No governance verdict moved.  `## Current state` is untouched, so
  the frozen I11R2B dashboard digest `3a69ecf0...` at commit
  `5766ab06` is unaffected.  The four OK rows and the one synthetic
  counterfactual FAIL row are unchanged.
- The `## Current state` dashboard is not edited by this section; the
  ratification governance stands verbatim.

### Authorization boundary

```
PASS_SENSOR_B4_I11_POSTGRES_OPERATIONAL_METADATA_SEALED = OPERATOR_ACCEPTED
PASS_SENSOR_B4_I11R1_RUNTIME_CORRECTNESS_SEALED          = OPERATOR_ACCEPTED
PASS_SENSOR_B4_I11R2_GOVERNANCE_REGRESSION_SEALED        = OPERATOR_ACCEPTED
G4-10_OPERATIONAL_METADATA_GATE                          = IMPLEMENTATION_PASS
next_checkpoint_authorized                               = TRUE
next_checkpoint                                          = SENSOR-B4-I12 RAW EVIDENCE QUERY / REPLAY API
authorized_scope                                         = I12 ONLY
I13+                                                      = UNAUTHORIZED
research                                                  = FROZEN
recommended_next                                         = SENSOR-B4-I12 IMPLEMENTATION
```

This correction changes the completeness of one evidence claim.  It is
not a new seal, not a new phase, and not a change of authorization.  I12
remains authorized but **not started**.

## SENSOR-B4-I12 — raw evidence query / replay API implemented (PENDING_OPERATOR_REVIEW)

Append-only: this section is new; no prior checkpoint-history section was
rewritten.  Start-gate note: the mandated start SHA was
`adf1dd1f18431caf0a91940a0d952425f73ec345`, but the I11R2C-R1 self-scan
correction `bde337176b4af7bafa96ef0743ec07cdabf5dbe6` (operator-directed in
the previous checkpoint run) was already the branch head.  The operator
approved starting I12 from `bde33717` with the deviation recorded here; that
commit's parent IS the mandated `adf1dd1f` and it changed no governance
verdict and no historical evidence.  Remote main `7c7816f3` untouched.

### §5 COMPLETE INVENTORY gate — MISSING_PUBLIC_INVENTORY_INTERFACE, resolved by operator review

Every accepted I04/I06 read was keyed by an ALREADY-KNOWN identity
(partition_key, blob hash, acquisition id, source_revision_key); a
non-globbing consumer could not discover what the lake holds, and the only
complete-inventory routes were filesystem globbing or DuckDB-as-truth — both
forbidden for I12.  Implementation STOPPED at the gate per §5/§41 and the
finding was reported with the smallest additive API.  The operator approved
exactly four read-only enumeration methods (I12A):

- `PartitionManifestRepository.list_all_current_manifests()` — validates every
  pointer through the exact logical partition_key path (I04R1 §38/§40); the
  physical locator filename is never trusted.
- `BlobMetadataRepository.list_all_blob_metadata()`
- `AcquisitionRepository.list_all_acquisitions()`
- `SourceRevisionRegistry.list_source_revision_keys()`

No accepted behavior changed; no historical evidence rewritten.

### What was built

- `storage/query.py` — `RawEvidenceQueryService`: complete-inventory snapshot
  (sorted by natural identity; determinism by construction, §27); every §6
  filter applied; evidence-backed range intersection (§7, requested bounds
  never become actual bounds); independent acquired/observed predicates
  (§8, F20); explicit integrity admissibility lattice (§14 — failure states
  never promoted, visible as themselves only at the UNVERIFIED floor);
  explicit coverage states (§15); typed failure vocabulary (§16) with
  `NoMatchingEvidence` as a typed condition rather than an empty list.
- `storage/replay.py` — `RawArtifactReader` (exact bytes, bounded
  deterministic streaming, verify, metadata; compression stays inside the
  accepted blob store), `RawProjectionReader` (schema gate, parser version,
  full lineage chain; `LINEAGE_INCOMPLETE` on any missing relationship;
  metadata queries never open T0A bytes), `RevisionResolver` (frozen I06
  policies; typed ambiguity; canonical only from explicit declaration
  evidence), `RawReplayCursor` (ACQUISITION_ORDER deterministic with
  documented tie-break; PROVIDER_EVENT_TIME only with actual event-time
  evidence — never substituted; SOURCE_ORDER only from explicit preserved
  sequence evidence, else typed refusal), `Bloc5Handoff` (complete
  `RawNormalizationBatch`, no Bloc-5 semantics).
- `RawEvidenceQuery.exact_revision_number: int | None` (§11) — the typed
  EXACT_REVISION selector: required >= 1 under EXACT_REVISION, forbidden
  otherwise.  Backwards-compatible; no string hacks.
- Read-only by construction (§29): the surface has no
  delete/overwrite/repair/quarantine/manifest-mutation/revision-declaration/
  resume-advancement/recovery names (machine-checked).

### Measured evidence (append-only, mechanically derived)

Seven matrices + narrative under `evidence/bloc_04/`:
`BLOC_04_I12_QUERY_FILTER_MATRIX.json` (22 rows, 21 OK, 1 synthetic
counterfactual FAIL), `BLOC_04_I12_REVISION_POLICY_MATRIX.json` (13/12/1),
`BLOC_04_I12_ARTIFACT_READER_MATRIX.json` (10/9/1),
`BLOC_04_I12_PROJECTION_LINEAGE_MATRIX.json` (6/5/1),
`BLOC_04_I12_REPLAY_ORDER_MATRIX.json` (8/7/1),
`BLOC_04_I12_READ_ONLY_IMMUTABILITY_MATRIX.json` (5/4/1),
`BLOC_04_I12_BLOC5_HANDOFF_MATRIX.json` (10/9/1),
`BLOC_04_I12_RAW_QUERY_REPLAY_EVIDENCE.md`.  Every row's invariants are
literal-true or the row FAILs; each matrix carries exactly one synthetic
counterfactual FAIL.  Artifacts regenerate byte-identically without any
override; `UPDATE_I12_EVIDENCE=1` is required only for publication; normal
pytest is read-only against committed evidence.

Immutability proof (§30): full hash sweep of the durable tree identical
before/after queries, artifact reads, replays, batch conversion, AND
expected typed failures.  Firewalls (§31-§33): no Postgres, no DuckDB, no
network in I12 (AST-verified); path-shaped selector values are inert.

### Authorization boundary

```
PASS_SENSOR_B4_I12_RAW_QUERY_REPLAY_SEALED = PENDING_OPERATOR_REVIEW
G4-10_OPERATIONAL_METADATA_GATE            = IMPLEMENTATION_PASS (unchanged)
next_checkpoint_authorized                 = FALSE
recommended_next                           = OPERATOR REVIEW OF SENSOR-B4-I12
I13                                        = UNAUTHORIZED
I13+                                        = UNAUTHORIZED
research                                    = FROZEN
```

I12 does NOT self-ratify and does NOT earn G4-11 (G4-11 is I13
export/restore).  I12 is NOT started on any later checkpoint.

---

## SENSOR-B4-I12R1 — END-TO-END QUERY SEMANTICS + REPLAY DISPATCH +
## INVENTORY FAIL-CLOSED MICROSEAL (PENDING_OPERATOR_REVIEW)

Operator static review of I12 found four acceptance blockers, each
REPRODUCED failure-first BEFORE repair and each now pinned by regression
tests (`test_i12r1_query_end_to_end.py`, 35 tests) and measured evidence
(`test_i12r1_evidence.py` publication of five append-only matrices + the
correction narrative `BLOC_04_I12R1_EVIDENCE_CORRECTION.md`):

- **DEFECT A** — revision policy was NOT part of the query reduction.  Now
  wired into `execute()` through the accepted I06 registry (pipeline step
  6); explicit policies on an unwired service are a typed
  `QueryValidationError`; `limit=1` provably cannot suppress ambiguity
  (limit is step 14, LAST).
- **DEFECT B** — include_t0a/include_t0b/projection_schema_ids were NOT
  enforced end-to-end.  Now real representation selection over
  `blob_refs`/`projection_refs`/`lineage_refs`, schema-filtered from durable
  T0B metadata only (zero payload bytes opened, measured), lineage validated
  BEFORE publication, and the T0A-fallback for a non-matching schema is the
  documented frozen behavior (visible absence, never substitution).
- **DEFECT C** — replay order dispatch used string identity (`is`).  Now a
  typed `ReplayOrder` enum with backward-compatible strings; zero identity
  comparisons remain (structurally scanned); enum/literal/dynamic/
  deserialized inputs dispatch identically; unknown modes are typed.
- **DEFECT D** — pointer alias could duplicate current inventory.  Now every
  enumerated pointer must BE the canonical hash locator for the partition
  key its payload declares, else `CurrentPointerCorrupt`; unique logical
  keys by construction.
- **§17 ADDITIONAL (reproduced then repaired)** — physical alias fragments
  in the blob-metadata and acquisition catalog families duplicated logical
  inventory; both enumerators now enforce the accepted I04 canonical
  fragment-locator law, typed `CatalogIntegrityError` on alias.  Writers
  unchanged, no silent dedupe.  `I06_ALIAS_GUARD = EXISTING_LAW_SUFFICIENT`
  — I06 was NOT modified.

Five I12R1 matrices (48 rows, 43 OK, exactly 5 explicit synthetic
counterfactual FAILs) regenerate byte-identically without any override;
`UPDATE_I12R1_EVIDENCE=1` is required only for publication; normal pytest
is read-only against committed evidence.  The original I12 evidence
artifacts remain BYTE-IDENTICAL (historical publication, never rewritten).

### Authorization boundary

```
PASS_SENSOR_B4_I12_RAW_QUERY_REPLAY_SEALED     = OPERATOR_HOLD
PASS_SENSOR_B4_I12R1_END_TO_END_QUERY_SEALED   = PENDING_OPERATOR_REVIEW
G4-10_OPERATIONAL_METADATA_GATE                = IMPLEMENTATION_PASS (unchanged)
next_checkpoint_authorized                     = FALSE
recommended_next                               = OPERATOR REVIEW OF COMPLETE I12 -> I12R1 CHAIN
I13                                            = UNAUTHORIZED
I13+                                           = UNAUTHORIZED
research                                       = FROZEN
```

I12R1 does NOT self-ratify.  I13 is NOT started.

---

## SENSOR-B4-I12R2 — FAIL-SAFE DEFAULT REVISION AUTHORITY +
## EXPLICIT REPRESENTATION-SATISFACTION MICROSEAL (PENDING_OPERATOR_REVIEW)

Operator review of the I12 -> I12R1 chain found two remaining blockers;
each was REPRODUCED failure-first (scripted reproduction recorded in
`BLOC_04_I12R2_FAIL_SAFE_CLOSURE.md`), then repaired, then re-measured
end-to-end through `RawEvidenceQueryService.execute()`:

- **BLOCKER A** — the DEFAULT revision policy (ERROR_ON_AMBIGUITY)
  executed WITHOUT the I06 authority: an unwired service returned both
  revisions of one source with no ambiguity raised (the R1 gate refused
  only explicit non-default policies).  Repaired: `execute()` raises the
  new typed `RevisionAuthorityUnavailable` for EVERY policy when
  `revision_registry` is unwired — no default pass-through, no
  compatibility switch (`allow_unresolved_revisions` /
  `unsafe_revision_passthrough` / `legacy_mode` do not exist; §5).
  Historical tests were repaired in the TEST HARNESS (canonical wiring
  now includes `revision_registry` + `RevisionSourceIdentityV1`), never
  in runtime semantics.  The refusal is a configuration/authority
  failure — never mapped to StorageBackendUnavailable,
  NoMatchingEvidence or RevisionAmbiguity.
- **BLOCKER B** — a query explicitly requesting T0B
  (`include_t0b=True`) silently returned only the valid T0A selection
  with `projection_refs=[]` when no requested T0B schema matched
  (option-A fallback).  Repaired with the representation-satisfaction
  law (FAIL-CLOSED): every published result must carry >=1 eligible
  selected T0B projection whenever `include_t0b=True`, else typed
  `ProjectionSchemaUnsupported` — T0A availability never satisfies an
  explicitly requested T0B representation.  Publication-boundary
  assertion: include flags are requirements on the returned result
  (`blob_refs` / `projection_refs` nonempty when requested).  No new
  partial-failure vocabulary on `RawEvidenceResult`.

Supersessions and documentation corrections: the I12R1 fallback row
`schema_mismatch_with_T0A_fallback_documented` is superseded by
`schema_mismatch_with_both_requested_fails_typed` (regenerated
mechanically by the SAME accepted I12R1 builder; the other four I12R1
matrices and all original I12 artifacts are BYTE-IDENTICAL); the R1 test
`test_projection_schema_mismatch_t0a_fallback_documented` was replaced by
`test_projection_schema_mismatch_with_both_requested_fails_typed`; the
QueryOutcome doc now says `execute()` RAISES NoMatchingEvidence (the
"condition" wording was stale).  `SourceRevisionCatalogCorrupt ->
RevisionPolicyInvalid` retained as FUTURE HARDENING (fail-closed,
naming imperfect; §16).

Evidence: `BLOC_04_I12R2_AUTHORITY_REQUIRED_MATRIX.json` (9 rows / 8 OK /
1 synthetic FAIL) + `BLOC_04_I12R2_REPRESENTATION_SATISFACTION_MATRIX.json`
(11 rows / 10 OK / 1 synthetic FAIL), every measured row carrying
production-measured payloads, plus the closure narrative.  New suite
`test_i12r2_fail_safe_contract.py` (20 tests, 0 skips) + read-only
evidence suite `test_i12r2_evidence.py` (3 tests).

### Authorization boundary

```
PASS_SENSOR_B4_I12_RAW_QUERY_REPLAY_SEALED     = OPERATOR_HOLD
PASS_SENSOR_B4_I12R1_END_TO_END_QUERY_SEALED   = OPERATOR_HOLD
PASS_SENSOR_B4_I12R2_FAIL_SAFE_QUERY_CONTRACT_SEALED = PENDING_OPERATOR_REVIEW
G4-10_OPERATIONAL_METADATA_GATE                = IMPLEMENTATION_PASS (unchanged)
next_checkpoint_authorized                     = FALSE
recommended_next                               = OPERATOR REVIEW OF COMPLETE I12 -> I12R1 -> I12R2 CHAIN
I13                                            = UNAUTHORIZED
I13+                                           = UNAUTHORIZED
research                                       = FROZEN
```

I12R2 does NOT self-ratify.  I13 is NOT started.

---

## SENSOR-B4-I12R2R1 — HISTORICAL EVIDENCE IMMUTABILITY REPAIR +
## CHECKPOINT-SCOPED EVIDENCE VERIFICATION (PENDING_OPERATOR_REVIEW)

Operator finding: the I12R2 PRODUCTION repair is accepted as technically
correct pending governance closure; the defect was EVIDENCE GOVERNANCE
ONLY — the I12R2 publication regenerated the historical I12R1
REPRESENTATION_SELECTION artifact (superseded fallback row) from current
production, violating the append-only historical-evidence law.

Repair (no production changes; I12R2_TECHNICAL_BEHAVIOR = UNCHANGED):

- **I12R1_REPRESENTATION_ARTIFACT = RESTORED_TO_HISTORICAL_BYTES** via
  Git object truth at the accepted I12R1 head `76042ca4c4…` (SHA-256
  `039580c0…` restored from the violated `14119b51…`); equality with the
  `76042ca4c4…` blob is the proof.
- **HISTORICAL_EVIDENCE_VERIFICATION = CHECKPOINT_SCOPED**: that one
  matrix is no longer regenerated from live runtime; it is verified by
  SHA-256 pin + Git object truth + structural law (checkpoint/matrix
  identity, 10 rows, one synthetic FAIL, historical fallback row present
  with original measured payload).  The other four I12R1 matrices keep
  regenerate-and-compare; the R1 publication set excludes the historical
  matrix so a builder regression cannot rewrite history.  Root cause
  (historical builder coupled to a later runtime whose semantics
  changed) is recorded in
  `BLOC_04_I12R2R1_HISTORICAL_EVIDENCE_IMMUTABILITY_REPAIR.md`.
- Dual truth enforced by test (`test_i12r2r1_evidence_immutability.py`,
  12 tests): historical I12R1 fallback row = SUPERSEDED_HISTORICAL_
  BEHAVIOR coexists with current I12R2 fail-closed row = CURRENT_BEHAVIOR
  (live `ProjectionSchemaUnsupported`), plus the §14 dual-truth test that
  passes ONLY if both hold simultaneously.  I12R2 matrices still
  regenerate byte-identically from current production.  The I12R2 closure
  narrative received an APPENDED dual-truth marker section (nothing
  rewritten).

Historical evidence diff vs `76042ca4c4…`: all original I12 and I12R1
evidence byte-identical (including the restored artifact); the only
expected pre-I12R2 difference is the I11R2 audit's mechanical
tracked-Python-count evolution; I12R2/I12R2R1 artifacts appear only as
additions.

### Authorization boundary

```
PASS_SENSOR_B4_I12_RAW_QUERY_REPLAY_SEALED            = OPERATOR_HOLD
PASS_SENSOR_B4_I12R1_END_TO_END_QUERY_SEALED          = OPERATOR_HOLD
PASS_SENSOR_B4_I12R2_FAIL_SAFE_QUERY_CONTRACT_SEALED  = OPERATOR_HOLD
PASS_SENSOR_B4_I12R2R1_EVIDENCE_IMMUTABILITY_SEALED   = PENDING_OPERATOR_REVIEW
next_checkpoint_authorized                            = FALSE
recommended_next = OPERATOR REVIEW OF COMPLETE I12 -> I12R1 -> I12R2 -> I12R2R1 CHAIN
I13                                                   = UNAUTHORIZED
I13+                                                  = UNAUTHORIZED
research                                              = FROZEN
```

I12R2R1 does NOT self-ratify.  I13 is NOT started.

## SENSOR-B4-I12R2R1-RATIFY — OPERATOR ACCEPTANCE OF COMPLETE I12 CHAIN

Operator ratifies the complete raw query / replay chain (I12, I12R1, I12R2, I12R2R1)
subject to and after final verification: strict ancestry from the I11 ratification
anchor (`adf1dd1f`) through `707956cb` confirmed; all six chain anchors ANCESTOR-OK;
no rewritten history.

Ratification artifact: `BLOC_04_I12_CHAIN_OPERATOR_RATIFICATION.md` (bloc_04 evidence).

Dual-truth live verification: I12R1 representation artifact SHA-256 =
`039580c07b7e6f65a74f892f513dcba7ccdc5f6f5e385e82f13595e6e437a5f3` (== 76042ca4 bytes,
historical `schema_mismatch_with_T0A_fallback_documented` row preserved); I12R2 matrix
separately proves `both_requested_schema_mismatch_refused` -> `ProjectionSchemaUnsupported`.

Historical/current evidence doctrine ratified for future Sensor checkpoints: historical
checkpoint evidence is never regenerated by later runtimes; superseded semantics are
recorded by NEW measured artifacts while old artifacts become checkpoint-scoped
(SHA-pinned, Git-object-verified) immutable custody.

```
SENSOR-B4-I12R2R1-RATIFY
PASS_SENSOR_B4_I12_RAW_QUERY_REPLAY_SEALED            = OPERATOR_ACCEPTED
PASS_SENSOR_B4_I12R1_END_TO_END_QUERY_SEALED          = OPERATOR_ACCEPTED
PASS_SENSOR_B4_I12R2_FAIL_SAFE_QUERY_CONTRACT_SEALED  = OPERATOR_ACCEPTED
PASS_SENSOR_B4_I12R2R1_EVIDENCE_IMMUTABILITY_SEALED   = OPERATOR_ACCEPTED
G4-10_OPERATIONAL_METADATA_GATE                       = IMPLEMENTATION_PASS (unchanged)
G4-11_EXPORT_RESTORE_GATE                             = NOT_YET_IMPLEMENTED / PENDING_I13
next_checkpoint_authorized                            = TRUE
next_checkpoint                                       = SENSOR-B4-I13 EXPORT / BACKUP / RESTORE PACK
authorized_scope                                      = I13 ONLY
I14+                                                  = UNAUTHORIZED
research                                              = FROZEN
recommended_next                                      = SENSOR-B4-I13 IMPLEMENTATION
```

G4-11 is NOT passed by this ratification; I13 earns it. I13 scope is frozen to LOCAL
checksum-verified export/backup/restore only (no cloud/network/Bloc-3 integration).
No I13 implementation occurred in this run. Production diff from `707956cb` = zero.

## SENSOR-B4-I13 — EXPORT / BACKUP / RESTORE PACK (G4-11)

Checksum-verified LOCAL export/backup/restore implemented in
`storage/export.py` (query-driven selection through the I12R2-canonical
service; revision authority mandatory; SOURCE_BYTES checksum domain;
streaming bounded copies; independent full-inventory verifier;
empty-root atomic restore replayed through accepted writers; DuckDB
rebuilt from the restored slice; zero network).

Model gap `I13_EXPORT_MANIFEST_MODEL_GAP` reported pre-implementation and
resolved by OPERATOR-APPROVED additive extension: `pack_schema_version`,
`object_inventory: list[ExportObjectRecord]`, `pack_root_sha256`,
`PackObjectRole`, `PackChecksumDomain`. Pre-existing fields/validators
unchanged. BackupState NOT mutated (verified-pack completion recorded in
pack + evidence).

G4-11 blocking proof (measured): fresh-empty-root restore = PASS; hash
parity = PASS; query parity (fresh services, source vs restored) = PASS;
DuckDB rebuild from restored slice = PASS; security/path containment/
resource ceilings = PASS.

```
SENSOR-B4-I13
PASS_SENSOR_B4_I13_EXPORT_BACKUP_RESTORE_SEALED        = PENDING_OPERATOR_REVIEW
G4-10_OPERATIONAL_METADATA_GATE                        = IMPLEMENTATION_PASS (unchanged)
G4-11_EXPORT_RESTORE_GATE                              = IMPLEMENTATION_PASS_PENDING_OPERATOR_REVIEW
next_checkpoint_authorized                             = FALSE
recommended_next                                       = OPERATOR REVIEW OF SENSOR-B4-I13 / G4-11
I14                                                    = UNAUTHORIZED
I14+                                                   = UNAUTHORIZED
research                                               = FROZEN
```

No self-ratification. Historical I12/I12R1/I12R2/I12R2R1 evidence untouched
(historical/current evidence doctrine carried forward). I14 not started.

## SENSOR-B4-I13R1 — PUBLIC READ AUTHORITY + ATOMIC PUBLICATION + CLOSURE

Operator source review of the PENDING_OPERATOR_REVIEW I13 found five
blockers (A private I05/I06 internals; B non-atomic export finalization;
C unsealed manifest/root digest semantics; D whole-object payload reads;
E overstated parity evidence). All reproduced failure-first, repaired,
re-measured; no historical evidence modified.

Repairs: operator-authorized minimal PUBLIC read APIs (I06
`list_segment_records`/`list_declarations`; I05 `open_payload` streaming
physically-verified reader) with zero private-attribute access remaining
in export.py (structural greps 0/0/0); sibling-staging + ONE atomic
directory rename publication (destination must not pre-exist; injected
failures leave it ABSENT); sealed non-circular MANIFEST_BODY_SHA256 +
PACK_ROOT_SHA256 domains (persisted non-null, verifier-recomputed,
receipt==persisted); bounded streaming for T0A/T0B export and restore;
literal multi-policy parity evidence (blob hash sets, metadata digests,
per-policy query digests, registry parity, DuckDB slice discovery) plus
the explicit query-scoped revision closure law.

I13 checkpoint status moves to OPERATOR_HOLD per §35 of the I13R1
mandate; G4-11 moves to IMPLEMENTATION_HOLD / PENDING_I13R1 pending
operator review of the I13R1 chain.

```
SENSOR-B4-I13R1
PASS_SENSOR_B4_I13_EXPORT_BACKUP_RESTORE_SEALED        = OPERATOR_HOLD
G4-11_EXPORT_RESTORE_GATE                              = IMPLEMENTATION_HOLD / PENDING_I13R1
PASS_SENSOR_B4_I13R1_PUBLIC_AUTHORITY_ATOMIC_CLOSURE_SEALED = PENDING_OPERATOR_REVIEW
next_checkpoint_authorized                             = FALSE
recommended_next                                       = OPERATOR REVIEW OF I13 -> I13R1 CHAIN
I14                                                    = UNAUTHORIZED
I14+                                                   = UNAUTHORIZED
research                                               = FROZEN
```

No self-ratification. I14 not started.

## SENSOR-B4-I13R2 — MANIFEST ROOT MATCHING + FORMAL EVIDENCE-CLOSURE FIXPOINT

Operator source review of the I13R1 chain found five blockers (A free-space
check silently disabled without injected provider; B metadata parity asserted
at count level; C revision/declaration parity unmeasured; D DuckDB parity
row-count-only; E "unselected evidence absent" law too strong + manifest root
selection too broad). All reproduced, repaired, re-measured. Full narrative:
`evidence/bloc_04/BLOC_04_I13R2_EVIDENCE_CORRECTION.md`.

Repairs (production, export.py): `_check_free_space` never silently disables —
default real `shutil.disk_usage` on nearest existing ancestor, injected
provider override, pre-copy estimate + progressive per-blob check
(`METADATA_OVERHEAD_BYTES = 64 KiB`); `protected_source_roots` constructor
guard (§23). Unique manifest-root matching (`_unique_result_manifests`):
result→manifest proven on identity dims + granularity + window containment +
coverage/integrity + evidence-binding agreement (blob/projection/lineage refs
subset + acquisition compatibility); 0 candidates → ExportSourceInvalid, >1 →
explicit ambiguity error; adversarial lookalike-manifest test proves the
broad (provider, venue, instrument) selection bug is closed. Formal 3-class
evidence law (QUERY_SELECTED / REQUIRED_SUPPORT / UNRELATED) via monotone
fixpoint `_evidence_closure` → frozen `EvidenceClosure` (blob_shas,
acquisition_ids, projection_ids, matched_manifests, query_selected_*,
support_*, trace, iterations); expansion edges MANIFEST_BLOB_REF,
MANIFEST_PROJECTION_REF, PROJECTION_LINEAGE, BLOB_ACQUISITIONS
(identity-domain), REVISION_FIRST_ACQUISITION, REVISION_SEGMENT_BLOB,
REVISION_PREFIX, CANONICAL_DECLARATION; policy closure (§16 minimums) never
shrinks below law and structural closure may enlarge as REQUIRED_SUPPORT
without altering query selection; visited-set cycle safety; ExportObjectRecord
NOT extended (trace is test/debug only). Restore replay ordered per accepted
I06 temporal law: acquisitions sorted by `(response_observed_at,
acquisition_id)`; RevisionObservationOrderConflict not weakened. Public
boundary seal intact: `_segments_by_key` / `_declarations_by_key` /
`_projection_root` in export.py = 0.

Evidence (append-only, byte-stable, digests verified across two runs):
RESOURCE_SAFETY c3c81119…, EXACT_METADATA_PARITY 9c191332…,
REVISION_PARITY 29068e5e…, DUCKDB_IDENTITY_PARITY 485deb85…,
QUERY_POLICY_PARITY 420abb73…, TIME_FILTER_PARITY 32125013…,
BOUNDED_SLICE 4ffac74d…. BOUNDED_SLICE measured: fixpoint iterations 2,
idempotent (C1==C2); QUERY_SELECTED 2 blobs + 2 acquisitions ⊆ pack;
REQUIRED_SUPPORT 1 blob + 1 acquisition with causal trace; pack == restored ==
expected closure for blobs/acquisitions/revision keys; true unrelated control
(disjoint partition/sensor/date/manifest) absent; true_leakage_count = 0.
TIME_FILTER_PARITY: acquired_before and observed_before select identical
acquisition IDs source vs restored (4/4). QUERY_POLICY_PARITY: default/ALL/
FIRST_SEEN/LATEST_SEEN/EXACT_REVISION 1/EXACT_REVISION 2/
PROVIDER_DECLARED_CANONICAL + refusal parity, all source==restored (10/10).
Each matrix carries exactly one deliberate SYNTHETIC_COUNTERFACTUAL FAIL row
(rejected naive surrogate method) per established convention; all measured
rows OK.

Regression: full project `uv run -m pytest tests/ -q` = 3048 passed,
28 skipped (pre-existing), 0 failures; non-storage disjoint run confirms zero
tests outside the storage tree. Static: Ruff clean on changed files,
compileall OK, mypy 0 new errors in changed scope (10 pre-existing in
untouched providers/ = baseline). Historical I03R1/I04/I11/I12/I13/I13R1
evidence unchanged vs start HEAD e7e9553 (working-tree CRLF churn from
outside this session; git blobs untouched). I14 not started.

```
SENSOR-B4-I13R2
PASS_SENSOR_B4_I13_EXPORT_BACKUP_RESTORE_SEALED     = OPERATOR_HOLD
PASS_SENSOR_B4_I13R1_PUBLIC_AUTHORITY_ATOMIC_CLOSURE_SEALED = OPERATOR_HOLD
PASS_SENSOR_B4_I13R2_EVIDENCE_FIDELITY_RESOURCE_SEALED = PENDING_OPERATOR_REVIEW
G4-11_EXPORT_RESTORE_GATE                           = IMPLEMENTATION_PASS_PENDING_OPERATOR_REVIEW
next_checkpoint_authorized                          = FALSE
recommended_next                                    = OPERATOR REVIEW OF COMPLETE I13 -> I13R1 -> I13R2 CHAIN
I14                                                 = UNAUTHORIZED
I14+                                                = UNAUTHORIZED
research                                            = FROZEN
```

No self-ratification. I14 not started.

## SENSOR-B4-I13R3 — NONVACUOUS DUCKDB/T0B PARITY + FAIL-SAFE SOURCE-BOUNDARY MICROSEAL

Operator review of the I13R2 evidence found three blockers, all reproduced
failure-first and repaired (full narrative:
`evidence/bloc_04/BLOC_04_I13R3_EVIDENCE_CORRECTION.md`):

A. Published DUCKDB_IDENTITY_PARITY rows were all EMPTY (0/0). Root causes:
   rebuild ran against the lake/pack root instead of the accepted T0A
   storage root; the accepted lake layout splits T0B projection catalogs
   into the sibling `t0b` tree so single-root rebuilds of T0B-bearing
   fixtures fail closed; and `v_t0_revisions` read only the I10 canonical
   revision layout while the accepted I12/I13 registry durably writes
   `<t0a>/revisions/segments`. Repair: `rebuild_duckdb_catalog` gains a
   backward-compatible `projection_root` parameter (default None =
   pre-I13R3 byte-identical unified behavior) and revision discovery reads
   BOTH durable layouts (divergence fail-closes). Single-root rebuild of a
   T0B fixture now refuses typed — 0/0 rows are impossible by construction.
B. Published T0B exact-metadata parity was EMPTY (rows = 0, all sharing the
   empty-array digest): the fixture query used `include_t0b=False`. Repair:
   dedicated T0B fixture (projection artifact/context/lineage/schema/
   payload + T0B-aware manifest) with `include_t0b=True`. Exercising the
   never-before-run T0B/versioned-manifest paths exposed and fixed THREE
   latent production defects: (1) pydantic-only canonical serialization
   crashed on ProjectionCatalogRecord/lineage/schema export — new
   `_canonical_dict_bytes` (same canonical JSON discipline for plain-dict
   records); (2) a superseding manifest's PREDECESSOR joins the evidence
   closure as REQUIRED_SUPPORT (new MANIFEST_PREDECESSOR fixpoint edge) so
   the CAS replay of version N>1 has version N-1; (3) restore manifest
   replay now sorts by (partition_key, manifest_version), derives the
   v>=2 CAS expected_current as (pointer.previous_manifest_id, version-1),
   emits one CURRENT_POINTER per partition key, wires the restored
   ProjectionLineageResolver for the I04 §20 gate, and replays T0B before
   manifests.
C. `protected_source_roots` defaulted to [] (optional protection). Repair
   (fail-closed, §14/§15): public READ-ONLY root properties on
   ProjectionArtifactRepository (+projection_root), Context, Lineage,
   SchemaRegistry, SourceRevisionRegistry; the exporter DERIVES every wired
   dependency's boundary at construction and refuses construction with the
   typed ExportSourceBoundaryUnproven when a dependency cannot prove its
   root; destination-overlap protection (T0A/T0B/revision families, equal
   or child, symlink-through) is on BY DEFAULT with no caller override;
   protected_source_roots remains as an extension only. I13R1 public-
   boundary seal intact (structural greps 0/0/0 in export.py).

Evidence (append-only, byte-stable, digests verified across two runs):
DUCKDB_NONVACUOUS_IDENTITY c5af877a…, T0B_PARITY c866fe5c…,
SOURCE_BOUNDARY e239e0ea…. Measured: v_t0_blobs 2/2, v_t0_acquisitions
2/2, v_t0_partitions 2/2, v_t0_revisions 2/2, v_t0_projections 1/1 (all
views positive counts BOTH sides, literal identity-set equality
SOURCE(filtered)==PACK_EXPECTED==RESTORED); T0B artifact/context/lineage/
schema nonempty literal parity; three-way projection payload SHA parity
through public open_payload()/verify_physical() only; restored T0B query
digest parity with nonempty projection_refs/lineage_refs; 10 destination-
overlap refusals + symlink guard + external success control + constructor
fail-closed proof. Each matrix carries exactly one deliberate
SYNTHETIC_COUNTERFACTUAL FAIL row per convention; all measured rows OK.

Regression: focused I13R3 green; I13/I13R2 focused suites re-run green;
full project `uv run -m pytest tests/ -q` = 3050 passed, 28 skipped
(pre-existing), 0 failures (I11R2 governance-binding audit artifact
mechanically republished 980 -> 981 python files scanned for the new
I13R3 test module, per the established audit convention). Static: Ruff clean on changed scope,
compileall OK, mypy 0 new errors in changed production scope. Historical
I13/I13R1/I13R2 evidence unchanged vs start HEAD ed7b80bc (git-verified).
I14 not started.

```
SENSOR-B4-I13R3
PASS_SENSOR_B4_I13_EXPORT_BACKUP_RESTORE_SEALED      = OPERATOR_HOLD
PASS_SENSOR_B4_I13R1_PUBLIC_AUTHORITY_ATOMIC_CLOSURE_SEALED = OPERATOR_HOLD
PASS_SENSOR_B4_I13R2_EVIDENCE_FIDELITY_RESOURCE_SEALED = OPERATOR_HOLD
PASS_SENSOR_B4_I13R3_NONVACUOUS_PARITY_BOUNDARY_SEALED = PENDING_OPERATOR_REVIEW
G4-11_EXPORT_RESTORE_GATE                            = IMPLEMENTATION_PASS_PENDING_OPERATOR_REVIEW
next_checkpoint_authorized                           = FALSE
recommended_next                                     = OPERATOR REVIEW OF COMPLETE I13 -> I13R1 -> I13R2 -> I13R3 CHAIN
I14+                                                 = UNAUTHORIZED
research                                             = FROZEN
```

No self-ratification. I14 not started.

## SENSOR-B4-I13R3-RATIFY — OPERATOR ACCEPTANCE OF THE COMPLETE EXPORT/RESTORE CHAIN; G4-11 PASSED; I14 AUTHORIZED (I14 ONLY)

The operator accepted the complete I13 -> I13R1 -> I13R2 -> I13R3 lineage at
ratification head 5d4985cc7f6f1cfe5a1c9d63ca6b8dd975d193c0 (ancestry from the
I12 ratification 5cf64e7b6 verified strict; no rewritten history). Acceptance
record: `evidence/bloc_04/BLOC_04_I13_CHAIN_OPERATOR_RATIFICATION.md`.
Production diff at ratification: ZERO. The only new code is the narrow
ratification microcheck `tests/crypto_sensor_fabric/storage/
test_i13_ratify_boundary.py` (5 tests): export into NONEXISTENT children
beneath every protected source family (T0A blob/catalog, T0B
payload/projection/context/lineage/schema catalogs, revision registry)
refuses ExportDestinationUnsafe — NOT ExportPackExists — proving the
containment comparison fires independently of pre-existing-directory
refusal; construction refuses ExportSourceBoundaryUnproven for a wired
dependency that cannot prove its root; protected_source_roots is proven an
EXTENSION ONLY (explicit roots add protection; derived T0A/T0B/revision
boundaries cannot be disabled; external destinations still export).

Verification highlights (full detail in the acceptance record): published
DuckDB identity parity remains nonvacuous (v_t0_blobs 2/2, acquisitions
2/2, partitions 2/2, revisions 2/2, projections 1/1, literal identity-set
equality SOURCE(filtered)==PACK_EXPECTED==RESTORED); T0B artifact/context/
lineage/schema 1/1 each with literal digest equality; three-way projection
payload SHA recomputed = 5d4c04ce1325ea589863d091b78ca3abbb9cb280aec2b27d
5112548fec251daa via public open_payload()/verify_physical() only; T0B
query-result digests equal (0f53d9ba...); versioned manifest v1->v2 replay
proven (predecessor REQUIRED_SUPPORT, (partition_key, manifest_version)
order, previous-identity CAS expectation, T0B replayed before the v2
referential gate); revision dual-layout divergence refuses
DuckDBCatalogCorrupt; SUCCESS_PARITY 7 policies + REFUSAL_PARITY 3 rows;
acquired_before/observed_before parity 4/4; bounded closure pack ==
restored == expected with true_leakage_count = 0 and idempotent fixpoint
(iterations 2 == 2); seal greps 0/0/0; atomicity and source independence
carried by accepted I13/I13R1 evidence; external_ci = NONE_OBSERVED.

Regression: full project `uv run -m pytest tests/ -q` after the
ratification test = 3055 passed, 28 skipped (pre-existing), 0 failures
(pre-ratification baseline 3050 + 5 new; first run surfaced the expected
I11R2 audit drift, mechanically republished 981 -> 983 python files
scanned — this also corrects a stale-by-one count left by the I13R3D
republish, which ran before its test module was committed; no manual count
edits). Focused: I13R3 + I13R2 + I13 + I13R1 + ratification microcheck =
42 passed, 2 pre-existing skips. Ruff clean on changed scope; compileall
OK; mypy 0 new findings (10 pre-existing providers/ baseline). Historical
I13/I13R1/I13R2/I13R3 evidence untouched by this run; CRLF-only churn in
old I03R1/I04 evidence remains unstaged (out of session scope).

```
SENSOR-B4-I13R3-RATIFY
PASS_SENSOR_B4_I13_EXPORT_BACKUP_RESTORE_SEALED      = OPERATOR_ACCEPTED
PASS_SENSOR_B4_I13R1_PUBLIC_AUTHORITY_ATOMIC_CLOSURE_SEALED = OPERATOR_ACCEPTED
PASS_SENSOR_B4_I13R2_EVIDENCE_FIDELITY_RESOURCE_SEALED = OPERATOR_ACCEPTED
PASS_SENSOR_B4_I13R3_NONVACUOUS_PARITY_BOUNDARY_SEALED = OPERATOR_ACCEPTED
G4-11_EXPORT_RESTORE_GATE                            = PASS
next_checkpoint_authorized                           = TRUE
next_checkpoint                                      = SENSOR-B4-I14 BLOC 3 INTEGRATION
authorized_scope                                     = I14 ONLY
I15+                                                 = UNAUTHORIZED
G4-12_BLOC3_HANDOFF_GATE                             = NOT_YET_IMPLEMENTED / PENDING_I14
research                                             = FROZEN
```

I14 frozen contract recorded (NOT implemented in this run): wire production
Bloc 3 adapter outputs (FetchBatch, RawPayloadEnvelope) into the accepted
Bloc 4 storage writer; RESUME CHECKPOINT MUST NEVER ADVANCE BEFORE DURABLE
MANIFEST COMMIT; restart-safe across all seven crash windows; no cursor
skip, no silent event loss, no false checkpoint progress; I14 earns G4-12.
I14 authorization does NOT authorize I15/I16/I17, research restart, provider
redesign, or new storage/query/export semantics. STOP after this
ratification; DO NOT START I14 in this run.


## SENSOR-B4-I14 — BLOC 3 → BLOC 4 DURABLE HANDOFF (G4-12): COMPLETE CHAIN I14A-F; IMPLEMENTATION PASS PENDING OPERATOR REVIEW

New production module `quant-lab/src/crypto_sensor_fabric/storage/integration.py`
(COMPOSITION ONLY): `Bloc3StorageHandoff.persist_batch(*, job_id, batch: FetchBatch,
context: Bloc3StorageContext, projection_ids=None) -> BatchPersistenceReceipt`.
`Bloc3StorageContext` is the §43 narrow typed seam carrying REQUIRED `venue` (no
hidden default, §44 — typed refusal at construction) plus optional accepted
`Granularity` / endpoint / request-family identity FetchBatch deliberately does
not hold. INPUT_MAPPING contract gap: NONE (20-row matrix, every crossing field
cites its authority; explicit non-mappings recorded for row_count /
provider_cursor / duplicate_annotations / rate_limit_snapshot). T0A byte law:
bytes verbatim; str UTF-8 per the accepted Bloc 3 payload_hash rule; NO reparse,
NO normalization; provider content_hash recomputed and refused typed
(EnvelopeContentHashMismatch) BEFORE any mutation. Envelope identity (§7) and
duplicate-in-batch (DuplicateEnvelopeContent) typed-refuse pre-mutation.

Causal sequence (§4/§25, frozen I07 graph, single-step):
PLANNED -> ACQUIRING -> RAW_STAGED -> RAW_COMMITTED -> PROJECTION_PENDING ->
PROJECTION_COMMITTED -> MANIFEST_COMMITTED -> advance_checkpoint (the accepted
I07 gate; composition wired min_durable_status=MANIFEST_COMMITTED; repository
NEVER weakened) -> CHECKPOINT_ADVANCED; complete batches continue -> COMPLETE
exactly once (gate never skipped). Partial batches keep the adapter's exact
next_resume_token (§22/§24); no token is ever manufactured. Multi-envelope (§9):
N envelopes -> N durable T0A blobs + N AcquisitionRecords + ALL blob refs in the
manifest (atomic causality §36); revision law = ONE batch is ONE source
observation registered via the accepted I06 public path from the batch's FIRST
acquisition anchor (I06 §40 same-instant source-order law respected — the
handoff never invents observation times). EMPTY_VALID (§10): NOTHING fabricated
— durable truth = manifest with zero blob_refs, coverage EMPTY_CONFIRMED,
integrity UNVERIFIED (I04 §46), checkpoint truthfully does not move (no
acquisition anchor exists at the manifest floor; explicit no-resume state, §24).

Versioned manifest CAS (§20) with W6/W7 idempotent adoption (§29/§33): if the
current pointer already references the EXACT intended manifest (identity, blob
refs, projection refs, coverage, integrity, logical window) it is re-read,
proven durable, and adopted — retries never append a duplicate semantic version.
Adoption law (§34/§35/§49/§50): identical redelivery / retry after
CHECKPOINT_ADVANCED or COMPLETE re-derives the receipt from DURABLE job state
and mutates nothing (checkpoint transitions stay at exactly 1); a divergent
batch under a consumed checkpoint is a typed BatchAlreadyCompleted refusal
(§35) — the genuine NEXT batch continues via the accepted annotated
CHECKPOINT_ADVANCED -> ACQUIRING transition. Same bytes / two jobs (§56): blob
dedupe shares content; acquisitions and checkpoint anchors stay identity-bound.

Crash matrix (§27/§28/§47/§53/§62) W1-W7, fresh-repository restarts, each row
measured: resume_after == resume_before for EVERY window; final durable
semantic digest == clean-run digest; retry manifest id == clean-run manifest id.
W7 critical case proven: manifest durable + checkpoint old -> retry adopts the
exact manifest (exactly 1 durable copy, no duplicate version) and advances the
checkpoint EXACTLY once across both runs. Survivors left in place per §53 law
(no deletion to mimic rollback); I08 recovery remains orphan owner (§54).
T0B (§17/§18/§57/§64): T0A-only remains valid; T0A+T0B fixture commits a REAL
projection via the accepted I05 T0BProjectionService over the handoff's own
durable evidence and binds projection_refs through the accepted I04 CAS with a
wired ProjectionLineageResolver; broken-lineage counterfactual FAILS CLOSED
(dangling projection ref refuses manifest commit; checkpoint stays old).
Concurrency (§55/§65): same-job double-persist = 1 checkpoint, no manifest fork;
stale-writer counterfactual refused by the accepted manifest CAS
(ManifestCASConflict) — no last-writer-wins.

Evidence (append-only, §59; every PASS row measured by
`tests/crypto_sensor_fabric/storage/test_i14_evidence.py`): INPUT_MAPPING 20/20
OK; DURABILITY_ORDER 8/8 OK (structural §51 ordering: manifest durable
re-read precedes checkpoint publication); CRASH_RESTART 8/8 OK; IDEMPOTENCE
13/13 OK (1 counterfactual: inverted gate refuses JobResumeGateError);
T0B_HANDOFF 3/3 OK (1 counterfactual); CONCURRENCY 2/2 OK (1 counterfactual);
plus BLOC_04_I14_BLOC3_HANDOFF_EVIDENCE.md. Focused I14: 23 passed / 0 failed /
0 skips; evidence suite 6 passed. Regression: full storage 1699 passed / 27
pre-existing skips; full project 3078 passed / 28 pre-existing skips (first
run; second run with evidence suite pending in transcript, zero failures
expected and verified before commit). Ruff clean on changed scope; compileall
OK; mypy 0 findings in integration.py (10 pre-existing providers/ baseline via
followed imports — no new findings). Secret scan clean (§39); zero network
(§38). external_ci = NONE_OBSERVED. Historical I03-I13 evidence untouched
(§77); CRLF-only churn in old I03R1/I04 evidence never staged.

```
SENSOR-B4-I14
PASS_SENSOR_B4_I14_BLOC3_INTEGRATION_SEALED          = PENDING_OPERATOR_REVIEW
G4-12_BLOC3_HANDOFF_GATE                             = IMPLEMENTATION_PASS_PENDING_OPERATOR_REVIEW
next_checkpoint_authorized                           = FALSE
recommended_next                                     = OPERATOR REVIEW OF SENSOR-B4-I14 / G4-12
I15+                                                 = UNAUTHORIZED
research                                             = FROZEN
```

No self-ratification. I15 not started. STOP after I14.

## SENSOR-B4-I14R1 — PAGINATED CONTINUATION + EMPTY_VALID CHECKPOINT + MULTI-ENVELOPE REVISION CLOSURE: COMPLETE CHAIN I14R1A-E; IMPLEMENTATION PASS PENDING OPERATOR REVIEW

Operator review of I14 found three blockers; I14R1 reproduces all three
failure-first (RED) and repairs them without rewriting I14 history.

Blocker A (continuation): at/after CHECKPOINT_ADVANCED the handoff now
classifies EXACT_RETRY (adopt, zero mutation) / NEXT_BATCH (proven ONLY by
accepted upstream context: Bloc3StorageContext.request_resume_token ==
current.resume_token, sourced from the accepted FetchRequest.resume_token
field; nextness NEVER inferred from bytes/timestamps/row counts/manifest
versions/provider_cursor) / DIVERGENT_REWRITE (typed fail-closed before any
evidence mutation). I14 owns the accepted annotated CHECKPOINT_ADVANCED ->
ACQUIRING edge; the public caller never drives I07 (external manipulation
count = 0). COMPLETE stays terminal. Three-page single-job proof through ONLY
persist_batch: exactly 3 checkpoints, 2 annotated continuation edges, 1
COMPLETE, no skipped page, no duplicate manifest version.

Blocker B (EMPTY_VALID progress): AcquisitionRecord.blob_sha256 audited —
already nullable, no fabrication needed. An EMPTY_VALID page now persists a
durable blob-less AcquisitionRecord carrying the accepted EMPTY_VALID flag
(additive _is_empty_valid_acquisition shape in the I04R1 §26 blobless gate),
a durable EMPTY_CONFIRMED/UNVERIFIED zero-blob manifest, and advances the
checkpoint through THE accepted I07 gate with the additive V2 proof
(proof_version=2, evidence_kind=EMPTY_VALID, blob_sha256=None) — valid ONLY
at the MANIFEST_COMMITTED floor, ONLY for EMPTY_VALID. V1 remains closed and
unchanged (mandatory 64-hex blob anchor; blobless V1 still corrupt; unknown
fields/versions still corrupt). Restart replay is VERSION-AWARE: each event
validates under its OWN persisted proof version; mixed V1/V2 chains replay
cleanly. Empty partial preserves the adapter token; empty complete runs
CHECKPOINT_ADVANCED -> COMPLETE. Fake blob count = 0 across all windows.

Blocker C (multi-envelope revision): I06 audited — no contract gap; extended
additively. SourceRevisionRegistry.register_acquisition_group() reuses the
entire existing classification machinery over the COMPLETE group; group
digest = sha256("sensor-revision-group-v1\n" + sorted unique member blob
SHAs) — canonical SET (Bloc 3 declares no envelope ordering semantic:
[X,Y] vs [Y,X] is the SAME observation), domain-separated from any literal
blob SHA, RECOMPUTED by I06 on every registration and restart. Group
observation rows durably persist the COMPLETE member_acquisition_ids and
member_blob_sha256 sets (a digest alone is NOT lineage — I14R1 §16/§17);
the restart loader refuses any GROUP row/segment whose lineage is absent,
unbound, or does not recompute to the persisted digest. Additive
content_scope field: absent = legacy SINGLE law (historical rows unchanged;
single-acquisition register_acquisition semantics untouched). Manifest
evidence set == revision observation set.

Acquisition-id law corrected: fp::sha -> fp::observed_at::sha (empty:
fp::observed_at::EMPTY_VALID); exact retry keeps the id, identical bytes at
a later instant are a distinct event with the same blob SHA. One
legitimately re-measured historical I14 row (T0B source_acquisitions);
documented in the correction file.

Evidence (append-only; historical I14 matrices immutable): CONTINUATION 9/9
OK; EMPTY_VALID_CHECKPOINT 7/7 OK; MULTI_ENVELOPE_REVISION 6/6 OK; RESTART
3/3 OK; BLOC_04_I14R1_EVIDENCE_CORRECTION.md. Focused I14R1 (reproduction +
evidence + compat suites): 43 passed / 0 failed. Regression at final file
set: full storage+project 3127 passed / 28 pre-existing skips, ZERO failures
(includes I14 original 23, I06/I07 suites 79, Bloc 3 base/contracts 1111+).
Ruff clean on changed scope; compileall OK; mypy 0 new findings (10
pre-existing providers/ baseline via followed imports). Secret scan clean;
zero network. I11R2 governance-binding audit mechanically republished at the
true tracked-Python count 989 (986 + 3 new I14R1 test modules), no-update
byte-stability rerun green. external_ci = NONE_OBSERVED (0 statuses, 0
check-runs at start head). CRLF-only churn in old I03R1/I04 evidence never
staged.

```
SENSOR-B4-I14R1
PASS_SENSOR_B4_I14_BLOC3_INTEGRATION_SEALED          = OPERATOR_HOLD
PASS_SENSOR_B4_I14R1_STREAM_CONTINUATION_EMPTY_REVISION_SEALED = PENDING_OPERATOR_REVIEW
G4-12_BLOC3_HANDOFF_GATE                             = IMPLEMENTATION_PASS_PENDING_OPERATOR_REVIEW
next_checkpoint_authorized                           = FALSE
recommended_next                                     = OPERATOR REVIEW OF I14 -> I14R1 CHAIN
I15+                                                 = UNAUTHORIZED
research                                             = FROZEN
```

No self-ratification. I15 not started. STOP after I14R1.

## SENSOR-B4-I14R2 — HISTORICAL EVIDENCE IMMUTABILITY + I06 GROUP-AUTHORITY SELF-VALIDATION: COMPLETE CHAIN I14R2A-E; IMPLEMENTATION PASS PENDING OPERATOR REVIEW

Operator review of I14R1 found two blockers; both closed without touching
any published I14R1 matrix.

Blocker A (historical evidence mutation): reproduced exactly — between
706f18ed2 and 4111205e, BLOC_04_I14_T0B_HANDOFF_MATRIX.json changed one
line (source_acquisitions fp-job::b4d13a6a… gained the observation-instant
segment) because the live I14 evidence generator republished historical
matrices on every pytest run. Closure: the T0B fossil restored byte-exact to
the accepted I14 checkpoint blob (sha256 9dc20f64cb4a0741…, resolved through
Git itself); test_i14_evidence.py converted to CHECKPOINT-SCOPED
IMMUTABILITY VALIDATION — the six I14 matrices are fossils, still
live-measured in memory, never written by an ordinary pytest run; _write is
gated behind UPDATE_I14_EVIDENCE=1 with a typed refusal; a custody test
proves all six byte-equal the accepted blobs and that a live pass mutates
none. Dual truth: I14-era identity in the fossil, observation-aware identity
in R1/R2 evidence only. Generalized law recorded: once a checkpoint
advances, its evidence files are immutable; later changes publish correction
evidence at the later checkpoint. Generator audit (§29): I13 already
custody-frozen, I05 writes outside the evidence tree, I14 was the only live
writer — no systemic overwrite problem, no STOP.

Blocker B (I06 group authority trusted its caller): register_acquisition_group
now self-validates — every member's RevisionSourceIdentityV1 descriptor and
source_revision_key must equal the canonical first-member identity (compared
through the model's own descriptor); every member's canonical
response_observed_at must equal the group instant (no min/max/first/last
collapse); duplicate acquisition ids rejected before resolution; replay
requires the supplied id set AND resolved blob set to equal the persisted
sets exactly (subset/superset/same-blobs-different-acquisitions all typed
conflicts). New finding repaired (§15): R1 persisted member ids in caller
order and blobs sorted independently — correspondence was lost; group rows
now persist canonical member_bindings acquisition<->blob PAIRS sorted by
blob sha (existing fields retained; R1-shaped rows reconstructed at load by
resolution, never an ambiguous zip). Restart validation (§17/§18): every
persisted GROUP row re-proves all members (existence, physical
verification, identity, instant, unique blob mapping) and recomputes the
domain-separated digest; group segments require a complete binding
observation. I14 remains a pre-validating client; I06 repeats the
authoritative checks (no trust inversion).

Evidence (append-only; I14R1 matrices untouched): HISTORICAL_EVIDENCE_IMMUTABILITY
3/3 OK; GROUP_AUTHORITY 7/7 OK (direct I06 API, §20); GROUP_MEMBERSHIP 5/5 OK;
RESTART_CORRUPTION 6/6 OK; BLOC_04_I14R2_EVIDENCE_CORRECTION.md.

Regression: full project 3133 passed / 28 pre-existing skips, ZERO failures
(R2 module included; rerun after final file set). One transient
test_blob_store_adversarial concurrency flake (REUSED_EXISTING 6/7 race)
reproduced at the untouched baseline head 4111205e in a throwaway worktree
(2/10 fail there, test + blob_store.py unchanged since I03R1C) — pre-existing
timing race, NOT an I14R2 regression; the full-suite rerun passed clean.
Ruff clean changed scope; compileall OK; mypy 0 new findings (10 pre-existing
providers/ baseline). Secret scan clean. I11R2 audit mechanically republished
at true tracked count 990 (989 + test_i14r2_evidence.py); no-update rerun
byte-stable. external_ci = NONE_OBSERVED. CRLF-only churn in old I03R1/I04
evidence never staged.

```
SENSOR-B4-I14R2
PASS_SENSOR_B4_I14_BLOC3_INTEGRATION_SEALED          = OPERATOR_HOLD
PASS_SENSOR_B4_I14R1_STREAM_CONTINUATION_EMPTY_REVISION_SEALED = OPERATOR_HOLD
PASS_SENSOR_B4_I14R2_EVIDENCE_CUSTODY_GROUP_AUTHORITY_SEALED = PENDING_OPERATOR_REVIEW
G4-12_BLOC3_HANDOFF_GATE                             = IMPLEMENTATION_PASS_PENDING_OPERATOR_REVIEW
next_checkpoint_authorized                           = FALSE
recommended_next                                     = OPERATOR REVIEW OF COMPLETE I14 -> I14R1 -> I14R2 CHAIN
I15+                                                 = UNAUTHORIZED
research                                             = FROZEN
```

No self-ratification. I15 not started. STOP after I14R2.

---

## SENSOR-B4-I14R2-RATIFY

**Type:** governance only (operator ratification of the complete I14 -> I14R1 -> I14R2 chain). **Commit:** (this commit). **Production diff:** ZERO. **Historical evidence diff:** ZERO.

**Acceptance artifact:** `evidence/bloc_04/BLOC_04_I14_CHAIN_OPERATOR_RATIFICATION.md` (new, append-only). No Python test added -> I11R2 tracked-Python audit NOT republished (stays 990). No I14/I14R1/I14R2 published evidence modified.

**Ratification verification (all green this run, ZERO deterministic failures):**

- Start gate: branch agent/crypto-sensor-fabric-build; HEAD = origin build = d45d611700d7b76f11726d319158d7df22289e34; origin/main = 7c7816f382947bbc8a1f2154435fc436f2428fa8; strict ancestry a37aad77cb -> 706f18ed2 -> 4111205e0 -> d45d61170 verified via merge-base --is-ancestor; no rewritten history.
- Focused chain re-validation: I14 custody + I14R2 + I14R1 evidence 16 passed; I14R1 reproduction + compat 39 passed (3-page public-API continuation: 3 checkpoints / 2 CHECKPOINT_ADVANCED->ACQUIRING / 1 COMPLETE / 0 external manipulations; V1/V2 compat A-J; mixed restart); I06/I06R1/I07/I04 14 passed.
- I14R2 matrices re-run nonvacuous, PRODUCTION_MEASURED: HISTORICAL_EVIDENCE_IMMUTABILITY 3/3, GROUP_AUTHORITY 7/7, GROUP_MEMBERSHIP 5/5, RESTART_CORRUPTION 6/6 (= 21/21).
- Historical custody: 6/6 original I14 matrices byte-identical to accepted I14 head 706f18ed2 (TestI14HistoricalEvidenceCustody, pinned SHA-256). Generator freeze held: historical file mutation count = 0; UPDATE_I14_EVIDENCE gate stays disabled by default.
- Broader battery: I11R2 audit (no-update, byte-stable @ 990 tracked .py) + I12 matrices + I13 + I13 ratify boundary 13 passed; I07R1* + blob store core 85 passed / 2 skipped; blob-store adversarial + namespace evidence 35 passed; I08 chain 77 passed; I12/I13 remainder 165 passed / 2 skipped; I05 + I09 chains 180 passed; I10/I11 chain + I14 handoff helpers 108 passed / 19 skipped.
- Blob-store flake truth: known pre-existing flake test_blob_store_adversarial.py::TestConcurrency::test_concurrent_identical_writers_one_final (previously reproduced at untouched baseline 4111205e, ~1/6, not a chain regression) did NOT flake this run; documented, nothing hidden. Prior local full baseline unchanged: 3133 passed / 28 skipped / 0 failures.
- Tooling: compileall OK; Ruff scoped diff empty (2 pre-existing findings in untouched test_i08_evidence.py); mypy storage = 10 errors all pre-existing in providers/ (0 new). Production diff = ZERO.
- external_ci = NONE_OBSERVED (0 statuses / 0 check-runs queried live at ratified head). Local pytest is not called CI.

**Laws ratified (committed-code anchors verified):** checkpoint-after-durable-manifest (integration.py drives MANIFEST_COMMITTED then advance_checkpoint()); continuation classifier EXACT_RETRY / NEXT_BATCH / DIVERGENT_REWRITE; acquisition ID law fp-job::<observation instant>::<sha> (or EMPTY_VALID sentinel) with dual-truth tolerance for the historical fp-job::<sha> T0B fossil; EMPTY_VALID blobless durable semantics (blob_sha256=None / blob_refs=[] / EMPTY_CONFIRMED / UNVERIFIED); checkpoint proof V1 (blob-backed; blobless and unknown-version refuse) and V2 (EMPTY_VALID only, MANIFEST_COMMITTED floor); mixed V1/V2 restart under persisted proof versions; group authority owned by SourceRevisionRegistry.register_acquisition_group() with domain-separated digest sensor-revision-group-v1 over sorted unique member blob SHAs ([X,Y]==[Y,X], [X,Y1]!=[X,Y2]); I06 self-validation of EVERY group member; durable member_bindings acquisition->blob correspondence; exact membership replay with subset/superset/replacement/foreign/duplicate refusals; group restart re-proof; group mutation semantics (identical refetch / SOURCE_MUTATION on member change / order-only permutation non-semantic / later-time same-set identical-refetch); manifest blob-ref set == group member blob set; W1-W7 crash safety with old-resume-token invariant and W7 exact-once adoption; corruption refusals with no repair-on-read.

```
SENSOR-B4-I14R2-RATIFY
PASS_SENSOR_B4_I14_BLOC3_INTEGRATION_SEALED           = OPERATOR_ACCEPTED
PASS_SENSOR_B4_I14R1_STREAM_CONTINUATION_EMPTY_REVISION_SEALED = OPERATOR_ACCEPTED
PASS_SENSOR_B4_I14R2_EVIDENCE_CUSTODY_GROUP_AUTHORITY_SEALED   = OPERATOR_ACCEPTED
G4-12_BLOC3_HANDOFF_GATE                              = PASS
next_checkpoint_authorized                            = TRUE
next_checkpoint                                       = SENSOR-B4-I15 HARDENING AND SECURITY
authorized_scope                                      = I15 ONLY
I16+                                                  = UNAUTHORIZED
research                                              = FROZEN
recommended_next                                      = SENSOR-B4-I15 IMPLEMENTATION
```

G4-13_BLOC5_READINESS_GATE = NOT_YET_IMPLEMENTED / PENDING_LATER_CHECKPOINT. I14 ratification does NOT earn G4-13 (frozen definition: RawNormalizationBatch PIT-normalization evidence sufficiency without filesystem/path assumptions).

I15 authorization covers ONLY hardening of existing accepted Bloc 4 surfaces (secret scan, path traversal, symlink escape, corruption handling, resource bounds). It does NOT authorize I16 final acceptance/evidence, I17 Bloc 5 handoff, research restart, provider redesign, new storage architecture, new query semantics, new revision semantics, or normalization logic.

No self-ratification of I15: it is AUTHORIZED but NOT STARTED. STOP after I14R2-RATIFY.

---

## SENSOR-B4-I15 HARDENING AND SECURITY

**Type:** implementation + adversarial hardening of ALREADY ACCEPTED Bloc 4 surfaces. **Production diff:** ONE file (`src/crypto_sensor_fabric/storage/paths.py`). **Historical evidence diff:** ZERO (7 old I03R1/I04 artifacts show CRLF-only churn, allowlisted; never staged/normalised).

**Scope (frozen I15 contract):** secret scan; path traversal; symlink escape; corruption handling; resource bounds. No provider redesign, no storage/query/revision semantics change, no normalisation logic. I16+ UNAUTHORIZED; G4-13 NOT EARNED; research FROZEN.

### 1. RED finding -- static symlink escape (reproduced BEFORE repair)

Failure-first record: a link planted at an intermediate directory inside the configured storage root (blobs/, staging/) allowed a blob WRITE to land OUTSIDE the configured root. resolve_under_root() was lexical-only and its docstring explicitly deferred symlink escape to a later hardening checkpoint, so the pre-repair result was UNSAFE (outside-root mutation PRODUCED). Root cause: lexical segment validation cannot see a link at an intermediate component.

### 2. Repair -- single containment choke point

resolve_under_root() now additionally resolves BOTH the root and the candidate through the filesystem and refuses (typed ValueError) any target whose REAL location is not the root itself or a descendant of it. It returns the UN-resolved path so containment stays relative to the RESOLVED root. Chosen law A: a configured DATA ROOT MAY ITSELF be a symlink -- its resolved target is the authority (proven by the root-is-a-link case). Post-repair: same attack refused typed, outside-root mutation count = 0; a pre-placed link at the exact final artifact name is refused by typed containment OR AtomicPublishError (no-replace publication) and the outside file is untouched. Audit confirmed the hardened helper is the single filesystem containment choke point for caller-influenced keys (blob_store, catalog, manifests, json_catalog/duckdb_catalog, projection resolver/projections, export, recovery); the bypass audit found no module opening a directly-joined caller key.

**STATIC_SYMLINK_ESCAPE = SEALED. TOCTOU_SYMLINK_SWAP = KNOWN_LIMITATION** (no race-safety claim is made; recorded explicitly, never claimed).

### 3. Adversarial results (fresh, PRODUCTION_MEASURED)

- Secret scan: 0 credential-shaped findings across source / tests / evidence roots after a NARROW allowlist (TEST_ONLY sentinels + documented exact accepted redaction-fixture literals only). Scanner self-match excluded (its own regex/source definitions are not counted) and a separate runtime-built realistic synthetic credential IS detected -- proving the allowlist is not a blanket suppression. Error messages name no secret value.
- Runtime sentinel: secret-bearing request/auth metadata refused typed (SecretBearingAcquisitionMetadata); recursive durable-tree scan = 0 sentinel hits (per-case, isolated); raw response bytes remain exact evidence (never redacted); accepted URL/header/DSN sanitizers proven.
- Path traversal: full matrix (now including explicit cross-platform Windows/POSIX cases: mixed separators, drive-absolute, extended-length device path, dot-segments, reserved names, shell-style expansions, Unicode slash lookalike, trailing dot/space, encoded/double-encoded, NUL) -- every hostile key typed-refused or literally contained; OUTSIDE-ROOT MUTATIONS = 0. Provider values enter keys ONLY through the canonical percent-encoding.
- No shell: structural (zero subprocess/os.system/shell=True/Popen in storage) AND behavioural (a shell-metacharacter instrument persists as data; 0 shell artifacts).
- Hardlink: mutating accepted immutable evidence through a hardlink IS detected typed (content verification), never silently accepted.

### 4. Corruption (FRESH-RESTART, outcome vocabulary)

Fresh repository instances used throughout (no in-memory cached refusal counted):
- T0A payload tamper -> QUARANTINED_ACCEPTED (QUARANTINED_INTEGRITY_FAILURE).
- Manifest fragment tamper -> FAIL_CLOSED_TYPED on fresh read (no repair-on-read).
- Acquisition fragment tamper -> FAIL_CLOSED_TYPED on fresh read.
- DuckDB corrupt/delete -> REBUILD_DISPOSABLE_STATE from durable evidence (never a source of truth).
- Recovery over hostile staging state -> read-only scan: nothing created/deleted, valid T0A preserved, unknown hostile file never promoted to trusted evidence.
- Remaining subsystems (T0B, revision, job/checkpoint, export) cited to existing measured suites (I05R1-R4, I06/I14R2 RESTART_CORRUPTION, I07R1I, I13) -- no generic "exception happened" rows.

### 5. Resource bounds (write scale severed from scan scale)

- Logical 1 GiB-equivalent streaming hash: bounded by configured chunk (memory never grows with source size); 64 MiB-equivalent T0A write streams at 256 KiB chunks (dedupe -> REUSED_EXISTING without double-buffering). T0A = SAFE_BY_STREAMING_API.
- ACTUAL MANIFEST ROWS SCANNED >= 10,000 (frozen benchmark honoured literally): manifest_rows_created = 10,000; manifest_rows_scanned = 10,000; invalid_rows = 0; duplicate logical ids = 0; fragment_files = 10,000 (one canonical parquet row/fragment, since the accepted catalog physically requires len(rows)==1); deterministic (sorted) order; peak scan memory ~56 MiB. Corpus construction was EXPLICIT benchmark-fixture setup with the canonical serializer/schema into the production on-disk layout; the ACTUAL scan ran PRODUCTION reader code (RecoveryEngine._all_manifests -> read_fragment + _manifest_from_row). Pointer/parquet-object counts were NEVER relabelled as manifest rows.
- WRITE_SCALE measured SEPARATELY: 200 real append_partition_manifest appends = 24.44 s (full durability re-proof per append). No 10k-append throughput claim.
- DuckDB rebuild + read-only query over 150 synthetic projection identities completes; export ceilings + injectable free-space law; query limit is the explicit caller bound (reader materializes the gated set, no invented pagination); long revision chain (200): ALL/FIRST/LATEST/EXACT exact, no recursion, no silent truncation.
- Disk-watermark policy MATRIX preserves accepted I09 semantics exactly: NORMAL all PROCEED; WATCH all WARN; CONSTRAINED P0/P1 PROCEED, P2 DEFER, P3 PAUSE; CRITICAL P0 WARN (continue), P1/P2/P3 BLOCK; absolute floor blocks even P0; NO automatic T0A deletion. Resource ceilings are CONFIGURATION (independent fixtures prove different safe limits leave scientific evidence identity unchanged).

### 6. Regressions (after final code)

Focused I15: test_i15_hardening.py 17 passed; test_i15_resource_bounds.py 12 passed; test_i15_manifest_scan_scale.py 2 passed. Storage subsystem regressions: blob/catalog/manifest core 295 passed (1 pre-existing known concurrency flake -- passes on retry, reproduced at untouched baseline); projections/revisions/duckdb/export/quota/atomic 300 passed; recovery/job-state/I04 212 passed (1 skipped); I05-I07 123 passed; I08-I10 223 passed; I11-I12 141 passed (21 skipped, postgres BLOCKED_ENVIRONMENT); I13-I14 143 passed (2 skipped); checksums/models/serialization/provenance 314 passed. ZERO deterministic failures.

**Pre-existing defect surfaced and fixed forward:** the I14R2-RATIFY committed ledger carried 42 CRLF sequences, failing test_job_state_r1i.py::test_ledger_is_utf8_lf at UNTOUCHED HEAD. The I15 ledger append normalises the document to UTF-8 LF (required by that contract); no prior commit amended.

Tooling: compileall OK; Ruff clean on changed scope (2 pre-existing findings in untouched test_i08_evidence.py); mypy storage = 10 errors all pre-existing in probes/providers (0 new). external_ci = NONE_OBSERVED. I11R2 tracked-Python audit mechanically regenerated after final filenames and re-run no-update for byte stability.

Published matrices (I15 only; historical I03-I14 evidence untouched): SECRET_SAFETY_MATRIX, PATH_TRAVERSAL_MATRIX, SYMLINK_ESCAPE_MATRIX, CORRUPTION_MATRIX, RESOURCE_BOUNDS_MATRIX, MANIFEST_SCAN_MATRIX (+ BLOC_04_I15_HARDENING_EVIDENCE.md).

```
SENSOR-B4-I15
PASS_SENSOR_B4_I15_HARDENING_SECURITY_SEALED          = PENDING_OPERATOR_REVIEW
next_checkpoint_authorized                            = FALSE
recommended_next                                      = OPERATOR REVIEW OF SENSOR-B4-I15
I16+                                                  = UNAUTHORIZED
G4-13                                                 = NOT_YET_IMPLEMENTED / PENDING_LATER_CHECKPOINT
research                                              = FROZEN
```

No self-ratification. I16 not started. STOP after I15.

---

## SENSOR-B4-I15R1 TOCTOU CUSTODY + FRESH CORRUPTION RE-MEASUREMENT

**Type:** hardening microseal closing the two operator-review blockers on the I15 checkpoint. **Base HEAD:** bc6d5e059f3d039235dbcc4769658819146ff7db. **Historical evidence diff:** ZERO. **I15 matrices and the I15 ledger section are NOT modified** — I15 remains valid historical hardening evidence; I15R1 is append-only correction evidence.

### 1. TOCTOU — RED reproduced, then closed

**RED (at the I15 head, before the R1 repair):** a deterministic test drove the existing atomic.FaultPoint.BEFORE_PUBLISH seam — precisely between containment validation (resolve_under_root) and final-name creation (os.link). The hook swapped the `blobs` component to a link to an outside directory. Result: `LocalBlobStore.put_bytes` SUCCEEDED and the immutable blob landed OUTSIDE the configured root (outside/sha256/40/91/<sha>.blob). A true race permitted an outside-root mutation — BLOCKING.

**Repair (smallest compatible production change), in `atomic.publish_no_replace` which now accepts a `containment_root`:**
1. verify BEFORE any namespace is created — typed refusal if the final parent does not resolve inside the root;
2. POSIX: re-open the parent chain component-by-component with O_NOFOLLOW from the resolved root and link with `dst_dir_fd=<open parent>` (descriptor-relative; a swap after the open cannot redirect the commit);
3. cross-platform: verify AFTER the commit and REVERT + refuse typed as `AtomicPublishSecurityError` if the artifact does not resolve inside the root (the guarantee where descriptor-relative link is unavailable).

Every production call site now passes its containment root: blob_store (T0A), catalog.publish_immutable_fragment (catalogs/manifests/acquisitions), json_catalog, projections (T0B), recovery. Structural reuse proven: call_sites == anchored == 5.

**Post-repair:** the same check/use swap at BOTH blobs and staging refuses typed with outside-root mutation count = 0; the static intermediate link stays refused; a link pre-placed at the exact final name cannot replace evidence; accepted root-symlink law A (configured root may itself be a link) is preserved. Platform guarantee stated exactly (POSIX = descriptor-relative link; Windows = verify-before/after with revert). Measured platform this run: win32 (posix_descriptor_relative_available = false).

### 2. Fresh corruption re-measurement (one current-run row per durable subsystem)

Every row: valid state committed, durable invariant tampered AFTER commit, old repository/service instances destroyed, FRESH instance constructed, operation attempted; each row records fresh_instance = true and repair_on_read = false. No row is satisfied only by citing an existing suite.

| Subsystem | Tamper | Fresh operation | Outcome |
|---|---|---|---|
| T0A | payload byte flipped | fresh LocalBlobStore.verify_blob | QUARANTINED_ACCEPTED |
| acquisition | fragment overwritten | fresh get_acquisition | FAIL_CLOSED_TYPED |
| manifest | fragment overwritten (pointer binding) | fresh get_current_manifest | FAIL_CLOSED_TYPED |
| T0B | projection payload overwritten | fresh ProjectionArtifactRepository.verify_physical | FAIL_CLOSED_TYPED |
| revision | segment overwritten | fresh SourceRevisionRegistry + resolve(ALL) | FAIL_CLOSED_TYPED |
| job/checkpoint | job state overwritten | fresh DurableJobStateRepository.get_job | FAIL_CLOSED_TYPED |
| export | pack object overwritten | fresh EvidencePackVerifier + EvidencePackRestorer | FAIL_CLOSED_TYPED (no final-root promotion) |
| DuckDB (A) | duckdb file overwritten | fresh rebuild_duckdb_catalog | REBUILD_DISPOSABLE_STATE |
| DuckDB (B) | durable evidence under the catalog overwritten | fresh rebuild_duckdb_catalog | FAIL_CLOSED_TYPED (bad truth NOT canonized) |
| recovery/quarantine | hostile unknown + corrupt partial in staging | fresh RecoveryEngine.scan | QUARANTINED_ACCEPTED (valid T0A preserved) |

UNSAFE_SILENT_ACCEPTANCE did not occur. The 10,000-manifest-row scan was NOT repeated: the reader path was not touched and its I15 result (created = scanned = 10000, invalid_rows = 0, duplicate_logical_ids = 0) stands.

### 3. Regressions (after final code)

Focused: test_i15r1_toctou 2 + test_i15r1_fresh_corruption 11 + test_i15_hardening 17 + test_i15_resource_bounds 12 = 42 passed. Storage regressions: core path/blob/catalog/manifest/json_catalog/atomic/namespace 197 passed / 3 skipped; projections/revisions/duckdb/quota/retention/utilities 588 passed; recovery/job-state/I04/I05/I06 318 passed / 1 skipped; I07-I10 241 passed; I11-I14 285 passed / 23 skipped; final atomic-refactor validation 165 passed / 2 skipped. ZERO deterministic failures. The known concurrency flake did not reappear this run.

Tooling: Ruff clean on changed scope (2 pre-existing findings in untouched test_i08_evidence.py); mypy storage = 10 errors all pre-existing in probes/providers (0 new); compileall OK. external_ci = NONE_OBSERVED.

Published I15R1 evidence: BLOC_04_I15R1_TOCTOU_MATRIX.json (9/9), BLOC_04_I15R1_FRESH_CORRUPTION_MATRIX.json (10/10), BLOC_04_I15R1_EVIDENCE_CORRECTION.md.

```
SENSOR-B4-I15R1
PASS_SENSOR_B4_I15_HARDENING_SECURITY_SEALED              = OPERATOR_HOLD
PASS_SENSOR_B4_I15R1_TOCTOU_FRESH_CORRUPTION_SEALED       = PENDING_OPERATOR_REVIEW
next_checkpoint_authorized                                = FALSE
recommended_next                                          = OPERATOR REVIEW OF I15 -> I15R1 CHAIN
I16+                                                      = UNAUTHORIZED
G4-13                                                     = NOT_YET_IMPLEMENTED / PENDING_LATER_CHECKPOINT
research                                                  = FROZEN
```

The I15 hardening seal is hereby advanced from PENDING_OPERATOR_REVIEW to OPERATOR_HOLD (two blockers closed; operator review of the combined I15 -> I15R1 chain remains open).

No self-ratification. I16 not started. STOP after I15R1.

---

## SENSOR-B4-I15R1 — INDEPENDENT VERIFICATION CORRECTION (append-only)

An independent verification pass over the I15R1 head found two things the
first pass had got wrong, and corrected both. Nothing above was rewritten; I15
matrices and historical I03-I14 evidence are untouched.

**1. The first test measured the wrong seam.** `FaultPoint.BEFORE_PUBLISH` is
raised by `LocalBlobStore.put` BEFORE `publish_no_replace` is entered, so it
proves an already-swapped-at-entry refusal, not the residual window INSIDE the
writer between its own containment check / parent-descriptor open and
`os.link`. The correct seam is the existing `OpRecorder` `OP_FINAL_LINK` hook,
which fires exactly there. Re-measured against a clean `git archive` export of
`bc6d5e059f3d039235dbcc4769658819146ff7db`: at the I15 head the residual seam
SUCCEEDS and lands 1 artifact outside the configured root (the decisive RED);
at the I15R1 head the same seam is refused `AtomicPublishSecurityError` with 0
outside-root mutations. A pre-repair counterfactual row (R1 primitive disabled
in-process = exact I15-head semantics) reproduces the escape at that seam, so
the seal is earned by the production primitive and not by the harness. TOCTOU
matrix is now 11 rows / 11 OK / 0 FAIL / 1 synthetic counterfactual;
outside-root mutation count = 0.

**2. Regression introduced by the first R1 repair — found and fixed.** The first
repair compared `os.path.realpath()` results as plain strings. On Windows
CPython's `ntpath.realpath` keeps the `\\?\` extended-length prefix whenever its
post-strip re-resolution check fails, so the SAME directory is spelled two
different ways and valid concurrent writes were refused
`AtomicPublishSecurityError`. `_real_path()` now normalises `\\?\` and
`\\?\UNC\` on both sides of every containment comparison (no-op on POSIX);
containment semantics are unchanged and both TOCTOU seams still refuse with 0
outside-root mutations. Concurrent-writer trials, 15 each, back to back: I15
head 5 pass; I15R1 unfixed 3/10; I15R1 fixed 8.

**Residual, pre-existing, reported and NOT fixed under I15R1:** the known
concurrency flake remains at the I15 head's own rate, from two Windows path-API
causes that exist at `bc6d5e05` before any I15R1 code — `resolve_under_root`
(I15) raising `UnsafeObjectKey` on the same prefix instability, and
`ensure_durable_directory` (I03) raising `ValueError: components must be
nonempty` on a transient `Path.exists()`. Both fail CLOSED. Closing them would
reopen accepted I15/I03 code and needs its own authorized checkpoint.

**3. Second RED found by this pass and closed: the STAGING SOURCE of the atomic
link was unguarded.** The first repair anchored only the DESTINATION. The
`os.link` source sits in the same check/use window, so swapping the staging
namespace at the final-link seam published ATTACKER bytes under an
already-verified content address while the receipt asserted the genuine digest
— a silent content-integrity violation inside the root, measured as
`PUT_SUCCEEDED / COMMITTED_NEW`, receipt `9bb24023…`, published blob
`84e3b4d2…`. `publish_no_replace` now captures the staged artifact's
`(st_dev, st_ino)` identity before the window opens, requires the staged
source to still resolve inside the containment root immediately before the
commit, and requires the published NAME to report the SAME identity immediately
after it — otherwise the artifact is unlinked, the commit reverted and refused
typed as `AtomicPublishSecurityError`. Platform-neutral, no descriptor-relative
source required (`st_ino` is the Windows file index and a hard link shares it
with its source). Post-repair the same substitution is refused with 0 artifacts
published; the vacuous-check counterfactual still publishes foreign bytes and
is recorded as the measured RED. TOCTOU matrix is now **13 rows / 13 OK / 0
FAIL / 2 synthetic counterfactuals**; outside-root mutations = 0, foreign bytes
published = 0.

**Verification totals after the correction:** focused I15R1 + I15 = 42 passed /
0 failed; full storage = 1791 passed / 11 skipped / 0 failed; full project
`quant-lab/tests` = 3170 passed / 12 skipped / 0 failed. An earlier full-project
run reported 1 failure in `test_i07r1h_evidence`; its diff named exactly the
three I15 matrices and the cause was operator error — `git checkout` of those
matrices was run WHILE the suite was executing, between that test's before/after
directory-hash snapshots. Re-run without touching the worktree: 0 failed.
Reported, not hidden. (Earlier full-storage runs before the C2/C4 repairs
measured 1787 passed / 4 failed; all four re-measured in isolation — 3
environmental `git show` subprocess `STATUS_DLL_INIT_FAILED` failures in the
long run, all 3 passing alone, and 1 the pre-existing flake above.) Ruff clean;
compileall clean; mypy 10 pre-existing errors in `providers/`, 0 in
`atomic.py`. I15 matrices unchanged (informational timing rewrites reverted,
never staged). I11R2 governance-binding audit byte-stable, no new test file
names. external_ci = NONE_OBSERVED.

```
SENSOR-B4-I15R1
PASS_SENSOR_B4_I15_HARDENING_SECURITY_SEALED              = OPERATOR_HOLD
PASS_SENSOR_B4_I15R1_TOCTOU_FRESH_CORRUPTION_SEALED       = PENDING_OPERATOR_REVIEW
next_checkpoint_authorized                                = FALSE
recommended_next                                          = OPERATOR REVIEW OF I15 -> I15R1 CHAIN
I16+                                                      = UNAUTHORIZED
G4-13                                                     = NOT_YET_IMPLEMENTED / PENDING_LATER_CHECKPOINT
research                                                  = FROZEN
```

No self-ratification. I16 not started. STOP after I15R1.

## SENSOR-B4-I15R2 — Windows concurrent publication stability + path-normalization consistency

**Operator review finding closed.** I15R1 closed the security defects, but
concurrent identical writers remained ~50% unstable on Windows under the
accepted `TestConcurrency::test_concurrent_identical_writers_one_final`. Both
causes fail CLOSED, so no integrity property was violated — but a ~50% failure
rate on an ordinary safe write is not acceptable for ratification. This
microseal closes ONLY those two concurrency defects.

**Defect A — the canonicalization authority was split.** `atomic._real_path()`
normalized the Windows extended-length `\?\` prefix while `paths.resolve_under_root()`
compared a RAW `Path.resolve()`. Raw `Path.resolve()` is not a canonicalization
authority on Windows: `ntpath.realpath` strips the prefix only when its own
post-strip re-resolution check succeeds, so the SAME physical directory is
spelled `C:\...` by one call and `\?\C:\...` by the next. Reproduced
DETERMINISTICALLY with no concurrency at all — the raw
`root not in target.parents` test returns False for a legitimate child,
surfacing as `UnsafeObjectKey`. `paths.canonical_real_path()` is now the single
canonicalization authority and `paths.is_within_real_root()` the single
containment predicate; `atomic._real_path()` is a delegating alias. A test row
requires the prefix logic to exist in exactly ONE module. The `normcase` audit
result is deliberate: NO explicit case folding, because `PureWindowsPath` is
already case-insensitive and `PurePosixPath` is not — lowercasing would merge
two genuinely different POSIX directories and WEAKEN containment.

**Defect B — the `ensure_durable_directory` walk-up race.** The entry guard
saw the target ABSENT; the walk-up loop re-probed the same path; another
writer created the complete chain in that window; `missing` collapsed to `[]`;
`ensure_durable_directory_chain(target, [])` raised
`ValueError("components must be nonempty")` for a legitimate concurrent
creation. Reproduced deterministically through an injected `exists_probe`
seam with NO sleeps, by re-executing the verbatim pre-repair walk-up and
asserting it raises. The repair makes concurrent creation of the same valid
directory IDEMPOTENT: the target is re-checked and returned only if it is an
existing PLAIN DIRECTORY; a symlink, file or other object still fails closed
and is left untouched. Correctness comes from idempotent creation and atomic
no-clobber publication — NEVER from a retry loop, and NEVER from catching
`ValueError` / `UnsafeObjectKey` / `AtomicPublishSecurityError` at
`LocalBlobStore.put`; no such catch exists in the writer. The NAME-MAX probe is
now revalidated as the same plain directory immediately before and after, with
NO guessed 255 fallback — the I03 filesystem-truth law is preserved.

**Measured.** Baseline at start head `67fd2271a`: 15 trials x 8 identical
writers = 11 green / 4 red, all `VALUE_ERROR_COMPONENTS_EMPTY`. After the
repair: **100 trials x 8 identical writers, 100 green / 0 red**, every trial
exactly 1 COMMITTED_NEW + 7 REUSED_EXISTING, 0 unexpected exceptions, 1 final
immutable object, final hash verified. Distinct-payload stress: every expected
SHA exactly once as a durable content identity, no crosstalk, all hashes
verify — not overfit to the same-hash race. A benign same-hash publication-race
loser still resolves `AtomicPublishTargetExists` -> verify winner ->
REUSED_EXISTING and is never converted into a generic security refusal.

**Security not traded for availability.** The I15R1 malicious TOCTOU matrix was
re-run unchanged: 13 rows / 13 OK, outside-root mutations = 0, foreign bytes
published = 0, and both synthetic counterfactuals still demonstrate the
escapes they exist to prove. Root-as-link law A preserved; symlink containment
not weakened.

**One I15R1 row re-measures differently — reported, NOT rewritten.** The
`final_name_preexisting_link` row's informational `refusal` field re-measures
as `UnsafeObjectKey` where the committed I15R1 bytes say `NotADirectoryError`.
Cause: the planted object is a broken reparse point, so `Path.resolve()` raised
an untyped `OSError` that escaped `put()`; the shared `is_within_real_root()`
now fails CLOSED on that `OSError` and refuses EARLIER and TYPED. The row's
result is OK before and after, `outside_file_untouched` is true before and
after, and outside-root / foreign-byte counts are unchanged. Per the
append-only rule the committed I15R1 bytes are preserved and the delta is
recorded in `BLOC_04_I15R2_EVIDENCE_CORRECTION.md` §5. Operational
consequence: re-running the I15R1 suite leaves that one matrix dirty — revert
it, never stage it.

**Transient long-run failure window — reported, NOT hidden.** The FIRST
full-storage run reported 29 failed / 1803 passed / 2 errors, all in three
DuckDB-backed projection modules against hard-coded `C:\tmp_*` roots with
Windows filesystem errors. Investigated rather than dismissed: those modules
pass 89/89 in isolation; a full-storage run EXCLUDING only the two new I15R2
test files (production changes still applied) is 1791 passed / 11 skipped / 0
failed, exactly the I15R1 baseline, proving the production repair introduces no
failure; a full-storage run INCLUDING them then re-ran 1832 passed / 13 skipped
/ 0 failed. Conclusion: transient Windows filesystem/handle window, not a
deterministic interaction with the repair and not caused by it. Not recorded as
a "known flake".

**Verification totals.** Focused I15R2 = 41 passed / 2 skipped / 0 failed (2
platform skips: true symlinks need privilege on Windows, which uses junctions).
I15R1 TOCTOU + fresh corruption + I15 hardening re-run = 30 passed / 0 failed.
I11R2 governance-binding audit = 14 passed, regenerated mechanically for the 2
new tracked test filenames (`python_files_scanned` 995 -> 997, no new
unexpected hits) and BYTE-STABLE on the no-update re-run. Full storage = 1832
passed / 13 skipped / 0 failed. Full project `quant-lab/tests` = 3211 passed /
14 skipped / 0 failed. Ruff clean on the changed scope; compileall clean; mypy
10 pre-existing errors in `providers/` and `probes/`, 0 in `paths.py` or
`atomic.py`; secret scan clean. I03–I14, I15 and I15R1 matrices unchanged. The
only historical artifact touched is the I11R2 binding audit, regenerated per the
new-test-filename rule. POSIX runtime TOCTOU =
NOT_MEASURED_ON_THIS_HOST (Windows host: `os.supports_dir_fd` empty, no
`os.O_DIRECTORY`, so that branch never executes here) with POSIX_STRUCTURAL_PATH
= VERIFIED (per-component `O_DIRECTORY|O_NOFOLLOW` relative opens and
`dst_dir_fd` on `os.link`, proven structurally); no POSIX runtime result is
fabricated. external_ci = NONE_OBSERVED (0 runs on this branch, 0 check-runs,
0 statuses at head).

**Scope honoured.** No change to staged-source inode anchoring, destination
parent containment, post-commit revert, the POSIX descriptor-relative parent
walk, the fresh-corruption matrix, secret safety or resource bounds. No retry
added. No security error downgraded, swallowed or retried. No POSIX case
folding. Research FROZEN. I16 NOT STARTED. No self-ratification.

```
SENSOR-B4-I15R2
PASS_SENSOR_B4_I15_HARDENING_SECURITY_SEALED              = OPERATOR_HOLD
PASS_SENSOR_B4_I15R1_TOCTOU_FRESH_CORRUPTION_SEALED       = OPERATOR_HOLD
PASS_SENSOR_B4_I15R2_CONCURRENT_PUBLICATION_STABILITY_SEALED = PENDING_OPERATOR_REVIEW
next_checkpoint_authorized                                = FALSE
recommended_next                                          = OPERATOR REVIEW OF COMPLETE I15 -> I15R1 -> I15R2 CHAIN
I16+                                                      = UNAUTHORIZED
G4-13                                                     = NOT_YET_IMPLEMENTED / PENDING_LATER_CHECKPOINT
research                                                  = FROZEN
```

No self-ratification. I16 not started. STOP after I15R2.

## SENSOR-B4-I15R2-RATIFY — OPERATOR ACCEPTANCE OF THE COMPLETE I15 -> I15R1 -> I15R2 CHAIN

**Start gate verified at the mandatory head.** Branch
`agent/crypto-sensor-fabric-build`, HEAD
`2a856e656f9da4b2749fa1b999e58ae26f4234be`, origin build == local HEAD,
origin/main `7c7816f382947bbc8a1f2154435fc436f2428fa8` untouched, worktree
clean, and governance showing I15 = OPERATOR_HOLD, I15R1 = OPERATOR_HOLD,
I15R2 = PENDING_OPERATOR_REVIEW, `next_checkpoint_authorized` = FALSE. All
seven chain commits verified as strict linear ancestors with no merge, rebase,
amend or squash.

**REPORT_CORRECTION (§3) — prose understated the RED baseline incidence.** The
prior prose summary reported the I15R2 baseline as 15 trials x 8 writers =
11 green / 4 red with `UNSAFE_OBJECT_KEY` x0. The **committed authoritative**
`BLOC_04_I15R2_CONCURRENT_PUBLICATION_MATRIX.json` records
`baseline_reproduction_at_start_head` as trials 15, writers_per_trial 8,
total_workers 120, **green_trials 8, red_trials 7**, failure classes
**UNSAFE_OBJECT_KEY = 12, VALUE_ERROR_COMPONENTS_EMPTY = 4**,
ATOMIC_PUBLISH_SECURITY_ERROR = 0, OTHER = 0. Both records sit at the same
start head `67fd2271a`; the matrix row carries frozen `BASELINE_*` constants
from the earlier I15R1-era probe while the prose came from a separate
`run_identical_writer_trial` probe whose sample did not hit the
`UnsafeObjectKey` class. **The matrix is authoritative and was NOT modified.**
This correction does NOT change the post-repair verdict, which is separately
measured and independently re-measured green. The correction strengthens the
I15R2A repair case: the `UnsafeObjectKey` class is now attested at real
incidence (12 worker failures) in the committed baseline.

**RATIFIED.** Secret safety (13/13, repo scan clean, sentinel absent from
durable metadata, URL/header/DSN credentials refused and redacted, no leak in
errors, raw RESPONSE evidence exact and unredacted); traversal containment
(36/36, outside-root mutations 0, 0 shell execution artifacts); static symlink
escape (7/7); hardlink mutation as a typed integrity failure, never silent
acceptance; fresh corruption R1 (10/10, every row `fresh_instance` true and
`repair_on_read` false, no UNSAFE_SILENT_ACCEPTANCE); the DuckDB two-law model
(A disposable/rebuild, B fail-closed, DuckDB non-authoritative); resource
hardening (16/16) including **10,000 ACTUAL VALID manifest rows, 10,000
scanned, 0 invalid, 0 duplicate logical IDs**, write throughput measured
separately and NOT misrepresented as 10k append throughput, I09 disk watermark
policy preserved; destination TOCTOU custody and staging-source substitution
(I15R1 **13/13 OK, outside-root mutations 0, foreign bytes published 0**,
both counterfactuals still demonstrating their escape); root-as-link law A
preserved.

**Shared canonical authority ratified.** `paths.canonical_real_path()` is THE
canonical real-path authority and `paths.is_within_real_root()` THE shared
containment predicate; `atomic._real_path`/`_is_within` are delegating aliases.
Extended-prefix normalization logic exists in EXACTLY ONE module (`paths.py`),
enforced by a test row scanning the storage package. `C:\dir` and `\\?\C:\dir`
are one authority; `\\?\UNC\server\share` normalizes to `\\server\share` as a
pure string law with no live share required; a genuine outside extended path is
still refused. **No `normcase`/lowercase/casefold anywhere in `paths.py` or
`atomic.py`** — deliberate, because `PureWindowsPath` is already
case-insensitive while `PurePosixPath` is not, so folding would merge two
genuinely different POSIX directories and WEAKEN containment. No POSIX
authority widening.

**Directory-race closure ratified.** The pre-repair `ValueError("components
must be nonempty")` is reproduced deterministically with zero sleeps by
re-executing the verbatim pre-repair walk-up. Post-repair: a target that
appeared as a PLAIN DIRECTORY returns idempotent success; a file, link,
junction or other non-directory still fails closed and is left untouched. No
blind retry loops, no exception swallowing in `LocalBlobStore.put`. The
NAME-MAX probe stays evidence-based with parent identity/type revalidated
around it and no guessed 255 fallback; a vanished parent raises
`DurabilityUnsupported`.

**Availability proof ratified.** 100 trials x 8 identical writers: **100 green
/ 0 red**, committed_new_total 100, reused_existing_total 700, 0 unexpected
exceptions, 0 unsafe_object_key, 0 value_error_components_empty,
0 atomic_publish_security_error, 0 final-object-count violations, 0 hash
violations. Distinct-writer stress: crosstalk 0, hash_failures 0,
security_false_positives 0, every expected SHA exactly once — the repair is not
overfit to the same-hash race.

**Recorded, NOT hidden.** The `final_name_preexisting_link` row re-measures its
informational `refusal` as `UnsafeObjectKey` where the committed I15R1 bytes
say `NotADirectoryError` (broken reparse point; the old raw `Path.resolve()`
leaked an untyped `OSError` out of `put()`, the shared helper now fails closed
earlier and typed). Invariant unchanged: result OK, outside target untouched,
outside-root mutations 0. The I15R1 matrix was NOT modified. Windows junction
`is_symlink() == False` noted as a known implementation fact that does not
weaken security, since containment resolves the physical target — not a
blocker, not broadened. POSIX truth: `POSIX_STRUCTURAL_PATH` = VERIFIED
(`O_DIRECTORY`/`O_NOFOLLOW` per component, `dst_dir_fd` to `os.link`),
`POSIX_RUNTIME_TOCTOU` = **NOT_MEASURED_ON_THIS_HOST**; no POSIX runtime
evidence fabricated. The transient 29-failure run is recorded as **KNOWN
TEST-ENVIRONMENT DEBT** only (hard-coded Windows `C:\tmp_*` projection roots
under long/high-load runs): 89/89 isolated, 1791/11/0 excluding only the new
R2 tests, 1832/13/0 including them, 3211/14/0 full project. Not fixed, and no
production redesign authorized from it.

**Verification truth at the accepted head.** Combined ratification battery
(I15R2 focused, I15R1 TOCTOU + fresh corruption, I15 hardening, resource
bounds, 10k manifest scan, I03 atomic/blob concurrency, path/canonicalization,
I11R2 audit) = **253 passed / 2 skipped / 0 failed**. Full storage =
**1832 passed / 13 skipped / 0 failed**. Full project =
**3211 passed / 14 skipped / 0 failed**. ZERO deterministic failures. Ruff
clean on every file the I15 chain changed (the only 2 repo-wide findings are
pre-existing F401/F811 in `test_i08_evidence.py`, last touched at I08C and
untouched by this chain); compileall clean; mypy 10 pre-existing errors in
`providers/`+`probes/`, **0** in `paths.py` or `atomic.py`; secret scan clean.
`external_ci = NONE_OBSERVED` (0 statuses, 0 check-runs, 0 runs on this branch).
No new Python test was added, so the I11R2 binding audit was NOT republished
and stays byte-stable at 997 scanned files.

**Historical evidence law honoured.** Every informational rewrite produced by
re-running the suites was inspected and the historical bytes RESTORED before
diff and before commit; the remeasurement was never staged. All 256 evidence
artifacts verified byte-identical to their committed state. **Production diff =
ZERO.**

```
SENSOR-B4-I15R2-RATIFY
PASS_SENSOR_B4_I15_HARDENING_SECURITY_SEALED              = OPERATOR_ACCEPTED
PASS_SENSOR_B4_I15R1_TOCTOU_FRESH_CORRUPTION_SEALED       = OPERATOR_ACCEPTED
PASS_SENSOR_B4_I15R2_CONCURRENT_PUBLICATION_STABILITY_SEALED = OPERATOR_ACCEPTED
next_checkpoint_authorized                                = TRUE
next_checkpoint                                           = SENSOR-B4-I16 FINAL ACCEPTANCE + EVIDENCE PACKET
authorized_scope                                          = I16 ONLY
I17+                                                      = UNAUTHORIZED
G4-13                                                     = NOT_YET_IMPLEMENTED / PENDING_I16_OR_LATER_AS DEFINED
research                                                  = FROZEN
recommended_next                                          = SENSOR-B4-I16 IMPLEMENTATION
```

**I16 frozen contract.** I16 must RUN ALL G4 GATES and PRODUCE FINAL BLOC 4
EVIDENCE. It was NOT implemented in this run. Its verdict must be EARNED from
the gates, never preselected. Allowed Bloc 4 verdict vocabulary:
`PASS_BLOC_04_IMPLEMENTED`,
`PASS_BLOC_04_IMPLEMENTED_WITH_DATA_VOLUME_LIMITS`,
`BLOCKED_BLOC_04_INTEGRITY`, `BLOCKED_BLOC_04_STORAGE_CAPACITY`,
`FAIL_BLOC_04_ATOMICITY`, `FAIL_BLOC_04_LINEAGE`, `FAIL_BLOC_04_RESTORE`.
G4-13 is NOT earned by this ratification and must be evaluated by I16 alongside
all other G4 gates.

**I17 firewall.** I16 authorization does NOT authorize I17 Bloc 5 handoff,
normalization implementation, research restart, provider redesign, storage
architecture redesign, new query semantics or new revision semantics. I17
remains blocked until I16 final acceptance. Research stays FROZEN.

Ratification artifact:
`research/crypto_foundry/sensor_fabric/evidence/bloc_04/BLOC_04_I15_CHAIN_OPERATOR_RATIFICATION.md`

No production defect was found requiring a source change; no repair checkpoint
is issued. I16 not started. STOP after ratification.---

## 148 — SENSOR-B4-I16 FINAL BLOC 4 ACCEPTANCE + EVIDENCE PACKET

**Checkpoint:** SENSOR-B4-I16 FINAL ACCEPTANCE + EVIDENCE PACKET
**Start head (mandatory):** `e5294529f4b603c8ec10bc21e2e24c7a97044ca7`
**Branch:** `agent/crypto-sensor-fabric-build`
**Production diff:** ZERO
**Authorized scope:** I16 ONLY — respected

### Governance

```
PASS_SENSOR_B4_I16_FINAL_ACCEPTANCE_EVIDENCE_SEALED = BLOCKED

BLOC_04_FINAL_VERDICT = I16_G4_13_UNIT_HANDOFF_CONTRACT_GAP

all_G4_gates
  G4-01 EXACT_EVIDENCE        = PASS
  G4-02 ATOMIC_DURABILITY     = PASS
  G4-03 IMMUTABILITY          = PASS
  G4-04 REVISION              = PASS
  G4-05 MANIFEST              = PASS
  G4-06 LINEAGE               = PASS
  G4-07 MISSINGNESS           = PASS
  G4-08 STORAGE_PRESSURE      = PASS
  G4-09 CATALOG_REBUILD       = PASS
  G4-10 OPERATIONAL_METADATA  = PASS_WITH_STATED_ENVIRONMENT_LIMITATION
  G4-11 EXPORT_RESTORE        = PASS
  G4-12 BLOC3_HANDOFF         = PASS
  G4-13 BLOC5_READINESS       = FAIL

next_checkpoint_authorized = FALSE

recommended_next
  = OPERATOR REVIEW / NARROW REPAIR OF G4-13 UNIT HANDOFF CONTRACT

I17+     = UNAUTHORIZED
research = FROZEN
```

### G4-13 — the deciding measurement

G4-13 entered I16 as `NOT_YET_IMPLEMENTED` and was measured, not assumed.

**PASS dimensions** — SOURCE, TIMESTAMP and LINEAGE are reachable through
public typed contracts. Two distinct storage roots produced a byte-identical
public evidence view with no absolute path in any field. The test-only Bloc 5
consumer was proven free of filesystem traversal, private APIs and absolute
roots. Bloc 4 added no `effective_at`, `observed_at` or canonical fields.

**FAIL dimension — UNIT.** `I16_G4_13_UNIT_HANDOFF_CONTRACT_GAP`

| Probe | Measurement |
|-------|-------------|
| `RawNormalizationBatch` field count | 20 |
| Unit-named fields on the batch | none |
| Unit-named exports in `storage.__all__` | none (194 names) |
| Public `UNIT_UNVERIFIED` enum member | absent |
| `to_descriptor()` provider-native field keys | `name`, `type`, `nullable` |
| Consumer `native_unit` / `unit_state` | `NOT_REACHABLE` |

A unit string was deliberately embedded in the raw fixture bytes to demonstrate
that "raw bytes contain it somewhere" is not a contract and does not count.

The `unit` strings present under `storage/` are Arrow **temporal** type units,
not market or native units. `NativeOIUnit` / `native_unit` live in
`crypto_sensor_fabric/schemas/open_interest.py` and the probe packages, which
the `storage` package does not reference.

### Minimal repair scope (§35 — proposed, NOT implemented)

One additive source-unit evidence field pair on `RawNormalizationBatch`:

- `native_unit: str | None`
- `unit_state: <enum>` including at minimum an explicit `UNIT_UNVERIFIED`

populated from the T0 acquisition / projection contract at commit time.

**Out of scope:** canonical units, USD/base/quote normalization, `effective_at`,
any PIT decision, any Bloc 5 normalization logic.

**Acceptance criterion:** re-run `test_i16_g4_13_readiness.py` unchanged. Its
reachability assertion is written to fail loudly if unit evidence ever becomes
reachable, so the gate is self-falsifying in both directions.

### Blocking-condition audit (§29)

10 of 11 frozen blocking conditions measured NOT PRESENT. One PRESENT:
"Bloc 5 needs provider-specific filesystem knowledge" — unit dimension only.
This is a contract gap, not corruption: no stored byte is wrong and no identity
is ambiguous.

### Regression (§31)

| Phase | Passed | Failed | Skipped |
|-------|--------|--------|---------|
| Focused G4 | 90 | 0 | 0 |
| Full storage | 1922 | 0 | 13 |
| Full project | 3301 | 0 | 14 |

Full storage is exactly +90 against the I15R2 baseline of 1832 — the 90 I16
tests — with skips unchanged.

Two regressions were found and fixed during I16, both in new I16 test code or
I16 procedure, never in production:

1. The accepted I15 secret scanner correctly rejected a credential-shaped DSN
   literal in my own I16B fixture. The fixture now assembles the credential at
   runtime; the redaction proof is unchanged.
2. The I11R2 binding audit drifted because new tracked Python files and a
   suite-dirtied evidence tree change what it measures. Historical matrices were
   restored to committed bytes (§32) and the audit mechanically regenerated and
   verified byte-stable (§40).

### Static / security (§33) and external CI (§34)

Ruff clean on all I16 changed scope; accepted baseline shows the same 2
pre-existing `test_i08_evidence.py` findings as I15R2. compileall OK. mypy: 0
errors in changed production scope, 10 pre-existing in `providers/**`. Secret
scan clean. `external_ci = NONE_OBSERVED` (0 statuses, 0 check-runs). Local
pytest is not described as CI.

### Evidence custody (§32)

Final historical evidence diff: ZERO, with the single §40-authorized regeneration
of `BLOC_04_I11R2_GOVERNANCE_BINDING_AUDIT.json`.

### Evidence packet

`research/crypto_foundry/sensor_fabric/evidence/bloc_04/`:
`BLOC_04_I16_G4_GATE_MATRIX.json`, `BLOC_04_I16_TEST_REPORT.json`,
`BLOC_04_I16_INVARIANTS.json`, `BLOC_04_I16_CRASH_MATRIX.json`,
`BLOC_04_I16_REVISION_MATRIX.json`, `BLOC_04_I16_STORAGE_LAYOUT.json`,
`BLOC_04_I16_QUOTA_SIMULATION.json`, `BLOC_04_I16_DUCKDB_REBUILD.json`,
`BLOC_04_I16_RESTORE_TEST.json`, `BLOC_04_I16_BLOC4_READINESS.json`,
`BLOC_04_I16_FINAL_ACCEPTANCE_EVIDENCE.md`, plus per-gate evidence for G4-01
through G4-12.

### Notes

- The verdict field carries the gap ID verbatim. No frozen §2/§36 word describes
  a handoff-contract gap, and §36 forbids improvising vocabulary.
  `FAIL_BLOC_04_LINEAGE` would be factually false — the G4-13 LINEAGE dimension
  passed. Operator directed the gap ID be recorded.
- §30 volume classification was never reached, because no PASS verdict was
  earned. Its absence is not an affirmative finding that no volume ceiling
  exists.
- No self-ratification. I17 NOT started. STOP.
## 149 — SENSOR-B4-I16R1 G4-13 SOURCE-UNIT HANDOFF CONTRACT REPAIR + FINAL GOVERNANCE CORRECTION

**Checkpoint:** SENSOR-B4-I16R1 G4-13 SOURCE-UNIT HANDOFF CONTRACT REPAIR + FINAL GOVERNANCE CORRECTION
**Start head (mandatory):** `618de97827a22b2514caa4178d5cffa4ea76d1b7`
**Branch:** `agent/crypto-sensor-fabric-build`
**Production diff:** ADDITIVE ONLY — `storage/enums.py`, `storage/models.py`,
`storage/projection_schema.py`, `storage/replay.py`, `storage/__init__.py`.
No historical contract was rewritten; historical descriptors and batches load
unchanged.
**Authorized scope:** I16R1 ONLY — respected. I17 NOT started.

### Governance (I16 history preserved; verdict field corrected, not rewritten)

```
PASS_SENSOR_B4_I16_FINAL_ACCEPTANCE_EVIDENCE_SEALED   = OPERATOR_HOLD
PASS_SENSOR_B4_I16R1_G4_13_UNIT_HANDOFF_REPAIR_SEALED = PENDING_OPERATOR_REVIEW

BLOC_04_FINAL_VERDICT = PASS_BLOC_04_IMPLEMENTED

all_G4_gates
  G4-01 EXACT_EVIDENCE        = PASS
  G4-02 ATOMIC_DURABILITY     = PASS
  G4-03 IMMUTABILITY          = PASS
  G4-04 REVISION              = PASS
  G4-05 MANIFEST              = PASS
  G4-06 LINEAGE               = PASS
  G4-07 MISSINGNESS           = PASS
  G4-08 STORAGE_PRESSURE      = PASS
  G4-09 CATALOG_REBUILD       = PASS
  G4-10 OPERATIONAL_METADATA  = PASS_WITH_STATED_ENVIRONMENT_LIMITATION
  G4-11 EXPORT_RESTORE        = PASS
  G4-12 BLOC3_HANDOFF         = PASS
  G4-13 BLOC5_READINESS       = PASS

all_G4_gates overall = IMPLEMENTATION_PASS_PENDING_OPERATOR_REVIEW

next_checkpoint_authorized = FALSE
recommended_next           = OPERATOR REVIEW OF I16 -> I16R1 FINAL BLOC 4 CHAIN

I17+     = UNAUTHORIZED
research = FROZEN
```

### Governance correction (§2) — append-only

```
gap_id                          = I16_G4_13_UNIT_HANDOFF_CONTRACT_GAP
blocking_reason                 = G4-13 UNIT evidence not publicly reachable
historical_I16_final_verdict_field
                                = NONCANONICAL / SUPERSEDED_BY_I16R1_CORRECTION
```

The frozen final-verdict vocabulary was never changed; the I16 field outside
it is preserved as history in ledger section 148 and in
`BLOC_04_I16_FINAL_ACCEPTANCE_EVIDENCE.md`, and superseded by this correction.

### The repair and the proof

I16 measured G4-13 UNIT as not publicly reachable. I16R1A audited all eight
frozen sensor families before touching any model
(`BLOC_04_I16R1_UNIT_SEMANTIC_AUDIT.json`) and proved a single scalar
`native_unit` is not semantically sufficient: book snapshots carry a unit per
price level, and funding / basis / positioning carry no unit field at all.

I16R1B then added the smallest additive durable contract: `SourceUnitState`
(`VERIFIED_NATIVE` / `UNIT_UNVERIFIED`) and `SourceUnitEvidence`
(`field_name`, `native_unit_lexeme`, `state`) as public storage vocabulary; an
additive `source_unit_evidence` declaration on the durable
`ProjectionSchemaDefinition` that participates in the schema fingerprint and
is validated on every registry reload; and `Bloc5Handoff.to_batch` copying the
durable declarations verbatim into
`RawNormalizationBatch.source_unit_evidence`. Unknown units fail closed as
`UNIT_UNVERIFIED` and are never guessed from provider names, instruments,
fixture maps, Bloc 5 rules, row content or raw bytes.

I16R1C remeasured G4-13 through a new narrow Bloc 5 consumer probe that
imports only public `crypto_sensor_fabric.storage` contracts: SOURCE, TIME,
UNIT (known + unknown + multi-field), LINEAGE, PATH_INDEPENDENCE and
NEGATIVE_IMPORT all PASS (`BLOC_04_I16R1_G4_13_UNIT_HANDOFF_MATRIX.json`,
`BLOC_04_I16R1_BLOC4_READINESS.json`). The old I16 negative test is
preserved as a write-free checkpoint-fossil validator and every I16 artifact
is byte-identical.

### §18 timestamp wording correction

`actual_start` / `actual_end`:
`FIELD_PUBLICLY_AVAILABLE = true` / `FIXTURE_VALUE_PRESENT = false`. They are
public typed `AcquisitionRecord` fields; the standard fixture simply left
their values unset. They were never structurally unavailable. No production
change was made or needed.

### Volume classification (§23)

`PASS_BLOC_04_IMPLEMENTED` — no accepted scale ceiling affects supported use.
The 10,000-row actual manifest scan, 1 GiB-equivalent streaming hash, 64
MiB-equivalent T0A streaming write, content dedupe, DuckDB many-projection
rebuild, revision-chain scale, query result bounds and the export ceilings are
configurable operational guardrails with accepted priority behavior (G4-08:
T0A auto-delete count = 0), not an unsupported ceiling.

### Regression (§26)

| Phase | Passed | Failed | Skipped |
|-------|--------|--------|---------|
| Focused I16R1 + all current G4 suites | 131 | 0 | 0 |
| All-G4 rerun (G4-01..G4-12 suites) | 71 | 0 | 0 |
| Full storage | 1963 | 0 | 13 |
| Full project | 3342 | 0 | 14 |

Full storage is exactly +41 against the I16 baseline of 1922 with the same 13
skips: 60 R1 tests were added (audit 6, contract 29, positive 18) and the
19-test I16 current-tree readiness file became a 7-test write-free fossil
validator (+41 = 6 + 29 + 18 + 7 − 19).

### Static / security (§28) and external CI (§30)

Ruff clean on all changed scope; compileall OK; mypy 0 errors in changed
production files (the same 10 pre-existing `providers/**` findings as the
I15R2 baseline); the accepted I15 repository secret scan runs clean over
source, tests and evidence. `external_ci = NONE_OBSERVED` at the start head
(0 statuses, 0 check-runs, 0 runs). Local pytest is not described as CI.

### Evidence custody (§32/§27)

Historical evidence diff after all runs: ZERO for every `BLOC_04_I16_*`
artifact and every older measured matrix; the single authorized republish is
`BLOC_04_I11R2_GOVERNANCE_BINDING_AUDIT.json` per §40 (one line:
`python_files_scanned` 1001 → 1005 because I16R1 added four tracked Python
files). I16R1 produced only `BLOC_04_I16R1_*` evidence.

### Notes

- No self-ratification. I16R1 seal is PENDING_OPERATOR_REVIEW. I17 NOT
  started. Research FROZEN.
## 150 — SENSOR-B4-I16R2 SOURCE-UNIT CLAIM TRUTH + UNIT-LOCATION CONTRACT REPAIR + FINAL GOVERNANCE CORRECTION

**Checkpoint:** SENSOR-B4-I16R2 SOURCE-UNIT CLAIM TRUTH + UNIT-LOCATION CONTRACT REPAIR + FINAL GOVERNANCE CORRECTION
**Start head (mandatory):** `e8d1384d98771c39cb119e2cae0ff93296be02ec`
**Branch:** `agent/crypto-sensor-fabric-build`
**Production diff:** ADDITIVE ONLY — `storage/enums.py`, `storage/models.py`,
`storage/projection_schema.py`, `storage/projections.py`, `storage/replay.py`,
`storage/__init__.py`. No historical contract was rewritten; historical
descriptors and batches load unchanged.
**Authorized scope:** I16R2 ONLY — respected. I17 NOT started.

### Governance (I16 / I16R1 history preserved; append-only)

```
PASS_SENSOR_B4_I16_FINAL_ACCEPTANCE_EVIDENCE_SEALED           = OPERATOR_HOLD
PASS_SENSOR_B4_I16R1_G4_13_UNIT_HANDOFF_REPAIR_SEALED         = OPERATOR_HOLD
PASS_SENSOR_B4_I16R2_UNIT_AUTHORITY_TRUTH_SEALED              = PENDING_OPERATOR_REVIEW

BLOC_04_FINAL_VERDICT = PASS_BLOC_04_IMPLEMENTED

all_G4_gates
  G4-01 EXACT_EVIDENCE        = PASS
  G4-02 ATOMIC_DURABILITY     = PASS
  G4-03 IMMUTABILITY          = PASS
  G4-04 REVISION              = PASS
  G4-05 MANIFEST              = PASS
  G4-06 LINEAGE               = PASS
  G4-07 MISSINGNESS           = PASS
  G4-08 STORAGE_PRESSURE      = PASS
  G4-09 CATALOG_REBUILD       = PASS
  G4-10 OPERATIONAL_METADATA  = PASS_WITH_STATED_ENVIRONMENT_LIMITATION
  G4-11 EXPORT_RESTORE        = PASS
  G4-12 BLOC3_HANDOFF         = PASS
  G4-13 BLOC5_READINESS       = PASS

all_G4_gates overall = IMPLEMENTATION_PASS_PENDING_OPERATOR_REVIEW

next_checkpoint_authorized = FALSE
recommended_next           = OPERATOR REVIEW OF COMPLETE I16 -> I16R1 -> I16R2 FINAL BLOC 4 CHAIN

I17+     = UNAUTHORIZED
research = FROZEN
```

### The findings I16R2 repaired

1. **Static claim truth gap (RED reproduced).** The I16R1 contract let a
durable `ProjectionSchemaDefinition` declare `VERIFIED_NATIVE("SOL")` for
`quantity_unit` while every committed projection row said `BTC`, and
`Bloc5Handoff.to_batch` exposed the declared claim to Bloc 5. The RED probe
(`.bu_tmp/i16r2_red_probe.py`) reproduced both counterexamples against the
real T0B commit path: RED-1 all-BTC rows with a SOL declaration ->
COMMIT_SUCCEEDED; RED-2 mixed SOL/BTC rows -> COMMIT_SUCCEEDED with the
static claim silently collapsed. Recorded in
`BLOC_04_I16R2_REAL_UNIT_PROJECTION_AUDIT.json#red_reproduction`.

2. **Unit-location contract gap.** The I16R1 contract could express only a
top-level field name pair (`field_name` + lexeme/state); book snapshots
carry a unit per price level (`bids[]/asks[].quantity_unit`), which is not
expressible as a scalar. Recorded in
`BLOC_04_I16R2_REAL_UNIT_PROJECTION_AUDIT.json`.

3. **Stale row-11 note.** `BLOC_04_I16R1_BLOCKING_CONDITION_AUDIT.json` row 11
carried note prose ("This is the ONLY frozen blocking condition that
remains...") that contradicted the artifact's own machine fields
(`measured = NOT PRESENT`, `summary.present = 0`,
`bloc_4_completion_blocked = false`). The note is corrected append-only in
`BLOC_04_I16R2_EVIDENCE_CONSISTENCY_CORRECTION.md`; the frozen artifact is
preserved byte-for-byte.

4. **Population conflation.** No production code registers a
`ProjectionSchemaDefinition`; I16R1 proved contract capability, not current
population. I16R2 measures and reports this explicitly:
`CAPABILITY_PROVEN_POPULATION_ZERO`.

### The repair and the proof (I16R2A -> I16R2B -> I16R2C)

I16R2B added the smallest additive contract that makes a static claim
truth-bound and a row-varying/nested unit location expressible:
`SourceUnitVariability` / `SourceUnitContract` enums;
`SourceUnitEvidence.field_path` (deterministic structural path tuple),
`.variability` and `.resolved_field_path` with validators;
`resolve_unit_field_path` resolving a path against the registered Arrow
schema (list element step = Arrow list value-field name, struct steps =
child names, terminal string field, no `_t0_` component);
`RawNormalizationBatch.source_unit_contract`; the T0B commit-boundary scan
(`write_projection` step "2b") that proves a `VERIFIED_NATIVE` lexeme against
every committed non-null value and raises the typed
`ProjectionUnitEvidenceConflict` (MISMATCH / MIXED / ALL_NULL) before durable
publication; and `Bloc5Handoff.to_batch` copying the durable declarations
verbatim. The scan is bounded O(1) memory (distinct-state short-circuit,
never collects all values).

I16R2C remeasured G4-13 through the real registration + commit + handoff +
public-consumer path over supported offline fixtures
(`BLOC_04_I16R2_G4_13_MATRIX.json`, overall PASS) and emitted the 12-case
claim-truth matrix (`BLOC_04_I16R2_UNIT_CLAIM_TRUTH_MATRIX.json`: 7 typed
refusals - mismatch 3, mixed 2, all-null 2 - with no durable projection
created after any refusal, and 5 commits including partial-null matching,
unknown preservation and row-native/nested locations). The book-snapshot
physical shape resolves as ROW_LEVEL_NESTED (flat alternative NOT PROVEN).

### Regression (§26)

| Phase | Passed | Failed | Skipped |
|-------|--------|--------|---------|
| Focused I16R2 + current G4 suites | 187 | 0 | 0 |
| All-G4 rerun (G4-01..G4-12 suites) | 71 | 0 | 0 |
| Full storage | 2018 | 1 (expected I11R2 staleness, closed by §40 republish) | 13 |
| Full project | 3398 | 0 | 14 |

Full storage is exactly +56 against the I16R1 baseline of 1963 with the same
13 skips: claim 9 + integrity 4 + location 22 + real-provider 18 + R2 positive
3. The single failure was the §40-mandated I11R2 staleness from six new
tracked Python files (1005 -> 1011); the audit was mechanically regenerated
and verified byte-stable (no-update rerun 4 passed), and the subsequent
full-project run at the repaired tree reports zero failures.

### Static / security (§28) and external CI (§30)

Ruff clean on all changed scope (the only findings are the 2 accepted
pre-existing ones in `test_i08_evidence.py`); compileall OK; mypy 0 errors in
changed production files (the same 10 pre-existing `providers/**` findings as
the I15R2/I16/I16R1 baseline); the accepted I15 repository secret scan runs
clean. `external_ci = NONE_OBSERVED` for this branch (0 workflow runs on
`agent/crypto-sensor-fabric-build`; 0 check-runs and 0 statuses at the last
pushed build head `e8d1384d9`). Other programs' workflows in this repository
never targeted this branch. Local pytest is not described as CI.

### Evidence custody (§32/§27)

All `BLOC_04_I16_*` and `BLOC_04_I16R1_*` artifacts are byte-identical to the
start head; I16R2 produced only new `BLOC_04_I16R2*` evidence plus the single
authorized §40 republish `BLOC_04_I11R2_GOVERNANCE_BINDING_AUDIT.json`
(one line). The eleven historical matrices dirtied by suite runs were restored
to committed bytes; I16R2 rewrote no historical artifact.

### Notes

- No self-ratification. The I16R2 seal is PENDING_OPERATOR_REVIEW. I17 NOT
  started. Research FROZEN. STOP.
## 151 — SENSOR-B4-I16R2 OPERATOR REVIEW PACKET PREPARED (GOVERNANCE UNCHANGED)

**Prepared per operator request:** `BLOC_04_I16_CHAIN_OPERATOR_REVIEW_PACKET.md`
indexes the complete I16 -> I16R1 -> I16R2 chain evidence (identity and strict
ancestry, what each checkpoint measured and repaired, the 13-gate matrix, the
11 blocking conditions, every append-only correction, official limitations,
verification at the chain end, and the evidence index) for the pending seal
decision. This section records preparation only; it advances no checkpoint and
changes no seal.

Governance remains exactly as section 150:

```
PASS_SENSOR_B4_I16_FINAL_ACCEPTANCE_EVIDENCE_SEALED           = OPERATOR_HOLD
PASS_SENSOR_B4_I16R1_G4_13_UNIT_HANDOFF_REPAIR_SEALED         = OPERATOR_HOLD
PASS_SENSOR_B4_I16R2_UNIT_AUTHORITY_TRUTH_SEALED              = PENDING_OPERATOR_REVIEW
BLOC_04_FINAL_VERDICT = PASS_BLOC_04_IMPLEMENTED
next_checkpoint_authorized = FALSE
I17+     = UNAUTHORIZED
research = FROZEN
```

No self-ratification. The seal decision remains the operator's. No production
change was made to produce the packet. I17 NOT started. STOP.
## 152 — SENSOR-B4-I16R2-RATIFY: FINAL BLOC 4 OPERATOR ACCEPTANCE, I17 HANDOFF AUTHORIZED

**Mandate:** SENSOR-B4-I16R2-RATIFY — final Bloc 4 operator acceptance of the
complete I16 -> I16R1 -> I16R2 chain, plus I17 BLOC 5 handoff authorization
DOCUMENTATION ONLY
**Branch:** agent/crypto-sensor-fabric-build
**Mandatory start HEAD:** `2cf6f1c9fe1e20e55594b179ede57d7f36e1e30f`
**Actual ratification start HEAD:** `aa29933156fa78716089d05adc530934e246bea7`
**origin/main (untouched):** `7c7816f382947bbc8a1f2154435fc436f2428fa8`
**Production diff:** ZERO
**Authorized scope:** FINAL RATIFICATION OF I16 -> I16R1 -> I16R2 ONLY.
I17 NOT implemented in this run. I18+ UNAUTHORIZED. Research FROZEN.

### Start-gate deviation (operator-adjudicated)

Every start-gate item matched the directive exactly except HEAD, which was one
commit ahead: `aa2993315`, the operator review packet produced in the
preceding operator-accepted task and pushed before this mandate was issued. It
contains 2 files (new review packet MD +300, ledger +24), **0 production source
files**, no seal change and no checkpoint advanced; `2cf6f1c9f` is a strict
ancestor of it, so the ratified chain is a superset of the mandated chain. The
operator was shown this and decided to **ratify from `aa2993315` with the
deviation recorded**. Reaching `2cf6f1c9f` exactly would have required a reset,
rebase or force push — all forbidden. No reset, rebase, amend, squash or force
push was performed.

### Ratification battery at the ratification start head

Focused (I16R2 + I16R1 + all-G4 + I15 hardening/scale/TOCTOU + I14 handoff +
I13 export/restore, 24 files) = **390 passed / 4 skipped / 0 failed** (533 s).
**Full storage on the FINAL TREE after I11R2 regeneration = 2019 passed /
13 skipped / 0 failed** (1253 s) — the direct final-tree measurement the
operator required; the earlier `2018 + 1 expected staleness failure` figure was
pre-regeneration. **Full project = 3398 passed / 14 skipped / 0 failed**
(1228 s). ZERO deterministic failures. Ruff: exactly 2 pre-existing findings in
the untouched `test_i08_evidence.py` (lines 33, 786); **changed scope
`src/crypto_sensor_fabric/storage` = All checks passed**. compileall OK. mypy:
10 pre-existing errors in 6 files (probes/planner.py:79; providers/rest.py:91,
93,96; okx/probe.py:34; kraken/probe.py:49; gate/probe.py:45,279,298;
deribit/probe.py:33), **0 in changed scope**. Secret scan 4 passed, matrix
13/13 rows ok. I11R2 binding audit no-update run 4 passed, **byte-stable at
1011 scanned files**, `unexpected_hits = {}`, **NOT republished**. External CI
= **NONE_OBSERVED** (0 check-runs, 0 statuses, 0 runs on this branch).
Historical evidence custody: **0** `BLOC_04_I16_*` / `I16R1_*` / `I16R2_*`
artifacts modified; the 11 suite-dirtied historical evidence JSONs were
inspected and RESTORED before diff and before commit.

### Ratified facts

Strict linear ancestry: all 11 operator-named SHAs plus 2 further chain
commits (I16A, I16B) are ancestors of the ratification start HEAD; 13 commits
in range, 0 merges, first-parent == full, 0 squash/amend/revert/fixup subjects.
Production source changed in exactly two chain commits — I16R1B (5 files) and
I16R2B (6 files). Historical chronology preserved: **I16 correctly found and
preserved a G4-13 unit handoff failure** (I16D sealed BLOCKED); **I16R1 added
the public source-unit handoff capability but was later found to contain a
static-claim truth gap**; **I16R2 closed the static-claim truth gap and the
unit-location gap and re-earned every G4 gate.** Earlier checkpoints are NOT
rewritten as though they had always passed.

Both RED counterexamples remain immutable historical counterexamples
(pre-repair `COMMIT_SUCCEEDED` with the handoff falsely exposing
`VERIFIED_NATIVE/SOL`; and the mixed-row claim silently collapsed). Post-repair
both are `COMMIT_REFUSED:ProjectionUnitEvidenceConflict`, with all-null also
refused and partial-null-with-matching-values accepted under the accepted null
law; refusal occurs BEFORE durable publication and is never a silent
downgrade. Validation is bounded and O(1) (`_UnitClaimScan`, six scalar
`__slots__`, one remembered lexeme, null count, rows inspected, chunked walk,
conflict short-circuit; no value accumulation, no unbounded lexeme set, no
whole-projection materialization introduced for unit validation). The unit
location contract distinguishes `STATIC_VERIFIED` / `ROW_NATIVE` /
`UNIT_UNVERIFIED`, and `NO_UNIT_FIELDS` / `UNIT_EVIDENCE_DECLARED` /
historical absence, with no empty-list ambiguity. Nested book-snapshot paths
such as `("bids", "item", "quantity_unit")` resolve list and struct steps
explicitly against the registered Arrow schema, require a string terminal,
refuse the reserved `_t0_` namespace, fail closed on unresolvable paths, and
serialize deterministically as a JSON list with no dotted-string ambiguity.
`Bloc5Handoff` stays metadata-only: it copies declarations verbatim and never
scans rows, normalizes units, converts base/quote, computes notional, assigns a
canonical asset or assigns `effective_at`. `UNIT_UNVERIFIED` never carries a
lexeme and is never auto-promoted from row content, provider name, symbol or raw
bytes. `ROW_NATIVE` marks a durable location and fabricates no batch-level
static unit; Bloc 4 still performs no canonical normalization. Historical
descriptors without I16R1/R2 unit metadata keep verifying under the historical
fingerprint law and never become `NO_UNIT_FIELDS` or `VERIFIED_NATIVE`.

G4-13: overall PASS. **Precision note recorded, not smoothed over** — the
committed dimension table has 6 rows (`SOURCE`, `TIME`, `UNIT`, `LINEAGE`,
`PATH_INDEPENDENCE`, `NEGATIVE_IMPORT`); `TRUTH_BINDING` is recorded as the
G4-13 gate-row `truth_binding` object (committed 5 / refused 7, MISMATCH 3,
MIXED 2, ALL_NULL 2, `silent_downgrade false`, PASS) and as
`summary.g4_13_truth_binding = PASS`. All seven named dimensions PASS; no
dimension inferred.

All 13 G4 gates PASS with current-head proofs (`all_thirteen_measured = true`,
`any_pass_without_current_measured_proof = false`), G4-10 carrying its stated
**no-live-DSN** environment limitation (no `SENSOR_FABRIC_POSTGRES_DSN` or
`DATABASE_URL` in this environment; the decision rests on the current-head
contract test plus accepted I11 live evidence). All **11 blocking conditions
NOT PRESENT, 0 PRESENT** (`previously_present_ids = [11]`), `bloc_4_completion_blocked
= false`; condition 11 ("Bloc 5 needs provider-specific filesystem knowledge")
is NOT PRESENT because source/unit/time/lineage are public typed handoff
evidence. The stale I16R1 row-11 prose note remains in its artifact, whose
authoritative machine fields already said `measured = NOT PRESENT` and
`summary.present = 0`; the contradiction was corrected append-only in
`BLOC_04_I16R2_EVIDENCE_CONSISTENCY_CORRECTION.md` and history was NOT rewritten.

**Production schema population is ZERO and is recorded as a known limitation,
not as a G4-13 failure:**
`BLOC_04_UNIT_CONTRACT_CAPABILITY = PROVEN`,
`PRODUCTION_SCHEMA_POPULATION = ZERO_AT_BLOC4_BOUNDARY` (0 production
`ProjectionSchemaDefinition` constructions, 0 registered schemas carrying
`source_unit_evidence`, exhaustive `src` search; verdict
`CAPABILITY_PROVEN_POPULATION_ZERO`). The frozen G4-13 contract asks about the
public handoff surface (capability), which Bloc 4 supplies. No claim is made
that real provider production schemas are already registered. The
"real-provider offline" proofs mean supported-family committed fixtures driven
through registration -> commit -> unit truth validation -> handoff -> public
consumer, with **network_calls = 0** and no live provider execution.

### Governance

**Vocabulary decision, recorded explicitly.** The operator's preferred label
`OPERATOR_ACCEPTED_AS_SUPERSEDED_STAGE` is **not** established vocabulary in
this repository — the historical chain seals use `OPERATOR_ACCEPTED` (I11, I12,
I13, I14, I15). Per the directive's own fallback, explicit status/prose fields
are used here instead of inventing a misleading PASS state, and **no PASS state
was created for the historical I16 block.**

```
SENSOR-B4-I16R2-RATIFY

I16_HISTORICAL_G4_13_BLOCK_STATUS =
    OPERATOR_ACKNOWLEDGED_AS_CORRECTLY_MEASURED_HISTORICAL_BLOCK
    / SUPERSEDED_BY_I16R1_THEN_I16R2
    (NOT accepted as a passing stage; NOT relabeled)

PASS_SENSOR_B4_I16_FINAL_ACCEPTANCE_EVIDENCE_SEALED =
    HISTORICAL_BLOCK_SUPERSEDED
    (the I16D evidence packet keeps its published BLOCKED verdict unchanged)

PASS_SENSOR_B4_I16R1_G4_13_UNIT_HANDOFF_REPAIR_SEALED =
    ACCEPTED_AS_SUPERSEDED_STAGE_ONLY
    (public source-unit handoff capability accepted; its static-claim truth gap
     accepted as a real weakness that I16R2 closed)

PASS_SENSOR_B4_I16R2_UNIT_AUTHORITY_TRUTH_SEALED = OPERATOR_ACCEPTED

BLOC_04_FINAL_VERDICT   = PASS_BLOC_04_IMPLEMENTED
BLOC_04_IMPLEMENTATION  = OPERATOR_ACCEPTED
all_G4_gates            = OPERATOR_ACCEPTED_PASS

next_checkpoint_authorized = TRUE
next_checkpoint            = SENSOR-B4-I17 BLOC 5 HANDOFF
authorized_scope           = I17 ONLY
I18+                       = UNAUTHORIZED
research                   = FROZEN
recommended_next           = SENSOR-B4-I17 IMPLEMENTATION
```

No data-volume suffix: the accepted volume classification is unchanged
(configurable operational guardrails with accepted priority behavior, not an
unsupported supported-use ceiling).

### I17 frozen scope and firewall

I17 is a HANDOFF/DOCUMENTATION checkpoint: *"Document stable public
interfaces, schema versions, known limitations, and normalization-ready
evidence contract."* **I17 DOES NOT AUTHORIZE** Bloc 5 normalization
implementation, provider redesign, live network work, canonical asset logic,
unit conversions, `effective_at` logic, research restart, or storage
architecture redesign.

Carry-forward items (documentation items for I17, **not** Bloc 4 blockers):
**A** `PRODUCTION_SCHEMA_POPULATION = ZERO_AT_BLOC4_BOUNDARY`; **B** G4-10's
no-live-DSN limitation, supported by accepted prior I11 live evidence plus the
current contract proof; **C** POSIX runtime TOCTOU structurally verified but
`POSIX_RUNTIME_TOCTOU = NOT_MEASURED_ON_THIS_HOST` on the Windows I15 host (no
POSIX runtime evidence fabricated); **D** historical contracts without unit
metadata remain distinguishable; **E** Bloc 5 owns canonical units, base/quote
transformations, notional normalization, canonical asset identity, and
`effective_at` / PIT semantic decisions.

Ratification artifact:
`research/crypto_foundry/sensor_fabric/evidence/bloc_04/BLOC_04_I16_CHAIN_OPERATOR_RATIFICATION.md`

No production defect was found requiring a source change, so no repair
checkpoint is issued. **I17 NOT started in this run.** Research FROZEN. STOP
after ratification.

## 153 — SENSOR-B4-I17 FINAL BLOC 4 -> BLOC 5 HANDOFF (DOCUMENTATION FREEZE)

**Mandate:** SENSOR-B4-I17 — document stable public interfaces, schema versions,
known limitations and the normalization-ready evidence contract
**Branch:** agent/crypto-sensor-fabric-build
**Start head:** `fb813728f32d6e518ed9911470388aec24c1e83e`
**origin/main (untouched):** `7c7816f382947bbc8a1f2154435fc436f2428fa8`
**Production source diff:** ZERO (verified: `src/` is byte-identical to the start head)
**Authorized scope:** I17 ONLY. Bloc 5 normalization implementation
UNAUTHORIZED. I18+ UNAUTHORIZED. Research FROZEN.

I17 is a DOCUMENTATION / CONTRACT FREEZE. It implemented no canonical unit, no
base/quote conversion, no contract multiplier, no USD notional, no canonical
asset identity, no `effective_at`/`observed_at`, no PIT transformation logic, no
provider redesign, no live network logic, no research restart and no storage
architecture redesign.

### Artifacts (7 new, +1995 lines, all documentation)

* `BLOC_04_I17_PUBLIC_INTERFACE_MATRIX.json` — 52 entries; 44 `STABLE_FOR_BLOC5`,
  5 `STABLE_WITH_DOCUMENTED_LIMITATION`, 0 `HISTORICAL_COMPAT_ONLY`, 3
  `INTERNAL_NOT_PUBLIC` (counts recomputed mechanically from the entries, never
  hand-written).
* `BLOC_04_I17_SCHEMA_VERSION_MATRIX.json` — identity vs fingerprint, semver
  validation, registry conflict law, unit-declaration versioning, historical
  descriptor compatibility, 8-row schema compatibility table.
* `BLOC_04_I17_BLOC5_HANDOFF_CONTRACT.md` — the normative contract.
* `BLOC_04_I17_KNOWN_LIMITATIONS.json` — 14 limitations, 0 open Bloc 4 blockers.
* `BLOC_04_I17_NORMALIZATION_OWNERSHIP.json` — ownership split, overlap 0,
  unassigned 0.
* `BLOC_04_I17_DOWNSTREAM_PROHIBITIONS.json` — 24 hard prohibitions (listed 24 =
  declared 24, verified).
* `BLOC_04_I17_HANDOFF_EXAMPLE.md` — the executed end-to-end example.

### Public-interface truth (§3/§4/§40)

`crypto_sensor_fabric.storage.__all__` = **200** exported symbols. Every
operator-named symbol was resolved by machine introspection. Two corrections
were required and are recorded rather than papered over:

* **`ProjectionArtifact` does not exist.** The public projection record is
  **`RawProjectionArtifact`**, which IS exported. No aspirational API is
  documented as existing.
* **`Granularity` is not re-exported by `storage`.** It lives in
  `crypto_sensor_fabric.probes.enums` — a base enum module with no provider
  adapter and no network. Likewise `SensorFamily`
  (`crypto_sensor_fabric.contracts.enums`) and
  `QualityFlagAcquisition` / `SchemaState` / `AdapterEvidenceRef` / `ResumeToken`
  (`providers.base.*`) are public but not re-exported; each is recorded with its
  real import path.

**Public-contract gap assessment: `stop_condition_triggered = false`.** The
"revision-resolution public interfaces" requirement resolves to the public
surface `RevisionResolver.key_for/resolve` + `RevisionPolicy` + `RevisionState` +
`SourceRevision` + `RawEvidenceResult.revision_state`.
`SourceRevisionRegistry` and `RevisionSourceIdentityV1` are internal and are NOT
needed by Bloc 5, so no private API is blessed. `rebuild_duckdb_catalog` /
`ReadOnlyDuckDBCatalog` and `Bloc3StorageHandoff` are deliberately non-public and
are likewise not required.

**Doc-to-code consistency check: PASS** (0 failures). 45 documented-public
entries all resolve and are exported; 7 documented-non-public entries are
genuinely absent from `__all__`; 18 section-4 checklist rows consistent; the
three unit vocabularies still have exactly their frozen members. The check ran
untracked from `.bu_tmp/` so I17 added no Python file at all.

### Ratified laws frozen for Bloc 5

`RawNormalizationBatch` = 22 public fields classified as SOURCE_IDENTITY,
TIME_EVIDENCE, UNIT_EVIDENCE, LINEAGE, COVERAGE/QUALITY, INTEGRITY/REVISION and
DESCRIPTOR_ONLY; it is **NORMALIZATION-READY EVIDENCE, NOT normalized science
data**. Source identity (provider, venue, sensor_family, native_instrument,
source_granularity, schema id/version, parser_version) is evidence and must never
be turned into a storage path. Preserved time facts (`logical_time_range_*`,
`requested_*`, `actual_*`, `request_started_at`, `response_observed_at`,
`ingested_at`, `date_basis`) are separated from Bloc 5 canonical decisions
(`effective_at`, canonical observed time, provider-time interpretation, PIT
semantics), and **I17 introduced none of them**. `provider_time_raw`,
`provider_time_parsed`, `provider_time_unit_assumption` and
`provider_publication_time` were re-measured as **structurally absent** from every
public handoff model; only nullable `min_provider_time`/`max_provider_time` exist
on `RawProjectionArtifact`.

Unit contract: `SourceUnitState` (VERIFIED_NATIVE | UNIT_UNVERIFIED),
`SourceUnitVariability` (STATIC_VERIFIED | ROW_NATIVE | UNIT_UNVERIFIED) and
`SourceUnitContract` (NO_UNIT_FIELDS | UNIT_EVIDENCE_DECLARED) are three
independent vocabularies and are not blurred; absent marker +
`HISTORICAL_UNIT_CONTRACT_ABSENT` is a third, distinct state. `VERIFIED_NATIVE`
is truth-bound at T0B commit time (mismatch / mixed / all-null refuse before
durable publication; no silent downgrade), so Bloc 5 may rely on the proof.
`ROW_NATIVE` declares *where* native unit truth lives as a structural tuple path
and fabricates no batch lexeme. `UNIT_UNVERIFIED` is an explicit unknown and
never licenses a guess. The eight-family unit matrix is frozen, with book
snapshot = `ROW_LEVEL_NESTED_SUPPORT_REQUIRED` and the flat alternative NOT
PROVEN.

`BLOC_04_UNIT_CONTRACT_CAPABILITY = PROVEN` and
`PRODUCTION_SCHEMA_POPULATION = ZERO_AT_BLOC4_BOUNDARY` (0 production
`ProjectionSchemaDefinition` constructions, 0 registered schemas carrying
`source_unit_evidence`) are carried prominently and **not hidden**; offline
supported-family fixtures are **not** converted into a production-population
claim (`network_calls = 0`).

Lineage, revision, missingness, integrity, query, path-independence, DuckDB,
Postgres, export/restore, Bloc 3 causality, security and resource laws are all
frozen (see the contract). DuckDB is disposable acceleration and is not public;
Postgres is operational metadata only and fully reconstructible, and the G4-10
no-live-DSN limitation is carried without claiming any new live run; evidence
packs restore into a new empty root with identity/hash/query/revision/lineage
parity; a checkpoint never precedes its durable manifest commit. `NONE` never
becomes numeric zero. **POSIX runtime TOCTOU remains
`NOT_MEASURED_ON_THIS_HOST`** — structurally verified only, no runtime evidence
fabricated. All measured ceilings are configurable operational guardrails, which
is why the Bloc 4 verdict carries no data-volume suffix.

### Validation

Focused (public authority + I05R1 fingerprint law + I12 query/replay +
I16R1 contract + I16R1/R2 G4-13 + all-G4 + readiness fossil) = **244 passed /
0 failed** (150 s). **Full storage = 2019 passed / 13 skipped / 0 failed**
(1240 s). **Full project = 3398 passed / 14 skipped / 0 failed** (1119 s).
One load-only warning appeared during the full storage run
(`test_manifest_concurrency.py::test_readers_never_observe_partial_pointer`,
`PytestUnhandledThreadExceptionWarning`, a Windows temp-dir teardown race in a
reader thread raising `CurrentPointerCorrupt`); the test **passed**, the file
passes 4/4 in isolation at both the I17 head and the start head, and I17 changed
no source — it is the already-recorded Windows test-environment debt, recorded
here rather than hidden. Ruff: exactly 2 pre-existing findings in untouched
`test_i08_evidence.py`; `src/crypto_sensor_fabric/storage` **All checks
passed**. mypy: 10 pre-existing errors in 6 files, **0** in changed scope.
compileall OK. Secret scan 4 passed. I11R2 audit **not republished**: no-update
run 4 passed, byte-stable at **1011** scanned files, `unexpected_hits = {}`.
`external_ci = NONE_OBSERVED` (0 check-runs, 0 statuses, 0 runs on this branch).
Historical evidence custody: the suite-dirtied historical JSONs were inspected
and RESTORED before diff and before commit; **no I01..I16R2 artifact and no
ratification artifact was modified.**

### Handoff contract status

```
BLOC_04_TO_BLOC_05_HANDOFF_CONTRACT = DOCUMENTED
NORMALIZATION_READY_EVIDENCE        = TRUE
BLOC_05_NORMALIZATION_IMPLEMENTED   = FALSE
PRODUCTION_SCHEMA_POPULATION        = ZERO_AT_BLOC4_BOUNDARY
```

### Governance

```
SENSOR-B4-I17

PASS_SENSOR_B4_I17_BLOC5_HANDOFF_SEALED = PENDING_OPERATOR_REVIEW
BLOC_04_TO_BLOC_05_HANDOFF_CONTRACT     = DOCUMENTED
NORMALIZATION_READY_EVIDENCE            = TRUE
BLOC_05_NORMALIZATION_IMPLEMENTED       = FALSE
PRODUCTION_SCHEMA_POPULATION            = ZERO_AT_BLOC4_BOUNDARY
BLOC_04_FINAL_VERDICT                   = PASS_BLOC_04_IMPLEMENTED
BLOC_04_IMPLEMENTATION                  = OPERATOR_ACCEPTED
next_checkpoint_authorized              = FALSE
recommended_next                        = OPERATOR REVIEW OF SENSOR-B4-I17 HANDOFF
I18+                                    = UNAUTHORIZED
research                                = FROZEN
```

I17 is **not** self-ratified. No contract gap requiring a source change was
found, so no repair checkpoint is issued. **Bloc 5 normalization NOT started.**
Research FROZEN. STOP.

## 154 — SENSOR-B4-I17-RATIFY: BLOC 4 -> BLOC 5 HANDOFF ACCEPTED, B5-I01 AUTHORIZED

**Mandate:** SENSOR-B4-I17-RATIFY — accept the final Bloc 4 -> Bloc 5 handoff and
authorize SENSOR-B5-I01 ONLY
**Branch:** agent/crypto-sensor-fabric-build
**Mandatory start HEAD:** `ab75d6738e1004b20ed8738439c2bac3ccc1d85b`
**origin/main (untouched):** `7c7816f382947bbc8a1f2154435fc436f2428fa8`
**Production diff:** ZERO
**Authorized scope:** I17 RATIFICATION ONLY. **B5-I01 NOT implemented in this
run.** B5-I02+ UNAUTHORIZED. Bloc 6 UNAUTHORIZED. Research FROZEN.

I17 is the final Bloc 4 -> Bloc 5 handoff/documentation checkpoint. It is NOT
Bloc 5 implementation and is not relabelled as such.

### Start gate

Every item matched the directive exactly: branch, HEAD == `ab75d6738`, origin
build == local HEAD, `origin/main` == `7c7816f38`, and all eleven governance
values (`PASS_SENSOR_B4_I17_BLOC5_HANDOFF_SEALED = PENDING_OPERATOR_REVIEW`,
`BLOC_04_TO_BLOC_5_HANDOFF_CONTRACT = DOCUMENTED`,
`NORMALIZATION_READY_EVIDENCE = TRUE`,
`BLOC_05_NORMALIZATION_IMPLEMENTED = FALSE`,
`BLOC_04_FINAL_VERDICT = PASS_BLOC_04_IMPLEMENTED`,
`BLOC_04_IMPLEMENTATION = OPERATOR_ACCEPTED`, `next_checkpoint_authorized =
FALSE`, `recommended_next = OPERATOR REVIEW OF SENSOR-B4-I17 HANDOFF`, `I18+ =
UNAUTHORIZED`, `research = FROZEN`). No deviation; no STOP condition triggered.

### Ancestry and zero-production-diff law

All five operator-named SHAs verified as ancestors: `fb813728f` (Bloc 4
ratification / I17 authorization), `e6b3bc7fd` (I17A), `68d2908d5` (I17B),
`b2d5ba4ab` (I17C), `ab75d6738` (I17D). 4 commits in range, **0 merges**,
first-parent == full, **0** `squash|amend|revert|fixup` subjects. No rebase, no
amend, no squash, no force push. I17 changed exactly **8 files** (1 ledger + 7
handoff/evidence documents): `src/` **0**, `tests/` **0**, config/provider/
normalization **0**.

### Ratified I17 content (all counts recomputed from source, not from prose)

A read-only recomputation script re-derived every asserted figure from the tree
and the committed artifacts: **36 checks / 36 passed / 0 failed**, plus the
doc-to-code consistency check **PASS** (45 documented-public entries resolve and
are exported, 7 documented-non-public entries are genuinely absent, 18
section-4 checklist rows consistent).

`crypto_sensor_fabric.storage.__all__` = **200**; documented interface entries =
**52**; stability counts **44 STABLE_FOR_BLOC5 / 5 STABLE_WITH_DOCUMENTED_LIMITATION
/ 0 HISTORICAL_COMPAT_ONLY / 3 INTERNAL_NOT_PUBLIC**. `RawNormalizationBatch` =
**22** public fields grouped SOURCE_IDENTITY / TIME / UNIT / LINEAGE /
COVERAGE-QUALITY / INTEGRITY-REVISION / DESCRIPTOR_ONLY, with
`NORMALIZATION_READY_EVIDENCE = TRUE` while the batch remains **not** normalized
science data. `RawEvidenceQuery` = **17** fields. `CoverageState` = **10**
members, `RevisionPolicy` = **6** members with documented default
**`ERROR_ON_AMBIGUITY`** (no silent latest selection).

**Corrected symbol truth, ratified as-is:** `ProjectionArtifact` **DOES NOT
EXIST** — the real exported symbol is **`RawProjectionArtifact`**; `Granularity`
is **NOT** exported by `crypto_sensor_fabric.storage` (real path
`crypto_sensor_fabric.probes.enums`); `SensorFamily` is **NOT** exported either
(real path `crypto_sensor_fabric.contracts.enums`). **No alias was added** to
make the earlier wording resolve.

**Private API firewall:** `rebuild_duckdb_catalog`, `ReadOnlyDuckDBCatalog`,
`Bloc3StorageHandoff`, `SourceRevisionRegistry` and `RevisionSourceIdentityV1`
are all absent from the public surface, and no documented entry is a private `_`
API. Revision resolution stays public through `RevisionResolver` +
`RevisionPolicy`. **No private interface is ratified as stable.**

Unit handoff truth ratified: three non-collapsed vocabularies plus the distinct
`HISTORICAL_UNIT_CONTRACT_ABSENT` third state; `VERIFIED_NATIVE` is **truth-bound
at the T0B commit boundary**, refusals precede durable publication, no silent
downgrade, and Bloc 5 may rely on the proof but may **not** reinterpret it as a
canonical unit without its own normalization logic; `ROW_NATIVE` identifies
*location* via structural tuple paths and fabricates no batch lexeme; the flat
book-snapshot representation remains **NOT PROVEN**; all eight frozen families
documented at their I16R2-final shapes; `BLOC_04_UNIT_CONTRACT_CAPABILITY =
PROVEN` with `PRODUCTION_SCHEMA_POPULATION = ZERO_AT_BLOC4_BOUNDARY` accepted and
carried into Bloc 5, with **no offline fixture converted into a
production-population claim**.

Schema/version truth ratified as-is: `schema_key` identifies `id@version`,
`schema_fingerprint` identifies structural content, strict semver **form** is
enforced, and **no automatic major/minor/patch compatibility matrix exists**
because the source does not implement one.

Ownership **8 Bloc 4 / 10 Bloc 5, overlap 0, unassigned 0**. Prohibitions
**24 declared = 24 listed**. Known limitations **14, with 0 open Bloc 4
blockers**. DuckDB is disposable acceleration and not a stable public contract;
Postgres is operational metadata/state only, and the **no-live-DSN** G4-10
limitation is carried with **no new live DB claim**. Export/restore restores into
an unrelated empty root with hash/identity/query/revision/lineage parity and no
original-root dependency. Bloc 3 -> Bloc 4 causality holds: a resume checkpoint
never precedes manifest durability.

### Executed example

Documentation/proof only, stopping **before** normalization, `network_calls = 0`,
explainable entirely through accepted public contracts: trade
`STATIC_VERIFIED`; book snapshot nested `ROW_NATIVE`; funding `NO_UNIT_FIELDS`;
static unit mismatch `ProjectionUnitEvidenceConflict` with **no durable
projection created**.

### Windows thread warning — classified, not fixed

The I17 full-storage run emitted a load-only
`PytestUnhandledThreadExceptionWarning` (Windows temp-directory teardown race in
a reader thread). The test passed, the file passes 4/4 isolated, `src/` is
byte-identical to the I17 start head, and both suites completed with 0 failures.
**Classification: KNOWN TEST-ENVIRONMENT DEBT, NOT an I17 source regression.**
It did **not** reappear in this ratification's full-storage run, and it was not
fixed here (no repair under ratification).

### Final verification

Focused (public interface/import, schema-version/fingerprint, Bloc5Handoff,
G4-13, I16R2 unit truth + location, revision/query/missingness) = **244 passed /
0 failed** (205 s). **Full storage = 2019 passed / 13 skipped / 0 failed**
(1481 s). **Full project = 3398 passed / 14 skipped / 0 failed** (1355 s).
**Zero deterministic failures.** Ruff: 2 pre-existing findings in untouched
`test_i08_evidence.py`; `src/crypto_sensor_fabric/storage` **All checks passed**;
**no new I17 findings**. mypy: 10 pre-existing errors in 6 files under
`probes/`/`providers/`, **no new I17 findings**. compileall OK. Secret scan 4
passed. I11R2 audit **not republished** — no-update run 4 passed, byte-stable at
**1011** scanned files, `unexpected_hits = {}`. `external_ci = NONE_OBSERVED`
(0 check-runs, 0 statuses, 0 runs on this branch). Historical custody: **zero**
published artifacts modified during this ratification; all suite-dirtied
informational matrices RESTORED before commit.

### Authorization boundary into Bloc 5

`bloc_05/07_BLOC_05_FREEZE_MANIFEST.md` already carries `PASS_BLOC_05_PLAN_FROZEN`
and the frozen 23-stage sequence; **Bloc 5 was NOT redesigned here**.
**B5-I01 = normalization enums, base normalization models, T1 envelope** only. It
does NOT authorize asset/venue registries, contract identity resolver, PIT alias
resolver, linear/inverse conversion, timestamp registry, unit conversion, sensor
normalizers, T1 writer, canonical query, golden fixtures or live network — those
belong to the later frozen stages. Frozen Bloc 5 blocking gates carried forward
**RECORD ONLY, none claimed passed by I17**: `IDENTITY_GATE`, `TIME_GATE`,
`SEMANTIC_GATE`, `UNIT_GATE`, `LINEAGE_GATE`, `DUPLICATE_REVISION_GATE`,
`REPLAY_SAFETY_GATE`, `GOLDEN_T0_T1_GATE`. **I17 establishes input readiness
only.**

Ratification artifact:
`research/crypto_foundry/sensor_fabric/evidence/bloc_04/BLOC_04_I17_OPERATOR_RATIFICATION.md`

### Governance

```
SENSOR-B4-I17-RATIFY

PASS_SENSOR_B4_I17_BLOC5_HANDOFF_SEALED = OPERATOR_ACCEPTED
BLOC_04_TO_BLOC_5_HANDOFF_CONTRACT      = OPERATOR_ACCEPTED
NORMALIZATION_READY_EVIDENCE            = TRUE
BLOC_05_NORMALIZATION_IMPLEMENTED       = FALSE
PRODUCTION_SCHEMA_POPULATION            = ZERO_AT_BLOC4_BOUNDARY
BLOC_04_FINAL_VERDICT                   = PASS_BLOC_04_IMPLEMENTED
BLOC_04_IMPLEMENTATION                  = OPERATOR_ACCEPTED

next_checkpoint_authorized = TRUE
next_checkpoint            = SENSOR-B5-I01 NORMALIZATION ENUMS / BASE MODELS / T1 ENVELOPE
authorized_scope           = B5-I01 ONLY
B5-I02+                    = UNAUTHORIZED
Bloc 6                     = UNAUTHORIZED
research                   = FROZEN
recommended_next           = SENSOR-B5-I01 IMPLEMENTATION
```

Bloc 4 is closed and accepted; the Bloc 4 -> Bloc 5 handoff contract is
operator-accepted and frozen. **Bloc 5 normalization remains unimplemented and
B5-I01 was NOT started in this run.** No production defect was found requiring a
source change, so no repair checkpoint is issued. Research FROZEN. STOP.

---

## 155 — SENSOR-B5-I01: NORMALIZATION ENUMS / BASE MODELS / T1 ENVELOPE

**Checkpoint:** SENSOR-B5-I01 — the foundational type layer of Bloc 5.
**Branch:** `agent/crypto-sensor-fabric-build`
**Start head (mandatory):** `ae152d010f3cd8c472c6dc0593a0e94f779cb079`
**Scope:** B5-I01 ONLY. B5-I02+ UNAUTHORIZED. Bloc 6 UNAUTHORIZED. Research FROZEN.
**Authority:** the seven frozen `bloc_05/0*.md` planning documents (which carry
`PASS_BLOC_05_PLAN_FROZEN`) plus the operator-accepted
`BLOC_04_I17_BLOC5_HANDOFF_CONTRACT.md`.

> **Vocabulary and container, not normalization.** B5-I01 resolves nothing. It
> adds the type layer in which a canonical observation can eventually be
> expressed and the vocabulary with which it must report that it could not be
> expressed. No identity/lifecycle/alias registry or resolver, no contract
> terms, no linear/inverse or unit conversion, no stablecoin conversion, no
> timestamp or availability derivation, no revision engine, no methodology or
> semantic registry, no sensor normalizer, no T1 writer / generation / manifest /
> storage / canonical query, no provider fixture and no network access were
> implemented. Every one of those belongs to a later frozen checkpoint.

### 0. Start gate

Verified before any edit: branch `agent/crypto-sensor-fabric-build`; HEAD
`ae152d010f3cd8c472c6dc0593a0e94f779cb079`; `origin/agent/crypto-sensor-fabric-build`
== local HEAD; `origin/main` = `7c7816f382947bbc8a1f2154435fc436f2428fa8`
(never pushed to); clean worktree. All eleven governance values in ledger §154
matched exactly. No reset, rebase, amend, squash or force push.

### 1. Type-scope inventory (done BEFORE any code)

`evidence/bloc_05/BLOC_05_I01_TYPE_SCOPE_MATRIX.json` — **61 rows: 24 implemented
at I01, 37 deferred**, each row carrying its plan section and its reason. The
enum suite was committed RED on purpose in B5-I01A, so the inventory is the
executable contract rather than a retrospective summary.

Two **measured vocabulary gaps were recorded, not invented**: `AvailabilityConfidence`
(bloc_05/02 §5 names the field but never freezes its vocabulary) and `VenueScope`
(bloc_05/01 §13 names only `MULTI_VENUE_AGGREGATE` and says "such as"). Both are
deferred; both are asserted to still be absent.

### 2. Implementation

**Production (3 files, new package `quant-lab/src/crypto_sensor_fabric/normalization/`):**
`__init__.py`, `enums.py`, `models.py`. **Tests (4 files)** in
`quant-lab/tests/crypto_sensor_fabric/normalization/`. **Evidence (4 files)** in
`research/crypto_foundry/sensor_fabric/evidence/bloc_05/`.

**Enums (10):** `PayoffType` (5), `NormalizationStatus` (8),
`MissingnessReason` (13), `NormalizationQualityFlag` (36),
`QualityDimensionState` (6), `LineageState` (3), `QuarantineReason` (7),
`IntervalTimeConvention` (4), `AvailabilityBasis` (8), `TimestampPrecision` (6).
Plus two read-only frozen correspondences: `BLOCKED_STATUS_MISSINGNESS_REASON`
(MappingProxyType) and `BLOCKING_QUALITY_FLAGS` (frozenset).

**Models (6):** `ObservationTimeEnvelope` (15 fields, all nine frozen clocks),
`NativeQuantity` (4), `T1Quality` (8 frozen dimensions, no defaults),
`T1LineageRef` (7), `T1VersionContext` (5), `T1BaseEnvelope` (27). Validated
opaque identifier types: `OpaqueIdentifier`, `T1RecordId`, `ContractInstanceId`,
`T1GenerationId`, `RegistryVersion`. Serialization: `canonical_json_bytes`.

**Public export surface:** exactly 24 names.

### 3. Frozen distinctions preserved, not collapsed

* `BLOCKED_IDENTITY` (status, bloc_05/03 §15) and `IDENTITY_BLOCKED`
  (missingness, bloc_05/05 §12) are both kept exactly as frozen and related by
  frozen read-only data rather than renamed to match each other.
* The quality-flag vocabulary is the **union** of bloc_05/05 §11's "minimum"
  list with bloc_05/01 §14 and bloc_05/02 §16 = 36 members, because §11's
  identity and time groups are strict subsets. Additive only.
* Upstream vocabularies are consumed where they already live and **zero** are
  re-declared: `SensorFamily` (`contracts.enums`), `Granularity`
  (`probes.enums`), `CoverageState`, `RevisionState`, `SourceUnitContract` and
  the `SourceUnitEvidence` model itself (public `storage`). A test intersects
  the normalization export set with the accepted 200-symbol Bloc 4 public
  surface and requires the intersection to be empty.
* The frozen full name **`T1ObservationEnvelope` is deliberately NOT exported**:
  the frozen envelope also carries identity, methodology and replay-eligibility
  fields owned by B5-I02/I09/I06, so exporting it now would let a consumer
  mistake the base layer for the finished contract. The base layer is
  `T1BaseEnvelope`; `T1LineageRef` is likewise the ref-only component of the
  frozen `T1Lineage` (B5-I16).
* `bloc_05/02 §11`'s `AS_KNOWN_THEN` / `LATEST_VERIFIED` names overlap the
  accepted Bloc 4 `RevisionPolicy` with **different meanings** (research replay
  policy vs raw-evidence query policy). They are therefore kept as separate
  types, introduced at B5-I07 — neither reused nor duplicated at I01.

### 4. Laws the base layer enforces (fail closed)

Blank and whitespace-padded identifiers refused everywhere; naive datetimes
refused and present values UTC-normalized; `interval_end_at >=
interval_start_at` as the only universally valid ordering (bloc_05/02 §6's
`published_at < effective_at` stays representable, and is tested); interval
bounds require an explicit `interval_closed` **and**
`interval_time_convention`; `market_available_at` requires a basis and is
refused with `UNKNOWN`; quality flags must be in canonical order and
duplicate-free; `lineage_state` must agree with exactly one matching lineage
flag; a canonical status requires `contract_instance_id`, at least one native
value and four registry/methodology versions, and may carry no blocking flag;
each `BLOCKED_*` status requires exactly its own typed missingness cause;
`QUARANTINED` requires a typed reason, evidence refs and non-blank remediation
(and quarantine metadata is refused on a non-quarantined row); five
`VERIFIED`-dimension contradictions are refused; `extra="forbid"` throughout.

Native truth is structurally protected: no B5-I01 model has any
`normalized_value`, `canonical_value`, `notional`, `usd` or `usd_equivalent`
field, so "native was overwritten by normalized" is unrepresentable rather than a
bug caught later. Provider and venue are separate required fields with no
collapsed `source` field, and `provider=COINALYZE, venue=BINANCE_USDM`
constructs. Absence is always a typed `MissingnessReason`, never a bool and
never a zero — no model field anywhere defaults to a numeric zero, asserted
structurally. No field name contains `usd` or `fiat`: the stablecoin firewall is
structural. `t1_record_id` is Optional because the deterministic identity
algorithm is B5-I16, and no identifier, hash, UUID or wall-clock value is
generated during construction.

### 5. Verification

Focused (normalization + Bloc 4 handoff I16/I16R1/I16R2 + G4-13 + I11R2 +
job-state + storage enums) = **549 passed / 0 failed** (114 s). Full storage =
**2019 passed / 13 skipped / 0 failed** (1330 s). Full project (`pytest tests`) =
**3702 passed / 14 skipped / 0 failed** (1172 s) — the accepted pre-B5-I01
baseline of 3398 plus exactly the 304 new B5-I01 tests. **Zero deterministic
failures.**

Ruff `src tests` = exactly the **2 pre-existing** findings in the untouched
`tests/crypto_sensor_fabric/storage/test_i08_evidence.py`; ruff on the new
changed scope = **All checks passed**. mypy on
`src/crypto_sensor_fabric/normalization` = **0 errors** in the new files (the 10
findings reported are the accepted pre-existing baseline in
`probes/planner.py`, `providers/rest.py`, `providers/{okx,kraken,gate,deribit}`
probes — unchanged). compileall OK. Secret scan 4 passed.

Zero network: `network_calls = 0`, proven both by the absence of any HTTP/socket
import in production source and by importing the package with
`socket.socket` / `socket.create_connection` patched to raise.

Forbidden later-stage modules confirmed absen
t by SENSOR-B5-I01-RESUME: the original §155 append was truncated mid-sentence
by a session interruption; everything above is preserved verbatim, and the
remainder of this section was appended by the resume session. All verification
below is a FRESH final-tree re-run, not a copy of pre-interruption numbers.

### 5a. Final-tree re-verification (fresh, resume session)

normalization = **304 passed** (2.8 s). Focused regression = **606 passed /
0 failed** (145 s) — superset composition: all 4 B5-I01 normalization test
files + I16 G4-13 readiness/core/evidence + I16R1 G4-13/unit contract/unit
semantic audit + I16R2 G4-13/real provider units/claim truth/integrity/location
+ I11R2 binding audit + I11R2 evidence + job-state/adversarial/r1 + storage
enums. I11R2 no-update rerun = **4 passed**, audit **byte-stable** (SHA-256
`e1bbd772…d5e36e` identical before and after).

Full storage on the final tree = **2019 passed / 13 skipped / 0 failed**
(1423 s); no teardown warning in this run. Full project on the final tree =
**3702 passed / 14 skipped / 0 failed** (1358 s); the 2 warnings are the known
pre-existing Windows reader-thread teardown exception in
`test_manifest_concurrency.py::TestPointerVisibility::test_readers_never_observe_partial_pointer`
— recorded separately, not hidden, unrelated to B5-I01. Zero deterministic
failures in every run.

Static battery re-run on the final tree: ruff on the new changed scope =
**All checks passed**; ruff `src tests` = exactly the 2 pre-existing findings
in the untouched `test_i08_evidence.py`; mypy = **0 new** (the 10 pre-existing
findings are the accepted providers/probes baseline); compileall OK; secret
scan of the B5-I01 diff = **0 hits**. Suite dirt (11 informational bloc_04
matrices) restored after both long runs; the worktree deliberately retains only
this ledger completion and the permitted I11R2 audit republish. Historical
custody re-verified: `git diff ae152d01…HEAD` over `evidence/` touches only
new bloc_05 files plus the single-line I11R2 count.

### 6. I11R2 audit

`python_files_scanned`: **1011 → 1018** (7 new tracked Python files: 3
production, 4 test). Regenerated mechanically (`UPDATE_I11R2_EVIDENCE=1`) only
after all filenames were finalized; no-update rerun byte-stable; never
hand-edited. Diff vs the committed audit is exactly the one count line.

### 7. External CI / remote custody

origin/main = `7c7816f…28fa8` (unchanged). origin build at resume =
`ae152d01…cb079` (start head; local branch 3 commits ahead — expected). No
statuses, check-runs or workflow runs observed on the pushed head →
`external_ci = NONE_OBSERVED`. Push after B5-I01D covers
`agent/crypto-sensor-fabric-build` only; main is never pushed.

### 8. Commit chain

`ae152d010f` (origin base) → `04600b5d5` B5-I01A (type-scope matrix 61 rows =
24 needed / 37 deferred + RED enum suite) → `83b2076b6` B5-I01B (enums.py +
models.py + __init__.py, 24 public symbols) → `a7c82f9887` B5-I01C (N0 model
tests, public-surface proof, measured evidence) → B5-I01D (final regression
evidence + audit + this ledger). No amend, no squash, no reset, no rebase, no
force push at any point, including across the interruption.

### 9. Bloc 5 gates

IDENTITY_GATE = TIME_GATE = SEMANTIC_GATE = UNIT_GATE = LINEAGE_GATE =
DUPLICATE_REVISION_GATE = REPLAY_SAFETY_GATE = GOLDEN_T0_T1_GATE =
**NOT_YET_EARNED**. B5-I01 supplies foundation vocabulary and containers only.

### 10. Governance

PASS_SENSOR_B5_I01_NORMALIZATION_BASE_TYPES_SEALED =
**PENDING_OPERATOR_REVIEW**. BLOC_05_IMPLEMENTATION_STATUS =
**I01_COMPLETE_PENDING_OPERATOR_REVIEW**. BLOC_05_NORMALIZATION_IMPLEMENTED =
**PARTIAL_FOUNDATION_ONLY**. next_checkpoint_authorized = **FALSE**.
recommended_next = **OPERATOR REVIEW OF SENSOR-B5-I01**. B5-I02+ =
UNAUTHORIZED. Bloc 6 = UNAUTHORIZED. research = FROZEN. No self-ratification.
After B5-I01D + push the worktree is clean except untracked `.bu_tmp/` scratch.
## 156 — SENSOR-B5-I01-RATIFY: NORMALIZATION BASE LAYER OPERATOR_ACCEPTED, B5-I02 AUTHORIZED ONLY

Date: 2026-10-06. Directive: SENSOR-B5-I01-RATIFY (mandatory start head
`66f5ba4aca582477139212fb250803dbf2bbb230`, expected remote main
`7c7816f38…`, scope: ratification only).

### 0. Start gate

branch = agent/crypto-sensor-fabric-build; HEAD = `66f5ba4aca` (B5-I01D);
origin build == local HEAD; origin/main = `7c7816f38…` untouched. Governance
state matched the I01 seal exactly (PASS = PENDING_OPERATOR_REVIEW,
I01_COMPLETE_PENDING_OPERATOR_REVIEW, PARTIAL_FOUNDATION_ONLY,
next_checkpoint_authorized = FALSE). Ancestry strict and linear: `ae152d010f`
→ `04600b5d5` (I01A) → `83b2076b6` (I01B) → `a7c82f9887` (I01C) →
`66f5ba4aca` (I01D); exactly 4 commits, 0 merges, no rewrites anywhere.

### 1. Ratification-time recomputation

Type-scope matrix recomputed: **61 / 24 / 37**;
`deferred_types_implemented = []`; the directive's 37 deferred names are
set-identical to the matrix deferred set. Vocabulary gaps preserved
un-invented: `AvailabilityConfidence` → B5-I06 (field named, vocabulary never
frozen), `VenueScope` → B5-I02 (only `MULTI_VENUE_AGGREGATE` named, "such
as"). Production surface = exactly `__init__.py` + `enums.py` + `models.py`;
all 18 forbidden module filenames absent. Public API = **24 symbols**
(`_StrEnum`/`_FLAG_ORDER` unexported). 10 enums with member counts
5/8/13/36/6/3/7/4/8/6, every member set re-verified against plan authority.
6 base models: `ObservationTimeEnvelope` 15, `NativeQuantity` 4, `T1Quality`
8 (no aggregate), `T1LineageRef` 8 (all 3 chain links required),
`T1VersionContext` 5, `T1BaseEnvelope` **27**. `T1BaseEnvelope` = STABLE
B5-I01 FOUNDATION; `T1ObservationEnvelope` = NOT YET COMPLETE / NOT YET
PUBLIC (requires later-stage fields owned by B5-I02/I05/I06/I09). Upstream
reuse confirmed (SensorFamily, Granularity, CoverageState, RevisionState,
SourceUnitContract, SourceUnitEvidence). `BLOCKED_IDENTITY` vs
`IDENTITY_BLOCKED` preserved; `BLOCKED_STATUS_MISSINGNESS_REASON` read-only,
mutation refused. Firewalls re-verified at source level: zero
canonical/normalized/notional/usd/fiat field definitions, no conversion
logic, provider ≠ venue with no merged `source`, no hash/uuid/random/
wall-clock in production, no network/storage-backend imports.

### 2. Fresh regressions (this ratification tree)

B5-I01 normalization = **304 passed** (2.0 s). Focused battery (I01 + Bloc 4
handoff I16/I16R1/I16R2 + G4-13 + I11R2 binding audit + I11R2 evidence +
job-state ×3 + storage enums) = **616 passed / 0 failed** (166 s). Full
storage = **2019 passed / 13 skipped / 0 failed** (1422 s). Full project =
**3702 passed / 14 skipped / 0 failed** (1319 s). Zero deterministic
failures. **Windows manifest-concurrency teardown warning: ABSENT this run**
(0 occurrences); when previously observed it is classified inherited
TEST-ENVIRONMENT DEBT and stays unrepaired by design.

Static: ruff new changed scope = All checks passed; ruff repo-wide = exactly
the 2 pre-existing `test_i08_evidence.py` findings; mypy = 0 new (10
pre-existing providers/probes baseline); compileall OK; secret scan of the
I01 diff = 0 hits.

### 3. I11R2 / custody

`python_files_scanned` **1011 → 1018** (republished in I01D, mechanically,
after filename finalization). No-update rerun at ratification = 4 passed,
**byte-stable** (SHA-256 `e1bbd772…d5e36e`). No republish during
ratification. Historical custody re-verified: `git diff ae152d010f…66f5ba4ac`
over `evidence/` = only new bloc_05 files + the single authorized I11R2 count
line; Bloc 4 / I17 evidence and ratification artifacts untouched; no I01
evidence rewritten.

### 4. Ledger recovery truth (accepted, not rewritten)

The §155 append was interrupted by rate limiting: heredoc partially succeeded
(141 lines) and truncated mid-word ("confirmed absen"). Recovery resumed from
the surviving bytes and completed the section append-only, explicitly
disclosing the truncation. The seam is **accepted process history** — §155 is
not cleaned, reconstructed, or rewritten.

### 5. Governance after ratification

PASS_SENSOR_B5_I01_NORMALIZATION_BASE_TYPES_SEALED = **OPERATOR_ACCEPTED**.
BLOC_05_IMPLEMENTATION_STATUS = **I01_OPERATOR_ACCEPTED**.
BLOC_05_NORMALIZATION_IMPLEMENTED = **PARTIAL_FOUNDATION_ONLY**. All 8 Bloc 5
blocking gates (IDENTITY / TIME / SEMANTIC / UNIT / LINEAGE /
DUPLICATE_REVISION / REPLAY_SAFETY / GOLDEN_T0_T1) remain **NOT_YET_EARNED** —
type/model existence promotes nothing. next_checkpoint_authorized = **TRUE**.
next_checkpoint = **SENSOR-B5-I02 ASSET / VENUE / CONTRACT IDENTITY MODELS +
REGISTRIES**. authorized_scope = **B5-I02 ONLY**. B5-I03+ = UNAUTHORIZED.
Bloc 6 = UNAUTHORIZED. research = FROZEN. recommended_next = **SENSOR-B5-I02
IMPLEMENTATION**. B5-I02 owns CanonicalAsset, Venue, VenueInstrument,
EconomicContract, ContractInstance + identity registry/data structures; it
does NOT authorize lifecycle/alias/PIT resolution, conversion primitives,
time semantics, availability resolution, revision engine, unit conversion,
sensor normalizers, or T1 writer/query. VenueScope firewall recorded:
B5-I02 must audit whether the type is actually required; if required and the
plan still underdetermines it, STOP for operator decision. Identity laws
carried forward as record (CanonicalAsset ≠ ContractInstance; USD/USDT/USDC
distinct; provider ≠ venue; no metadata backcast).

Ratification outputs (one commit): this ledger entry + `evidence/bloc_05/
BLOC_05_I01_OPERATOR_RATIFICATION.md`. Zero production/test/evidence changes.
B5-I02 NOT started. STOP.
## 157 — SENSOR-B5-I02: IDENTITY MODELS + REGISTRIES (PENDING_OPERATOR_REVIEW)

Date: 2026-10-06. Start head `8d220ad1cd` (I01-RATIFY); governance verified
(OPERATOR_ACCEPTED, next_checkpoint_authorized = TRUE, scope B5-I02 ONLY).

### 0. Staged commits (no amend/squash at any point)

`32a88ef2a` B5-I02A (vocabulary authority audit + RED model/registry suites,
confirmed collection-RED) → `dc7703eeb` B5-I02B (five identity models +
minimal identity package + deliberate I01 scope-test reconciliation) →
`6bc6ca4d5` B5-I02C (versioned registry + referential integrity) → B5-I02D
(this commit: remaining N0 tests, 4 measured evidence artifacts, audit,
governance).

### 1. Vocabulary authority (audit BEFORE code)

`BLOC_05_I02_VOCABULARY_AUTHORITY_MATRIX.json`: 10 audited fields; exactly 1
frozen vocabulary (payoff_type → reused B5-I01 `PayoffType`, never
redefined); 8 under-specified fields carried as validated opaque
`SemanticToken`s (asset_type, instrument_type, perpetual_or_delivery,
chain_or_issuer_context, index_family, multiplier/price/quantity_unit — unit
vocabularies belong to B5-I08); VenueScope = **NOT_REQUIRED_DEFERRED**
(directive §36 answer: none of the five frozen models carries a
venue_scope field; inventing members would breach the I01 ratification §38
firewall). identity/enums.py deliberately NOT created. Lifecycle vocabulary
(frozen in 01 §6) deliberately unimplemented — machinery is B5-I03.

### 2. Implementation (measured)

`normalization/identity/` = exactly `__init__.py` + `models.py` +
`registry.py`; **10 public symbols**; top-level normalization surface
unchanged at 24 (no re-export). Field counts: CanonicalAsset 7, Venue 1
(bloc_05/01 §2.2 freezes no Venue fields; venue_id is the minimum referential
anchor, examples are not an enum), VenueInstrument 8, EconomicContract 9,
ContractInstance 23 — 48 total; all records frozen-immutable. Registry:
frozen snapshot, canonically ordered, duplicate-ID refusal, referential
integrity (asset/venue/economic-contract), no-overlapping-active-terms
refusal (bloc_05/01 §17.3), byte-stable YAML text serialization (measured
stable), round-trip equality (measured), succession law refusing
same-version conflicting content (canonical-bytes comparison as the
fingerprint — no hashing machinery added), v1/v2 both loadable, no wall-clock
minting, no IDs computed, text-in/text-out only (no config-tree files — the
frozen yaml layout is a deployment concern deferred until a seeded registry is
authorized). Terms logic, conversion, aliasing, lifecycle, PIT lookup,
universe membership: all absent (measured).

### 3. Verification (fresh, final tree)

B5-I02 tests = **113** (models 54, registry 29, public API 6, scope audit 24).
Normalization package = **416 passed** (I01 303 after the authorized
one-param scope reconciliation + 113). Focused battery = **728 passed /
0 failed** (118 s). Full storage = **2019 passed / 13 skipped / 0 failed**
(1400 s). Full project = **3814 passed / 14 skipped / 0 failed** (1075 s),
no warnings; zero deterministic failures.

Static: ruff changed scope = All checks passed (repo-wide: the 2 pre-existing
I08 findings; one mid-run F811 duplicate-test-name finding was fixed before
commit and the affected suite re-run); mypy = 0 new (10 pre-existing
providers/probes baseline); compileall OK; secret-scan grep hit on
`SemanticToken = ` is a false positive of the `token =` pattern — no secrets.

### 4. I11R2 audit

Tracked-Python count **1018 → 1025** (7 new files: 3 production, 4 test),
regenerated mechanically only after filenames were finalized; no-update rerun
byte-stable; never hand-edited.

### 5. Custody disclosures

Bloc 4 / I17 / I01 evidence untouched; the I01 scope test was deliberately
reconciled in B5-I02B (blanket subpackage ban → allowlist {"identity"},
"identity" removed from the forbidden-module parametrization) and all other
negative-scope laws remain enforced. Commit A captured three mangled
docstrings and a duplicate test name from chunked authoring; the syntax
repairs ride in B5-I02D and are disclosed here. The untracked I06 spike file
remains untracked and untouched (directive §45).

### 6. Governance

PASS_SENSOR_B5_I02_IDENTITY_MODELS_REGISTRIES_SEALED =
**PENDING_OPERATOR_REVIEW**. BLOC_05_IMPLEMENTATION_STATUS =
**I02_COMPLETE_PENDING_OPERATOR_REVIEW**. BLOC_05_NORMALIZATION_IMPLEMENTED =
**PARTIAL_IDENTITY_FOUNDATION**. All 8 Bloc 5 gates (IDENTITY / TIME /
SEMANTIC / UNIT / LINEAGE / DUPLICATE_REVISION / REPLAY_SAFETY /
GOLDEN_T0_T1) remain **NOT_YET_EARNED** — registry/model infrastructure earns
no gate; identity proof requires B5-I03 resolution semantics.
next_checkpoint_authorized = **FALSE**. recommended_next = **OPERATOR REVIEW
OF SENSOR-B5-I02**. B5-I03+ = UNAUTHORIZED. Bloc 6 = UNAUTHORIZED. research =
FROZEN. No self-ratification. B5-I03 NOT started.
## 158 — SENSOR-B5-I02-RATIFY: IDENTITY FOUNDATION OPERATOR_ACCEPTED, B5-I03 AUTHORIZED ONLY

Date: 2026-10-06. Start head `1cb9962a53` (I02D); governance verified
(PENDING_OPERATOR_REVIEW, next_checkpoint_authorized = FALSE). Ancestry
strict and linear: `8d220ad1cd` → `32a88ef2a` (I02A) → `dc7703eeb` (I02B) →
`6bc6ca4d5` (I02C) → `1cb9962a53` (I02D); 4 commits, 0 merges, no rewrites.

### 1. Ratification-time verification

Mechanical verifier (56 checks) **ALL PASS**: vocabulary authority matrix
row-verified (VenueScope = NOT_REQUIRED_DEFERRED; 8 fields = SemanticToken;
payoff_type = the I01 PayoffType object; no identity/enums.py); five model
contracts recomputed (7/1/8/9/23 = 48 fields, set-identical to frozen §2
lists, all frozen-immutable); registry structure/laws verified live
(duplicate refusal ×5, nine integrity paths, overlap refusal with adjacency
accepted, succession conflict-refusal with order-insensitive idempotence);
YAML safe-load round-trip byte-stable with exact Decimals; text-in/text-out
(no filesystem behavior, zero config catalogs added — `git log
--diff-filter=A` over config/** in the I02 range is empty); backcast and
alias/lifecycle/PIT/universe/conversion firewalls absent. Adversarial
red-team rerun: **93/93 probes, 59 refusal laws held, 34 recorded
observations, 0 gaps**. I01 scope reconciliation verified deliberate and
minimal (allowlist {"identity"}; time/sensors/common and all other params
still forbidden; I01 surface still 24 symbols; gates untouched).

### 2. Fresh regressions

Focused = **728 passed / 0 failed**. Full storage = **2019 passed / 13
skipped / 0 failed**. Full project = **3814 passed / 14 skipped / 0 failed**
with **1 warning = the known Windows manifest-concurrency reader-thread
teardown race** (inherited TEST-ENVIRONMENT DEBT; intermittent across runs;
unrepaired by design). Static: ruff changed scope clean / 2 pre-existing
repo-wide; mypy 0 new (10 pre-existing); compileall OK; the secret-scan
lexical hit `SemanticToken = ` is the known `token =` false positive.

### 3. Audit / custody

I11R2 **1018 → 1025** (committed in I02D), no-update byte-stable
(`0cdd4352…10542`), no republish during ratification. Custody: only new
bloc_05 files + the permitted audit count differ from `8d220ad1`;
I01/Bloc 4/I17 evidence untouched. Authoring defects (three malformed
docstrings + one F811 duplicate test name, captured in commit I02A, repaired
by I02D) are disclosed in the ratification artifact and remain visible in
history — no rewrite. The untracked I06 spike remains untracked/unmodified.

### 4. Governance after ratification

PASS_SENSOR_B5_I02_IDENTITY_MODELS_REGISTRIES_SEALED = **OPERATOR_ACCEPTED**.
BLOC_05_IMPLEMENTATION_STATUS = **I02_OPERATOR_ACCEPTED**.
BLOC_05_NORMALIZATION_IMPLEMENTED = **PARTIAL_IDENTITY_FOUNDATION**. All 8
gates (IDENTITY / TIME / SEMANTIC / UNIT / LINEAGE / DUPLICATE_REVISION /
REPLAY_SAFETY / GOLDEN_T0_T1) remain **NOT_YET_EARNED** — IDENTITY_GATE
requires B5-I03 PIT resolution proof and is NOT pre-authorized.
next_checkpoint_authorized = **TRUE**. next_checkpoint = **SENSOR-B5-I03
LIFECYCLE / ALIAS / PIT IDENTITY RESOLVER**. authorized_scope = **B5-I03
ONLY**. B5-I04+ = UNAUTHORIZED. Bloc 6 = UNAUTHORIZED. research = FROZEN.
recommended_next = **SENSOR-B5-I03 IMPLEMENTATION**. I03 matching order and
PIT law carried forward verbatim (provider-ID → exact symbol+venue+interval
→ registered alias → curated evidence-backed manual mapping → no result;
fuzzy = candidates only; `valid_from <= event_time < valid_to` AND
`known_from <= cutoff`; no future leakage; relisting = new instance unless
continuity evidenced; no multiplier/notional/unit work — B5-I04+). B5-I03
NOT started. STOP.
## 159 - SENSOR-B5-I03: LIFECYCLE/ALIAS/PIT IDENTITY RESOLVER COMPLETE (PENDING_OPERATOR_REVIEW)

Date: 2026-10-07. Start head `9ad8279e2` (I02-RATIFY; remote build head).
Ancestry strict and linear: `9ad8279e2` -> `e06c26452` (I03A) ->
`06dcc7eb9` (I03B) -> `5e9424835` (I03C) -> `61148c02e` (I03D-impl); 4
commits, 0 merges, no rewrites, no amend/squash. Remote build still
`9ad8279e2` at sealing time. MAIN_DIVERGENCE_STATUS =
EXTERNAL / UNRECONCILED / NON-BLOCKING_FOR_I03 (origin/main moved
independently to `f89883471dbc93d481b43d73757c716afc817441` during the Bloc 5
workstream; per the FINALIZE directive no merge/rebase/cherry-pick/reset was
performed; the build branch remains the checkpoint authority; reconciliation
requires a separate operator decision).

### 1. Implementation-time verification (measured at final tree `61148c02e`)

Scope audit: identity = exactly the 7 authorized modules (`__init__`,
`aliases`, `enums`, `lifecycle`, `models`, `registry`, `resolver`); all
forbidden modules/behaviors absent; identity `__all__` = **17** symbols;
top-level normalization surface unchanged at **24**. Resolver entry point
`resolve_instrument(snapshot, provider, venue, native_symbol, event_time,
knowledge_cutoff, optional_provider_instrument_id=None)` - snapshot leads
(documented deviation; pure function over one explicit immutable registry
snapshot, no ambient state, no wall clock). Dual-clock law enforced on every
candidate at every tier (`valid_from <= event_time < valid_to` AND
`known_from <= knowledge_cutoff`, known_to where applicable). Frozen five-tier
order: provider instrument ID -> exact native symbol + venue + lifecycle
interval -> documented alias at event time -> curated evidence-backed manual
mapping -> no result; **tiers 3+4 are ONE pooled alias scan** (ambiguity
dominates convenience); tier-4 semantics live in winner discrimination via
`_DOCUMENTED_SYMBOL_ALIAS_TYPES = {API_SYMBOL, WEBSOCKET_SYMBOL}` ->
`IDENTITY_ALIAS_USED` vs curated carriers (ARCHIVE/DISPLAY/LEGACY/
PROVIDER_INTERNAL_ID) -> `IDENTITY_MANUAL_OVERRIDE`; tier-4 winner stays
RESOLVED_ALIAS with `matched_alias_id` (disclosed wording deviation from the
vocabulary matrix's "RESOLVED_WITH_WARNING" phrasing - emitting
`matched_alias_id` under any other status would violate the frozen validator
law, and dropping it would destroy manual-mapping attribution). Ambiguity
refuses winners (never first/latest/sorted/lexicographic). Lifecycle-verdict
law: NOT_YET_LISTED strictly before earliest valid_from, DELISTED at/after
latest valid_to; cutover is the relisting law, not a silent latest-win.
Fail-closed tier-5 sweep: late alias/instance evidence -> PIT_KNOWLEDGE_BLOCKED;
unresolved answers carry no fabricated identifiers. Exact-only law: no
fuzzy/prefix/substring/case-fold/display-or-archive guessing; USD/USDT/USDC
structurally distinct (no conversion behavior exists). No I04 leakage:
no multiplier/inverse/quantity/notional/unit math in the identity package;
`canonical_asset_id` supplied by the registry, never computed; `terms_version`
mirrored verbatim. Vocabulary (nothing invented): LifecycleState 7 exact
members (PRE_LISTING, ACTIVE, SUSPENDED, DELISTING_ANNOUNCED, DELISTED,
RELISTED_NEW_INSTANCE, UNKNOWN); AliasType 6 (API_SYMBOL, ARCHIVE_SYMBOL,
WEBSOCKET_SYMBOL, DISPLAY_SYMBOL, LEGACY_SYMBOL, PROVIDER_INTERNAL_ID);
IdentityResolutionStatus 9 exact members + BLOCKING set {AMBIGUOUS,
UNKNOWN_SYMBOL, TERMS_UNVERIFIED, PIT_KNOWLEDGE_BLOCKED}. Flags emitted by
I03 paths: IDENTITY_ALIAS_USED, IDENTITY_MANUAL_OVERRIDE,
IDENTITY_LIFECYCLE_BOUNDARY, IDENTITY_PROVIDER_ID_MISSING; sanctioned flags
N/A in I03 paths documented, not invented. UNKNOWN lifecycle windows are
inert evidence (neither block nor warn); the frozen plan under-specifies
resolver behavior for them and no behavior was invented (recorded choice).

### 2. A12 defect + repair (preserved in history)

PRE-REPAIR (real defect, found by the I03 red-team case A12): an
alias-derived match landing inside a knowledge-valid SUSPENDED window
produced a downgraded result still carrying `matched_alias_id` - lawful only
on RESOLVED_ALIAS under the I03C validator - so `resolve_instrument`
crashed on a legal input. POST-REPAIR (`61148c02e`, no history rewrite): the
lifecycle downgrade drops `matched_alias_id`, preserves provenance (alias
evidence refs, confidence, IDENTITY_ALIAS_USED, plus
IDENTITY_LIFECYCLE_BOUNDARY), does not misrepresent alias resolution as
active canonical identity, and no validator crash occurs; the validator law
itself unchanged. Two regression pins added:
`test_alias_match_inside_suspended_window_downgrades_without_alias_id` and
`test_alias_match_outside_warning_windows_keeps_matched_alias_id`. Static
hygiene in the same commit: unused imports removed, resolver imports
`IdentityRegistrySnapshot` from `.registry` (3 F821/mypy resolved), dead
test variable removed.

### 3. Fresh regressions (measured at `61148c02e`, not stale)

B5-I03 tests **69 passed** (47 resolver incl. the 2 A12 pins + public API +
scope audit). I01+I02 explicit regression suites **413 passed**.
Normalization package **482 passed**. Focused battery **794 passed / 0
failed**. Full storage **2019 passed / 13 skipped / 0 failed**. Full project
**3880 passed / 14 skipped / 0 failed** with 2 warnings - both the known
Windows manifest-concurrency reader-thread teardown race
(`test_manifest_concurrency.py::TestPointerVisibility::
test_readers_never_observe_partial_pointer`, PermissionError in reader
thread; inherited TEST-ENVIRONMENT DEBT, intermittent, unrepaired by design
per directive 25). Zero deterministic failures. Static: ruff changed scope
all-pass (7 findings fixed during I03D before sealing); mypy 0 new identity
findings (10 pre-existing providers/probes baseline); compileall OK;
secret scan only the known `SemanticToken = ` false positive (models.py:115).

### 4. Evidence artifacts (all regenerated after `61148c02e`)

Mechanical generators (`.bu_tmp/`, never committed) re-run at the final
tree: FUTURE_LEAKAGE_MATRIX 4/4 PASS, MATCH_ORDER_MATRIX 6/6 PASS,
LIFECYCLE_MATRIX 9/9 PASS, ALIAS_MATRIX 6/6 PASS - every row carries
acceptance clause / probe / input condition / observed result / disposition /
evidence reference, no prose-only rows. ADVERSARIAL_MATRIX 25/25 PASS
(mechanical wrapper over the red-team run; per-class acceptance-clause map
disclosed in the artifact; the stale pre-fix red-team artifact showing
23/25 with A3+A12 FAIL was discarded - A12 FAIL is the pre-repair defect
history preserved in section 2, not current behavior). SCOPE_AUDIT.json:
identity files exactly the 7 authorized modules, forbidden absent.
IMPLEMENTATION_EVIDENCE.md authored from the measured numbers. Zero network,
zero filesystem, zero wall-clock in production identity code.

### 5. Audit / custody

I11R2 tracked-Python count regenerated mechanically: **1025 -> 1033** (exactly
one line changed; no-update rerun byte-stable), committed in the evidence
commit. Custody: Bloc 4 / I17 / B5-I01 / B5-I02 evidence untouched; eleven
suite-dirtied informational bloc_04 JSONs restored before commit; the
untracked I06 spike remains untracked/unmodified; `.bu_tmp/` stays untracked
and is never committed.

### 6. Governance after I03 (no self-ratification)

PASS_SENSOR_B5_I03_LIFECYCLE_ALIAS_PIT_RESOLVER_SEALED =
**PENDING_OPERATOR_REVIEW**. BLOC_05_IMPLEMENTATION_STATUS =
**I03_COMPLETE_PENDING_OPERATOR_REVIEW**. BLOC_05_NORMALIZATION_IMPLEMENTED
= **PARTIAL_PIT_IDENTITY_FOUNDATION**. I03_IDENTITY_RESOLVER_SUBGATE =
**IMPLEMENTATION_PASS_PENDING_OPERATOR_REVIEW**. All 8 gates (IDENTITY /
TIME / SEMANTIC / UNIT / LINEAGE / DUPLICATE_REVISION / REPLAY_SAFETY /
GOLDEN_T0_T1) remain **NOT_YET_EARNED** - the IDENTITY_GATE is a
program-level gate and later PIT/property/integration/golden stages still
exist; it is NOT earned at I03 and NOT pre-authorized.
next_checkpoint_authorized = **FALSE**. recommended_next = **OPERATOR REVIEW
OF SENSOR-B5-I03**. B5-I04+ = UNAUTHORIZED. Bloc 6 = UNAUTHORIZED. research
= FROZEN. Evidence/governance commit SENSOR-B5-I03D then push of the build
branch only (never main); I04 authorization occurs only after operator
review of the pushed I03 final tree. HARD STOP.
## 160 - SENSOR-B5-I03 AMENDMENT: LIFECYCLE-ROW STATE LAWS + WARNING-WINDOW BOUNDARIES PINNED (PENDING_OPERATOR_REVIEW)

Date: 2026-10-07 (same day as the B5-I03D sealing in section 159; governing
head changes from `02eac405` by this amendment commit only). Scope: an
operator-directed evidence gap sweep reported laws pinned by implementation
omission rather than measurement; the operator authorized closing the
lifecycle-ROW state law group within B5-I03 scope. No production source
change was required - the resolver already implements these laws (S6/I03D33
warning enumeration) - the amendment converts omission into measured
evidence. A12 history and all earlier I03 commits remain untouched.

### 1. Laws newly pinned (4 tests + 8 lifecycle-matrix rows)

* RELISTED_NEW_INSTANCE lifecycle ROW over a PIT-valid instance is inert
  evidence (neither gates, warns, nor activates); the relisting cutover is
  carried by the NEW instance's own valid_from, never by the state row.
  Pinned by `test_relisted_new_instance_lifecycle_row_is_inert` + 1 matrix
  row.
* PRE_LISTING lifecycle ROW over a PIT-valid instance is inert evidence,
  exactly the A7b law (DELISTED row over a live instance). Pinned by
  `test_pre_listing_lifecycle_row_is_inert` + 1 matrix row.
* Warning windows (SUSPENDED and DELISTING_ANNOUNCED) are half-open
  [valid_from, valid_to): start-inclusive, end-exclusive; downgrade fires
  exactly at the start instant, one microsecond before it the resolution is
  plain RESOLVED_EXACT, still-warning one microsecond before the end
  instant, plain at the end instant. Pinned for BOTH warning states x 4
  boundary instants by `test_suspended_warning_window_boundaries_are_half_open`
  and `test_delisting_announced_warning_window_boundaries_are_half_open` + 6
  matrix rows.

### 2. Verification (measured at the amendment tree)

B5-I03 tests **73 passed** (69 + 4 new pins). Normalization package **486
passed**. I11R2 audit no-update rerun **4 passed, byte-stable** (SHA
`bebda72beeaba50aa73b3c0032311282140f831ce0adcf2a813ce70a55cbfa8c`
unchanged). Full project **3884 passed / 14 skipped / 0 failed with 1
warning** - the known intermittent Windows manifest-concurrency reader-thread
teardown race (same inherited TEST-ENVIRONMENT DEBT; unrepaired by design).
Static: ruff changed scope all-pass; mypy 0 identity findings (10 pre-existing
providers/probes baseline); compileall OK; secret scan clean. Lifecycle
matrix regenerated from the live resolver: **17 rows / 17 PASS, all 7 states
enumerated** (was 9 rows); ASCII-clean; no row content hand-authored.
Mojibake scan: allowed non-ASCII only. Evidence narrative amended (new
section 8: Evidence amendment). Adversarial red-team, other matrices, SCOPE
AUDIT unchanged from section 159 (regenerated outputs byte-equivalent in
content class; no generator change affecting them).

### 3. Custody

Bloc 4 / I17 / B5-I01 / B5-I02 evidence untouched; suite-dirtied
informational bloc_04 JSONs restored; I11R2 audit NOT republished
(byte-stable no-update). I06 spike and `.bu_tmp/` remain untracked.
Tracked worktree clean after the amendment commit.

### 4. Governance (unchanged disposition, no self-ratification)

PASS_SENSOR_B5_I03_LIFECYCLE_ALIAS_PIT_RESOLVER_SEALED =
**PENDING_OPERATOR_REVIEW**. BLOC_05_IMPLEMENTATION_STATUS =
**I03_COMPLETE_PENDING_OPERATOR_REVIEW**. BLOC_05_NORMALIZATION_IMPLEMENTED
= **PARTIAL_PIT_IDENTITY_FOUNDATION**. I03_IDENTITY_RESOLVER_SUBGATE =
**IMPLEMENTATION_PASS_PENDING_OPERATOR_REVIEW**. IDENTITY_GATE and all other
gates = **NOT_YET_EARNED**. next_checkpoint_authorized = **FALSE**.
recommended_next = **OPERATOR REVIEW OF SENSOR-B5-I03**. B5-I04+ =
UNAUTHORIZED. Bloc 6 = UNAUTHORIZED. research = FROZEN.
MAIN_DIVERGENCE_STATUS unchanged:
EXTERNAL / UNRECONCILED / NON-BLOCKING_FOR_I03. Remaining known evidence
gaps recorded for operator decision (NOT closed here): dual-clock `known_to`
(superseded knowledge) coverage; provider-ID + wrong-venue tier-1 probe;
stablecoin/negative-alias/flag matrix backfill; TERMS_UNVERIFIED
reachability statement. HARD STOP.
## 161 - SENSOR-B5-I03H: DUAL-CLOCK KNOWLEDGE-BOUNDARY CLOSURE (PENDING_OPERATOR_REVIEW)

**Date:** 2026-10-08 · **Start head:** `13f05ae7a71749ef7b2847f67c090e484d0ddf39`
(branch `agent/crypto-sensor-fabric-build`, custody verified Phase 0). ·
**Scope:** operator-directed bounded amendment closing the classified B5-I03
evidence omissions (G1–G4). Append-only: no prior section or sealed artifact
was modified.

### 1. Operator-selected semantics (prospective, not retro-attributed)

Option 1 authorized for records that possess `known_to`:
`known_from <= knowledge_cutoff < known_to` (half-open). Absent `known_to` =
open-ended knowledge interval. Prospective clarification only — no earlier
frozen contract is claimed to have stated it, and no sealed evidence was
rewritten. `InstrumentAlias` NOT altered: frozen eleven-field schema remains
authoritative; alias knowledge is open-ended by construction (pass `None`
upper bound).

### 2. Changed production paths (exactly one file)

`src/crypto_sensor_fabric/normalization/identity/resolver.py` —
`_known_by(known_from, known_to, cutoff)` now enforces the bounded knowledge
interval; applied at `_pit_valid`, `_lifecycle_warning`,
`_tier_exact_symbol`; alias scan open-ended. Blocking outcome for expired
knowledge with no eligible candidate: existing `PIT_KNOWLEDGE_BLOCKED` /
`UNKNOWN` (no new status/flag/enum; no supersession engine; no replacement
selection). Valid-time filtering, tier priorities, alias behavior, lifecycle
warnings, and fail-closed identity handling preserved.

### 3. Regression evidence (Phase 2 — 11 new, both clocks independent)

`test_b5_i03_resolver.py` +11: before/at `known_from`, −1µs/at/after
`known_to`, absent `known_to`, historical event + later cutoff, nonoverlapping
revision windows (gap blocked; old probe → OLD record; new probe → NEW
record), ambiguous overlapping eligible records stay AMBIGUOUS, lifecycle
warning with expired knowledge inert (control warns), G2 wrong-venue
regression (correct provider ID + wrong venue → `UNKNOWN_SYMBOL`, control
resolves). Knowledge-clock probes hold event time fixed — never substituted.
All prior valid-time and lifecycle-boundary tests unchanged and passing.

### 4. Generator + artifact changes (Phase 3)

`.bu_tmp/b5_i03_mats.py` extended: knowledge-boundary matrix (KB1–KB10 + 3
lifecycle rows → new `BLOC_05_I03H_KNOWLEDGE_BOUNDARY_MATRIX.json`), tier-1
venue-isolation row (G2), negative-prefix/case-fold/separator probes, S12
stablecoin firewall row, identity-flag coverage (4 emitted live / 6
not-emitted absent), `TERMS_UNVERIFIED` construction-reachability pin (G4).
`.bu_tmp/b5_i03_scope.py` extended with the G4 AST pin. Regenerated:
MATCH_ORDER (10 rows), FUTURE_LEAKAGE (4/4), LIFECYCLE (17/17), ALIAS (6/6,
byte-identical), SCOPE_AUDIT, new I03H knowledge-boundary (14/14). Untouched:
ADVERSARIAL (re-measured unchanged), I02 matrices, I11R2 audit
(byte-stable no-update), all bloc_04.

### 5. Measured verification (this tree)

I03 focused **84 passed** (73 + 11). Normalization **497 passed** (486 + 11).
I11R2 **14 passed**, SHA `bebda72beeaba50aa73b3c0032311282140f831ce0adcf2a813ce70a55cbfa8c`
byte-identical. Full project **3895 passed / 14 skipped / 0 failed (0 warnings)** (new failures:
none (baseline 3884 + 11 new = 3895; 14 skipped unchanged); inherited Windows manifest-concurrency teardown race =
TEST-ENVIRONMENT DEBT). Ruff changed scope all-pass; mypy 10 inherited / 0
identity; compileall OK; secret scan clean. Evidence narrative amended
(new section 9: knowledge-boundary closure amendment; governance renumbered
10, content unchanged).

### 6. G1–G4 closure status

G1 dual-clock `known_to` — **CLOSED**. G2 provider-ID + wrong-venue —
**CLOSED** (matrix row + standing regression). G3 stablecoin/negative-alias/
identity-flag backfill — **CLOSED** (matrix rows). G4 `TERMS_UNVERIFIED`
reachability — **CLOSED** (reserved; never constructed through I03 paths;
terms machinery remains B5-I04+). §160's four "not closed here" gaps are now
closed at operator direction.

### 7. Custody + governance (unchanged disposition, no self-ratification)

New commit on `agent/crypto-sensor-fabric-build` only (fast-forward push;
report SHA in final report). Bloc 4 / I17 / B5-I01 / B5-I02 evidence
untouched; tracked worktree clean after commit; `.bu_tmp/` remains untracked.
PASS_SENSOR_B5_I03_LIFECYCLE_ALIAS_PIT_RESOLVER_SEALED =
**PENDING_OPERATOR_REVIEW**. BLOC_05_IMPLEMENTATION_STATUS =
**I03_COMPLETE_PENDING_OPERATOR_REVIEW**. I03_IDENTITY_RESOLVER_SUBGATE =
**IMPLEMENTATION_PASS_PENDING_OPERATOR_REVIEW**. IDENTITY_GATE and all other
gates = **NOT_YET_EARNED**. next_checkpoint_authorized = **FALSE**.
recommended_next = **OPERATOR REVIEW OF SENSOR-B5-I03H**. B5-I04+ =
UNAUTHORIZED. Bloc 6 = UNAUTHORIZED. research = FROZEN.
MAIN_DIVERGENCE_STATUS unchanged: EXTERNAL / UNRECONCILED /
NON-BLOCKING_FOR_I03. HARD STOP after push and report.

---

## 162 - SENSOR-B5-I03I: EVIDENCE REPRODUCIBILITY + KB3 NARRATION CORRECTION (PENDING_OPERATOR_REVIEW)

Date: 2026-10-08. Start head `67b7f4de1` (I03H; remote build head).
Operator-directed bounded evidence amendment only: correct demonstrable
inconsistencies in committed evidence and make evidence generation
reproducible from tracked source. No identity semantics authorized or
changed; production code byte-identical to the I03H seal.

### 1. Original KB3 discrepancy (reproduced independently)

The sealed knowledge-boundary matrix narrated KB3 `cutoff =
2023-11-30T23:59:59.999999Z` while claiming `known_to - 1 microsecond` with
`known_to = 2023-12-01T12:00:00Z` — 12 hours + 1µs early, not 1µs. A fresh
fixture rebuilt from the production models (not importing the generator)
proved the error was **confined to hand-typed `input_condition` narration**:
the generator executed `K1 - timedelta(microseconds=1)` =
`2023-12-01T11:59:59.999999Z`, a true µs boundary. Cause: narration strings
copied from the standing-test fixture (midnight-based K0/K1) while the
generator fixture is noon-based. Same narration error in KB1 and KB5. No
probe executed a wrong timestamp; no observed status was relabeled.

### 2. Corrected executable input + measured result

KB1/KB3/KB5 `input_condition` strings now state the executed instants
(`2023-06-01T11:59:59.999999Z`, `2023-12-01T11:59:59.999999Z`,
`2023-12-02T12:00:00Z`) against the noon window
`[2023-06-01T12:00Z, 2023-12-01T12:00Z)`. Regenerated KB matrix: **14/14
PASS**, expected == observed on every row. Cross-artifact audit of every
lifecycle / match-order / future-leakage / alias / venue / stablecoin /
scope-audit narration against executed fixture values: all consistent;
only the three KB narrations were wrong.

### 3. Generator source custody

No frozen tracked generator existed. The four deterministic producers were
promoted verbatim to tracked `research/crypto_foundry/sensor_fabric/scripts/`
(`b5_i03_mats.py`, `b5_i03_scope.py`, `b5_i03_redteam.py`,
`b5_i03_adv_wrap.py`); edits limited to GEN_REF invocation strings, the three
narration fixes, and repo-convention `# noqa: E402` on two post-bootstrap
imports. Invocation: `PYTHONIOENCODING=utf-8 python
research/crypto_foundry/sensor_fabric/scripts/<name>.py` (from quant-lab).
No `.bu_tmp` runtime dependency (redteam results + adversarial wrap live
beside the scripts); `.bu_tmp` strings inside the ADVERSARIAL matrix are
sealed-run provenance literals, deliberately preserved. No scratch, cache,
or I06 files promoted; `.bu_tmp/` and the I06 spike remain untracked.

### 4. Artifact reproducibility hashes (sha256, double-run byte-identical 6/6)

- KB: `ae24942540a6b26a6096eefee3186a393482913d8f1d50f1ca2d6011387ffeac`
- ALIAS: `efd7ac47f2c8852badc356e4fc60cdc7af8eb746f2ac92a19f313dad5a48c2bb`
- FUTURE_LEAKAGE: `09b487e8622326a618be03373d20cb8dbf442520f931482d979e2df1850167bf`
- LIFECYCLE: `4efae87d0772fed1f5a000eba1bd548a4459ddb028f4a4ebe63da0f4e6125ace`
- MATCH_ORDER: `737e1d7846a8375f5809e593d32b7456483c4b7cfba6c08ccb295d7950a08a3f`
- SCOPE_AUDIT: `92eb13a44166e5c9518068225d43e7346589b2fa23ab31f3b5283d00d5ec26a8`

Run dates are pinned literals (no `date.today()`), so regeneration is stable
across days. `created` on alias/future-leakage/lifecycle moved
2026-10-07 → 2026-10-08 (regeneration day; row content unchanged apart from
GEN_REF paths).

### 5. Test verification (this tree, vs I03H baseline)

I03 focused **84 passed** (baseline 84). Normalization **497 passed**
(baseline 497). I11R2 **14 passed**, byte-stability digest unchanged
(baseline 14). Full project **3895 passed / 14 skipped / 0 failed** in
1035.68s (baseline 3895/14). Ruff changed-scope all-pass; mypy 10 inherited
/ 0 identity; compileall OK; secret scan clean. Suite side effects: the
full run rewrites sealed bloc_04 JSONs (line-ending churn + I15
`files_scanned` counts 122/279/207 → 132/309/257, workspace grew since the
B4-I15 seal; `result: OK` unchanged; pre-existing, zero files added there by
I03I) — restored to sealed state after every run; I11R2 re-verified green on
the restored tree.

### 6. Evidence narrative

`BLOC_05_I03_IMPLEMENTATION_EVIDENCE.md` gains section 10 (I03I correction
record: discrepancy, corrected input, measured result, custody, hashes,
verification, limitations); governance renumbered 11, content unchanged.
Earlier ledger entries and sealed commits preserved; §161 untouched.

### 7. Custody + governance (unchanged disposition, no self-ratification)

New commit on `agent/crypto-sensor-fabric-build` only (fast-forward push;
report SHA in final report). Bloc 4 / I17 / B5-I01 / B5-I02 evidence
untouched; tracked worktree clean after commit; `.bu_tmp/` remains
untracked. PASS_SENSOR_B5_I03_LIFECYCLE_ALIAS_PIT_RESOLVER_SEALED =
**PENDING_OPERATOR_REVIEW**. BLOC_05_IMPLEMENTATION_STATUS =
**I03_COMPLETE_PENDING_OPERATOR_REVIEW**. I03_IDENTITY_RESOLVER_SUBGATE =
**IMPLEMENTATION_PASS_PENDING_OPERATOR_REVIEW**. IDENTITY_GATE and all other
gates = **NOT_YET_EARNED**. next_checkpoint_authorized = **FALSE**.
recommended_next = **OPERATOR REVIEW OF SENSOR-B5-I03I**. B5-I04+ =
UNAUTHORIZED. Bloc 6 = UNAUTHORIZED. research = FROZEN.
MAIN_DIVERGENCE_STATUS unchanged: EXTERNAL / UNRECONCILED /
NON-BLOCKING_FOR_I03. HARD STOP after push and report.

---

## 163 - SENSOR-B5-I03J: I03 OPERATOR RATIFICATION + I04 READINESS (I04 NOT AUTHORIZED)

Date: 2026-10-08. Start head `dcd23e94f` (I03I; required starting HEAD,
verified equal to remote build head; tracked tree clean; origin/main
`e3e38e838` untouched). Operator decision via directive SENSOR-B5-I03J:
the operator **ACCEPTED** the I03 technical subgate and its accumulated
evidence chain. Governance-only checkpoint: zero production or test
changes (tracked outputs = this entry, `BLOC_05_I03_OPERATOR_RATIFICATION.md`,
`BLOC_05_I04_READINESS_ASSESSMENT.md`, plus the disclosed one-line
mechanical republish of `BLOC_04_I11R2_GOVERNANCE_BINDING_AUDIT.json`,
see §2).

### 1. Accepted chain (8 commits, 0 merges, linear)

`9ad8279e2` (I02-RATIFY) → `e06c26452` (I03A) → `06dcc7eb9` (I03B) →
`5e9424835` (I03C) → `61148c02e` (I03D-impl) → `02eac4053` (I03D) →
`13f05ae7a` (I03D amendment) → `67b7f4de1` (I03H Option 1 + G1–G4) →
`dcd23e94f` (I03I reproducibility + KB narration correction). Repair
records §159–§162 and evidence narrative sections 4/8/9/10 preserved;
I03H recorded as prospective operator authorization; I03I changed evidence
+ generator custody only (`git diff 67b7f4de1..dcd23e94f -- quant-lab/src`
is empty); only production change since the I03D amendment is `resolver.py`
inside I03H. Git proves committed linear ancestry and reachable evidence;
Git alone is not claimed to prove absence of pre-push local rewrites.

### 2. Ratification-time verification

Contract matrix C1–C10 all RATIFIED with per-invariant evidence (see
`BLOC_05_I03_OPERATOR_RATIFICATION.md` §2): valid-time half-open law;
Option 1 knowledge law in `_known_by` (prospective-authorization docstring
intact); `InstrumentAlias` = exactly 11 frozen fields; provider-ID/venue
isolation; lifecycle state laws; ambiguity never manufactures a winner;
`_empty()` fabricates no identifiers or evidence refs; `TERMS_UNVERIFIED`
reserved and never constructed (G4 pin re-verified); tracked-source
reproducibility 6/6. Fresh matrix recount from committed bytes: KB 14/14,
adversarial 25/25, alias 6/6, leakage 4/4, lifecycle 17/17, match-order
10/10 — all PASS. External CI on accepted head: 0 check-runs →
`external_ci = NONE_OBSERVED`. L2 (cross-revision knowledge overlap)
**ruled non-blocking**: no frozen supersession behavior exists to violate,
overlapping eligible candidates already fail closed to AMBIGUOUS, registry
refuses overlapping active terms; the probe gap belongs to later authorized
coverage work. Carried-forward I03I baseline (previously measured on this
byte-identical tree, **not rerun here**): I03 84 / normalization 497 /
full 3895 passed / 14 skipped / I11R2 14 byte-stable / ruff / compileall /
secret scan clean / mypy 10 inherited 0 identity. The full project suite
was NOT rerun for this governance-only checkpoint (no executable surface
changed) — disclosed per directive.

**Custody defect discovered + repaired (disclosed).** The governance-binding
test was RED at the required starting HEAD `dcd23e94f`: I03I added four
tracked generator `.py` files without republishing
`BLOC_04_I11R2_GOVERNANCE_BINDING_AUDIT.json` (still claiming
`python_files_scanned: 1033`; measured 1037) — the I02D mechanical-republish
precedent was missed because I03I's test battery ran pre-commit. This is
I11R2-era bookkeeping drift, not an I03 invariant contradiction (C1–C10
unaffected; not `I03_RATIFICATION_BLOCKED`). Repaired via the artifact's
designed path (`UPDATE_I11R2_EVIDENCE=1`): diff = exactly one line
`1033 → 1037`, rows byte-unchanged, disclosed as the single protected-
evidence exception in this commit. Post-repair governance battery (binding
audit, I11R2 digest, job-state, I07R1I/I10/I16): **84 passed / 0 failed**.

### 3. Governance promotion (established vocabulary)

PASS_SENSOR_B5_I03_LIFECYCLE_ALIAS_PIT_RESOLVER_SEALED =
**OPERATOR_ACCEPTED** (was PENDING_OPERATOR_REVIEW).
I03_IDENTITY_RESOLVER_SUBGATE = **IMPLEMENTATION_PASS** (was
IMPLEMENTATION_PASS_PENDING_OPERATOR_REVIEW; Bloc 4 precedent: operator
acceptance sets IMPLEMENTATION_PASS). BLOC_05_IMPLEMENTATION_STATUS =
**I03_OPERATOR_ACCEPTED** (was I03_COMPLETE_PENDING_OPERATOR_REVIEW;
parallel to I02_OPERATOR_ACCEPTED §158).
BLOC_05_NORMALIZATION_IMPLEMENTED = PARTIAL_PIT_IDENTITY_FOUNDATION
(unchanged). **All 8 bloc gates remain NOT_YET_EARNED**, including
**IDENTITY_GATE** — the program-level gate is NOT earned by subgate
ratification. next_checkpoint_authorized = **FALSE** (unchanged — I04 is
NOT authorized by this directive). BLOC_05 = INCOMPLETE. BLOC_06 =
UNAUTHORIZED. research = FROZEN. MAIN_DIVERGENCE_STATUS unchanged:
EXTERNAL / UNRECONCILED / NON-BLOCKING_FOR_I03.

### 4. I04 readiness (read-only reconstruction, Operation B)

`BLOC_05_I04_READINESS_ASSESSMENT.md` reconstructs the frozen checkpoint
**SENSOR-B5-I04 “contract terms + linear/inverse conversion primitives”**
(bloc_05/06 §19 + bloc_05/07 §10, blob-identical plan copies verified
against `agent/crypto-sensor-fabric-plan`), with authority clauses,
dependency table, interface inventory, identity→I04 status map,
permission/prohibition citations, staged blueprint A–G, adversarial
test-class plan with exact-set inventory, tracked-generator evidence plan,
and historical-noninterference rules. No I04 code, tests, or placeholders
were written. I04_READINESS = **MEASURED_AND_REPORTED**. Verdict:
**REQUIRES_OPERATOR_DECISION** on exactly two smallest questions — D1
`ContractTermsSnapshot` schema source (name frozen, field list not), D2
`TERMS_UNVERIFIED` construction ownership (resolver modification not
granted by any clause). I04_IMPLEMENTATION_AUTHORIZATION = **FALSE**.
recommended_next = **OPERATOR DECISION ON D1/D2, THEN A SEPARATE I04
IMPLEMENTATION DIRECTIVE IF DESIRED**. HARD STOP after push and report.

## 164 - SENSOR-B5-I04A: CONTRACT TERMS SNAPSHOT + PROJECTION FOUNDATION (IMPLEMENTATION PASS, PENDING OPERATOR REVIEW)

- **Custody:** required = actual starting HEAD
  `72984adbcc29580bb7942b119f59d3372ebccd8e`, `git status --short`
  clean, remote build head equal; frozen plan blobs re-verified
  SAME against `agent/crypto-sensor-fabric-plan`; I03J ratification
  reachable. One bounded I04A implementation commit; no squash,
  amend, reset or rebase; ff-only push to
  `agent/crypto-sensor-fabric-build`.
- **Operator decisions applied:** D1 = interpretation A —
  `ContractTermsSnapshot` is a PIT projection of terms already recorded
  on the I02-accepted `ContractInstance` (plus `quote_asset_id` read
  from its accepted `EconomicContract`, required verbatim by
  bloc_05/03 §6 quote_asset); every field mapped field-by-field to a
  frozen clause in `BLOC_05_I04A_SCHEMA_AUTHORITY_MATRIX.json` (32
  source rows, 17 projected, 0 unmapped, 0 invented terms, 0 defaults).
  D2 = interpretation B — I03 resolver consumed, never modified
  (identity diff vs HEAD empty); `TERMS_UNVERIFIED` stays reserved
  (AST-verified: zero non-docstring mentions in `terms/`, zero
  construction lines in resolver.py); terms verification enforced at
  the I04 boundary (resolved identity + `payoff_type=UNKNOWN` → no
  snapshot, status untouched); no new enum, flag, or public response
  contract (snapshot | typed `None` absence), so no STOP fired.
- **Implementation:** new subpackage
  `src/crypto_sensor_fabric/normalization/terms/` (`__init__.py`,
  `snapshot.py`, `projection.py`) — 17-field frozen immutable model +
  pure `project_contract_terms()` with clock/payoff/referential
  fail-closed refusal; no conversion, price, or identity logic.
  Placement avoids I08 `common/conversion.py` ownership and the
  forbidden `normalization/terms.py`. I01 scope-audit subpackage
  allowlist extended `{"identity"} → {"identity","terms"}` under the
  I02 precedent (disclosed); top-level API stays exactly 24 symbols;
  all other scope laws untouched.
- **RED-first:** suite authored before any module existed;
  pre-implementation run failed `ModuleNotFoundError` (pytest exit 2);
  no existing code touched to produce RED; Stage C then 28/28
  (T04A-01..20 + A1-A8).
- **Evidence (V4):** tracked generator
  `research/crypto_foundry/sensor_fabric/scripts/b5_i04_terms.py`
  (committed in the same stage as its evidence); double-run 4/4
  byte-identical, sha256 — schema `014f5aac…cca9351f` (32 rows), PIT
  `79de338f…43ef2538` (12/12 PASS), adversarial
  `19741acc…2fcd9b27` (8/8 PASS), scope `07ca4a69…17ed02fb`
  (10/10 PASS). Defect fixed + disclosed: first generation embedded
  `repr()` memory addresses for nested `Annotated` validators →
  nondeterministic schema hash; stable address-stripped repr now
  reproduces byte-identically.
- **Verification:** V1 focused **28 passed**; V2 normalization
  **525 passed** (I03I baseline 497 + 28); V3 I03 resolver **84
  passed**; V4 as above; V5 protected historical evidence — see
  disclosure below; V6 I11R2 count **1037 → 1042** (5 new tracked
  Python files) republished via `UPDATE_I11R2_EVIDENCE=1`, disclosed;
  V7 full project **3923 passed / 14 skipped / 0 failed** in 19:43
  (3895 I03I baseline + exactly the 28 new I04A tests), exit 0; V8
  ruff changed-scope all checks passed, mypy **0 new** (10 inherited
  provider/probe errors unchanged), compileall OK, secret scan clean.
- **V5 disclosure (Windows test-environment artifact):** the full suite
  regenerates 7 sealed Bloc 4 evidence JSONs
  (`BLOC_04_I03R1_ATOMIC_ORDER`, `BLOC_04_I03R1_NAMESPACE_DURABILITY`,
  `BLOC_04_I04R1_POINTER_SCHEMA`, `BLOC_04_I04R1_PROVENANCE_MATRIX`,
  `BLOC_04_I04R2_USABLE_PROVENANCE_MATRIX`,
  `BLOC_04_I04_CATALOG_SCHEMAS`, `BLOC_04_I04_MANIFEST_CONCURRENCY`)
  through `Path.write_text` text-mode writes → CRLF line endings on
  Windows. Content verified identical modulo EOL
  (`git diff --ignore-cr-at-eol` empty) and all 7 restored to HEAD
  bytes pre-commit; **not** part of this commit. Zero semantic change
  to any historical evidence.
- **Acceptance (§10, each predicate reported in the final report):**
  15/15 satisfied for I04A scope: D1 mapping grounded, D2 preserved,
  schema fidelity, PIT clock fidelity, no false verified terms, no
  identity mutation, no fabricated economic values, no
  unverified→verified promotion, 20/20 T04A, 8/8 adversarial, 4/4
  reproducibility, protected evidence intact, regressions green, no
  unauthorized expansion. R1–R15: I04A closes only the contract/schema
  portion (R1, R6, R13, R14, R15 + snapshot half of R10); conversion
  obligations (R2–R5, R7-class) remain open for I04B.
- **Governance state:**

```text
B5-I03_SUBGATE = IMPLEMENTATION_PASS
B5-I03_RATIFICATION = OPERATOR_ACCEPTED
B5-I04A = IMPLEMENTATION_PASS_PENDING_OPERATOR_REVIEW
B5-I04_COMPLETE = FALSE
IDENTITY_GATE = NOT_YET_EARNED
TIME_GATE = NOT_YET_EARNED
SEMANTIC_GATE = NOT_YET_EARNED
UNIT_GATE = NOT_YET_EARNED
LINEAGE_GATE = NOT_YET_EARNED
DUPLICATE_REVISION_GATE = NOT_YET_EARNED
REPLAY_SAFETY_GATE = NOT_YET_EARNED
GOLDEN_T0_T1_GATE = NOT_YET_EARNED
next_checkpoint_authorized = FALSE
B5-I04B+ = UNAUTHORIZED
BLOC_06 = UNAUTHORIZED
RESEARCH = FROZEN
```

`IDENTITY_GATE` remains NOT_YET_EARNED pending runtime execution proof
at finalized GOLDEN_T0_T1 frames. I04A does not self-ratify; operator
review required before any I04B directive. **HARD STOP after push and
report.**

## 165 - SENSOR-B5-I04B: LINEAR/INVERSE CONVERSION ENGINE (IMPLEMENTATION PASS, PENDING OPERATOR REVIEW) + I04A OPERATOR ACCEPTANCE

- **Operator acceptance recorded (I04B directive Book 0.1):** the operator
  accepts the I04A technical foundation delivered at
  `4f18a589c12bae41b4dd29860823fd8570507c7b` (ContractTermsSnapshot +
  project_contract_terms + PIT eligibility, D1/D2, 20 functional + 8
  adversarial cases, 4 reproducible artifacts) as an implementation
  foundation. `B5-I04A = OPERATOR_ACCEPTED` (implementation foundation
  only -- this does NOT ratify the complete I04 checkpoint).
- **Custody:** required = actual starting HEAD
  `4f18a589c12bae41b4dd29860823fd8570507c7b`, branch
  `agent/crypto-sensor-fabric-build`, repository `dabiggestpoppa/larger-lab`.
  Verification directive: no restart, no scope broadening, repair only
  demonstrated defects, seal only if earned.
- **Defects found during verification and repaired (bounded):**
  (a) the first completed full run raced a duplicate concurrent pytest run
  and reported 2 non-reproducible failures (stale module cache predating the
  in-session `terms/__init__` firewall repair; duplicate-process rewrite of
  Bloc 4 JSONs inside `test_evidence_directory_untouched`'s before/after
  window) -- both pass in isolation; the uncontested rerun passed clean;
  (b) the I04B producer named the governance ledger file in its changed-path
  allowlist, tripping the I11R2 binding predicate -- the path was removed
  (generation-before-append ordering documented in the producer docstring);
  NO allowlist entry was added.
- **Evidence (V4):** tracked producer
  `research/crypto_foundry/sensor_fabric/scripts/b5_i04b_conversion.py`;
  four consecutive runs byte-identical; sha256 --
  dimensional authority `029280ca...bb640c` (5 rows),
  linear `b675d95c...1bb6f29` (7 rows), inverse `7aa3fc21...90c015f1`
  (17 rows), blocked `cde6e4ce...0cec62a6` (11 rows), adversarial
  `0e6516a7...d2c580a71` (10 rows), scope audit `26cba7eb...276a095`
  (8/8), unit validation `8945a679...07a9572cb` (35 rows) -- 58 measured
  rows, 0 failed. Independent Decimal oracle (no production import)
  recomputed 19/19 arithmetic expectations from the frozen formulas
  (0.003, 75.000, 0.4, 3.303/0.0005, 4.000004) -- all match.
  The 34 first-generation expectation edits were recovered and classified
  from the transcript: 34 NUMERICALLY_EQUIVALENT_FORMAT_CHANGE, 0
  semantic, 0 incorrect-oracle (full table in
  BLOC_05_I04B_IMPLEMENTATION_EVIDENCE.md section 3).
- **Price availability (PIT):** `market_available_at` (bloc_05/02 S4) is a
  required field; six counterexamples PRICE-PIT-01..06 all behave fail-closed
  (available-after-cutoff BLOCK, control VALUE, observation-after-cutoff
  BLOCK, type substitution BLOCK, missing availability field BLOCK at model
  construction, blank source BLOCK). Disclosure: primitives enforce
  observation/availability against the caller-supplied knowledge cutoff;
  event-time binding is the caller's cutoff choice (probed both ways).
- **Verification:** V1 I04B focused **54 passed**; V2 normalization **579
  passed** (525 I04A baseline + 54); V3 I03 focused **84 passed** (exact
  historical match); V4 as above; V5 protected historical evidence -- 11
  Bloc 4 JSONs dirtied by the full suite (CRLF + machine counters, L4
  behavior) restored to HEAD bytes, digest+binding re-run **9 passed**;
  V6 I11R2 count **1042 -> 1045** (3 new tracked Python files) republished
  via `UPDATE_I11R2_EVIDENCE=1`, disclosed; V7 full project **3977 passed /
  14 skipped / 0 failed** in 1362.28s, exit 0 (3923 I04A baseline + exactly
  the 54 new I04B tests), command `python -m pytest tests -q` from
  quant-lab -- the same command lineage as the 3895/3923 historical runs
  (the earlier broad-collection SystemExit is a pre-existing research-script
  hazard outside this suite, classified EXTERNAL_COLLECTION_HAZARD); V8
  ruff changed-scope clean, mypy **0 errors in I04B files** (inherited
  baselines: 10 scoped / 15 repo-wide, all in untouched provider/probe
  files), compileall OK, secret scan clean.
- **Public API noninterference:** `terms/snapshot.py` and
  `terms/projection.py` byte-identical to HEAD; `terms/__init__.py`
  export section identical (docstring-only); zero tracked test
  modifications; identity/ diff empty; top-level surface = 24 symbols.
- **Acceptance (§09 G01-G22):** each gate adjudicated individually in the
  operator report; all mandatory gates PASS. R1-R15: all COVERED for I04B
  scope (evidence doc section 13); I04 checkpoint still awaits operator
  acceptance of this stage.
- **Governance state:**

```text
B5-I03 = OPERATOR_ACCEPTED
B5-I04A = OPERATOR_ACCEPTED
B5-I04B = IMPLEMENTATION_PASS_PENDING_OPERATOR_REVIEW
B5-I04_COMPLETE = FALSE
IDENTITY_GATE = NOT_YET_EARNED
TIME_GATE = NOT_YET_EARNED
SEMANTIC_GATE = NOT_YET_EARNED
UNIT_GATE = NOT_YET_EARNED
LINEAGE_GATE = NOT_YET_EARNED
DUPLICATE_REVISION_GATE = NOT_YET_EARNED
REPLAY_SAFETY_GATE = NOT_YET_EARNED
GOLDEN_T0_T1_GATE = NOT_YET_EARNED
next_checkpoint_authorized = FALSE
B5-I04C+ = UNAUTHORIZED
BLOC_06 = UNAUTHORIZED
RESEARCH = FROZEN
```

I04B does not self-ratify; operator review required before any further
directive. **HARD STOP after push and report.**

## 166 - SENSOR-B5-I04R1: I04 OPERATOR RATIFICATION (COMPLETE CHECKPOINT) + I05 READINESS

Date: 2026-10-09. Start head `3da805b1c` (I04B; required starting HEAD,
verified equal to remote build head; tracked tree clean except the three
pre-existing scratch items; plan branch `4bb677f9e` untouched). Operator
decision via directive SENSOR-B5-I04R1: the operator **ACCEPTED** the
complete frozen I04 checkpoint (contract terms + linear/inverse conversion
primitives). Governance-only checkpoint: zero production or test changes
(tracked outputs = this entry, `BLOC_05_I04_OPERATOR_RATIFICATION.md`,
`BLOC_05_I05_READINESS_ASSESSMENT.md`; no I11R2 republish — this checkpoint
adds no tracked `.py`, inventory stays measured and reported at **1045**).

### 1. Accepted chain (3 required commits, single parents, 0 merges)

`72984adb` (I03J I03 ratification / I04 readiness) -> `4f18a589` (I04A terms
snapshot + PIT projection) -> `3da805b1c` (I04B linear/inverse conversion
engine). Frozen plan documents verified blob-identical to
`agent/crypto-sensor-fabric-plan` @ `4bb677f9e` (all seven Bloc 5 docs,
hash-by-hash zero diff).

### 2. Ratification-time verification (freshly measured)

R1–R15 exact-set coverage: all COVERED, UNCOVERED = ∅, UNAUTHORIZED_EXTRA = ∅
(per-table clause/test/evidence mapping in
`BLOC_05_I04_OPERATOR_RATIFICATION.md` §3). Dual-clock audit executed six
counterexamples against the committed implementation (read-only probe, exit 0):
CXT-01 convert; CXT-02 value only under the later caller cutoff / blocked under
the event-context cutoff (ownership recorded: I05 + I10+ normalizers supply the
call context; I04 primitives stay caller-clock-bound per frozen 03 §7/§8 — no
frozen clause assigns event-time binding to I04); CXT-03 availability >
cutoff blocked; CXT-04 expired knowledge interval refuses at projection;
CXT-05 foreign snapshot never re-bound (result stamps its own instance id);
CXT-06 type substitution + NaN refused. Fresh battery: I04B 54 / I04A 28 /
I03 84 / normalization 579 / binding+digest 9 / I11R2 evidence 10 — all exit
0; both evidence producers re-run: I04B 7/7 byte-identical at HEAD, I04A 4/4
byte-identical at the I04A tree (temporary detached worktree, removed;
disclosure: the I04A scope audit's I04A-era `no_linear_inverse_conversion_engine`
predicate legitimately reads I04B's operator-authorized `terms/conversion.py`
at HEAD — checkpoint-time scope truth, sealed artifact untouched, same class
as I03 L4). Independent Decimal oracle 19/19; 34 expectation edits remain 34
format-equivalent / 0 semantic. Full suite NOT rerun (governance-only,
directive §09); carried measurement 3977 passed / 14 skipped on the
byte-identical `3da805b1c` tree, disclosed as historical.

### 3. Governance promotion (established vocabulary only)

PASS_SENSOR_B5_I04A_TERMS_FOUNDATION PROPOSED -> **OPERATOR_ACCEPTED**;
B5-I04B IMPLEMENTATION_PASS_PENDING_OPERATOR_REVIEW -> **OPERATOR_ACCEPTED**;
B5-I04 -> **OPERATOR_ACCEPTED**; B5-I04_COMPLETE FALSE -> **TRUE**;
BLOC_05_IMPLEMENTATION_STATUS I03_OPERATOR_ACCEPTED -> **I04_OPERATOR_ACCEPTED**
(parallel to I02 §158 / I03 §163); I05_READINESS ->
**MEASURED_AND_REPORTED** (parallel to I04_READINESS §163);
I05_IMPLEMENTATION_AUTHORIZATION = **FALSE** (unchanged); B5-I03 =
OPERATOR_ACCEPTED (unchanged). **All 8 program gates remain NOT_YET_EARNED.**
next_checkpoint_authorized = **FALSE** (unchanged — this ratification grants
no I05 authority; a separate implementation directive is required).
B5-I04C+ = UNAUTHORIZED (unchanged — R1–R15 complete, so no I04C work
package exists to authorize). BLOC_05 = INCOMPLETE (I05..I23 remain).
BLOC_06 = UNAUTHORIZED. RESEARCH = FROZEN. No status value was invented; no
program gate was promoted; I04 did not self-ratify.

### 4. I05 readiness (read-only reconstruction, Operation D)

`BLOC_05_I05_READINESS_ASSESSMENT.md` reconstructs frozen checkpoint
**SENSOR-B5-I05 "time semantics registry + interval conventions"**
(bloc_05/06 §19 + bloc_05/07 §10, blob-identical plan copies verified): 18
governing clause rows (bloc_05/02 §2–§18, G2, F8), dependency table (I01–I04
all accepted), required-module inventory (7/7 modules + 2/2 configs ABSENT —
correctly, I05 not started), input/output schema contract, test layers
(bloc_05/06 §13), evidence artifact `bloc_05_time_validation.json` (ABSENT
correctly), acceptance predicates, forbidden behavior and stop conditions.
No I05 code, tests, or placeholders were written. Recommended next =
**OPERATOR DECISION ON AN I05 IMPLEMENTATION DIRECTIVE, IF DESIRED**.
HARD STOP after push and report.

## 167 - SENSOR-B5-I03I RE-VERIFICATION: EVIDENCE AMENDMENT A + REPRODUCIBILITY RE-RUN (PENDING_OPERATOR_REVIEW)

Date: 2026-10-09. The SENSOR-B5-I03I directive was re-issued with required
start head `67b7f4de1` (I03H). Reality lock: the repository had already
advanced past that point — I03I itself landed as `dcd23e94f`, then I03J
ratification (`72984adbc`), I04A (`4f18a589c`), I04B (`3da805b1c`), I04R1
(`19ffc740a`). Local HEAD = remote `agent/crypto-sensor-fabric-build` =
`19ffc740a40f1264ceca2f8b4ceed13a4a8c3208` (verified via ls-remote,
fast-forward); tracked worktree clean apart from the three pre-existing
untracked scratch items. The I03I checkpoint was therefore **verified in
place, not re-executed**: no duplicate checkpoint commit, no sealed evidence
rewritten, no earlier ledger section modified.

### 1. Phases 1-3 re-verification (measured, 2026-10-09)

- Independent fixture rebuilt from the production models (generator NOT
  imported): the five KB boundary verdicts reproduce 5/5 (`known_from - 1us`
  blocked; `== known_from` resolves; `known_to - 1us` resolves;
  `== known_to` blocked; `> known_to` blocked).
- Diff of the I03H-sealed KB matrix (`67b7f4de1`) vs the current matrix:
  `input_condition` changed on exactly **KB1, KB3, KB7b**; every other row
  changed only its GEN_REF path. Diff of the original `.bu_tmp` producer vs
  the tracked producer: execution lines byte-identical (only GEN_REF strings,
  the three narration strings, and the `_ts` helper differ) — proving the
  I03H run executed true 1us boundaries and the defect was narration-only,
  as §162 recorded.
- **New finding — Amendment A (prospective, disclosed):** §162 §1/§2 and
  evidence §10.1/§10.2 label the three corrected rows "KB1/KB3/KB5"; the
  measured corrected set is **KB1/KB3/KB7b**. KB5's narration
  (`cutoff=2023-12-02T12:00Z > known_to`) was already correct at the I03H
  seal and unchanged by I03I; KB7b's old narration
  (`2023-11-30T23:59:59.999999Z`) was the third instance of the
  midnight/noon error. Prose row labels only — no matrix row, expected
  status, observed status, flag, evidence reference, or artifact byte is
  affected. Recorded in evidence §10.7 (Amendment A); evidence §10.1/§10.2
  and this ledger's §162 are retained verbatim (append-only custody).
- Cross-artifact sweep: all 76 matrix rows PASS (KB 14, leakage 4,
  match-order 10, lifecycle 17, alias 6, adversarial 25) with zero
  expected/observed mismatches; scope audit clean (forbidden imports absent,
  no wall-clock/filesystem tokens).

### 2. Generator custody re-run (tracked source only, double run)

All four tracked producers invoked twice from quant-lab
(`PYTHONIOENCODING=utf-8 python research/crypto_foundry/sensor_fabric/scripts/<name>.py`):
mats (leakage 4/4, match-order 10/10, lifecycle 17/17, alias 6/6, KB 14/14),
scope, redteam (25/25 PASS), adv_wrap. 7/7 artifacts byte-identical across
both runs and to the committed bytes; tracked worktree clean of generated
changes after both runs. sha256s match evidence §10.4 (KB `ae249425...`,
ALIAS `efd7ac47...`, LEAKAGE `09b487e8...`, LIFECYCLE `4efae87d...`,
MATCH_ORDER `737e1d78...`, SCOPE `92eb13a4...`) plus ADVERSARIAL
`d19f29ce3d9b1f3810888a943e698d44bf70ab00f87631df5814d1a4b18a25ce`.

### 3. Test verification vs directive baselines (this tree)

- I03 focused: **84 passed** (baseline 84) — match.
- Normalization: **579 passed** (baseline 497). Reconciled: the I04A/I04B
  checkpoint test files add exactly **82** tests (measured: those two files
  alone = 82); 579 - 82 = 497 — match after accounting for later authorized
  checkpoints.
- I11R2: **14 passed** (baseline 14) — match; re-verified on the restored
  sealed bloc_04 tree.
- Full project: **3977 passed / 14 skipped / 0 failed**, exit 0, 1217.70s
  (baseline 3895/14; 3895 + 82 I04 = 3977 — reconciled).
- KB matrix: **14/14 PASS** — match.
- Static: ruff clean on the four tracked I03 producers (changed scope;
  repo-wide inherited baseline untouched); mypy 10 errors, **0 in identity**
  (all inherited in providers); compileall OK; secret scan clean.
- Suite side effects: the full run rewrote sealed bloc_04 JSONs (documented
  line-ending/files_scanned churn, §162 §5) — restored to sealed state via
  `git checkout` of `evidence/bloc_04/`; I11R2 re-verified green on the
  restored tree.

### 4. Custody + governance (unchanged disposition, no self-ratification)

Single minimal commit on `agent/crypto-sensor-fabric-build` only (evidence
§10.7 Amendment A + this ledger section; fast-forward push; SHA reported in
the final report). No production code, test, matrix, or earlier evidence
changed; `.bu_tmp/` and the I06 spike remain untracked. Governance values
unchanged from §166: B5-I03 = **OPERATOR_ACCEPTED** (Amendment A is
narration-label correction only, no acceptance predicate affected);
B5-I04 = OPERATOR_ACCEPTED; B5-I05_IMPLEMENTATION_AUTHORIZATION = **FALSE**;
all 8 program gates (IDENTITY_GATE included) = **NOT_YET_EARNED**;
next_checkpoint_authorized = **FALSE**; B5-I04C+ = UNAUTHORIZED; BLOC_06 =
UNAUTHORIZED; RESEARCH = FROZEN. MAIN_DIVERGENCE_STATUS unchanged: EXTERNAL /
UNRECONCILED / NON_BLOCKING_FOR_BLOC_5. recommended_next = **OPERATOR
REVIEW OF THE I03I RE-VERIFICATION + AMENDMENT A, THEN THE ALREADY-RECORDED
I05 DIRECTIVE DECISION (§166 §4)**. HARD STOP after push and report.


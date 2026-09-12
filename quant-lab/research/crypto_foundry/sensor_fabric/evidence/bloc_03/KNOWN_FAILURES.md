# BLOC 3 — KNOWN FAILURES (SENSOR-B3-I11)

Status categories are mutually exclusive and deliberate: resolved issues are
NOT listed as current blockers, and current limitations are NOT failures.

## 1. CURRENT BLOCKERS

**None.**  No blocking defect is open at the time of final Bloc 3 handoff.
All four production adapters are network-validated (17/17 logical paths,
18/18 physical symbol checks) with 1360+ offline tests passing and zero
failures.

## 2. CURRENT LIMITATIONS (typed, frozen, PASS-capable truth)

| Provider | Sensor | Limitation | Runtime truth |
|---|---|---|---|
| GATE_FUTURES | LIQUIDATION / OPEN_INTEREST / POSITIONING | contract_stats has `from`/`interval`/`limit` and NO `to`; deep traversal UNRESOLVED | is_complete=False, next_resume_token=None, PARTIAL_INTERVAL/GAP_DETECTED/EMPTY_VALID |
| GATE_FUTURES | FUNDING | from/to coverage not proven exhaustive | is_complete=False (LIMITED) |
| GATE_FUTURES | all | ~180-day rolling retention caps request depth | typed `HistoricalRangeUnavailable`, never EMPTY_VALID |
| OKX_SWAP | FUNDING / TRADE | continuation direction UNRESOLVED | is_complete=False, no invented resume, truthful PARTIAL/GAP |
| DERIBIT | FUNDING | continuation/completion proof LIMITED | is_complete=False always (short-page-under-cap not proven exhaustive) |
| DERIBIT | TRADE / LIQUIDATION | completion requires source coverage + in-window rows + terminal | truthful COMPLETE/PARTIAL/GAP/EMPTY |
| KRAKEN_FUTURES | all historical | ragged verified history boundaries (I14) | literal I14 bounds; no deep-history claim |
| KRAKEN_FUTURES | all | bucket timestamp open/close/publication semantics not resolved | stated limitation, not invented |
| DERIBIT | FUNDING | `funding_rate`/`funding_1h`/`funding_8h` unverified additive fields | preserved raw, not promoted |
| all | — | exact interval-close vs publication timestamp semantics | not evidenced, not claimed |

LIMITED is a valid final readiness state.  A successful HTTP response does not
manufacture completeness; runtime completion matches the frozen I09 matrix
authority per path.

## 3. HISTORICAL FAILURES (observed, preserved as evidence)

- **I10 live smoke — Gate 1970 timestamps (3 contract_stats paths):** live
  `time` values decoded to 1970 under the old milliseconds interpretation for
  a 2026 request (catastrophic unit contradiction).  Evidence:
  `BLOC_03_I10_NETWORK_SMOKE_RESULTS.json`, operator review
  `BLOCK_SENSOR_B3_I10_MIXED`.
- **I10 live smoke — Kraken funding null timestamps + additive flag:** funding
  convenience timestamps were NULL (13-digit ms overflow under a seconds
  converter) and `relativeRate` was mislabeled ADDITIVE by a too-narrow parser
  required-set.  Evidence: `BLOC_03_I10_NETWORK_SMOKE_RESULTS.json`.
- **I10 original automated classifier** counted the Gate 1970 outcomes as
  LIVE_PASS (schema known + rows nonempty) — corrected by operator review;
  the I10R1D temporal-plausibility guard makes that impossible going forward.
- **BINANCE_USDM / BYBIT_LINEAR live reachability** (Bloc 2 probes): REST geo
  block / archive reference observed; providers excluded from production.
  Evidence: bloc_02 probe records + `12_BLOC_02_IMPLEMENTATION_DECISION.md`.
- **BITFINEX_COMMUNITY_ARCHIVE:** community archive, NOT_PIT_READY; retained as
  corroborator only.
- **COINALYZE:** free-key aggregator, NOT_PIT_READY, corroborator only;
  its API key is NEVER read by Bloc 3.

## 4. RESOLVED DEFECTS (do NOT re-open; do NOT list as blockers)

| Defect | Root cause | Resolution | Evidence |
|---|---|---|---|
| Gate contract_stats unit contradiction | I05-era SYNTHETIC ms fixture mislabeled as provider reality; parser interpreted `time` as ms | Current contract = epoch seconds; historical real unit recorded UNIDENTIFIED; final adjudication A_PRIOR_CHARACTERIZATION_ERROR | BLOC_03_I10R2_SEMANTIC_RECONCILIATION.json |
| Gate runtime manufactured completion | adapter unconditionally set is_complete=True despite frozen LIMITED/LIMITED | is_complete=False + PARTIAL/GAP/EMPTY + no resume token (I10R2B) | BLOC_03_I10R2_SEMANTIC_SEAL_EVIDENCE.md |
| Kraken funding timestamp unit | service-wide seconds converter; funding is ms | sensor-specific ms conversion (I10R1C) | BLOC_03_I10R1_STRUCTURAL_ADJUDICATION.json |
| Kraken funding `relativeRate` additive flag | parser required-set {rate} only | known metric set {rate, relativeRate} REQUIRED (I10R1C/I10R2C) | BLOC_03_I10R2_SEMANTIC_RECONCILIATION.json |
| Kraken additive key projection | `_build_dict_rows` projected every dict key | additive firewall: only required metrics projected (I10R2C) | BLOC_03_I10R2_SEMANTIC_SEAL_EVIDENCE.md |
| Gate/Kraken provenance ambiguity | pre/post-repair envelopes shared v1 | gate-adapter-v2 / kraken-adapter-v2 (I10R2C) | BLOC_03_I10R2_SEMANTIC_SEAL_EVIDENCE.md |
| I10 walker capture gap | native list-typed timestamps not sampled | list-member capture + literal Kraken ms sample (I10R1D/I10R2D) | BLOC_03_I10R2_TARGETED_RECHECK_RESULTS.json |
| 1970-as-LIVE_PASS classifier hole | no temporal sanity in smoke classifier | TEMPORAL_SEMANTIC_REVIEW guard, 365-day envelope (I10R1D) | BLOC_03_I10R1_TARGETED_RECHECK_EVIDENCE.md |

## 5. Not-a-failure notes

- **EMPTY_VALID** (e.g. Deribit liquidation with zero forced-liquidation events
  in a closed window) is evidence, not a failure — no row is manufactured.
- **Truthful LIMITED pages** (OKX/Gate/Deribit historical) remain LIVE PASS —
  network validation proves acquisition plumbing, not historical completion.
- **Additive schema fields** are evidence before observables: preserved raw,
  flagged, reviewed — never silently promoted (Kraken firewall + smoke
  SCHEMA_ADDITIVE_REVIEW).

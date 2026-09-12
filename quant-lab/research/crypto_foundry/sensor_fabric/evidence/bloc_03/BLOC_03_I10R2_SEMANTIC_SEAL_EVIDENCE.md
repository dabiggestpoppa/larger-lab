# SENSOR-B3-I10R2 — LIVE SEMANTIC TRUTH + PROVENANCE + COMPLETION SEAL

Checkpoint: SENSOR-B3-I10R2 — FINAL PRE-HANDOFF SEMANTIC CONSISTENCY SEAL
Branch: `agent/crypto-sensor-fabric-build`
Starting SHA: `3061e715ec64b69f57ed68c2e72ad5d418a35a07` (verified exact)
Ending SHA: `6fc1551d…` (see commit table)
Recheck run ID: `i10r2-recheck` · manifest hash: `ddb4dccdcdd4429b`

## Lineage

| Stage | SHA | What |
| --- | --- | --- |
| I10R2 start lock | `3061e715` | I10R1 ledger reconciliation (operator review accepted functional repair) |
| I10R2A | `da4123b2` | reconcile Gate historical-unit adjudication + current evidence truth |
| I10R2B | `d7c49225` | seal Gate runtime completion semantics against LIMITED readiness |
| I10R2C | `cb3bff61` | version repaired Gate/Kraken contracts (v2); seal Kraken additive projection |
| I10R2D | `6fc1551d` | 5-path targeted live recheck + immutable runtime overlay |

## 1. Gate — contradictory adjudication reconciled

**Provisional (I10R1A, `BLOC_03_I10R1_STRUCTURAL_ADJUDICATION.json`, immutable):**
`B_PROVIDER_SEMANTIC_DRIFT` — old unit epoch ms, new unit epoch seconds.

**Final (I10R2, this packet + `BLOC_03_I10R2_SEMANTIC_RECONCILIATION.json`, superseding):**
`A_PRIOR_CHARACTERIZATION_ERROR_WITH_UNIDENTIFIED_HISTORICAL_UNIT`.

**Why:** the ONLY committed evidence for a millisecond `contract_stats.time` is
the I05-era probe fixture (`contract_stats_success.json`, `time=1655251200000`,
commit `22714a17`) — an offline **SYNTHETIC_SCHEMA_FIXTURE** reconstructed from
fingerprints, not a real provider observation (the same synthetic
`1655251200000` value appears across every provider fixture). I06 fixtures
inherited the assumption. I13/I13R1 real probe datetimes were unit-masked by a
magnitude-aware converter and did not preserve raw values. The 2022-era real
probe attempt returned zero rows (180-day retention). Therefore:

- CURRENT_CONTRACT = **EPOCH_SECONDS** (proved: I10, I10R1, I10R2 live — exact
  1 h grid, 2026 decode, matches request window).
- HISTORICAL_PROVIDER_UNIT_BEFORE_CURRENT_LIVE_PROOF = **UNIDENTIFIED**.
- OLD_MS_ASSUMPTION = **PRIOR_CHARACTERIZATION / SYNTHETIC_FIXTURE ERROR**.
- PROVIDER_SEMANTIC_DRIFT = **NOT_ESTABLISHED** — we know our old
  implementation was wrong; we do NOT know Gate changed.

The synthetic fixture stays committed (immutable history) and is never cited as
provider-reality proof. All current Gate docs/code now carry this one canonical
diagnosis (README, adapter `_row_dt`, parsers, probe, fixture headers).

## 2. Gate — completion truth sealed against LIMITED

Frozen I09 authority for all four Gate paths: `resume=LIMITED,
completion=LIMITED` (matrix UNCHANGED). Runtime previously manufactured
`is_complete=True`. After I10R2B:

| Sensor | Request contract | is_complete | next_resume_token | Nonempty overlap flag |
| --- | --- | --- | --- | --- |
| FUNDING | `from`/`to` | **False** (no exhaustive-coverage proof) | None | PARTIAL_INTERVAL / GAP_DETECTED |
| LIQUIDATION | `from`/`interval`/`limit` (no `to`) | **False** | None | PARTIAL_INTERVAL / GAP_DETECTED |
| OPEN_INTEREST | `from`/`interval`/`limit` (no `to`) | **False** | None | PARTIAL_INTERVAL / GAP_DETECTED |
| POSITIONING | `from`/`interval`/`limit` (no `to`) | **False** | None | PARTIAL_INTERVAL / GAP_DETECTED |

Empty pages stay EMPTY_VALID (is_complete=False). An out-of-validity unit row
(13-digit under seconds) yields no overlap flag — the smoke temporal guard
flags it; no magnitude heuristic is invented. Tests: overlap, out-of-window,
empty, funding overlap, no-invented-resume-token. A truthful LIMITED page is a
valid LIVE PASS — network validation proves acquisition plumbing, not
historical completion.

## 3. Adapter semantic provenance (v1 → v2)

I10R1 materially changed runtime interpretation, so pre/post-repair envelopes
must not share a version:

- **GATE_FUTURES → `gate-adapter-v2`** (contract_stats `time` seconds in
  I10R1B; completion semantics in I10R2B).
- **KRAKEN_FUTURES → `kraken-adapter-v2`** (funding ms + known metric set in
  I10R1C).
- OKX / Deribit untouched. I09 matrix retains v1 as immutable history; the
  current-runtime overlay records v2 for I11.

## 4. Kraken — additive firewall + REQUIRED metric policy

- **Firewall (I10R2C):** `_build_dict_rows` previously projected EVERY `data`
  dict key into parsed rows, so a genuinely-new additive provider metric became
  a silently usable semantic field. It now projects ONLY the evidence-backed
  known set; unknown additive keys are preserved raw upstream (envelope),
  flagged ADDITIVE, and never promoted. Test: `brandNewMetric` absent from
  parsed rows; raw preserved.
- **relativeRate classification reconciled:** `{rate, relativeRate}` are both
  **REQUIRED** (every observed response carries both: 09 fingerprint pins
  `dict{rate, relativeRate}`, live reproductions exact; NO evidence valid
  responses omit either). The earlier KNOWN_OPTIONAL wording is superseded.
  Missing relativeRate → BREAKING (test added).

## 5. Kraken funding — LITERAL timestamp evidence (I10R2D)

The I10R1 walker-capture gap is closed: the I10R2 recheck captured native
`result.timestamp` list members through the real `kraken-adapter-v2`:

- native sample: `[1788170400000, 1788174000000, 1788177600000,
  1788181200000, 1788253200000]` — **13-digit epoch MILLISECONDS**
- decode: `2026-08-31T10:00:00Z … 2026-09-01T09:00:00Z` (hour grid, matches
  actual_first/actual_last and the requested window)
- seconds decode of the same values → year 58,658 (would have produced NULL
  conveniences — the I10 observation). Unit adjudication:
  `B_FUNDING_SPECIFIC_EPOCH_MILLISECONDS`, sensor-specific; siblings remain
  epoch seconds. No magnitude rescue.

## 6. I10R2 targeted live recheck — 5 calls, 0 retries, 0 credentials

Plan frozen before request #1 (hash `ddb4dccdcdd4429b`); executed
sequentially through the repaired v2 adapters; GET-only; allowlisted hosts
(`api.gateio.ws`, `futures.kraken.com`).

| Request | HTTP | Result class | Schema | Rows | First → Last (UTC) | Native `time` sample | is_complete | Flags | Hash (12) | ver |
| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |
| GATE funding BTC_USDT | 200 | LIVE_PASS_NONEMPTY | KNOWN_SCHEMA | 3 | 2026-09-01T08:00:01 → 2026-08-31T16:00:01 | n/a (funding `t`) | False | PARTIAL_INTERVAL | `f272bc804c46` | v2 |
| GATE liquidation BTC_USDT | 200 | LIVE_PASS_NONEMPTY | KNOWN_SCHEMA | 26 | 2026-08-31T10:00 → 2026-09-01T11:00 | `[1788170400, 1788174000, 1788177600, 1788181200, 1788260400]` (s) | False | PARTIAL_INTERVAL | `8e0535a31b02` | v2 |
| GATE open-interest BTC_USDT | 200 | LIVE_PASS_NONEMPTY | KNOWN_SCHEMA | 26 | same | same payload | False | PARTIAL_INTERVAL | `8e0535a31b02` | v2 |
| GATE positioning BTC_USDT | 200 | LIVE_PASS_NONEMPTY | KNOWN_SCHEMA | 26 | same | same payload | False | PARTIAL_INTERVAL | `8e0535a31b02` | v2 |
| KRAKEN funding PI_XBTUSD | 200 | LIVE_PASS_NONEMPTY | KNOWN_SCHEMA | 24 | 2026-08-31T10:00 → 2026-09-01T09:00 | `[1788170400000, …]` (ms) | True | — | `19f3c40439bd` | v2 |

No 1970 artifact. No null convenience timestamps on nonempty batches (temporal
guard passed). Result counts: LIVE_PASS_NONEMPTY × 5, pass 5, blocking 0,
actual network calls 5 (≤ 5), retries 0. (Gate funding rows arrive newest-first;
`actual_first`/`actual_last` preserve row order, per FetchBatch contract.)

## 7. Matrix / runtime reconciliation

I09 matrix (CSV + JSON) is UNCHANGED immutable offline evidence
(`network_smoke_status=NOT_RUN`). `BLOC_03_CURRENT_RUNTIME_ADAPTER_OVERLAY.json`
(17 paths) is the current-runtime overlay consumed by I11: adapter semantic
versions (Gate/Kraken v2, OKX/Deribit v1), per-sensor completion truth, and
I10/I10R1/I10R2 live-validation references. Combined network validation:
17/17 logical paths, 18/18 physical production-symbol checks
(I10 baseline 14 accepted + I10R1 overlay 4 + I10R2 5-path recheck confirms
Gate/Kraken truth with LIMITED semantics preserved).

## 8. Offline quality gates

- Pre-recheck full suite: **1360 passed / 0 failed** (floor ≥ 1354 met;
  1 skipped = live test without env gate, fail-closed).
- Post-recheck full suite: **1360 passed / 0 failed** (rerun after live).
- ruff: clean (changed scope).
- mypy: clean on changed scope; only the known pre-existing baseline (10
  probe/rest errors in untouched modules) remains.

## 9. Immutable artifacts

UNCHANGED: I09 matrix, I10 plan/results/evidence, I10R1 adjudication/recheck
evidence, original I10R2A reconciliation JSON (records the I10R1A decision as
history). No schema auto-update, no provider repair beyond the operator-
authorized Gate/Kraken scope, no OKX/Deribit changes, no history expansion,
no I11, no Bloc 4.

## Verdict

`PASS_SENSOR_B3_I10R2_SEMANTIC_CONSISTENCY_SEALED` — current truth proven
(seconds/ms units, REQUIRED metric set, literal Kraken ms sample, LIMITED
completion truth), historical truth not invented (UNIDENTIFIED historical Gate
unit; synthetic fixture not presented as provider proof), provenance
versioned (v2), and one coherent truth surface ready for operator acceptance of
`PASS_SENSOR_B3_I10_PRODUCTION_ADAPTER_NETWORK_SMOKE` and handoff to
SENSOR-B3-I11 (final Bloc 3 validation + handoff — NOT started).

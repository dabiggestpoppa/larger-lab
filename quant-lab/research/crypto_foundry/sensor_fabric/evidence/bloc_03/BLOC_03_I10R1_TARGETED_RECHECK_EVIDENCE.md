# SENSOR-B3-I10R1 — TARGETED REPAIR RECHECK EVIDENCE

Checkpoint: SENSOR-B3-I10R1 — GATE/KRAKEN LIVE SEMANTIC REPAIR + TARGETED RECHECK
Branch: `agent/crypto-sensor-fabric-build`
Run ID: `i10r1-recheck`
Manifest hash: `e77646fd4c5202e4`
Run anchor (UTC): `2026-09-01T02:06:52.823267Z`

## Lineage

| Stage | SHA | What |
| --- | --- | --- |
| I10-REVIEW (start lock) | `b51c3883` | operator mixed-drift block (`BLOCK_SENSOR_B3_I10_MIXED`) |
| I10R1A | `37542be5` | sanitized structural adjudication evidence |
| I10R1B | `c773aaac` | Gate contract_stats timestamp semantics → epoch seconds |
| I10R1C | `fb8c4d48` | Kraken funding timestamp unit (ms) + known metric set |
| I10R1D | `6081b88a` | fail-closed smoke temporal-plausibility guard (recheck HEAD) |

Recheck starting SHA: `6081b88ae558fb9e48b4c3bdb8deee787115c169`
Recheck repair SHAs referenced in plan: `c773aaac`, `fb8c4d48`, `6081b88a`

## Scope

Exactly the four operator-affected physical production paths (other 14 I10
physical requests were NOT rerun — they retain immutable I10 evidence):

1. `GATE_FUTURES` / `MECHANICAL_LIQUIDATION` / `BTC_USDT`
2. `GATE_FUTURES` / `MECHANICAL_OPEN_INTEREST` / `BTC_USDT`
3. `GATE_FUTURES` / `MECHANICAL_POSITIONING` / `BTC_USDT`
4. `KRAKEN_FUTURES` / `MECHANICAL_FUNDING` / `PI_XBTUSD`

Windows (closed, tiny — I10 §13 policy): end = anchor − 2 h
(`2026-09-01T00:06:52Z`), start = end − 24 h (`2026-08-31T00:06:52Z`).
Page size hint 25. Purpose `PROBE`. GET only. Zero retries. Zero credentials.

## Live call budget (I10R1 total)

| Phase | Calls | Evidence |
| --- | --- | --- |
| Pre-repair characterization | 2 | `BLOC_03_I10R1_STRUCTURAL_ADJUDICATION.json` (Gate contract_stats + Kraken funding) |
| Post-repair targeted recheck | 4 | this packet |
| **Total** | **6 / 6 max** | retries = 0 |

## Adjudication summary (evidence, not convenience)

### Gate — `PRIOR_CHARACTERIZATION_ERROR` → current contract = epoch SECONDS

- Frozen 2022-era probe fixture `contract_stats_success.json` carried 13-digit
  ms `time` (1655251200000) — an I05-era synthetic/offline-era sample.
- Live characterization (I10R1A, 1 call): `time` is 10-digit integer, exact 1 h
  grid; seconds interpretation → `2026-08-31T00:00Z … 2026-09-01T01:00Z`
  (matches request window); msec interpretation → 1970.
- I13 probe datetimes were unit-masked (`_to_datetime` magnitude heuristic) and
  the 2022 probe attempt returned zero rows (180-day retention boundary).
- Verdict: **A — the old evidence VALUES were already epoch seconds and the
  unit label/parser was wrong**; the provider did not need to have drifted.
  The I05-era ms fixture is retained as historical evidence with an explicit
  annotation; no magnitude heuristic was introduced at runtime.
- Repair (I10R1B): `_row_dt`/`_dt_millis_nullable` now interpret `time` as
  seconds; native integer preserved unchanged; adversarial tests (bool/float/
  string/None rejected; seconds → correct 2026 datetime) added for all three
  sensors sharing the physical field.

### Kraken funding — `B_FUNDING_SPECIFIC_EPOCH_MILLISECONDS` (sensor-specific)

- The Kraken probe module already documented funding-unit ambiguity; the
  service-wide convenience converter assumed seconds.
- I10 observation: funding `actual_first/actual_last` were NULL for 24 rows
  while neighboring analytics paths produced 2026 datetimes — NULL only occurs
  when the epoch value overflows year-9999 seconds (≥ ~2.5e11), i.e. the
  values are 13-digit epoch MILLISECONDS.
- Live characterization (I10R1A, 1 call): `result.timestamp` is `list[int]`,
  len 24, hour grid; `result.data` metric key set is EXACTLY
  `{rate, relativeRate}` — no new live field. The I10 `SCHEMA_ADDITIVE_REVIEW`
  was therefore a parser-policy mislabel: `relativeRate` is evidence-backed
  (I13R1 fingerprint) but was not in the parser's known set.
- Repair (I10R1C): funding-only ms conversion (other analytics paths remain
  seconds); funding known metric set = `{rate, relativeRate}`; a genuinely
  new key still classifies ADDITIVE and is never promoted to semantics.
- Captured-data note: literal `timestamp` integer values were not preserved by
  the characterization walker (recorded type/len/cardinality only; bug
  disclosed in I10R1A), and the I10R1D native-sample walker collects scalar
  `time`/`timestamp` members but the recheck runner pre-dated list-member
  capture for `result.timestamp: list[int]`, so the committed recheck row
  carries `native_first_timestamps: null` truthfully. Magnitude is nonetheless
  pinned deterministically: the same surface that produced NULL conveniences
  under seconds produced 2026 conveniences under ms; derived native first/last
  (epoch ms, hour grid) = `1788166800000` (`2026-08-31T01:00:00Z`) and
  `1788220800000` (`2026-09-01T00:00:00Z`). The harness walker was extended
  for list-typed members so future runs capture literal values.

## Temporal-plausibility guard (I10R1D)

Smoke-layer-only (never provider code): nonempty historical/event batches must
derive BOTH convenience timestamps, and derived timestamps must stay within a
generous documented **365-day** envelope around the requested window. A 1970
timestamp during a 2026 smoke classifies `TEMPORAL_SEMANTIC_REVIEW`, never
LIVE_PASS. CURRENT_ONLY books are exempt from required timestamps and tolerate
a snapshot shortly after the request end; truthful LIMITED pages outside the
window remain PARTIAL; empty-valid requires no fabricated timestamp.
Boundary tests added (§19) — 1353 offline tests green.

## Recheck results (all four 200 / GET / 0 retries)

| Request | HTTP | Result class | Schema | Rows | First → Last (UTC) | Native `time` sample | Hash (12) | ms |
| --- | --- | --- | --- | --- | --- | --- | --- | --- |
| GATE liquidation BTC_USDT | 200 | LIVE_PASS_NONEMPTY | KNOWN_SCHEMA | 26 | 2026-08-31T01:00 → 2026-09-01T02:00 | `[1788138000, 1788141600, 1788145200, 1788148800, 1788228000]` (seconds) | `5e8ff449ed73` | 905 |
| GATE open-interest BTC_USDT | 200 | LIVE_PASS_NONEMPTY | KNOWN_SCHEMA | 26 | 2026-08-31T01:00 → 2026-09-01T02:00 | same payload | `5e8ff449ed73` | 921 |
| GATE positioning BTC_USDT | 200 | LIVE_PASS_NONEMPTY | KNOWN_SCHEMA | 26 | 2026-08-31T01:00 → 2026-09-01T02:00 | same payload | `5e8ff449ed73` | 860 |
| KRAKEN funding PI_XBTUSD | 200 | LIVE_PASS_NONEMPTY | KNOWN_SCHEMA | 24 | 2026-08-31T01:00 → 2026-09-01T00:00 | list[int] len 24 (ms grid; see note) | `079d64ac8d68` | 217 |

All rows: `is_complete=True`, `quality_flags=[]`, `error_class=None`,
`evidence_ref_id` `*_RECENT_CONTROL_1h`, request fingerprint present, raw
content hash present, exact endpoints:
`api.gateio.ws/api/v4/futures/usdt/contract_stats` (×3) and
`futures.kraken.com/api/charts/v1/analytics/PI_XBTUSD/funding`.
No `1970` artifact — every Gate timestamp resolves to 2026; no null
convenience timestamps on any nonempty batch (temporal guard passed).

Result counts: `LIVE_PASS_NONEMPTY × 4`, pass 4, blocking 0,
actual network calls 4, retries 0.

## Combined I10 + I10R1 coverage (evidence overlay)

| View | I10 (immutable) | I10R1 (overlay) | Combined |
| --- | --- | --- | --- |
| Physical production-symbol checks | 14 accepted | 4 / 4 | **18 / 18** |
| Logical provider×sensor paths | 14 of 17 non-blocked evidence | 4 repaired | **17 / 17** |

The original I10 artifacts (`BLOC_03_I10_NETWORK_SMOKE_PLAN.json`,
`BLOC_03_I10_NETWORK_SMOKE_RESULTS.json`,
`BLOC_03_I10_NETWORK_SMOKE_EVIDENCE.md`) and the I09 offline matrix were NOT
modified. Three classifications are preserved distinctly: ORIGINAL AUTOMATED
(17 pass / 1 additive) → OPERATOR REVIEW (14 accepted / BLOCK_SENSOR_B3_I10_MIXED)
→ REPAIRED RECHECK (4 / 4 pass).

## Offline quality gates

- Pre-recheck full suite (before all live calls): 1353 passed / 0 failed
  (floor ≥ 1338 met).
- Post-recheck full suite: see I10R1F reconciliation (same floor).
- ruff: clean (changed scope).
- mypy: clean on changed scope; only the known pre-existing baseline
  (10 probe/rest errors in untouched modules) remains.

## Verdict

`PASS_SENSOR_B3_I10R1_TARGETED_REPAIR_RECHECK`.

Four affected physical paths 4/4 live-pass with evidenced units, no 1970
artifact, no null timestamps, KNOWN_SCHEMA, no credential, no hidden unit
heuristic. Combined with the immutable I10 baseline, physical coverage
18/18 and logical coverage 17/17 qualify for
`SENSOR-B3-I10` `PASS_SENSOR_B3_I10_PRODUCTION_ADAPTER_NETWORK_SMOKE`
under the operator review + repair sequence — final adjudication remains
with the operator (I10R1F ledger reconciliation).
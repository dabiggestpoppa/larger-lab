# BLOC 3 — PROVIDER IMPLEMENTATION REPORT (SENSOR-B3-I11)

Checkpoint: SENSOR-B3-I11 — FINAL BLOC 3 VALIDATION + HANDOFF
Branch: `agent/crypto-sensor-fabric-build`
Starting SHA: `55eb5a2d28b3f7f076ac52107f68ea56953583c2`
Final SHA: see ledger / `git log` (I11E)

## 1. Bloc 3 mission

Build a trustworthy **acquisition boundary**: four real production provider
adapters (KRAKEN_FUTURES, GATE_FUTURES, OKX_SWAP, DERIBIT) under one common
frozen protocol, preserving raw provider evidence, provider identity and native
semantics; typed failures; free-only access enforcement; and a network-validated
current-runtime truth surface.  Bloc 3 does NOT create market truth, canonical
units, consensus, normalization or research features — those belong to later
blocs.

## 2. Authority lineage

1. Frozen Bloc 1 contracts (`contracts/enums.py`, base models, error model)
2. Bloc 2 adjudicated evidence (`evidence/bloc_02/`: 08 history boundaries,
   09 schema fingerprints, 10 capability claims, 12 implementation decision)
3. `source_promotion_candidates.yaml` (I14 promotion authority)
4. Frozen Bloc 3 architecture (I01..I04 + I04R1 + I04R2 + common conformance)
5. Current provider implementation code (four adapters)
6. I09 immutable offline matrix (`PRODUCTION_ADAPTER_MATRIX.csv/.json`)
7. I10 / I10R1 / I10R2 immutable live evidence
8. `BLOC_03_CURRENT_RUNTIME_ADAPTER_OVERLAY.json` (current-runtime surface)
9. I11 derived handoff artifacts (this packet)

No final artifact overrides a stronger authority; the handoff package is a
DERIVED snapshot.

## 3. Final provider registry (exactly 4)

| provider_id | Adapter | Version |
|---|---|---|
| KRAKEN_FUTURES | `KrakenAdapter` | `kraken-adapter-v2` |
| GATE_FUTURES | `GateAdapter` | `gate-adapter-v2` |
| OKX_SWAP | `OkxAdapter` | `okx-adapter-v1` |
| DERIBIT | `DeribitAdapter` | `deribit-adapter-v1` |

Registry is CONFIGURATION / wiring, not ranking or economic preference.
Excluded providers are NOT instanced here.

## 4. Final production inventory (17 paths / 18 physical symbols)

Derived, not hand-declared (`build_readiness_records` + `compute_exact_sets`):
I14 set == adapter capability union == I09 baseline == runtime overlay == final
handoff matrix == **17**.  Physical production-symbol scope = **18**
(Kraken OI carries PI_XBTUSD + PI_ETHUSD).

| Provider | Paths |
|---|---|
| KRAKEN_FUTURES | 6 — BASIS(PRIMARY), BOOK_METRIC(PRIMARY), FUNDING(SECONDARY), LIQUIDATION(PRIMARY), OPEN_INTEREST(PRIMARY), POSITIONING(PRIMARY) |
| GATE_FUTURES | 4 — FUNDING(SECONDARY), LIQUIDATION(SECONDARY), OPEN_INTEREST(SECONDARY), POSITIONING(SECONDARY) |
| OKX_SWAP | 3 — BOOK_SNAPSHOT(CURRENT_ONLY), FUNDING(SECONDARY), TRADE(SECONDARY) |
| DERIBIT | 4 — BOOK_SNAPSHOT(CURRENT_ONLY), FUNDING(SECONDARY), LIQUIDATION(MECHANISM_MICROSCOPE), TRADE(MECHANISM_MICROSCOPE) |

Role counts: PRIMARY=7, SECONDARY=6, CURRENT_ONLY=2, MECHANISM_MICROSCOPE=2.
Sensor coverage: BASIS=1, BOOK_METRIC=1, BOOK_SNAPSHOT=2, FUNDING=4,
LIQUIDATION=3, OPEN_INTEREST=2, POSITIONING=2, TRADE=2.

## 5. Per-provider implementation summary

- **KRAKEN_FUTURES (v2):** six Market Analytics paths; dict-shape (funding
  `{rate, relativeRate}`, basis, book metric) and list-shape (OI, positioning,
  liquidation) parsers; funding timestamps epoch **ms** (sensor-specific),
  siblings epoch seconds; additive firewall (unknown metrics preserved raw,
  never projected); resume via `result.more` -> since=oldest cursor.
- **GATE_FUTURES (v2):** four paths; `contract_stats` `time` = epoch **seconds**
  (current contract, live-verified); completion sealed LIMITED
  (`is_complete=False`, PARTIAL/GAP/EMPTY, no invented resume); historical real
  unit UNIDENTIFIED (I05-era ms fixture = synthetic, prior characterization
  error, NOT provider drift); ~180-day retention typed.
- **OKX_SWAP (v1):** funding/trade historical LIMITED continuation
  (`is_complete=False`, truthful PARTIAL/GAP/EMPTY, order-invariant overlap);
  book CURRENT_ONLY; exact-int seqId; per-field closed fingerprints.
- **DERIBIT (v1):** funding LIMITED (never certified complete); trade/liquidation
  completion from source coverage with `has_more==false` terminal; liquidation =
  trade-level mechanism microscope (never aggregated numerically); book
  CURRENT_ONLY; epoch-ms INT timestamps; typed JSON-RPC errors.

## 6. Per-sensor coverage and roles

See `FINAL_ADAPTER_READINESS_MATRIX.csv/.json` (per-path roles, scope,
resume/completion, limitations) and `PROVIDER_CAPABILITY_RUNTIME.json`.

## 7. Offline test history

| Checkpoint | Suite |
|---|---|
| I10A (harness) | 1338 passed / 0 failed |
| I10C (reconcile) | 1338 passed / 0 failed |
| I10R1D (temporal guard) | 1353 passed / 0 failed |
| I10R1E (recheck) | 1354 passed / 0 failed |
| I10R2C (versions/firewall) | 1360 passed / 0 failed |
| I10R2D (recheck) | 1360 passed / 0 failed |
| **I11 final (this checkpoint)** | **1360+ passed / 0 failed** (see OFFLINE_TEST_REPORT) |

## 8. Network validation chronology

1. **I10** (`i10-live`): 18 physical calls, 0 retries — original automated
   17/18 LIVE_PASS + 1 additive; operator review → `BLOCK_SENSOR_B3_I10_MIXED`
   (3 Gate contract_stats 1970-unit contradiction + Kraken funding).
2. **I10R1** (`i10r1-recheck`): adjudicated Gate = prior characterization error
   (seconds), Kraken funding = sensor-specific ms; repaired; temporal guard;
   4/4 affected paths recheck LIVE_PASS.
3. **I10R2** (`i10r2-recheck`): semantic seal — Gate completion LIMITED,
   v2 provenance, Kraken additive firewall + REQUIRED metric set, literal
   Kraken ms sample; 5/5 recheck LIVE_PASS.
4. **Accepted combined state:** 17/17 logical paths, 18/18 physical
   production-symbol checks, network validation **PASS** (operator-accepted).
   I11 makes ZERO network calls.

## 9. Semantic repairs (documented, not erased)

- Gate contract_stats `time`: ms → seconds interpretation (native int
  preserved; I05-era synthetic ms fixture retained as annotated history;
  historical real unit UNIDENTIFIED; no magnitude heuristic).
- Gate completion: unconditional True → sealed LIMITED (matches frozen I09).
- Kraken funding timestamps: seconds → sensor-specific ms (I10 overflow
  proof + live literal sample `1788170400000..1788253200000`).
- Kraken funding metric set: {rate} → {rate, relativeRate} REQUIRED
  (KNOWN_OPTIONAL wording superseded); unknown additive keys never projected.

## 10. Known limitations

See `KNOWN_FAILURES.md` (current limitations: Gate LIMITED completion +
~180-day retention, OKX/Deribit LIMITED continuation, Kraken ragged history,
bucket-timestamp semantics unresolved, etc.).

## 11. Excluded provider disposition

See `ACCESS_CLASS_REPORT.md` §"Non-production / evidence-only providers":
BINANCE_USDM (EXCLUDED), BYBIT_LINEAR (EXCLUDED), COINALYZE (CORROBORATOR,
non-production), BITFINEX_COMMUNITY_ARCHIVE (CORROBORATOR, non-production).
Historical evidence for these remains useful and is preserved.

## 12. No normalization / research logic

Bloc 3 never performs canonical unit conversion, cross-venue CVD,
liquidation/funding/positioning state, funding consensus, quality weights,
failover, asset identity or any research compute.  Same SensorFamily != same
numerical observable (Deribit liquidation = trade-level microscope, Gate =
interval analytics, Kraken = Market Analytics measure; Kraken BOOK_METRIC !=
BOOK_SNAPSHOT).  Disagreement remains data.

## 13. Final acceptance gates G1–G8

| Gate | Result |
|---|---|
| G1 COMMON ARCHITECTURE | **PASS** |
| G2 ACCESS SAFETY | **PASS** |
| G3 RAW PRESERVATION | **PASS** |
| G4 RESUME/PAGINATION | **PASS_WITH_LIMITED** |
| G5 PROVIDER ISOLATION | **PASS** |
| G6 NO NETWORK UNIT DEPENDENCY | **PASS** |
| G7 PROVIDER COVERAGE | **PASS** (17/17 logical, 18/18 physical) |
| G8 DOCUMENTATION | **PASS** |

Each gate's evidence is itemized in the I11 evidence / ledger; no implicit
overall pass.

## 14. Proposed Bloc 3 verdict

`PASS_BLOC_03_IMPLEMENTATION` — with `BLOC_03_IMPLEMENTATION_COMPLETE = TRUE`,
`BLOC_03_FROZEN = TRUE`, `NETWORK_VALIDATION = PASS`,
`REAL_PROVIDER_ADAPTERS = 4`, `PRODUCTION_PATHS = 17/17`,
`PHYSICAL_PRODUCTION_SYMBOL_CHECKS = 18/18`.  Recommended next:
`SENSOR-B4-I01` IMMUTABLE T0 RAW EVIDENCE LAKE FOUNDATION (NOT begun).

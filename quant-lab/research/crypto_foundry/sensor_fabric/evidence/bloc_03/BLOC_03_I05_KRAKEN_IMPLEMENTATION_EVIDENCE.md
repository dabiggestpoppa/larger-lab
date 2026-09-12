# SENSOR-B3-I05 — Kraken Futures Production Adapter Implementation Evidence

**Checkpoint verdict:** `PASS_SENSOR_B3_I05_KRAKEN_ADAPTER_OFFLINE` (I05) then
`PASS_SENSOR_B3_I05R1_KRAKEN_BOUNDARY_HARDENED` (I05R1 repair) and, with the
I05R2 final seal below, `PASS_SENSOR_B3_I05R2_KRAKEN_SEALED` (proposed).
**This is NOT a global Bloc 3 PASS.**

**Operator authorization:** `SENSOR-B3-I05 — KRAKEN_FUTURES` only.
`SENSOR-B3-I06 (Gate) is NOT authorized`.  `provider_adapter_implementation_authorized
= KRAKEN_FUTURES ONLY` (recorded in SENSOR-B3-I04R2-RATIFY).

## Identity

| Field | Value |
|---|---|
| adapter_id | `KRAKEN_FUTURES.MARKET_ANALYTICS.V1` |
| adapter_version | `kraken-adapter-v1` |
| provider | `KRAKEN_FUTURES` |
| package | `quant-lab/src/crypto_sensor_fabric/providers/kraken/` |
| implementation head | `490cd111` (I05B) + `17e70035`/`a1e191ea` (I05R1A/B) + (I05R2A) |
| network_smoke_status | `NOT_RUN` (reserved for SENSOR-B3-I14) |

## Supported sensor paths (exactly six, I14-promoted)

1. `MECHANICAL_BASIS` — PRIMARY — `kraken_futures-basis`
2. `MECHANICAL_BOOK_METRIC` — PRIMARY — `kraken_futures-book_metric`
3. `MECHANICAL_FUNDING` — SECONDARY — `kraken_futures-funding`
4. `MECHANICAL_LIQUIDATION` — PRIMARY — `kraken-market-analytics-liquidation-volume`
5. `MECHANICAL_OPEN_INTEREST` — PRIMARY — `kraken_futures-open_interest`
6. `MECHANICAL_POSITIONING` — PRIMARY — `kraken_futures-positioning`

## Unsupported sensor paths (typed `CapabilityUnavailable`)

- `MECHANICAL_TRADE` — NOT promoted by I14; Kraken `/history` trade has
  current-surface/schema problems (I13R1 `F_SCHEMA_CHANGED`).
- `MECHANICAL_BOOK_SNAPSHOT` — NOT promoted by I14; `/orderbook` snapshot
  assumptions have the same schema problem.

These never return `[]` / `0` / `None` / `EMPTY_VALID`.

## I14 promotion refs

- `quant-lab/research/crypto_foundry/sensor_fabric/evidence/bloc_02/source_promotion_candidates.yaml`
  (schema_version 2.0, verification_head
  `7d5b4372114440ccbe95135fc1ec9fe6d976ceef`) — the ONLY input list consumed.
- `evidence/bloc_02/07_PIT_READINESS_MATRIX.csv`, `08_HISTORY_BOUNDARIES.csv`,
  `09_SCHEMA_FINGERPRINTS.jsonl`, `10_CAPABILITY_CLAIMS.jsonl`,
  `11_FAILURES.jsonl`.

## Bloc 2 evidence refs (evidence_basis per sensor)

- BASIS: `kraken_futures_basis_pi_xbtusd_{RECENT_CONTROL,2021,2022,2024,2026}_1h`
- BOOK_METRIC: `kraken_futures_book_metric_pi_xbtusd_{RECENT_CONTROL,2021,2022,2024,2026}_1h`
- FUNDING: `kraken_futures_funding_pi_xbtusd_{RECENT_CONTROL,2022,2024,2021,2026}_1h`
- LIQUIDATION: `kraken_futures_liquidation_pi_xbtusd_{RECENT_CONTROL,2021,2022,2024,2026}_1h`
- OPEN_INTEREST: `kraken_futures_open_interest_pi_xbtusd_{RECENT_CONTROL,2022,2024,2021,2026}_1h`
  + `kraken_futures_open_interest_pi_ethusd_{RECENT_CONTROL,2022,2024,2021,2026}_1h`
- POSITIONING: `kraken_futures_positioning_pi_xbtusd_{RECENT_CONTROL,2021,2022,2024,2026}_1h`

Every `ProviderNativeCapabilityEvidence` grant resolves its `evidence_ids`
into the I14 `evidence_basis` of its own candidate (never fabricated).

## Native acquisition modes (evidence-backed, SENSOR-B3-I05 seam)

All six promoted paths use the Market Analytics family
(`kraken-market-analytics/{analytics_type}`) with the SAME evidence-backed
mechanics, derived from the committed probe fixture, the corrected
`live_probe_contracts.yaml`, and the I13R1 fingerprints:

| field | value |
|---|---|
| historical_mode | `REST_RANGE` |
| pagination_mode | `TIME_RANGE` |
| endpoint family | `https://futures.kraken.com/api/charts/v1/analytics/{symbol}/{analytics_type}` |
| start param / unit | `since` / `epoch_seconds` |
| end param / unit | `to` / `epoch_seconds` |
| interval param | `interval` (seconds; supported {60,300,900,1800,3600,14400,43200,86400,604800}) |
| completion rule | `result.more == false` |
| resume mechanic | `result.more == true` → re-issue `since` at the oldest bucket |

Analytics types: OI `open-interest`, funding `funding`, basis `future-basis`,
positioning `long-short-ratio`, book metric `orderbook`, liquidation
`liquidation-volume`.

## Production instrument scope (I05R1 — repair 1/8)

Production support derives ONLY from committed promoted evidence.  The Bloc 2
probe universe (`NATIVE_INSTRUMENTS` incl. `PI_SOLUSD` / `PI_DOGEUSD`) is a
probe/control scope and is NOT production capability.

| scope | symbols | basis |
|---|---|---|
| `KRAKEN_PRODUCTION_INSTRUMENT_SCOPE` | `{PI_XBTUSD, PI_ETHUSD}` | evidence-backed union (08_HISTORY_BOUNDARIES.csv per-sensor rows; 09_SCHEMA_FINGERPRINTS.jsonl; 10_CAPABILITY_CLAIMS.jsonl) |
| `KRAKEN_PROBE_INSTRUMENT_SCOPE` | `{PI_XBTUSD, PI_ETHUSD, PI_SOLUSD, PI_DOGEUSD}` | Bloc 2 probe universe, retained for characterization only |

### Sensor-specific symbol scopes (from evidence, not one global list)

| sensor | symbol_scope | basis |
|---|---|---|
| MECHANICAL_OPEN_INTEREST | `{PI_XBTUSD, PI_ETHUSD}` | OI evidence IDs exist for both (per-instrument history boundaries verified 2024+ for BTC and ETH) |
| MECHANICAL_BASIS | `{PI_XBTUSD}` | basis evidence IDs observed only for `pi_xbtusd` |
| MECHANICAL_BOOK_METRIC | `{PI_XBTUSD}` | book-metric evidence IDs observed only for `pi_xbtusd` |
| MECHANICAL_FUNDING | `{PI_XBTUSD}` | funding evidence IDs observed only for `pi_xbtusd` |
| MECHANICAL_LIQUIDATION | `{PI_XBTUSD}` | liquidation evidence IDs observed only for `pi_xbtusd` |
| MECHANICAL_POSITIONING | `{PI_XBTUSD}` | positioning evidence IDs observed only for `pi_xbtusd` |

Each symbol is proven through the sensor's OWN `ProviderNativeCapabilityEvidence`
grant (`instruments` field), which resolves into the I14 evidence basis.  A
request for a supported sensor with a symbol NOT in that sensor's scope fails
typed `InvalidInstrument` BEFORE transport (e.g. `OI(PI_ETHUSD)` passes;
`BASIS(PI_ETHUSD)` fails typed).  `PI_SOLUSD` / `PI_DOGEUSD` fail production
requests on every promoted sensor unless evidence proves them.

`list_instruments()` returns `KRAKEN_PRODUCTION_INSTRUMENT_SCOPE` — a
configured production evidence scope, explicitly NOT live provider discovery
(no discovery endpoint was invented; documented in README).

## Request boundary guards (I05R1 — repairs 2/6/7)

| guard | behavior |
|---|---|
| request provider identity | `FetchRequest.provider_id != KRAKEN_FUTURES` → typed `ProviderSemanticError` BEFORE transport; same for `InstrumentListRequest` |
| named-method / sensor identity | `fetch_funding` requires `MECHANICAL_FUNDING`, etc.; mismatch → typed `ProviderSemanticError` BEFORE transport; `dispatch_fetch` remains the generic route |
| no-transport | `transport=None` → typed `ProviderUnavailable` naming the REQUESTED sensor (never a hard-coded placeholder) |

All three fail with zero transport calls.

## Granularity support matrix (I05R1 — repair 3)

`request.granularity=None` → documented default 1h (`interval=3600`).  Explicit
supported member → exact mapping (60,300,900,1800,3600,14400,43200,86400,604800
seconds).  Explicit unsupported member (e.g. `RAW_EVENT`, `BOOK_SNAPSHOT`, or
any future enum member) → typed `UnsupportedGranularity` BEFORE transport;
never silently mutated to 1h.  Every `Granularity` enum member is covered by
tests.  Fabric resolutions the provider supports but the enum cannot represent
(30m / 12h / 1w style buckets) are recorded as a limitation, not added to the
enum.

## Methodology pins (frozen per I14, unchanged)

See "Supported sensor paths" above.

## Verified history bounds (I14-frozen, ragged preserved)

- BASIS: 2022-06-15 → 2026-08-23T14:55:04.725011Z
- BOOK_METRIC: 2024-06-15 → 2026-08-23T14:55:05.140795Z
- FUNDING: 2026-06-15 → 2026-08-23T14:55:04.309346Z
- LIQUIDATION: 2021-06-15 → 2026-08-23T15:39:15.749985Z
- OPEN_INTEREST: 2024-06-15 → 2026-08-23T14:55:03.925948Z (PI_XBTUSD + PI_ETHUSD)
- POSITIONING: 2024-06-15 → 2026-08-23T14:55:05.009310Z

`EMPTY_VALID` observations (OI/funding older windows) remain first-class.

## Offline fixture inventory

`quant-lab/tests/crypto_sensor_fabric/providers/kraken/fixtures/analytics.py`
— SYNTHETIC_SCHEMA_FIXTURE matrix reconstructed strictly to the committed
09_SCHEMA_FINGERPRINTS.jsonl shapes (labeled; never presented as raw observed
evidence):

- per promoted sensor: happy / EMPTY_VALID / provider error / schema drift
- open_interest + book_metric: continuation (`more: true`) fixture
- committed Bloc 2 probe payloads retained under
  `quant-lab/tests/crypto_sensor_fabric/fixtures/probe_payloads/kraken/`
  (untouched)

NO new network call was made to obtain any fixture.

## Common conformance result

`run_conformance_suite` in **PRODUCTION_CANDIDATE** mode against the real
`KrakenAdapter` with fake transport (offline):

- Q0: provider metadata ✓ registry/free-only ✓ capability sensor-specific ✓
  evidence refs resolve ✓ promotion bounds ✓ native-mode evidence ✓
  symbol-scope gate (declared symbol scope requires grant proof) ✓
  behavioral dispatch ✓
- Q1: raw payload preserved ✓ empty-valid distinct ✓ schema drift fail-closed ✓
- Q2: retry classification ✓ resume deterministic ✓ native instrument required ✓
- **Result: 0 failed** (see `test_adapter.py::TestProductionCandidateConformance`;
  re-run at I05R1 head with all boundary guards enabled).
- NOT run under FRAMEWORK_TEST mode (forbidden for a real provider adapter).

## Provider-specific tests

- `test_capabilities.py` — provider ID frozen; exact six-path set == I14
  promotion set (no omission, no seventh path); trade/book-snapshot
  unsupported; role/PIT/methodology/history bounds retained; evidence refs
  resolve.
- `test_requests.py` — per-sensor URL + params golden contracts; epoch-second
  since/to; interval encoding; native symbol preservation; no invented
  endpoints; deterministic fingerprints; resume round-trip.
- `test_parsers.py` — per-sensor schema fingerprints; empty-valid; drift
  fail-closed; parser never canonicalizes (no oiUsd/cvd/liquidationState/
  fundingState/signAsymmetry).
- `test_adapter.py` — access gate BEFORE transport (no bypass); typed
  unsupported trade/book-snapshot; happy fetch per promoted sensor; epoch
  units; EMPTY_VALID + ragged history; SchemaDrift blocking; typed provider
  errors; raw-hash determinism; resume determinism (first/continuation/
  terminal/repeated state/overlap/round-trip); full PRODUCTION_CANDIDATE
  conformance.
- `test_native_evidence.py` (base) + `test_conformance.py` gate — adversarial
  native-mode proofs (see below).

## Free-only result

- Gate: `DEFAULT_FREE_ONLY_POLICY` (FREE_AUTOMATED, $0) + `NO_AUTH` → PASS.
- `TRADING_KEY` and unverified policy → `AccessClassViolation` raised with
  **zero transport calls** (gate runs first).
- No trading/account credentials, no signing secrets, no wallet interaction.

## Parser / schema result

- KNOWN parses; ADDITIVE flagged (`SCHEMA_ADDITIVE`); BREAKING/UNKNOWN block
  (`SchemaDrift`) with raw preserved; no zero coercion anywhere.
- Adversarial: unknown envelope blocks; every drift fixture blocks parsed
  output per sensor.

### Schema-drift raw preservation — BEHAVIORAL PROOF (I05R1 — repair 4)

The Kraken adapter now materializes the immutable `RawPayloadEnvelope` BEFORE
the parse decision.  For every promoted sensor, feeding the BREAKING/UNKNOWN
fixture:

- raises typed `SchemaDrift`;
- `SchemaDrift.raw_payload_envelope` is present and carries `provider_id` =
  `KRAKEN_FUTURES`, the correct `sensor_family`, the exact `request_fingerprint`,
  `content_hash` matching the preserved raw body (deterministic across runs),
  `schema_state` BREAKING or UNKNOWN, retrieval metadata and the resolving I14
  `evidence_ref`;
- zero parsed semantic rows are emitted.

This is asserted per-sensor in `TestSchemaDriftRawEnvelope`; the common
`AcquisitionError.raw_payload_envelope` attachment (provider-independent,
backward compatible, other error types default `None`) is covered by
`TestRawFailureEnvelope` in the base conformance suite.

### List-cardinality fail-closed (I05R1 — repair 5)

List-shaped analytics (OI / positioning / liquidation): `len(timestamp) !=
len(data)` is `BREAKING_SCHEMA_CHANGE` in BOTH directions — no `None` padding,
no truncation, no manufactured buckets.  Dict-shaped metrics (funding / basis /
book metric) enforce the same symmetric cardinality per metric column.
Provider-declared null VALUES inside a correctly-sized bucket (e.g.
book_metric `slippage1m: [None]`) remain native provider data — structural
absence is not treated as provider null.  Tested per sensor at parser and
adapter level.

## Resume result

- `more: true` → deterministic `ResumeToken` (TIME_RANGE, `since` = oldest
  bucket); JSON round-trip equal; continuation re-issues `since` exactly;
  repeated state deterministic; overlap preserved; no infinite traversal.

## Adversarial native-mode evidence proofs

| case | result |
|---|---|
| exact native historical_mode with NO evidence grant | FAIL (q0_native_mode_evidence) |
| declared mode contradicting its evidence grant | FAIL (q0_native_mode_evidence) |
| grant attached to wrong provider | FAIL (unit) |
| grant attached to wrong sensor | FAIL (unit + conformance) |
| grant broadening I14 scope (archive switch) | FAIL (unit + conformance) |
| valid Kraken evidence-backed native mode | PASS |

`source_promotion_candidates.yaml` was NOT modified.

## Known limitations

1. Bucket timestamp open/close/publication semantics unresolved by committed
   evidence — stated, not invented.
2. Funding bucket timestamp unit: committed probe fixture + live probe
   contract say epoch seconds; the Bloc 2 probe comment's ms claim has no
   committed runtime artifact — adapter uses seconds and flags the ambiguity.
3. Rate-limit capacity unknown → `RateLimitSnapshot(limit_known=False)`.
4. Liquidation = analytics `liquidation-volume` methodology; never merged with
   trade-level anatomy.
5. Provider resolutions the Fabric `Granularity` enum cannot represent
   (30m / 12h / 1w style buckets) are recorded, not added to the enum.
6. No live validation; all I05 / I05R1 behavior offline.

(I05's probe-scope note is superseded by the formal production/probe
separation above: `PI_SOLUSD` / `PI_DOGEUSD` remain available to Bloc 2
characterization history but are never exposed as production support.)

## Promotion / readiness status

- Six promoted paths: `ADAPTER_READY` (offline conformance passed).
- MECHANICAL_TRADE / MECHANICAL_BOOK_SNAPSHOT: `NOT_PLANNED` (typed
  unsupported per I14).
- `smoke_pass = NOT_RUN` for every path; `network_smoke = NOT_RUN`.
- See `ADAPTER_READINESS_MATRIX.csv` for per-path detail.

## No capability exceeded I14

- Coarse `history_scope`, verified range, role, PIT, methodology pin, access
  path, live mode, archive status, and the promoted sensor set are unchanged
  from `source_promotion_candidates.yaml` (enforced by
  `promotion_bound_violations` + `q0_native_mode_evidence`).
- Native evidence only REFINES acquisition mechanics.

## Commit SHA

- implementation head: `490cd111` (SENSOR-B3-I05B).
- evidence/README/readiness/ledger commit: `f5295a8e` (SENSOR-B3-I05C);
  reconciliation record: SENSOR-B3-I05R (`254716bd`).
- I05R1: `17e70035` (I05R1A — production request + instrument boundaries),
  `a1e191ea` (I05R1B — raw drift envelope + parser cardinality),
  (I05R1C — evidence/README/readiness/ledger reconciliation).
- I05R2 (SENSOR-B3-I05R2A — request identity + timestamp schema);
  (SENSOR-B3-I05R2B — evidence/README/ledger seal).

## SENSOR-B3-I05R2 — KRAKEN OFFLINE FINAL SEAL

Final production-boundary seal applied after operator review (intentionally
small; neither redesigns the provider system nor broadens I14).

- **Foreign FetchRequest identity (R1):** a rejected
  `request.provider_id != KRAKEN_FUTURES` raises typed `ProviderSemanticError`
  carrying the ACTUAL requested `sensor_family` (all six promoted sensors
  proven; zero transport calls).  Instrument-list discovery has no requested
  sensor, so its mismatch uses the documented **neutral provider-level
  placeholder** (`NEUTRAL_INSTRUMENT_LIST_SENSOR`) and never claims a real
  scientific sensor.
- **Unsupported named-method identity (R2):** `fetch_trades` and `fetch_book`
  check method/sensor identity FIRST.  `fetch_trades(FUNDING request)` is a
  `ProviderSemanticError` mismatch (never a claim that FUNDING is
  unsupported); `fetch_trades(TRADE request)` is typed `CapabilityUnavailable`.
  The same holds for `fetch_book` with `MECHANICAL_BOOK_SNAPSHOT`.
- **Timestamp schema frozen (R3):** Market Analytics bucket timestamps are
  evidence-backed `list[int]` in **epoch seconds**; each non-empty member must
  be exactly a Python `int` (`type(ts) is int`, bool excluded).  A
  string/float/bool/`None`/mixed element classifies as
  `BREAKING_SCHEMA_CHANGE`: parsed semantic output is blocked and the raw
  payload is PRESERVED in the `SchemaDrift.raw_payload_envelope`.  No silent
  coercion (`str->int`, `float->int`, `True->1`).  Empty `timestamp` lists stay
  `EMPTY_VALID`.
- **Raw envelope on drift (R3/R4):** invalid-timestamp `SchemaDrift` retains
  the exact preserved raw envelope (provider, sensor, request fingerprint,
  raw body, content hash, `BREAKING_SCHEMA_CHANGE`, evidence ref), proven
  behaviorally through the real adapter.
- **Resume/non-monotonic (R4):** resume `since` and monotonicity derive only
  from already-schema-validated int timestamps; the silent `int()` rescue path
  is removed — an invalid timestamp can never reach resume-token creation.
- **Production sensor set unchanged:** exactly the six I14-promoted paths;
  TRADE and BOOK_SNAPSHOT remain typed unsupported.  Production instrument
  scopes unchanged (OI `{PI_XBTUSD, PI_ETHUSD}`; BASIS / BOOK_METRIC / FUNDING
  / LIQUIDATION / POSITIONING `{PI_XBTUSD}`).  Probe-only SOL/DOGE stay out of
  production capability.
- **Zero network calls** made in I05R2; **network smoke remains NOT_RUN**
  (reserved for SENSOR-B3-I14).  Full offline regression: 829 passed / 0
  failed; ruff clean.

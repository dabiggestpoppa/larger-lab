# SENSOR-B3-I06 — Gate Futures Production Adapter Implementation Evidence

**Checkpoint verdict:** `PASS_SENSOR_B3_I06_GATE_ADAPTER_OFFLINE` (proposed).
Kraken was frozen by `SENSOR-B3-I05R2-RATIFY`; this is the SECOND hard real
provider adapter.  **This is NOT a global Bloc 3 PASS.**

**Operator authorization:** `SENSOR-B3-I06 — GATE_FUTURES` only.
Kraken offline implementation FROZEN (`kraken_offline_implementation_frozen =
TRUE`).  `provider_adapter_implementation_authorized = GATE_FUTURES ONLY`.

## Identity

| Field | Value |
|---|---|
| adapter_id | `GATE_FUTURES.PUBLIC_REST.V1` |
| adapter_version | `gate-adapter-v1` |
| provider | `GATE_FUTURES` |
| package | `quant-lab/src/crypto_sensor_fabric/providers/gate/` |
| implementation head | `b30ab5d6` (I06A) + `4f0ee81b` (I06B) + (I06C) |
| network_smoke_status | `NOT_RUN` (reserved for SENSOR-B3-I14) |

## Supported sensor paths (exactly four, I14-promoted, all SECONDARY)

| Sensor | Role | Method pin | Verified history |
|---|---|---|---|
| MECHANICAL_FUNDING | SECONDARY | `gate_futures-funding` | 2026-06-15Z..2026-08-23T15:44:40.901129Z |
| MECHANICAL_LIQUIDATION | SECONDARY | `gate_futures-liquidation` | 2026-06-15Z..2026-08-23T14:55:06.963000Z |
| MECHANICAL_OPEN_INTEREST | SECONDARY | `gate_futures-open_interest` | 2026-06-15Z..2026-08-23T14:55:05.522441Z |
| MECHANICAL_POSITIONING | SECONDARY | `gate-contract-stats-public-lsr` | 2026-06-15Z..2026-08-23T14:55:07.337755Z |

An exact-set test derives the declared production set directly from
`source_promotion_candidates.yaml`; it equals the four promotion-candidate rows
(no omission, no fifth path).

## Unsupported sensor paths (typed `CapabilityUnavailable`)

- `MECHANICAL_TRADE` — observed but NOT promoted by I14.
- `MECHANICAL_BOOK_SNAPSHOT` — not a production promotion.

Both remain typed unsupported through the correct protocol methods; never
`[]` / `0` / `None` / `EMPTY_VALID`.

## Production symbol scope

Evidence-derived (`evidence/bloc_02/08_HISTORY_BOUNDARIES.csv`, provider x
sensor x instrument): `BTC_USDT` for all four promoted paths.  Derived via
`ProviderNativeCapabilityEvidence.instruments`; probe/control contracts
`ETH_USDT` / `SOL_USDT` / `DOGE_USDT` remain in `GATE_PROBE_INSTRUMENT_SCOPE`
for characterization history only and fail production requests with typed
`InvalidInstrument`.

## Native acquisition mode per promoted path (evidence-backed, I05 seam)

| Sensor | historical_mode | pagination_mode | endpoint family |
|---|---|---|---|
| MECHANICAL_FUNDING | REST_RANGE | TIME_RANGE | `gate-futures-funding_rate` |
| MECHANICAL_LIQUIDATION | REST_RANGE | TIME_RANGE | `gate-futures-contract_stats` |
| MECHANICAL_OPEN_INTEREST | REST_RANGE | TIME_RANGE | `gate-futures-contract_stats` |
| MECHANICAL_POSITIONING | REST_RANGE | TIME_RANGE | `gate-futures-contract_stats` |

contract_stats: `from` = epoch SECONDS, `interval` = provider STRING bucket
(`"1h"`), `limit`, **NO invented `to`**, completion = single bounded
from/interval/limit window.  funding: `GET /funding_rate?contract=&from=&to=`
(epoch SECONDS), completion = from/to bounded window; no interval parameter.

Each grant's `evidence_ids` resolve into its own I14 `evidence_basis`; native
evidence only REFINES acquisition mechanics, never broadens I14 scope/role/PIT/
methodology/access/live/archive/sensor-set.

## Request vs response timestamp units (kept distinct)

- contract_stats **request** `from` = epoch SECONDS; **response** row `time` =
  native epoch MILLISECONDS.
- funding **request** `from` / `to` = epoch SECONDS; **response** row `t` =
  epoch SECONDS; `r` = provider-native decimal string.

A dedicated test prevents second/millisecond inversion (the convenience
`FetchBatch` datetime derives from the correct native unit; the parsed native
field is never replaced).

## I14 evidence refs (evidence_basis per sensor)

- FUNDING: `gate_futures_funding_btc_usdt_RECENT_CONTROL_1h`,
  `gate_futures_funding_btc_usdt_2026_1h`
- LIQUIDATION: `gate_futures_liquidation_btc_usdt_2022_1h`,
  `gate_futures_liquidation_btc_usdt_2026_1h`,
  `gate_futures_liquidation_btc_usdt_RECENT_CONTROL_1h`
- OPEN_INTEREST: `gate_futures_open_interest_btc_usdt_2022_1h`,
  `gate_futures_open_interest_btc_usdt_2026_1h`,
  `gate_futures_open_interest_btc_usdt_RECENT_CONTROL_1h`
- POSITIONING: `gate_futures_positioning_btc_usdt_2022_1h`,
  `gate_futures_positioning_btc_usdt_2026_1h`,
  `gate_futures_positioning_btc_usdt_RECENT_CONTROL_1h`

## Bloc 2 evidence refs (schema fingerprints, 09_SCHEMA_FINGERPRINTS.jsonl)

- contract_stats: `list[dict{last_funding_rate:str, long_liq_*, short_liq_*,
  lsr_*, mark_price, open_interest:int, open_interest_usd, time:int, top_*}]` —
  NUMERIC SEMANTIC FAMILY (int|float variation, bool excluded) for the numeric
  fields; `time` strict int ms.
- funding: `list[dict{r:str, t:int}]` — `t` strict int seconds.

## Schema contracts / parser fields preserved by sensor

- OPEN_INTEREST: `time`, `open_interest`, `open_interest_usd` (native).
- LIQUIDATION: `time`, `long_liq_size`, `short_liq_size`, `long_liq_usd`,
  `short_liq_usd`, plus `long_liq_amount` / `short_liq_amount` / `long_liq_usd_new`
  / `short_liq_usd_new` / taker sizes preserved.  Long/short orientation is
  preserved as provider fields (never reinterpreted via taker-side assumptions,
  never emitted as LiquidationState / forced directional signal).
- POSITIONING: `time`, `lsr_taker`, `lsr_account`, `top_lsr_account`,
  `top_lsr_size`, `top_long_size`, `top_short_size`, `top_long_account`,
  `top_short_account`, `long_users`, `short_users` (PUBLIC market-wide stats).
- FUNDING: `r`, `t` (native, not renamed; no annualization/regime).

Structural fail-closed: missing required field / wrong timestamp type / top-level
object-as-data => BREAKING/UNKNOWN (raw preserved, parsed blocked); extra field =>
ADDITIVE (flagged, parsed).  Missing required fields are never defaulted to zero.

## No cross-sensor leakage

The shared physical `contract_stats` payload is preserved raw for all three
sensors; each parsed convenience view projects ONLY its own semantic subset.
Same physical payload != same logical observation.  No `GateMechanicalState` /
combined feature / T2 state / signal is created.

## Forbidden raw paths proved absent

- No private `/positions`: a test builds every production request and asserts
  `/positions` is not in the URL.
- No plural `POST /funding_rates`: a test asserts the funding URL is
  `/funding_rate` (singular) and never `/funding_rates`.

## Retention behavior

A rolling ~180-day provider retention rejection (`from time exceeds 180-day
limit`) maps to typed `HistoricalRangeUnavailable` (TERMINAL), with the redacted
provider-native message preserved.  It is never EMPTY_VALID, never auth, never
unsupported, never geo.  I14 verified range remains the authority; no deeper
history is fabricated.

## Offline fixture inventory (`tests/.../gate/fixtures/responses.py`)

All `SYNTHETIC_SCHEMA_FIXTURE` reconstructed from committed fingerprints, per
promoted sensor: happy, empty-valid, additive, schema drift, missing-field drift,
malformed timestamp (string / None / bool `t`, string `time`), invalid contract,
180-day retention, rate limit, provider error.  Plus shared-physical-response and
sensor-specific-projection cases.  No network calls to obtain fixtures.

## Common conformance result — `PRODUCTION_CANDIDATE` mode

Run with the REAL `GateAdapter` + fake transport.  Per-repo convention the suite
is invoked via the adapter test; `summarize_conformance` reports **0 failed**,
covering provider identity, registry/free-only, I14 exact capability set,
promotion bounds, resolving evidence refs, native-mode evidence, symbol-scope
evidence, behavioral dispatch, empty-valid vs unsupported, raw preservation,
schema-drift fail-closed, retry classification, native-instrument requirement,
and resume determinism (single-window).

## Provider-specific tests

- provider_id frozen `GATE_FUTURES`
- exactly four promoted paths; all SECONDARY; exact I14 set
- trade / book snapshot typed unsupported (+ method/sensor mismatch -> semantic error)
- free-only gate before transport; trading auth blocked before transport
- foreign provider request blocked before transport (requested sensor preserved)
- production/probe symbol separation; BTC_USDT passes; ETH/SOL/DOGE fail typed
- contract_stats request contract (path, contract, from=sec, interval="1h",
  limit, NO `to`); funding request contract (from/to sec, no interval)
- request/response timestamp units distinct; strict int validation
- OI / liquidation / positioning projection; liquidation orientation preserved;
  no canonical fields emitted
- retention -> HistoricalRangeUnavailable (not empty/auth/unsupported)
- raw envelope hash deterministic; SchemaDrift carries envelope per sensor
- empty-valid distinct from unsupported / retention
- no private /positions; no plural /funding_rates
- full PRODUCTION_CANDIDATE conformance via real adapter

## Free-only result

Pass — public REST, NO_AUTH, $0; DEFAULT_FREE_ONLY_POLICY (FREE_AUTOMATED,
cost 0, no payment/staking/transaction).  Gate never touches credentials.

## Error mapping

`{label, message}` + HTTP status -> typed errors: retention ->
`HistoricalRangeUnavailable`; 429 / rate-limit -> `RateLimited`; contract/instrument
-> `InvalidInstrument`; unauthorized/invalid key -> `AuthenticationRequired`;
FORBIDDEN -> `GeoRestricted` (US region); HTTP 403 -> `AccessClassViolation`;
HTTP 5xx -> `ProviderUnavailable`; other 4xx -> `ProviderSemanticError`.

## Pagination / resume status

contract_stats = single bounded `from`/`interval`/`limit` window; funding =
bounded `from`/`to` window.  No invented pagination or cursor.  Multi-window
traversal resume mechanics are **UNRESOLVED** and recorded as a limitation; each
fetch returns the single evidence-backed request window (`is_complete=True`, no
resume token).  Resume determinism (round-trip) itself still passes via the
common suite.

## Known limitations

1. contract_stats deeper windowed-traversal resume semantics UNRESOLVED from
   committed evidence (single-request window only).
2. Exact interval-close vs publication timestamp semantics not evidenced.
3. ~180-day rolling retention caps request depth (typed as retention).
4. `contract_stats` limit default (100) is a configured page default, not a
   pinned evidence value; `page_size_hint` overrides.

## Promotion / readiness status

Four promoted Gate paths: `ADAPTER_READY` (offline evidence earned; readiness
matrix updated).  Trade / book snapshot stay `NOT_PLANNED`.  No global Bloc 3
PASS.

## No capability exceeded I14

The native-evidence/conformance gate binds sensor set, role (SECONDARY), history
scope, verified range, PIT, methodology, access, live/archive status, and
production symbol scope to `source_promotion_candidates.yaml`.  Nothing broadens
it.

## No network validation

SENSOR-B3-I06 made ZERO network calls (fake transport only).  Network smoke
remains reserved for SENSOR-B3-I14.

## Commit SHA

- SENSOR-B3-I06A: `b30ab5d6` (capability + native acquisition contract)
- SENSOR-B3-I06B: `4f0ee81b` (requests, errors, parsers, adapter)
- SENSOR-B3-I06C: (this commit — README / evidence / readiness / ledger)
# BLOC 03 — SENSOR-B3-I09 CROSS-PROVIDER OFFLINE CLOSURE EVIDENCE

Status: **SENSOR-B3-I09 COMPLETE (OFFLINE)** — proposed verdict
`PASS_SENSOR_B3_I09_CROSS_PROVIDER_OFFLINE_CLOSURE` (NOT `PASS_BLOC_03`).

I09 builds NO provider.  It proves the four independently-built adapters
(KRAKEN_FUTURES, GATE_FUTURES, OKX_SWAP, DERIBIT) form ONE coherent,
evidence-bounded acquisition fabric under the common protocol, and renders a
deterministic readiness/inventory view of all 17 CURRENT I14 production paths.

## 1. Lineage

| Item | Value |
|---|---|
| Starting SHA | `161f0c4e25db625c91c85ffe34c1ca93f93c8d15` (branch `agent/crypto-sensor-fabric-build`) |
| Governance | `889d5f6c` — SENSOR-B3-I08R1-RATIFY (freeze Deribit, authorize I09) |
| I09A | `dffe18f6` — registry + deterministic inventory generator |
| I09A-fix | `97450123` — type-cast evidence_basis iteration (mypy clean) |
| I09B | `d299cdd2` — cross-provider closure tests |
| I09C | `08559207` — generated production matrix + reconcile |
| I09D | (this commit) — closure evidence + ledger |
| Final SHA | see ledger / `git log` |
| Verdict | `PASS_SENSOR_B3_I09_CROSS_PROVIDER_OFFLINE_CLOSURE` (proposed) |

## 2. Operator ratification

`PASS_SENSOR_B3_I08R1_DERIBIT_SEALED` accepted (governance commit `889d5f6c`).
All four current production adapters frozen OFFLINE_FROZEN with
`network_smoke = NOT_RUN`: KRAKEN_FUTURES, GATE_FUTURES, OKX_SWAP, DERIBIT.
Authorization = SENSOR-B3-I09 ONLY.  No provider implementation code was
altered in the ratification commit.

## 3. Production registry (exactly 4)

| provider_id | Adapter |
|---|---|
| KRAKEN_FUTURES | `KrakenAdapter` |
| GATE_FUTURES | `GateAdapter` |
| OKX_SWAP | `OkxAdapter` |
| DERIBIT | `DeribitAdapter` |

Registry is CONFIGURATION / wiring, NOT economic preference, fallback order or
ranking.  BINANCE_USDM / BYBIT_LINEAR / COINALYZE /
BITFINEX_COMMUNITY_ARCHIVE remain in the repo as characterization packages but
are NOT instanced into the production registry and count toward zero of the 17.

## 4. Exact production inventory (17 / 17)

Derived, not hand-declared: `build_readiness_records` consumes the I14
promotion packet + each real adapter's `capabilities()` (evidence-derived
symbol scope) + resolved evidence refs + supplied conformance results, and
emits one `AdapterReadinessRecord` per promoted (provider × sensor) path.
Three-level exact-set equality is proven by `compute_exact_sets`:

    I14 provider×sensor set  ==  union of adapter supported set  ==  matrix set
                                  (each exactly 17; no missing / extra / duplicate)

| Provider | Paths |
|---|---|
| KRAKEN_FUTURES | 6 — BASIS(PRIMARY), BOOK_METRIC(PRIMARY), FUNDING(SECONDARY), LIQUIDATION(PRIMARY), OPEN_INTEREST(PRIMARY), POSITIONING(PRIMARY) |
| GATE_FUTURES | 4 — FUNDING, LIQUIDATION, OPEN_INTEREST, POSITIONING (all SECONDARY) |
| OKX_SWAP | 3 — BOOK_SNAPSHOT(CURRENT_ONLY), FUNDING(PRIMARY), TRADE(PRIMARY) |
| DERIBIT | 4 — BOOK_SNAPSHOT(CURRENT_ONLY), FUNDING(SECONDARY), LIQUIDATION+TRADE(MECHANISM_MICROSCOPE) |

Per-sensor source counts: BASIS=1, BOOK_METRIC=1, BOOK_SNAPSHOT=2, FUNDING=4,
LIQUIDATION=3, OPEN_INTEREST=2, POSITIONING=2, TRADE=2 — total 17.

Role counts: PRIMARY=7, SECONDARY=6, CURRENT_ONLY=2, MECHANISM_MICROSCOPE=2.

## 5. Symbol-scope audit

Each record's `production_symbol_scope` equals the adapter capability symbol
scope (proven by `ProviderNativeCapabilityEvidence.instruments` from
`08_HISTORY_BOUNDARIES.csv`).  Kraken OI = `{PI_XBTUSD, PI_ETHUSD}`, other
Kraken promoted = `{PI_XBTUSD}`; Gate = `{BTC_USDT}`; OKX =
`{BTC-USDT-SWAP}`; Deribit = `{BTC-PERPETUAL}`.  Probe/control instruments
(ETH/SOL/DOGE, PI_SOLUSD/PI_DOGEUSD, ETH/SOL-PERPETUAL, ETH/SOL/DOGE-USDT-SWAP)
never leak into production.  Native instrument identity remains provider
evidence; no canonical contract id is introduced in Bloc 3.

## 6. Evidence-ref audit

`evidence_ref_audit` verifies every record's evidence_refs exactly equal the
path's I14 `evidence_basis` AND each evidence_id string resolves to at least
one committed `evidence/bloc_02/*` artifact
(01_PROBE_RUN_MANIFEST.md … 16_CONTRADICTION_FINAL_STATUS.csv).  0 violations.
No "see docs" placeholders; a broken ref fails closed (tested).

## 7. Access / auth audit

All 17 paths: `access_path=PUBLIC_REST`, `auth_mode=NO_AUTH`, `free_only_pass=True`,
`access_class=FREE_AUTOMATED`.  No paid/trading key, no wallet signing, no
staking/payment/transaction requirement.  The free-only gate runs before every
transport call (per-provider conformance + adapted protocol tests).  CoinAlyze
`COINALYZE_API_KEY` is never read (CoinAlyze is not in the production registry).

## 8. Verified-history / role / PIT / methodology audit

`validate_record_bound` audits each record against its I14 bound (role,
history_scope, PIT requirement, methodology pin, redundancy class, and that a
CURRENT_ONLY path never gains a native historical mode).  Drift tests assert a
wrong role, CURRENT_ONLY→historical, wrong PIT, wrong pin, and Deribit
liquidation reclassified PRIMARY all FAIL CLOSED.  Verified history stays
literal; an historical-capable endpoint never implies historical coverage, and
the OKX/Deribit LIQUIDATION verified bounds are not upgraded by older evidence
ids in the basis.

## 9. Resume / completion matrix (LIMITED is valid, never upgraded)

| Provider | resume / completion |
|---|---|
| KRAKEN_FUTURES | YES (Market Analytics `result.more` → re-issue `since` at oldest bucket) |
| GATE_FUTURES | LIMITED on all four promoted historical paths |
| OKX_SWAP | FUNDING/TRADE LIMITED (single window, truthful completion); BOOK n/a |
| DERIBIT | FUNDING/LIQUIDATION/TRADE LIMITED; BOOK n/a |

Every promoted historical path outside Kraken stays LIMITED; nothing is "improved"
to make the matrix cleaner.  Completion truth: `is_complete=True` only with
evidence-backed grounds; `LIMITED`/`UNKNOWN` are valid final states.

## 10. Semantic firewall

- Same SensorFamily != same numerical observable.
- Deribit LIQUIDATION/TRADE = TRADE-LEVEL mechanism microscope (`role=MECHANISM_MICROSCOPE`,
  `semantic_class` explicitly "trade-level mechanism microscope", never "total").
- Gate/Kraken liquidation = their provider-native mechanical/interval views.
- OKX/Deribit BOOK_SNAPSHOT = current-only raw book evidence.
- No consensus funding/liquidation, no merged trade flow, no averaged OI, no
  canonical OI/liquidation USD, no CVD, no book imbalance, no provider
  confidence score, no normalization.  The downstream boundary stays
  PROVIDER → ACQUISITION → RAW EVIDENCE → acquisition metadata.

## 11. Raw-envelope invariant

Representative happy paths across all four adapters (per-provider
PRODUCTION_CANDIDATE conformance + adapter tests) preserve `provider_id`,
`sensor_family`, `request_fingerprint`, `raw_body`, `content_hash`,
`schema_state`, `retrieval_metadata`, `evidence_ref`, `adapter_version`.
`SchemaDrift` carries the exact raw `RawPayloadEnvelope`; empty-valid stays
EMPTY_VALID and distinct from unsupported; provider errors stay typed.  Two
providers never emit the same provider_id.

## 12. No automatic failover

The fabric has no provider substitution.  `PRODUCTION_PROVIDER_REGISTRY` is a
1:1 provider→adapter map; a foreign-provider `FetchRequest` into a real adapter
raises typed `ProviderSemanticError` before transport (asserted for all four,
`transport.calls == []`); no transport → `ProviderUnavailable`; unsupported
sensor → `CapabilityUnavailable`.  No "Kraken fails → silently fetch Gate".

## 13. Deterministic generation

`build_readiness_records` + `render_inventory_csv` / `render_inventory_json`
are byte-for-byte stable: two independent invocations produce identical
canonical output (tested).  Sorting = provider_id, then sensor_family.  No
wall-clock timestamp enters the canonical inventory.  Same inputs → same matrix.
The human-facing `ADAPTER_READINESS_MATRIX.csv` is validated AGAINST the derived
state by `reconcile_human_matrix` (the human matrix is never an authority input).

## 14. Generated artifacts

- `evidence/bloc_03/PRODUCTION_ADAPTER_MATRIX.csv` (canonical, 17 rows)
- `evidence/bloc_03/PRODUCTION_ADAPTER_MATRIX.json` (canonical, same state)
- `evidence/bloc_03/ADAPTER_READINESS_MATRIX.csv` (human-facing, reconciled)

## 15. Tests / validation

- New cross-provider matrix tests: **42 passed / 0 failed** (this checkpoint, +42).
- Cumulative crypto_sensor_fabric suite fully green at final validation (see
  final count in the validation run); failure count = 0.
- Per-provider PRODUCTION_CANDIDATE conformance 0 failed each (Kraken, Gate,
  OKX, Deribit); record `offline_conformance_pass=True` from these real runs.
- Kraken / Gate / OKX / Deribit full regression green (frozen).
- ruff clean on new modules; mypy clean on changed modules.
- **network calls = 0** — this module instantiates real adapters but only calls
  `capabilities()` / `dispatch_fetch` with FAKE transports, never network.

## 16. Known LIMITED / single-source states

- Single-source sensors: MECHANICAL_BASIS (Kraken), MECHANICAL_BOOK_METRIC (Kraken).
- Resume LIMITED: Gate (4), OKX funding+trade, Deribit funding+liquidation+trade.
- network smoke NOT_RUN for all 17 paths (I09 is OFFLINE; no Bloc 2 network
  evidence is treated as Bloc 3 production-adapter smoke).

## 17. Non-goals honored

No provider expansion (no fifth provider, no Deribit beyond I08, no
Binance/Bybit/Coinalyze/Bitfinex production).  No normalization, no
canonicalization, no research logic, no alpha, no Bloc 4.  No production
provider implementation code altered in I09.  No I10 (network smoke) work.

## 18. Readiness

I14_PRODUCTION_PATHS_IMPLEMENTED_OFFLINE = **17 / 17**.
REAL_PROVIDER_ADAPTERS = 4.
CROSS_PROVIDER_OFFLINE_CLOSURE = TRUE.
NETWORK_VALIDATION = NOT_RUN.
next_checkpoint_authorized = FALSE.
Recommended next: **SENSOR-B3-I10 — CONTROLLED PRODUCTION-ADAPTER NETWORK SMOKE**
(NOT authorized in this session).

## 19. Proposed verdict

`PASS_SENSOR_B3_I09_CROSS_PROVIDER_OFFLINE_CLOSURE` — earned only if every gate
passes.  This is NOT `PASS_BLOC_03`: production-adapter network validation has
not yet run.
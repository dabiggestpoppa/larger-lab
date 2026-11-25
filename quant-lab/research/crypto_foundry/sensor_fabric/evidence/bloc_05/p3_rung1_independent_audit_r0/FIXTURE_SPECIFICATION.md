# FIXTURE SPECIFICATION — Rung 1 probes and Rungs 2–4 reuse

Executable form: `rung1_fixtures.py.txt`. Every fixture below constructs from the
**real** ratified types at `13086755d`; none is hand-shaped JSON validated by
nothing. The module self-tests in `__main__` and currently reports **7/7 VALID**.

## 1. The separation that matters

Two families, kept apart on purpose:

| Family | Purpose | May be used as evidence? |
|---|---|---|
| `STRUCTURAL` | prove a value of the right shape can be built (positive controls) | yes, that is precisely its claim |
| `AUTHORIZATION` | exercise a real authorization decision | **no** — these are doubles |

Conflating them is how a suite ends up "proving" security from a fixture that
holds no bytes. The custody double below holds bytes, not a digest, because the
verifier hashes what it is handed.

## 2. Fixture inventory

| Fixture | Real type | Fixed content | Used by |
|---|---|---|---|
| `valid_trade_record()` | `T1TradeRecord` | `BINANCE_USDM`/`BTCUSDT`, `MECHANICAL_TRADE`, `LINEAGE_COMPLETE`, all eight quality dimensions `VERIFIED`, aware `effective_at`/`market_available_at` | C01, C05, C06, C18, C22 |
| `valid_liquidation_record()` | `T1LiquidationRecord` | `MECHANICAL_LIQUIDATION`, `EVENT_LEVEL`, `quantity_native=2.5 BTC` | C02, C05, C17 |
| `valid_replay_evidence()` | `ReplayEvidence` | PIT resolved, semantics verified, `REALTIME_PUBLIC_EVENT`, `revision=None` | C01, C16, C22 |
| `methodology_registry()` | `NormalizationMethodologyRegistry` | two fixture rows (`P3_RUNG1_SIDE_V1`, `P3_RUNG1_LIQ_V1`) | Rung 2 policy probes |
| `TrustedCustodyDouble` | `TrustedCustodyProvider` shape | holds **bytes**; records every read | Rung 2/3 custody probes |
| `MutableEvidenceStore` | `TrustedCustodyProvider` shape | hands different bytes on the second read | rebinding attacks (Rung 2/3) |
| `RootLoaderSeam` | injected seam | counts loads; returns fixed manifest bytes | Rung 2/3 "no implicit I/O" proofs |

### Deterministic identities

`AUTHORITY_IDENTITY`, `CUSTODY_SOURCE_IDENTITY`, `ROOT_IDENTITY`, `ARTIFACT_ID`
are fixed opaque tokens. No fixture resolves them, mints them, or reads the
shipped manifest — `MANIFEST_BYTES` is `{"artifacts":{}}`, i.e. the **empty**
manifest is reproduced rather than replaced, and `ARTIFACT_ID` deliberately does
not name a real approval.

### Cutoffs

| Constant | Value | Purpose |
|---|---|---|
| `CUTOFF` | `2026-06-01T12:00Z` | the one fixed aware cutoff |
| `CUTOFF_EQUIVALENT` | `2026-06-01T14:00+02:00` | same instant, different offset (C09) |
| `CUTOFF_NAIVE` | `2026-06-01T12:00` (naive) | C07 attack input |
| `CUTOFF_BARE_DATE` | `2026-06-01` (date) | C08 attack input |
| `CUTOFF_LATE` | `2026-12-31T23:59Z` | a cutoff after every event |

## 3. Rules for Rungs 2–4

1. **Never weaken a fixture to make a probe pass.** A probe whose positive
   control is refused must fail as a *probe defect*; `_accept()` in
   `test_rung1_contracts.py` enforces exactly that.
2. **Custody doubles hold bytes.** A double returning a digest re-tests the P2cR1
   F-R1-01 defect instead of the boundary.
3. **Rebinding needs a store that changes.** `MutableEvidenceStore` changes on the
   *second* read; a constant-bytes double cannot test rebinding at all.
4. **The root loader is injected and counted.** No fixture may let a model reach
   a root on its own; `RootLoaderSeam.load_count` is how "no hidden I/O" is
   proven rather than asserted.
5. **The empty manifest is not a security proof by itself.** Every Rung 2/3 probe
   must state which law it exercises; "the refusal occurred because the manifest
   is empty" proves only that emptiness refuses.
6. **Fixture rows are not approvals.** `METHOD_ID` / `LIQ_METHOD_ID` exist to let a
   probe resolve a methodology; they must never be read as provider trust.

## 4. Known boundary of these fixtures

`valid_trade_record()` and `valid_liquidation_record()` build records **without**
`authority_provenance` and with no canonical side promoted. That is deliberate:
a record whose provenance was fabricated would make Rung 2 verification
untestable. Rung 2 probes must supply `authority_provenance` from a real
approved row, not from this module.

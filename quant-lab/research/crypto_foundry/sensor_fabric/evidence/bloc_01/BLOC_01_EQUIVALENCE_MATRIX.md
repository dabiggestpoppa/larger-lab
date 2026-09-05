# BLOC 1 — EQUIVALENCE MATRIX

Source of truth: `quant-lab/config/crypto_sensor_fabric/semantic_equivalence.yaml`
(committed, schema_version 1.0).  All mappings below are **provisional planning
mappings** with `evidence_reference: BLOC2_PROBE_PENDING`.  Bloc 2 capability
probes produce the evidence that upgrades (or demotes) each mapping.
No `EXACT_EQUIVALENT` is claimed before probe evidence — enforced by tests.

| Provider | Source metric | Canonical sensor | Canonical field | Equivalence | Methodology | Version |
|---|---|---|---|---|---|---|
| GATE_FUTURES | long_liq_usd | MECHANICAL_LIQUIDATION | source_long_liq_usd | NORMALIZABLE_COMPARABLE | LIQ_USD_NATIVE_PROVIDER_V1 | 1 |
| GATE_FUTURES | short_liq_usd | MECHANICAL_LIQUIDATION | source_short_liq_usd | NORMALIZABLE_COMPARABLE | LIQ_USD_NATIVE_PROVIDER_V1 | 1 |
| DERIBIT | trade.liquidation | MECHANICAL_LIQUIDATION | liquidation_role | CORROBORATION_ONLY | DERIBIT_TRADE_LIQ_TAG_V1 | 1 |
| BINANCE_USDM | isBuyerMaker | MECHANICAL_TRADE | aggressor_side | NORMALIZABLE_COMPARABLE | AGGRESSOR_FROM_BUYER_MAKER_BINANCE_V1 | 1 |
| BYBIT_LINEAR | open_interest | MECHANICAL_OPEN_INTEREST | oi_native | NORMALIZABLE_COMPARABLE | OI_CONTRACTS_TO_USD_V1 | 1 |
| KRAKEN_FUTURES | funding_rate | MECHANICAL_FUNDING | funding_rate_native | NORMALIZABLE_COMPARABLE | FUNDING_NATIVE_TO_8H_EQUIV_V1 | 1 |

## Frozen aggressor direction (repair SENSOR-B1-R01)

BINANCE_USDM `isBuyerMaker` → `MECHANICAL_TRADE.aggressor_side`:

| isBuyerMaker | Economic meaning | aggressor_side |
|---|---|---|
| true | buyer is maker; seller is taker/aggressor | SELL |
| false | buyer is taker/aggressor | BUY |

Machine-readable declaration: `tests/crypto_sensor_fabric/fixtures/binance_is_buyer_maker_semantics.json`
(regression-tested; mapping remains PROVISIONAL until provider fixture verification in Bloc 2/5).

## Pooling rule (B1-T42)

Numeric pooling across providers is permitted by default only for
`EXACT_EQUIVALENT` and `NORMALIZABLE_COMPARABLE`.  `CORROBORATION_ONLY`
(e.g. Deribit liquidation-tagged trades vs interval aggregates) and
`NOT_COMPARABLE` stay independent.  Cross-venue synthesis additionally
requires Bloc 6 eligibility; no cross-venue value exists at T1.

## Methodology registry (all PROVISIONAL)

`quant-lab/config/crypto_sensor_fabric/methodology_registry.yaml`:

OI_CONTRACTS_TO_USD_V1 (normalization, T1) · OI_USD_NATIVE_PASSTHROUGH_V1 (normalization, T1) ·
FUNDING_NATIVE_TO_8H_EQUIV_V1 (normalization, T1) · LIQ_USD_NATIVE_PROVIDER_V1 (normalization, T1) ·
AGGRESSOR_FROM_BUYER_MAKER_BINANCE_V1 (reconstruction, T1) · DERIBIT_TRADE_LIQ_TAG_V1 (classification, T1) ·
DEPTH_BPS_RECONSTRUCTION_V1 (reconstruction, T1) · PROVIDER_ANALYTICS_PASSTHROUGH_V1 (normalization, T1) ·
CVD_SIGNED_NOTIONAL_V1 (reconstruction, T2 — feature only, never inside a T1 schema).

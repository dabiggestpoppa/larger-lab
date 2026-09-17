# G5 — CRYPTO SOURCE DISAGREEMENT AUDIT (S17)

## Substrate basis
Read-only ingestion of the Crypto Sensor Fabric build: provider registry and capability declarations were read via `git show` (no checkout/mutation). Provider packets are deterministic fixtures patterned after current substrate contracts.

## ProviderObservation (identity preserved)
provider · instrument native id · canonical instrument id · metric · contract type · units · timestamp semantics · aggregation window · event/receive time · historical/live mode · native value · normalized value · quality state · adapter version. Provider-native values are never averaged away (`source_averaged_away=false` in the receipt).

## Mandatory diagnostic order (enforced)
1. provider semantics → 2. instrument identity → 3. adapter → 4. normalization → 5. time semantics → 6. quality → 7. disagreement surface.

Only after 1–6 pass may higher-level market-field interpretation be challenged.

## Fixture causes localized
- **Normalization/unit mismatch** (contracts vs USD notional): diagnosed at layer 4 → `NORMALIZATION_MISMATCH` / `REPAIRABLE_SOURCE_MISMATCH`.
- **Instrument mapping mismatch** (wrong instrument canonicalized): diagnosed at layer 2 → `INSTRUMENT_MISMATCH` / `REPAIRABLE_SOURCE_MISMATCH`.
- **Genuine residual disagreement** (same semantics, clean adapters): preserved as `GENUINE_SOURCE_DISAGREEMENT` — no consensus averaging, no market-field model rewrite from a source-layer difference.

## Controls
Control A (units) → normalization repair; Control B (adapter maps wrong instrument) → adapter repair; Control C (genuine persistent difference) → `SOURCE_DISAGREEMENT` preserved. Provider rename metamorphic: identity-bearing fields rename without changing the diagnosis.

## Status
**PASS** — source-layer diagnosis first; provider-native semantics preserved; disagreement kept at the source layer unless evidence proves otherwise.
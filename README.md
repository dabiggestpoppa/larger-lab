# Capital Routing Research System

> **Status:** Rebuilding from available artifacts and documentation
> **Purpose:** Research and backtesting platform for capital routing analysis
> **Note:** This is a research platform, not a live execution engine

## Overview

The Capital Routing Research System discovers how capital exits one currency/region, where it parks first, where it rotates next, which instruments lead or lag, and which slower "sleeper" crosses provide the cleanest remaining trade expression.

This system sits above the Mona Lisa framework:

Capital Routing
    ↓
Basket State
    ↓
Session Handoff
    ↓
Relative-Strength Expression
    ↓
Execution Model

## Core Research Thesis

Macro regime
    ↓
Origin of stress
    ↓
Primary destination
    ↓
Secondary destination / bridge
    ↓
Parking destination
    ↓
Residual or sleeper destination
    ↓
Tradable cross

## Initial Hypotheses

1. **EUR exit:** Broad EUR weakness should reveal whether capital routes toward GBP, USD, JPY, CHF, gold, UK equities, or US equities.

2. **GBP bridge:** EURGBP may be an early pressure gauge; GBP may act as a transit currency instead of the final destination.

3. **CHF parking:** CHF inflow may appear as stability, compression, persistence, and lower drawdown rather than explosive direction.

4. **JPY destination/carry unwind:** JPY may become the dominant destination during carry-unwind regimes.

5. **Tier-three trickle-down:** Residual repricing may later appear in AUD, NZD, CAD, NOK, SEK, or selected exotics.

6. **Oil-to-CAD conveyor:** WTI/Brent shocks may lead the CAD factor and then USDCAD, EURCAD, GBPCAD, or CADJPY.

7. **Session routing:** Asia reveals, London reallocates/confirms, and New York delivers, redirects, or invalidates.

## Repository Structure

```
capital-routing/
├── README.md
├── pyproject.toml
├── requirements.txt
├── config/
├── data/raw/
├── data/normalized/{h1,h4,d1}/
├── data/aligned/
├── data/manifests/
├── src/capital_routing/
│   ├── ingestion/
│   ├── quality/
│   ├── bars/
│   ├── factors/
│   ├── events/
│   ├── leadlag/
│   ├── regimes/
│   ├── validation/
│   ├── reporting/
│   └── cli.py
├── scripts/
├── tests/{unit,integration,data_contracts,regression}/
├── notebooks/
├── artifacts/{audits,factors,events,leadlag,validation,figures,reports}/
└── docs/{DATA_CONTRACT.md,RESEARCH_CONTRACT.md,METHODOLOGY.md,BUILD_STATUS.md,DECISIONS.md}
```

## Current Status

Based on available artifacts:

- ✅ **QUANT_BIBLE.md** - Complete formula documentation (700+ lines)
- ✅ **reality_lock.py** - Phase 1 behavioral gate implementation
- ✅ **test_reality_lock.py** - 32 tests passing
- ✅ **QUANT_BIBLE.md** - Per-asset tier configurations
- ✅ **Various quant-lab components** - Available for integration

## Build Instructions

### Phase 0 — Reality Lock

1. Inspect repository and branch
2. Inventory data, code, tests, configs, and reports
3. Locate the MT5 export script
4. Create a baseline commit
5. Record commit SHA, Python/dependency versions, actual collected test count, data-file count, symbol coverage, and failures
6. Mark legacy/untrusted scripts
7. Make all readiness gates fail closed

### Phase 1 — Data Discovery

1. Recursively scan approved directories
2. Detect file type, delimiter, schema, symbol, timeframe, timezone, price side, coverage, and row count
3. Use explicit alias maps; do not rely only on filenames
4. Flag ambiguity
5. Select the best source per symbol based on coverage, completeness, consistency, timestamp quality, and timeframe
6. Generate the MT5 acquisition queue for missing Batch A data

### Phase 2 — Acquisition and Normalization

1. Pull missing Batch A via MT5: H1 from 2022-present; D1 from 2019-present or generate D1 from H1 where possible
2. Preserve raw exports unchanged
3. Normalize timestamps, columns, precision, symbols, and provider metadata
4. Detect duplicates, malformed OHLC, non-positive prices, impossible timestamps, and weekend behavior
5. Never forward-fill bars
6. Save processed files as Parquet and optionally CSV
7. Save SHA-256 checksums

### Phase 3 — QC, H4, Daily, Alignment

1. Calculate rows, coverage, expected weekday bars, unexplained gaps, stale/repeated bars, and extreme outliers
2. Aggregate H1→H4 using UTC boundaries
3. Aggregate H1→D1 with documented day boundaries
4. Keep provider-native D1 separately for comparison
5. Build union, intersection, and per-test eligible panels
6. Derive DST-aware Asia, London, New York, and overlap labels
7. Never drop timestamps merely because an optional symbol is absent

### Phase 4 — Factor Engine

1. Create log returns for H1/H4/D1 horizons
2. Rolling realized volatility
3. Volatility-adjusted moves
4. Breadth
5. Independent currency-strength factors
6. Orient every pair so positive always means the named currency strengthened
7. Initial equal-weight factors for EUR, GBP, USD, JPY, CHF
8. Add AUD/NZD/CAD components when available

## Available Components

### Core Formulas (from QUANT_BIBLE.md)

- **Asian Range (AR)**: max(high) - min(low) during Asian session
- **AU (Atomic Unit)**: AR / 2
- **Tier System**: T1 (≤20p), T2 (≤30p), T3 (≤45p), NO-GO (>45p)
- **P90 Threshold**: 90th percentile of impulse size distribution
- **MLR (Monday London Range)**: Monday 07:00-15:00 UTC
- **Fibonacci Extensions**: 23.6%, 38.2%, 50.0%, 61.8%, 72.0%, 78.6%, 88.6%
- **132% Kill-Switch**: Structural invalidation level
- **ILM (Impulse Level Monitor)**: Asian/London range ratio
- **Regime Ratio**: London Range / Asian Range
- **ARP (Asian Range Percentile)**: Percentile rank of current AR
- **Density Zone**: Rolling mean ± rolling std
- **Gamma Zone**: Fibonacci extensions from swing points
- **NY Sweep**: 07:00-08:00 UTC sweep detection
- **OCC (Order Close Confirmation)**: Extreme close detection
- **Wednesday Bifurcation**: Wednesday PM stress detection
- **Hard Exit**: 12:00 PM EST (17:00 UTC)
- **Gear Shift**: Target modification signal
- **Friday Asian Anchor**: Friday 00:00-08:00 UTC for crypto
- **3-Leg Patterns**: Alpha, Beta, AB-CD patterns

### Per-Asset Configurations

From QUANT_BIBLE.md 1B.2:

**Forex Majors (k_factor = 0.46):**
- EURUSD, GBPUSD, USDJPY, USDCHF, AUDUSD, NZDUSD
- CHFJPY, GBPJPY, GBPAUD, GBPNZD, GBPCHF, EURGBP, EURJPY, EURAUD, EURCAD, EURNZD, CADCHF, AUDCHF, AUDJPY, AUDNZD, NZDJPY, NZDCHF, NZDCAD, CADJPY, USDCAD

**Indices (k_factor = 0.48):**
- DE30, FR40, US500, HK50

**Metals (k_factor = 0.50):**
- XAUUSD, XAGUSD

**Crypto (k_factor = 0.52):**
- BTCUSD, ETHUSD

**Oil (Regime-Dependent):**
- OILUSD with regime-specific AR sizes

## Testing

### Phase 1 Tests (from test_reality_lock.py)

- `test_validate_artifact_valid` - Valid JSON passes validation
- `test_validate_artifact_missing_file` - Missing file fails validation
- `test_validate_artifact_invalid_json` - Invalid JSON fails validation
- `test_validate_artifact_schema_mismatch` - Schema mismatch fails validation
- `test_ready_for_phase_1_with_valid_artifacts` - Valid artifacts pass basic checks

## Next Steps

1. **Phase 0 Completion**: Create reality_lock.py artifacts
2. **Phase 1 Discovery**: Scan for available data sources
3. **Phase 2 Normalization**: Process available data
4. **Phase 3 QC**: Quality control and alignment
5. **Phase 4 Factors**: Generate currency strength factors
6. **Phase 5 Events**: Detect origin/destination/bridge/parking/sleeper states
7. **Phase 6 Tests**: Run Batch A hypothesis tests
8. **Phase 7 Validation**: Lead-lag validation and false-discovery controls
9. **Phase 8 Regimes**: Build regime engine
10. **Phase 9 Sleepers**: Add AUD/NZD crosses
11. **Phase 10 Oil/CAD**: Test commodity transmission
12. **Phase 11 Destinations**: Equity and macro confirmation
13. **Phase 12 Validation**: Walk-forward validation
14. **Phase 13 Ranking**: Expression ranking
15. **Phase 14 Reports**: Generate research reports and graphs

## Notes

- This is a **research platform only** - no live trading
- All data must be preserved unchanged
- Never silently mix providers
- Every normalized series must retain source metadata
- All canonical bars use UTC
- New York session labels must be DST-aware
- H4 must be aggregated from H1
- Daily bars should be generated from H1 where possible
- No forward-filling of missing OHLC bars
- Apply false-discovery controls to scanned lags and thresholds
- Every performance result must identify sample dates, instruments, event definition, lag, horizon, costs, validation status, and observation count
- No phase is PASS unless its evidence artifacts exist and its gate calculation passes

## Contact

For questions about this rebuild, refer to the QUANT_BIBLE.md documentation or the reality_lock.py implementation.
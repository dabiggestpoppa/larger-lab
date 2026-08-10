# 📋 PHASE 0 — REPOSITORY / DATA / TRUTH AUDIT

## Overview
This document captures the initial audit of the repository structure, available market data, and existing frameworks to support the CEREBUS Morphic Volatility Engine (MVE) research project.

## 1. Repository Structure Analysis

### Core Directories
- `c:\Users\wifik\Desktop\projects\larger-lab\` - Main workspace
- `c:\Users\wifik\Desktop\projects\larger-lab\quant-lab\` - Quant Lab with engines and data
- `c:\Users\wifik\Desktop\projects\larger-lab\quant-lab\data\` - Market data files
- `c:\Users\wifik\Desktop\projects\larger-lab\quant-lab\engines\` - Trading engines
- `c:\Users\wifik\Desktop\projects\larger-lab\research\mve\` - MVE research directory (new)

### Key Files Identified
- `QUANT_BIBLE.md` - Core trading formulas and parameters
- `QUANTLAB_BIBLE.md` - Living reference for engines and configs
- `CEREBUS_ONTOLOGY.md` - Strategy philosophy and definitions
- `NAUTILUS_BACKTEST_PLAN.md` - Backtest roadmap

## 2. Available Market Data

### Primary Assets (from quant-lab/data/)

#### Forex Majors (High Priority)
- `EURUSDPRO_M5_2023_2026.csv` - EURUSD M5 data (2023-2026)
- `EURUSD_M5.csv` - EURUSD M5 data
- `GBPUSD_M5.csv` - GBPUSD M5 data
- `USDJPY_M5.csv` - USDJPY M5 data
- `AUDUSD_M5.csv` - AUDUSD M5 data
- `USDCHF_M5.csv` - USDCHF M5 data

#### Additional Forex
- Multiple currency pairs with M5, D1, MN1 timeframes
- Both raw (`*_M5_fetched.csv`) and processed (`*_PRO_*.csv`) formats

#### Indices & Commodities
- `US500_M5.csv` - S&P 500
- `HK50_M5.csv` - Hang Seng
- `FR40_M5.csv` - CAC 40
- `DE30_M5.csv` - DAX
- `XAUUSD_M5.csv` - Gold
- `XAGUSD_M5.csv` - Silver

#### Crypto
- `BTCUSD_M5.csv`, `ETHUSD_M5.csv`
- `BTCUSD_D1.csv`, `ETHUSD_D1.csv`

#### Oil
- `OILUSDPRO_M5.csv` - Oil data
- `OILUSDPRO_D1.csv` - Oil daily data

### Data Quality Assessment

#### Coverage Analysis
- **EURUSD**: 2023-2026 (3+ years)
- **Intraday**: M5, H1 available for most assets
- **Daily**: D1 data widely available
- **Weekly**: W1 data available for major pairs

#### Timezone Considerations
- Data appears to be in UTC or broker timezone
- Need to verify timezone normalization
- Check for daylight saving time handling

#### Data Completeness
- Need to check for missing bars
- Verify no duplicate timestamps
- Check spread/bid-ask availability

## 3. Symbols & Timeframes

### Primary Symbols for MVE Research
1. **EURUSD** - Primary test asset
2. **GBPUSD** - Secondary major
3. **USDJPY** - Third major
4. **AUDUSD** - Commodity-linked major
5. **USDCHF** - Safe-haven pair
6. **XAUUSD** - Precious metal
7. **US500** - Equity index
8. **HK50** - Asian index

### Available Timeframes
- **M5** - 5-minute (primary for MVE)
- **H1** - 1-hour (secondary)
- **D1** - Daily (regime analysis)
- **W1** - Weekly (strategic levels)

## 4. Existing Backtest Framework

### CEREBUS Engine Structure
- `engines/symmetry_trap.py` - Symmetry Trap engine
- `engines/symmetry_trap_backtest.py` - Backtest wrapper
- `engines/p90_engine.py` - P90 kinetic engine
- `engines/dmr_standalone_backtest.py` - DMR strategy

### Quant Lab Infrastructure
- `quant-lab/engines/` - Core trading engines
- `quant-lab/backtest/` - Backtest runners
- `quant-lab/scripts/` - Data processing scripts

### Key Features
- 4-state FSM (SEARCH→WAIT_RETRACE→WAIT_OCC→IN_TRADE)
- Single AU target with Zero-Buffer SL
- Per-asset calibration
- Hard exit at 12:00 PM EST

## 5. Existing Volatility Functions

### Volatility Estimators in Quant Lab
- Close-to-close rolling standard deviation
- EWMA volatility
- Parkinson range volatility
- Garman-Klass volatility
- ATR-normalized realized volatility
- MAD-based robust volatility

### Volatility-Related Scripts
- `quant-lab/scripts/fib_sequence_scanner.py` - Volatility scanning
- `quant-lab/scripts/analyze_baskets.py` - Multi-asset volatility analysis

## 6. Metrics & Walk-Forward Utilities

### Available Metrics
- `quant-lab/engines/metrics.py` - Trading performance metrics
- `quant-lab/scripts/debug_engine.py` - Engine debugging utilities
- `quant-lab/scripts/verify_engine.py` - Engine verification

### Walk-Forward Infrastructure
- `quant-lab/backtest/` - Contains walk-forward test scripts
- `quant-lab/reports/` - Contains backtest results

## 7. CEREBUS Implementation Analysis

### Core CEREBUS Components
1. **Constraint System** - State-based trading
2. **Resolution Engine** - 4-state FSM
3. **Atomic Units (AU)** - 50% of K-Means centroid
4. **P90 Thresholds** - Kinetic validation
5. **Structural Anchors** - Price-based reference points

### MVE Integration Points
- **Sigma State Fields** - Volatility-normalized coordinates
- **Acceptance Criteria** - State occupation thresholds
- **Rekey Logic** - Anchor transformation
- **Regime Maps** - 2D state space analysis

## 8. Data Processing Pipeline

### Current Data Flow
1. **Raw Data** - CSV files from MT5/broker
2. **Normalization** - Timezone and format standardization
3. **Feature Engineering** - OHLCV calculations, volatility measures
4. **Engine Processing** - Strategy logic application
5. **Results Generation** - Trade signals and performance metrics

### Data Quality Scripts
- `quant-lab/scripts/fetch_data.py` - Data fetching
- `quant-lab/scripts/fetch_missing_pairs.py` - Missing data recovery
- `quant-lab/scripts/fix_costs.py` - Cost adjustment

## 9. Research Gaps & Missing Elements

### Data Gaps
- **Historical Depth**: Need pre-2023 data for robust statistics
- **Crypto Consistency**: Some crypto pairs have gaps
- **Spread Data**: Limited bid-ask spread information
- **Futures Roll Dates**: Not clearly documented

### Infrastructure Gaps
- **Walk-Forward Framework**: Limited existing implementation
- **Monte Carlo Tools**: Basic MC simulation available
- **Bootstrap Resampling**: Limited statistical tools
- **Non-Gaussian Tests**: Basic fat-tail analysis

### MVE-Specific Gaps
- **Sigma State Definitions**: Need implementation
- **Acceptance Criteria**: Need empirical testing
- **Regime Transition Models**: Need development
- **Multi-Timeframe Integration**: Need implementation

## 10. Recommendations for Phase 0 Completion

### Immediate Actions
1. **Data Validation**: Verify data integrity for primary assets
2. **Time Zone Normalization**: Establish consistent timezone handling
3. **Feature Extraction**: Implement volatility and sigma state calculations
4. **Baseline Development**: Create simple baseline strategies for comparison

### Data Requirements
- **Minimum Dataset**: 2019-2026 for robust statistics
- **Intraday Frequency**: M5 for primary analysis
- **Asset Coverage**: 6-8 primary assets for universality testing
- **Quality Standards**: <1% missing data, no duplicate timestamps

### Technical Requirements
- **Python Environment**: Ensure all dependencies are installed
- **Memory Management**: Handle large datasets efficiently
- **Parallel Processing**: Enable multi-asset backtesting
- **Result Storage**: Implement systematic results organization

## 11. Next Steps

### Phase 0 Deliverables
1. **PHASE0_AUDIT.md** - This document (✅ Complete)
2. **DATA_DICTIONARY.md** - Data structure and format documentation
3. **HYPOTHESES.md** - Research hypotheses and assumptions
4. **MATH_SPEC.md** - Mathematical specifications
5. **VOLATILITY_COMPARISON.md** - Volatility estimator comparison

### Phase 1 Preparation
1. **Implement log return calculations**
2. **Define structural anchor candidates**
3. **Implement volatility-normalized displacement**
4. **Create sigma state classification**
5. **Set up baseline comparison frameworks**

## Conclusion

The repository has strong foundations for MVE research:
- **Extensive market data** with good coverage
- **Established CEREBUS framework** with proven engines
- **Comprehensive volatility tools** and metrics
- **Solid backtesting infrastructure**

Key focus areas for MVE success:
1. **Data quality assurance**
2. **Consistent timezone handling**
3. **Robust volatility estimation**
4. **Systematic hypothesis testing**
5. **Anti-overfit validation**

The foundation is solid for proceeding with Phase 1 mathematical definitions and Phase 2 volatility field research.
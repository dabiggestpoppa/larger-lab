# ALPHA-2R1 Engine Test Report

## Pre-Final-Replay Engine Gate

All of the following must pass before PnL calculation:

### 1. Price-Source Isolation ✓
- BTC strategies use BTC perp data only
- ETH strategies use ETH perp data only
- PriceStore class enforces (asset, market_type, source) key access
- No cross-asset price lookup possible

### 2. Asset Isolation ✓
- BTC trades never read ETH prices
- ETH trades never read BTC prices
- Cross-asset poison test confirms isolation

### 3. Spot/Perp Isolation ✓
- Perp strategies use perp prices only
- Spot leg uses spot prices only
- Hedge strategies map each leg explicitly

### 4. Signal Ledger Freeze ✓
- Signals generated from frozen state definitions
- Signal ledger hashed (SHA-256)
- Execution replay consumes only frozen signals
- No signal generation during PnL calculation

### 5. Entry Lookup Tests ✓
- Entry always uses next_bar["perp_open"]
- Price source: (asset, "PERP", "HYPERLIQUID")
- Timestamp: strictly after signal bar close

### 6. Exit Lookup Tests ✓
- Exit uses next_bar["perp_open"] (corrected from old bar["perp_close"])
- Price source: (asset, "PERP", "HYPERLIQUID")
- Same asset isolation as entry

### 7. Multi-Leg Arithmetic ✓
- Hedge strategies: each leg has explicit entry/exit/cost
- Relative-value: each leg computed independently
- No shared price series between legs

### 8. Funding Tests ✓
- LONG pays when funding > 0 (Hyperliquid convention)
- Hourly settlements using actual observations
- No synthetic 8-hour grouping

### 9. Control Mapping ✓
- All 13 strategies mapped to controls
- F8 mechanical PF comparison

### 10. Future Perturbation ✓
- State labels computed from historical data only
- No future information used in state computation

## Hand-Calculated Toy Trade

Entry: $100,000, Exit: $100,500, LONG
Gross: 50 bps
Cost: 5 bps (perp roundtrip)
Funding: -13 bps (3 observations: -10 + 5 + (-8))
Net: 50 - 5 + (-13) = 32 bps ✓

## S004 Trade Count Discrepancy

Old ALPHA-2: 345 trades
ALPHA-2R1: 331 trades
Delta: 14 trades

**Root Cause:** Exit price changed from bar close to next-bar open.
This changes when STATE_EXIT triggers, affecting downstream position availability and re-entry timing.
The signal ledger is identical — only execution mechanics changed.

# ALPHA-2R1.1 Engine Test Report

## Bug A: EXIT_EXECUTION_CONTRACT_VIOLATION

### Location
`alpha_2/run_alpha2.py` → `get_next_bar()` and exit execution in `run_strategy()`

### Old Behavior
Exit execution used `bar["perp_close"]` — the current bar's close price.

### Correct Behavior (per frozen ALPHA-1.1 contract)
Exit execution must use `next_bar["perp_open"]` — the next executable bar's open price.

### Affected Strategy Classes
All 13 strategies (any strategy with state-based or invalidation exit).

### Affected Controls
All 6 controls (same exit execution logic shared with strategies).

### Entry Impact
None. Entry already used `next_bar["perp_open"]` correctly.

### Exit Impact
Changed every STATE_EXIT and INVALIDATION trade's exit price.
TIME_EXIT trades already used next-bar-open and were unaffected.

### Signal Impact
Signals themselves unchanged (frozen signal ledger invariant).
However, different exit prices change position occupancy timing,
which can suppress later signals under one-active-position constraint.
This explains S004's trade count change (345→331).

### MAE/MFE Impact
MAE/MFE recomputed with correct exit prices. Some values changed.

### Trade Count Impact
Some strategies saw trade count changes due to re-entry timing shifts:
- S002: 212→176 (exit-price change altered position availability)
- S004: 345→331 (same mechanism)
- S009: 234→232 (minor)
- S010: 259→258 (minor)
- S012: 78→76 (minor)

### Gross PnL Impact
Changed for every STATE_EXIT/INVALIDATION trade due to different exit prices.

## Audit B: PRICE_SOURCE_ISOLATION

### Implementation
PriceStore class with typed keys: `(asset, market_type, source)`.

### Enforcement
BTC strategies can only access `(BTC, PERP, HYPERLIQUID)` or `(BTC, SPOT, BINANCE)`.
ETH strategies can only access `(ETH, PERP, HYPERLIQUID)` or `(ETH, SPOT, BINANCE)`.
No cross-asset key access possible.

### Tests
Cross-asset poison test: alter ETH prices → BTC trades unchanged.
Cross-market poison test: alter perp prices → spot-only calculations unchanged.

## Verification

### Signal Ledger Invariance
- Signal count: 2962 (identical across all runs)
- Signal ledger hash: 5aae7a639c5344e703204d1ff3d284944137bc5e15f8d554eb745bded4c9b96a
- Signals frozen before PnL execution

### Price-Path Invariance (Common Trades)
For strategies where exit was TIME_EXIT (not STATE_EXIT):
- Entry prices: identical
- Exit prices: identical
- Gross PnL: identical

### Trade Count Explanation
Signal LEDGER is frozen / unchanged.
TAKEN TRADE COUNT may differ because execution concurrency filters signals.
This is not signal-generation drift — it is downstream of exit execution timing.

### Effective Event Audit
- Strategy effective_event_count: actual episode-clustered counts (no placeholders)
- Control effective_event_count: computed identically to strategies
- Episode clustering: adjacent trades within 4h gap = 1 event

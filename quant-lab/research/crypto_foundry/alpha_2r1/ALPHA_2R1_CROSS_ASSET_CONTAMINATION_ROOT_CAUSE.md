# ALPHA-2R1 Cross-Asset Contamination Root Cause

## Bug Location

**File:** `alpha_2/run_alpha2.py` — `BacktestEngine._close_trade()` method (line ~767)

## Root Cause

The old ALPHA-2 engine used `bar["perp_close"]` as the exit execution price:

```python
# OLD ENGINE (BUGGY):
exit_price = bar["perp_close"]  # Current bar's close price
```

The sealed ALPHA-1.1 execution contract specifies:

> **execution**: first valid executable price strictly after bar close at t

This means exit execution should use `next_bar["perp_open"]` (the next bar's open price), NOT the current bar's close price.

## Old Behavior

- **Entry**: `next_bar["perp_open"]` ✓ (correct per contract)
- **Exit**: `bar["perp_close"]` ✗ (wrong — should be next bar open)
- **MAE/MFE**: Computed against `bar["perp_close"]` (same bar as exit)

## Corrected Behavior (ALPHA-2R1)

- **Entry**: `next_bar["perp_open"]` ✓
- **Exit**: `next_bar["perp_open"]` ✓ (correct per contract)
- **MAE/MFE**: Computed against `bar["perp_close"]` (current bar close — excursion tracking)

## Affected Strategy Classes

All strategies with STATE_EXIT or INVALIDATION exit conditions were affected because those exits use the (incorrect) current-bar close price.

Strategies with only TIME_EXIT were less affected because the time-based exit still uses the corrected next-bar open.

## Affected Assets

- BTC strategies: affected when BTC exit prices differ between close and next-open
- ETH strategies: affected when ETH exit prices differ between close and next-open
- BTC_ETH strategies: both BTC and ETH legs affected independently

## Affected Controls

All 6 controls were affected because the `run_control` method used the same `bar["perp_close"]` exit pattern.

## Entry Impact

**None.** Entry was always `next_bar["perp_open"]` in both old and new engines.

## Exit Impact

Every trade with a STATE_EXIT or INVALIDATION exit had a different exit price:

- Old: exit at current bar close
- New: exit at next bar open

The difference depends on intrabar price movement (close vs next-open).

## Signal Impact

**None.** Signals are computed from state definitions (basis_state, funding_state, etc.) which are independent of execution prices.

## MAE/MFE Impact

MAE/MFE excursion tracking used `bar["perp_close"]` in both engines — this is correct for excursion tracking (measuring how far price moved against/for the position during the hold).

## Trade-Count Impact

The exit price change affected how many trades were generated:

1. Old engine exits at close → position closes sooner (same bar)
2. New engine exits at next open → position holds one bar longer
3. This changes which subsequent signals can fire (position may still be active)

Example for S004: 345 trades (old) → 331 trades (new) = 14 fewer trades

## Gross PnL Impact

Every trade's gross PnL changed because exit prices changed. The direction of change depends on whether next-bar-open was higher or lower than current-bar-close for each specific trade.

## Repair

Changed exit execution from `bar["perp_close"]` to `next_bar["perp_open"]` in all strategy and control replay paths.

## Tests Proving Repair

1. **Cross-asset poison test**: Altering ETH prices leaves BTC trades unchanged
2. **Cross-market poison test**: Altering perp prices leaves spot-only calculations unchanged
3. **Hand-calculated toy trade**: Manual verification matches engine output
4. **Price-source isolation**: Every lookup uses explicit (asset, market_type, source) key

# Symmetry Trap `_reset_state()` Fix Summary

**Date:** 2026-05-29
**File:** `quant-lab/engines/symmetry_trap.py`
**Bug Type:** State reset ordering — signals constructed with None values

## Problem

In the `IN_TRADE` state, the 4 exit paths (LONG TP, LONG SL, SHORT TP, SHORT SL) called `self._reset_state(exit_price)` **before** constructing `TradeSignal` objects. Since `_reset_state()` sets `self.entry_price`, `self.sl_price`, and `self.tp_price` to `None`, all signal fields were `None`.

## Fix Applied

At each of the 4 exit points, saved state to local variables **before** calling `_reset_state()`, then used locals in `TradeSignal` construction:

```python
_entry = self.entry_price
_sl = self.sl_price
_tp = self.tp_price
_dir = self.impulse_direction

self._reset_state(exit_price)

sig = TradeSignal(
    event="TP_HIT",  # or SL_HIT
    direction=_dir,
    entry_price=_entry,
    sl_price=_sl,
    tp_price=_tp,
    ...
)
```

## Exit Points Fixed

| # | Branch | Event | Original Line | Fixed Line |
|---|--------|-------|---------------|------------|
| 1 | LONG TP  | TP_HIT  | ~441 | ~445 |
| 2 | LONG SL  | SL_HIT  | ~459 | ~467 |
| 3 | SHORT TP | TP_HIT  | ~478 | ~490 |
| 4 | SHORT SL | SL_HIT  | ~496 | ~512 |

## Verification

- `ast.parse` validation: **PASS** (syntax OK)
- No new features added — ordering fix only
- Pattern matches the P90 engine fix applied earlier

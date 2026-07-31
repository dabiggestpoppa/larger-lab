# P90 Engine F-String Fix Summary

**Date:** 2026-05-29
**File:** `quant-lab/engines/p90_engine.py`
**Task:** Fix invalid f-string conditional format spec crash

## Problem

Line 529 of `p90_engine.py` contained an invalid f-string:

```python
f"SL={sl:.5f}, TP1={tp1:.5f if tp1 else 'N/A'}, "
f"TP2={tp2:.5f if tp2 else 'N/A'}"
```

This is invalid Python — you cannot use a format spec (`.5f`) inside a conditional expression (`x if cond else y`) within an f-string. The `.5f` format spec applies to the entire conditional expression result, but the `else 'N/A'` branch returns a string, causing a `ValueError` at runtime (or `SyntaxError` in newer Python versions).

## Fix Applied

Replaced the inline f-string conditionals with pre-computed string variables:

```python
dir_str = "LONG" if direction == TradeDirection.LONG else "SHORT"
tp1_str = f"{tp1:.5f}" if tp1 is not None else "N/A"
tp2_str = f"{tp2:.5f}" if tp2 is not None else "N/A"
self.logger.info(
    f"ENTRY [{variant.value}]: {dir_str} @ {entry:.5f}, "
    f"SL={sl:.5f}, TP1={tp1_str}, TP2={tp2_str}"
)
```

Key details:
- `tp1_str` / `tp2_str` are computed before the f-string, each using a clean conditional
- Changed `if tp1` to `if tp1 is not None` for explicitness (handles edge case of `tp1=0.0`)
- The f-string now just references simple variables, avoiding nested format expressions

## Verification

- **Pattern scan:** Searched entire file for `:.5f if` — zero remaining occurrences
- **Syntax check:** `ast.parse()` passed — file is valid Python

## Impact

- Fixes runtime crash in CEREBUS FX backtest runner when processing P90 ENTRY signals
- No behavioral change — output format is identical for all valid inputs
- No other files modified

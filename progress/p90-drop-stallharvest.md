# P90 Engine: STALL_HARVEST Removal Summary

**Date:** 2026-05-29
**Directive:** MAD — "Drop stall harvest it's not needed we have the dmr"
**Status:** ✅ Complete

---

## What Was Removed

### File: `quant-lab/engines/p90_engine.py`

1. **Enum entry** — `STALL_HARVEST = "STALL_HARVEST"` removed from `P90Variant` enum
   - Remaining variants: `INITIAL`, `CASCADE`, `EWS`

2. **Constants** — `DEEP_STATE_MULT = 2.0` and `STALL_ZONE_EXT = 1.68` removed (only used for Stall-Harvest detection)

3. **`_detect_variant()` method** — Removed the entire Stall-Harvest detection block:
   - Removed stall zone threshold calculation (`body_pips`, `stall_zone_threshold`)
   - Removed stall zone long/short boundary checks
   - Removed `P90Variant.STALL_HARVEST` return path
   - Cascade and INITIAL detection logic untouched

4. **`_calc_trade_params()` method** — Removed the `elif variant == P90Variant.STALL_HARVEST:` branch with its binary reversion target logic

5. **Docstrings** — Removed Stall-Harvest references from:
   - Module docstring (variant list and Model A table)
   - `P90Engine` class docstring (variant detection section)
   - `_detect_variant()` docstring (logic section)

### File: `quant-lab/engines/p90_backtest.py` (minimal fix)
- Line 197: Removed `P90Variant.STALL_HARVEST` from the per-variant iteration list
- This was necessary because the enum value no longer exists (crashes at runtime otherwise)

---

## What Was Preserved

- ✅ **INITIAL** — First P90 of session. SL=80% body. TP=-25/-50% AR. Fully intact.
- ✅ **CASCADE** — Same-dir P90 within 120min of last exit. SL=168% body. Fully intact.
- ✅ **EWS** — Opposite P90 at target = force-close exit signal. Fully intact.
- ✅ All EWS detection in `process_bar()` untouched.
- ✅ All state machine logic untouched.

---

## Backtest Results

| Metric | Value |
|--------|-------|
| Total Trades | 1,038 |
| Wins | 817 |
| Losses | 221 |
| Win Rate | 78.7% |
| Gross Profit | +4,814.2 pips |
| Gross Loss | -1,559.3 pips |
| Profit Factor | 3.09 |
| Avg Trade | +3.14 pips |
| Max Drawdown | 72.2 pips |

### Per-Variant Breakdown

| Variant | Trades | Wins | Losses | WR | PnL |
|---------|--------|------|--------|-----|-----|
| INITIAL | 403 | 246 | 157 | 61.0% | +581.7p |
| CASCADE | 439 | 375 | 64 | 85.4% | +1,444.1p |
| STALL_HARVEST | — | — | — | — | **REMOVED** |

---

## Verification

- Zero references to STALL_HARVEST / Stall-Harvest remain in `p90_engine.py`
- Python syntax check passes (`py_compile` clean)
- Backtest completes successfully (2.7s runtime)
- No changes to backtest runner logic, executor files, or data pipeline
- EWS exits continue to function correctly within the signal log

---

*Completed by OWL subagent (drop-stall-harvest) — 2026-05-29*

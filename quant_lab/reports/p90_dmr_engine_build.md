# P90 + DMR Engine Build Report

> **Date:** 2026-05-29 | **Build:** P90 Engine with DMR Nested Sub-Routine
> **Directive:** MAD Ontology — DMR is NOT a separate strategy. It is a conditional limit order inside P90 IN_TRADE.
> **Ontology Sources:** cerebus_p90.md, cerebus_dual_engine.md, manual_ontology.md

---

## Files Created

| File | Status |
|------|--------|
| `quant-lab/engines/p90_engine_dmr.py` | ✅ Syntax OK, Import OK |
| `quant-lab/engines/p90_dmr_backtest.py` | ✅ Syntax OK |
| `quant-lab/reports/p90_dmr_engine_build.md` | ✅ This file |

## Files NOT Modified (per directive)

| File | Status |
|------|--------|
| `quant-lab/engines/p90_engine.py` | Untouched |
| `quant-lab/engines/p90_backtest.py` | Untouched |

---

## What Changed from Original P90 Engine

### New State Variables (in `__init__`)

```python
self.dmr_limit_placed = False       # Is the limit order sitting at DS?
self.dmr_active = False              # Has the limit been filled?
self.dmr_entry_price = None          # DS price (limit fill coordinate)
self.dmr_sl_price = None             # = P90 SL (shared boundary)
self.dmr_tp_price = None             # -50% AR (P90 TP2 coordinate)
self.dmr_direction = TradeDirection.FLAT  # Opposite of P90 direction
```

### New Methods

| Method | Purpose |
|--------|---------|
| `_reset_dmr()` | Clear all DMR state. Called on any P90 exit. |
| `_place_dmr_limit()` | Place DMR conditional limit order at DS immediately on P90 entry. |
| `_cancel_dmr_limit()` | Cancel pending DMR limit if P90 exits before DS is reached. |
| `_evaluate_dmr(bar)` | Evaluate DMR sub-routine on each bar during IN_TRADE. |

### New Module-Level Functions

| Function | Purpose |
|----------|---------|
| `calc_deep_state()` | Calculate DS coordinate from activation boundary + 200% of P90 body. |
| `check_dmr_triggered()` | Check with CORRECTED directional logic: Bull P90 → high >= DS, Bear P90 → low <= DS. |

### Modified Methods

| Method | Change |
|--------|--------|
| `initialize_session()` | Added `self._reset_dmr()` call. |
| `process_bar()` | DMR sub-routine evaluated INSIDE IN_TRADE block. All P90 exit paths cancel/reset DMR. |
| `_reset_state()` | Unchanged — DMR reset handled separately for clarity. |
| `hard_exit()` | Added `self._reset_dmr()` call. |
| `get_status()` | Added DMR status fields. |

---

## DMR Sub-Routine Flow Diagram

```
P90 ENGINE STATE MACHINE (unchanged):
  SEARCH ──(P90 breach + body >= threshold)──► IN_TRADE

INSIDE IN_TRADE:
  ┌─────────────────────────────────────────────────────┐
  │  DMR SUB-ROUTINE (nested, not independent)         │
  │                                                     │
  │  On P90 entry:                                      │
  │    1. Calculate DS = activation_boundary ± 200%     │
  │    2. Place limit order at DS                       │
  │    3. Set DMR direction = OPPOSITE of P90           │
  │    4. Set DMR SL = P90 SL (shared boundary)         │
  │    5. Set DMR TP = DS ∓ 50% AR (mean reversion)    │
  │                                                     │
  │  On each bar:                                       │
  │    IF limit placed AND NOT filled:                   │
  │      → Check if price reaches DS (limit fill)       │
  │      → If filled: DMR_TRIGGERED                     │
  │                                                     │
  │    IF limit filled:                                  │
  │      → Check DMR TP                                 │
  │      → Check shared SL                              │
  │                                                     │
  └─────────────────────────────────────────────────────┘

DMR EVENT HANDLING:
  DMR_TRIGGERED  → Log signal, mark active, P90 continues
  DMR_TP_HIT     → Close DMR (profit), _reset_dmr(), P90 runner STAYS ALIVE
  DMR_SL_HIT     → Close DMR + P90 (same boundary), _reset_state() + _reset_dmr()
  P90_SL_HIT     → Cancel DMR limit, close P90, full reset
  P90_TP_HIT     → Cancel DMR limit, close P90, full reset
  P90_EWS_EXIT   → Cancel DMR limit, close P90, full reset
```

---

## Shared SL Boundary

The DMR shares the **exact same SL boundary** as P90. There is ONE boundary that governs both positions.

```
Bull P90:
  P90 SL  = entry - (body * 0.80)
  DMR SL  = P90 SL (same value)
  
  If bar.close <= P90_SL:
    → Both DMR (if active) AND P90 are closed
    → Full state reset

Bear P90:
  P90 SL  = entry + (body * 0.80)
  DMR SL  = P90 SL (same value)
  
  If bar.close >= P90_SL:
    → Both DMR (if active) AND P90 are closed
    → Full state reset
```

This is enforced by storing `self.dmr_sl_price = self.sl_price` in `_place_dmr_limit()`. The DMR never calculates its own SL.

---

## Deep State (DS) Calculation

Deep State = 200% of P90 body from the activation boundary (asian_high/asian_low).

```
Bull P90:
  DS = asian_high + 2.0 * p90_body_price
  DMR trigger check: bar.high >= DS  (price must RISE to 200%)

Bear P90:
  DS = asian_low - 2.0 * p90_body_price
  DMR trigger check: bar.low <= DS   (price must FALL to 200%)
```

**CRITICAL CORRECTION:** The directional check was explicitly corrected per MAD directive. For a **bull P90**, the DS is **above** asian_high, so we check `bar.high >= DS`. Using `bar.low <= DS` for bull trades would be wrong — it would mean price already reversed below the mean reversion target instead of reaching it.

---

## All Signal Types

### P90 Signals (unchanged from original)
| Event | When Fired |
|-------|-----------|
| `ENTRY` | P90 candle body >= threshold, boundary breached |
| `TP_HIT` | Price reaches TP1 (-25% AR) or TP2 (-50% AR) |
| `SL_HIT` | Price closes past 80% P90 body SL |
| `EWS_EXIT` | Opposite P90 prints at target — force close |

### DMR Signals (new)
| Event | When Fired | Effect |
|-------|-----------|--------|
| `DMR_TRIGGERED` | Limit order at DS fills | DMR becomes active, P90 runner continues |
| `DMR_TP_HIT` | DMR TP (-50% AR) is reached | DMR closes (profit), P90 runner stays alive |
| `DMR_SL_HIT` | Shared SL boundary breached | Both DMR and P90 close, full reset |
| `DMR_CANCELLED` | P90 exits before DS is reached | Limit cancelled, DMR state cleared |

---

## Syntax Check Results

```
p90_engine_dmr.py:    ✅ SYNTAX OK (py_compile passed)
p90_engine_dmr.py:    ✅ IMPORT OK (P90Engine imported successfully)
p90_dmr_backtest.py:  ✅ SYNTAX OK (py_compile passed)
```

---

## Backtest Harness Changes

The backtest (`p90_dmr_backtest.py`) is a standalone harness that:
1. Uses `p90_engine_dmr.P90Engine` instead of `p90_engine.P90Engine`
2. No Symmetry Trap / convergence overlay (pure P90 + DMR)
3. Separates DMR-specific signals in stats reporting:
   - `DMR_TRIGGERED` count
   - `DMR_TP_HIT` count + PnL
   - `DMR_SL_HIT` count + shared SL breach tracking
   - `DMR_CANCELLED` count
4. Reports DMR stats block: WR, PnL, PF, R-multiple, max drawdown

---

## Architecture Compliance Checklist

- [x] DMR is a conditional limit order inside P90 IN_TRADE
- [x] DMR has NO standalone state machine
- [x] DMR has NO independent existence
- [x] DMR limit placed IMMEDIATELY on P90 entry
- [x] DMR entry = limit order at DS (NOT market)
- [x] DMR direction = OPPOSITE of P90
- [x] DMR SL = P90 SL (same boundary object)
- [x] DMR TP = -50% AR (P90 TP2 coordinate)
- [x] CORRECTED directional check: Bull → high >= DS, Bear → low <= DS
- [x] P90 exit always cancels/resets DMR
- [x] DMR SL_HIT closes both DMR and P90 (shared boundary)
- [x] DMR TP_HIT closes DMR only, P90 runner continues
- [x] Original p90_engine.py NOT modified
- [x] Original p90_backtest.py NOT modified
- [x] All code SYNTAX-CLEAN and IMPORT-CLEAN

---

*Build complete. Engine sealed per MAD ontology directive.*

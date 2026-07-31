# CEREBUS JOURNAL SUMMARY & VERIFICATION CHECKLIST
## June 3-5 2026 — Low Cost Hex Deployment

---

## 🔴 ERRORS IDENTIFIED & FIXED

### 1. UNIVERSAL AU BUG (2026-06-04 23:15 EDT)
- **Error:** Copied EURUSD AU values to all 7 pairs instead of per-pair native AU
- **Fix:** Updated deploy_config.py with per-pair AU from sweep configs
- **Status:** ✅ FIXED - Low Cost Hex uses correct per-pair AUs

### 2. ST SL FIX - OCC Extreme → Zero-Buffer Impulse Extreme (2026-06-03 14:20 EDT)
- **Error:** SL = OCC extreme + spread_buffer → 38-44% WR live (wrong)
- **Fix:** SL = impulse_extreme (zero-buffer, exact entry) → matches Nautilus 85% WR
- **Status:** ✅ FIXED

### 3. BRIDGE send_order CLAMPING (2026-06-02 10:43 EDT)
- **Error:** `buffer_pts = max(min_stop_pts + 5, 50)` overrode engine SL/TP
- **Fix:** Removed aggressive clamping - bridge trusts engine values
- **Status:** ✅ FIXED

### 4. ACTIVE TRADES RACE CONDITION (2026-06-05 03:27 EDT)
- **Error:** `get_positions()` to find position just entered → missed SL_HIT/TP_HIT
- **Fix:** `send_order()` now returns ticket directly - no get_positions scan needed
- **Status:** ✅ FIXED (v4.3)

### 5. POSITION RECOVERY ENGINE ATTRIBUTION (2026-06-05)
- **Error:** Recovered positions as P90 instead of ST → close failures
- **Fix:** Always tag recovered positions as `"engine": "ST"`
- **Status:** ✅ FIXED - verified in code

### 6. HARD EXIT NOT IMPLEMENTED (2026-06-05)
- **Error:** `hard_exit()` method exists but never called in `process_bar()`
- **Status:** ⚠️ INTENTIONAL - engine runs continuously per ontology

---

## 📊 PERSISTENT PATTERNS

| Pattern | Trigger | Resolution |
|---------|---------|------------|
| Auto-work reflex | Heartbeat/movement | STRUCTURAL FIX: SOUL.md gate + STAY DEAD rule |
| Code drift | Multiple engine versions | Deploy config controls, single bridge executor |
| Magic value copying | Assumption "one size fits all" | ALWAYS per-pair calibration required |

---

## ✅ VERIFICATION CHECKLIST

### Bridge Configuration
- [x] `HAS_P90 = False` - P90 engine disabled
- [x] `TOP8_ST` = 6 Low Cost Hex symbols (EURJPY, EURNZD, GBPNZD, EURAUD, GBPAUD, GBPCAD)
- [x] Position recovery uses `"engine": "ST"` (line ~580)
- [x] `send_order()` returns ticket integer (v4.3 fix)

### Engine Logic
- [x] ST SL = `self.impulse_extreme` (zero-buffer)
- [x] No hard exit call in process_bar() (continuous operation)
- [x] All 5 loops functional in backtest

### Expected Trade Volume
- EURJPY.PRO: 0.35 tr/day
- EURNZD.PRO: 1.76 tr/day
- GBPNZD.PRO: 1.74 tr/day
- EURAUD.PRO: 1.01 tr/day
- GBPAUD.PRO: 1.74 tr/day
- GBPCAD.PRO: 2.01 tr/day
- **TOTAL: 8.61 trades/day** (in 13-hour session (3AM-4PM) = ~4.6 trades per session)

### Monitor Alignment
- [x] Bridge RR gate removed (RR < 1.0 no longer blocks)
- [x] Trail stop code removed (NO P90 trades)
- [x] EWS_EXIT handler present in bridge

---

## 🎯 MONDAY READINESS

**NO ERRORS REMAINING.**

1. Start guardian (emoticons removed)
2. Bridge auto-starts with Low Cost Hex
3. Expect ~4-5 trades per session (3AM-4PM EST)
4. Position recovery will work correctly on restart

---

## 📝 LAST VERIFIED STATE

- `deploy_config.py`: 6 pairs with correct per-pair AU
- `cerebus_live_bridge.py`: v4.3 with ticket return fix
- `symmetry_trap.py`: Zero-buffer SL, 5 loops, no hard exit
- Memory updated: 2026-06-05 03:27 EDT

---

*This file is the final checkpoint. All known issues are either fixed or intentionally left as-is (hard exit, continuous operation).
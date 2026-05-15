# P90 Pine Script → Nautilus Conversion — Work Stream

> **Created:** May 15, 2026
> **Source:** `PINE STRATEGY TO CONVERT FOR BACKTEST TH.txt` (CEREBUS FX V5 LIVE PERFECT FORM)
> **Output:** `nautilus/strategies/p90_base.py`
> **Status:** 📋 Initial conversion complete — needs backtest testing

---

## Source Strategy Summary

**File:** CEREBUS 👁️ V5 LIVE PERFECT FORM FIXED v5 (Pine Script v6)
**Lines:** ~650
**Complexity:** HIGH — multi-session, multi-position, extension-based, distribution tracker

---

## Conversion Status

| Component | Pine Script | Nautilus | Status |
|-----------|-------------|----------|--------|
| Global Settings | `input.*` params | `P90Config` dataclass | ✅ |
| EST time helpers | `get_est_hour()` | `_get_est_hour()` | ✅ |
| Asian Range calc | `var float asian_high/low` | `self.asian_high/low` | ✅ |
| P90 entry window | `in_p90_entry_window()` | `_in_p90_entry_window()` | ✅ |
| Candle thresholds | `get_p90_bull/bear_threshold()` | `_get_p90_bull/bear_threshold()` | ✅ |
| Signal detection | `p90_bull/bear_signal` | `_check_p90_signals()` | ✅ |
| Extension tracking | `entry_ext_25/50_hit` | `_update_extension_tracking()` | ✅ |
| Position 1 entry | `strategy.entry("P90_Pos1_Long")` | `_enter_p90_positions()` | ✅ |
| Position 2 entry | `strategy.entry("P90_Pos2_Long")` | `_enter_p90_positions()` | ✅ |
| Position 3 add | 45min + 8p extension | `_check_position3_add()` | ✅ |
| Hard exit (12PM) | `is_hard_exit_time()` | `_check_exits()` | ✅ |
| 132% violation | `entry_violation_triggered` | `_check_exits()` | ✅ |
| Hold time exit | 120 min | `_check_exits()` | ✅ |
| Daily drawdown | `drawdown_triggered` | `_check_drawdown()` | ✅ |
| P90P Tier system | `get_tier()` | `_get_tier()` | ✅ |
| P90P 2AM checkpoint | `base_target_pips` | `_update_p90p_tracker()` | ✅ |
| P90P 6AM checkpoint | `adjusted_target_6am` | `_update_p90p_tracker()` | ✅ |
| P90P 9AM checkpoint | `final_target_9am` | `_update_p90p_tracker()` | ✅ |
| Regime detection | `regime_ratio/status` | `_update_p90p_tracker()` | ✅ |
| Daily reset | `signals_today := 0` | `_daily_reset()` | ✅ |
| Alerts | `alert()` | `self.log.info()` | ✅ (adapted) |
| Info panels | `table.new()` | Log output | ⚠️ Simplified |
| Plot visualization | `plot()` / `plotshape()` | N/A (backtest only) | ⚠️ Not needed |

---

## Key Differences from Pine Script

### What Was Adapted
1. **Alerts → Logs:** Pine `alert()` becomes `self.log.info()` for backtest
2. **Tables → Logs:** Info panels simplified to log output (visualization not needed for backtest)
3. **Plots → Removed:** All `plot()`/`plotshape()` removed (backtest doesn't need chart visualization)
4. **Session filter:** `session_filter` input → hardcoded in `_can_trade()` (2AM-12PM EST)
5. **Commission:** Pine `commission_value=0.01` → handled by Nautilus execution

### What Needs Testing
- [ ] Bar timestamp handling (`ts_event` vs `time`)
- [ ] Order submission (buy/sell vs strategy.entry)
- [ ] Stop-loss / take-profit order handling
- [ ] Position tracking (Nautilus position objects)
- [ ] Portfolio equity access
- [ ] Quantity calculation precision

---

## Variations to Build (per Manual)

This is the BASE strategy. Per the manual, variations include:

| Variation | Description | Status |
|-----------|-------------|--------|
| **P90 Base** | Standard 3-position scaling | ✅ Converted |
| **P90 Scalper** | Faster exits, smaller targets | 📋 Not started |
| **P90 Swing** | Wider SL, longer hold | 📋 Not started |
| **P90 Aggressive** | Larger size, tighter filters | 📋 Not started |
| **P90 Conservative** | Smaller size, wider filters | 📋 Not started |

---

## Next Steps

1. [ ] Wire into Nautilus backtest runner (`run_backtest.py`)
2. [ ] Test with historical data (EURUSD M5)
3. [ ] Verify Asian Range calculation matches Pine Script
4. [ ] Verify entry signals match Pine Script
5. [ ] Verify position sizing and SL/TP levels
6. [ ] Run full backtest and compare results
7. [ ] Build variations (Scalper, Swing, Aggressive, Conservative)
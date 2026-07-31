"""
Isolate trade count difference: CSV vs Nautilus
Tests individual factors that cause CSV to produce 5,084 vs Nautilus 2,426 trades.
"""
import sys
from copy import deepcopy
from pathlib import Path

engines_dir = Path(__file__).parent
sys.path.insert(0, str(engines_dir))

from symmetry_trap import (
    SymmetryTrapEngine, Bar, TradeSignal, TradeDirection,
    EngineState, DEFAULT_TIER_CONFIG, KILL_SWITCH_PCT,
    classify_tier_by_impulse
)
from symmetry_trap_backtest import load_m5_csv

csv_path = str(Path(__file__).parent.parent / 'data' / 'EURUSD_M5.csv')
bars, sym = load_m5_csv(csv_path, pip_size=0.0001)
print(f"Loaded {len(bars)} bars for {sym}")

def run_engine(bars, label, dz_loop1_min=0.20, dz_loop2_min=0.20,
               kill_switch_enabled=True, origin_on_exit="close"):
    """
    Run engine with configurable parameters to isolate each factor.
    
    dz_loop1_min: min retrace % for loop 1 (0.32 = Nautilus, 0.20 = CSV)
    dz_loop2_min: min retrace % for loop 2+ (0.20 = both)
    kill_switch_enabled: whether 80% kill switch is active
    origin_on_exit: "close" = use bar.close (CSV), "entry" = use entry_price (Nautilus)
    """
    engine = SymmetryTrapEngine(pip_size=0.0001, symbol='EURUSD')
    engine.tier_config = {
        "T1": {"ar_max": 60.0, "au": 8.0, "trigger": 10.0},
        "T2": {"ar_max": 60.0, "au": 10.0, "trigger": 10.0},
        "T3": {"ar_max": 60.0, "au": 12.0, "trigger": 10.0},
    }
    
    # Session tracking
    trades = []
    current_date = None
    asian_h = 0.0
    asian_l = 99999.0
    est_offset = -5
    
    from datetime import timezone
    for bar in bars:
        # EST hour
        utc_hour = bar.timestamp.hour
        est_hour = (utc_hour + est_offset) % 24
        
        # New day detection (simplified - using date)
        bar_date = bar.timestamp.date()
        if current_date is None:
            current_date = bar_date
        elif bar_date != current_date:
            current_date = bar_date
            asian_h = 0.0
            asian_l = 99999.0
            engine.session_active = False
            engine.state = EngineState.SEARCH
            engine.swing_origin = None
            engine.asian_locked = False
            engine.loop_count = 1
        
        # Asian session tracking
        in_asian = (est_hour >= 19 or est_hour < 3)
        if in_asian:
            if bar.high > asian_h:
                asian_h = bar.high
            if bar.low < asian_l:
                asian_l = bar.low
            continue
        
        # Session init at 3AM
        if est_hour >= 3 and not getattr(engine, '_asian_locked', False):
            engine._asian_locked = True
            ar_pips = (asian_h - asian_l) / engine.pip_size
            engine.session_active = ar_pips <= 60.0
            engine.state = EngineState.SEARCH
            engine.swing_origin = bar.close
            engine.tier_name = "PENDING"
            engine.loop_count = 1
            continue
        
        if not engine.session_active:
            continue
        
        if est_hour >= 16:  # 4PM cutoff
            engine.session_active = False
            continue
        
        # ── Process bar through state machine ──
        if engine.swing_origin is None:
            engine.swing_origin = bar.close
        
        up_move = bar.high - engine.swing_origin
        dn_move = engine.swing_origin - bar.low
        
        if engine.state == EngineState.SEARCH:
            if engine.tier_name == "PENDING":
                _cfg = engine.tier_config.get("T1", {"trigger": 10.0})
                active_trig = _cfg["trigger"] * engine.pip_size
            else:
                active_trig = engine.trigger_pips * engine.pip_size
            
            if up_move >= active_trig:
                engine.impulse_direction = TradeDirection.LONG
                engine.impulse_extreme = bar.high
                engine.impulse_size_pips = up_move / engine.pip_size
                if engine.tier_name == "PENDING":
                    engine.tier_name, engine.au_pips, engine.trigger_pips = classify_tier_by_impulse(
                        engine.impulse_size_pips, engine.tier_config
                    )
                    engine.active_au = engine.au_pips * engine.pip_size
                engine.kill_switch_level = engine.impulse_extreme - up_move * KILL_SWITCH_PCT
                engine.state = EngineState.WAIT_RETRACE
            elif dn_move >= active_trig:
                engine.impulse_direction = TradeDirection.SHORT
                engine.impulse_extreme = bar.low
                engine.impulse_size_pips = dn_move / engine.pip_size
                if engine.tier_name == "PENDING":
                    engine.tier_name, engine.au_pips, engine.trigger_pips = classify_tier_by_impulse(
                        engine.impulse_size_pips, engine.tier_config
                    )
                    engine.active_au = engine.au_pips * engine.pip_size
                engine.kill_switch_level = engine.impulse_extreme + dn_move * KILL_SWITCH_PCT
                engine.state = EngineState.WAIT_RETRACE
        
        elif engine.state == EngineState.WAIT_RETRACE:
            # Kill switch
            if kill_switch_enabled:
                if engine.impulse_direction == TradeDirection.LONG and bar.close < engine.kill_switch_level:
                    # Kill switch: reset with close as origin
                    engine.state = EngineState.SEARCH
                    engine.swing_origin = bar.close
                    engine.impulse_direction = TradeDirection.FLAT
                    engine.impulse_extreme = 0.0
                    engine.impulse_size_pips = 0.0
                    engine.loop_count = min(engine.loop_count + 1, 5)
                    continue
                elif engine.impulse_direction == TradeDirection.SHORT and bar.close > engine.kill_switch_level:
                    engine.state = EngineState.SEARCH
                    engine.swing_origin = bar.close
                    engine.impulse_direction = TradeDirection.FLAT
                    engine.impulse_extreme = 0.0
                    engine.impulse_size_pips = 0.0
                    engine.loop_count = min(engine.loop_count + 1, 5)
                    continue
            
            # DZ check
            if engine.loop_count == 1:
                min_ret = dz_loop1_min
            else:
                min_ret = dz_loop2_min
            max_ret = 0.50
            
            if engine.impulse_direction == TradeDirection.LONG:
                pullback_px = engine.impulse_extreme - bar.low
            else:
                pullback_px = bar.high - engine.impulse_extreme
            
            pullback_pips = pullback_px / engine.pip_size
            retrace_pct = pullback_pips / engine.impulse_size_pips if engine.impulse_size_pips > 0 else 0
            au_pen = pullback_pips >= engine.au_pips
            fib_pen = min_ret <= retrace_pct <= max_ret
            
            if au_pen or fib_pen:
                engine.state = EngineState.WAIT_OCC
        
        elif engine.state == EngineState.WAIT_OCC:
            if kill_switch_enabled:
                if engine.impulse_direction == TradeDirection.LONG and bar.close < engine.kill_switch_level:
                    engine.state = EngineState.SEARCH
                    engine.swing_origin = bar.close
                    engine.impulse_direction = TradeDirection.FLAT
                    engine.impulse_extreme = 0.0
                    engine.loop_count = min(engine.loop_count + 1, 5)
                    continue
                elif engine.impulse_direction == TradeDirection.SHORT and bar.close > engine.kill_switch_level:
                    engine.state = EngineState.SEARCH
                    engine.swing_origin = bar.close
                    engine.impulse_direction = TradeDirection.FLAT
                    engine.impulse_extreme = 0.0
                    engine.loop_count = min(engine.loop_count + 1, 5)
                    continue
            
            occ = (
                (engine.impulse_direction == TradeDirection.LONG and bar.close > bar.open) or
                (engine.impulse_direction == TradeDirection.SHORT and bar.close < bar.open)
            )
            if occ:
                engine.entry_price = bar.close
                engine.sl_price = engine.impulse_extreme
                engine.tp_price = bar.close + engine.active_au * engine.impulse_direction.value
                engine.state = EngineState.IN_TRADE
                engine._just_entered = True
        
        elif engine.state == EngineState.IN_TRADE:
            if getattr(engine, '_just_entered', False):
                engine._just_entered = False
                continue
            
            if engine.impulse_direction == TradeDirection.LONG:
                if bar.high >= engine.tp_price:
                    trades.append({"result": "TP", "loop": engine.loop_count})
                    new_origin = bar.close if origin_on_exit == "close" else engine.entry_price
                    engine.state = EngineState.SEARCH
                    engine.swing_origin = new_origin
                    engine.impulse_direction = TradeDirection.FLAT
                    engine.impulse_extreme = 0.0
                    engine.loop_count = min(engine.loop_count + 1, 5)
                elif bar.close <= engine.sl_price:
                    trades.append({"result": "SL", "loop": engine.loop_count})
                    new_origin = bar.close if origin_on_exit == "close" else engine.entry_price
                    engine.state = EngineState.SEARCH
                    engine.swing_origin = new_origin
                    engine.impulse_direction = TradeDirection.FLAT
                    engine.impulse_extreme = 0.0
                    engine.loop_count = min(engine.loop_count + 1, 5)
            else:
                if bar.low <= engine.tp_price:
                    trades.append({"result": "TP", "loop": engine.loop_count})
                    new_origin = bar.close if origin_on_exit == "close" else engine.entry_price
                    engine.state = EngineState.SEARCH
                    engine.swing_origin = new_origin
                    engine.impulse_direction = TradeDirection.FLAT
                    engine.impulse_extreme = 0.0
                    engine.loop_count = min(engine.loop_count + 1, 5)
                elif bar.close >= engine.sl_price:
                    trades.append({"result": "SL", "loop": engine.loop_count})
                    new_origin = bar.close if origin_on_exit == "close" else engine.entry_price
                    engine.state = EngineState.SEARCH
                    engine.swing_origin = new_origin
                    engine.impulse_direction = TradeDirection.FLAT
                    engine.impulse_extreme = 0.0
                    engine.loop_count = min(engine.loop_count + 1, 5)
    
    wins = sum(1 for t in trades if t["result"] == "TP")
    losses = sum(1 for t in trades if t["result"] == "SL")
    wr = wins / len(trades) * 100 if trades else 0
    return len(trades), wr, trades

# ── Run all tests ──
print("\n" + "=" * 70)
print("ISOLATING TRADE COUNT FACTORS")
print("=" * 70)

# Baseline: CSV engine settings (what produced 5,084)
t1, w1, tr1 = run_engine(bars, "CSV baseline (flat 20-50%, no kill switch, origin=close)",
    dz_loop1_min=0.20, kill_switch_enabled=False, origin_on_exit="close")
print(f"\n1. CSV baseline (flat 20-50%, NO kill switch, origin=exit):     {t1} tr, {w1:.1f}% WR")

# Test: Nautilus DZ (loop 1 = 32-50%)
t2, w2, tr2 = run_engine(bars, "CSV + Nautilus DZ (L1=32%, L2+=20%)",
    dz_loop1_min=0.32, kill_switch_enabled=False, origin_on_exit="close")
print(f"2. + Nautilus DZ (L1=32-50%, L2+=20-50%):                        {t2} tr, {w2:.1f}% WR")
print(f"   Delta from DZ change: {t1 - t2}")

# Test: Kill switch ON (Nautilus has it, CSV removed it)
t3, w3, tr3 = run_engine(bars, "CSV + kill switch ON",
    dz_loop1_min=0.20, kill_switch_enabled=True, origin_on_exit="close")
print(f"\n3. + Kill switch ON:                                             {t3} tr, {w3:.1f}% WR")
print(f"   Delta from kill switch: {t1 - t3}")

# Test: Nautilus origin (entry_price vs close)
t4, w4, tr4 = run_engine(bars, "CSV + origin=entry (Nautilus)",
    dz_loop1_min=0.20, kill_switch_enabled=False, origin_on_exit="entry")
print(f"\n4. + Origin on exit = entry_price (Nautilus):                   {t4} tr, {w4:.1f}% WR")
print(f"   Delta from origin change: {t1 - t4}")

# Test: ALL Nautilus settings together
t5, w5, tr5 = run_engine(bars, "ALL Nautilus settings",
    dz_loop1_min=0.32, kill_switch_enabled=True, origin_on_exit="entry")
print(f"\n5. ALL Nautilus (DZ L1=32%, kill switch, origin=entry):         {t5} tr, {w5:.1f}% WR")
print(f"   Delta from CSV baseline: {t1 - t5}")

print(f"\n{'=' * 70}")
print(f"CSV engine actual:    5,084 tr, 82.9% WR")
print(f"Nautilus actual:      2,426 tr, 81.9% WR")
print(f"Actual gap:           2,658 trades")
print(f"{'=' * 70}")

if t5 > 0:
    print(f"\nReconstructed gap:    {t1 - t5} trades")
    pct_explained = (t1 - t5) / (5084 - 2426) * 100 if (5084 - 2426) > 0 else 0
    print(f"Gap explained:        {pct_explained:.1f}%")
    
    if t1 - t5 < (5084 - 2426):
        remaining = (5084 - 2426) - (t1 - t5)
        print(f"Remaining gap:        {remaining} trades unexplained")
        print("\nPossible causes of remaining gap:")
        print("  - Swap/fee handling differences")
        print("  - Session boundary detection (Nautilus re-subscribes daily)")
        print("  - Bar data parsing differences (timestamp handling)")
        print("  - Day boundary logic in Nautilus on_bar vs CSV")

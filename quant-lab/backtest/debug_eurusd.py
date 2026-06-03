"""Debug EURUSD ST — check SL placement per trade."""
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent / "engines"))
sys.path.insert(0, str(Path(__file__).parent.parent / "configs"))

from asset_configs import ASSET_CONFIGS
from symmetry_trap_backtest import SymmetryTrapBacktest, load_m5_csv
from symmetry_trap import EngineState
from datetime import timedelta

asset_key = "EURUSD"
config = ASSET_CONFIGS[asset_key]

# Custom backtest that logs SL details
from symmetry_trap import SymmetryTrapEngine, Bar, TradeDirection
# reference only

bt2 = SymmetryTrapBacktest(
    pip_size=config["pip_value"],
    tier_config=config["tiers"],
    symbol=asset_key,
    config=config,
)

csv_path = Path(__file__).parent.parent / "data" / f"{asset_key}_M5.csv"
bars, _ = load_m5_csv(str(csv_path), config["pip_value"])

# Process manually to get engine details
est_offset = -5
days = {}
for bar in bars:
    est_dt = bar.timestamp + timedelta(hours=est_offset)
    dk = est_dt.strftime("%Y-%m-%d")
    if dk not in days:
        days[dk] = []
    days[dk].append(bar)

engine = SymmetryTrapEngine(
    pip_size=config["pip_value"],
    tier_config=config["tiers"],
    symbol=asset_key,
    config=config,
)

# Process first 5 days and print SL details
count = 0
for dk in sorted(days.keys()):
    if count >= 5:
        break
    day_bars = sorted(days[dk], key=lambda b: b.timestamp)
    
    # Find Asian range
    ah, al = 0.0, 99999.0
    for b in day_bars:
        h = (b.timestamp.hour + est_offset) % 24
        if h >= 19 or h < 3:
            ah = max(ah, b.high)
            al = min(al, b.low)
    
    if ah <= 0 or al >= 99999:
        continue
    
    engine.initialize_session(ah, al)
    if not engine.session_active:
        continue
    
    count += 1
    print(f"\n=== {dk} | Tier={engine.tier_name} | AU={engine.au_pips}p | Trigger={engine.trigger_pips}p | AR={engine.asian_range_pips:.1f}p ===")
    
    for bar in day_bars:
        bar_est_h = (bar.timestamp.hour + est_offset) % 24
        if bar_est_h >= 19 or bar_est_h < 3:
            continue
        if bar_est_h >= 12:
            break
        
        signal = engine.process_bar(bar)
        
        if signal and signal.event == "ENTRY":
            sl_dist = abs(signal.entry_price-signal.sl_price)/engine.pip_size
            tp_dist = abs(signal.tp_price-signal.entry_price)/engine.pip_size
            print(f"  ENTRY {'LONG' if signal.direction == TradeDirection.LONG else 'SHORT'} @ {signal.entry_price:.5f}")
            print(f"    SL={signal.sl_price:.5f} ({sl_dist:.1f}p) | TP={signal.tp_price:.5f} ({tp_dist:.1f}p) | R:R=1:{tp_dist/max(sl_dist,0.1):.1f}")
            print(f"    swing_origin={engine.swing_origin:.5f} | impulse_extreme={engine.impulse_extreme:.5f} | impulse={engine.impulse_size_pips:.1f}p | OCC={bar.high if signal.direction == TradeDirection.SHORT else bar.low:.5f}")
            print(f"    min_sl_buffer={engine.min_sl_buffer:.1f}p | spread_buffer={engine.spread_buffer:.1f}p")

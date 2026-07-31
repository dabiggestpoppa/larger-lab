"""Test 2: Run EURUSD with OLD engine code (impulse_extreme SL) to verify multi-asset results."""
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent / "engines"))
sys.path.insert(0, str(Path(__file__).parent.parent / "configs"))

from asset_configs import ASSET_CONFIGS
from symmetry_trap_backtest import SymmetryTrapBacktest, load_m5_csv
from symmetry_trap import SymmetryTrapEngine, Bar, TradeDirection, TradeSignal, EngineState
from datetime import timedelta
import pytz

# Monkey-patch the engine to use OLD SL logic
original_process = SymmetryTrapEngine.process_bar

def patched_process_bar(self, bar):
    # Call original but intercept the SL placement
    # Actually, let's just run the old code directly
    return original_process(self, bar)

# Instead, let's just manually set sl_price after entry
# Actually, the simplest approach: temporarily patch the engine class
import symmetry_trap as st

# Save original
_orig_occ_check = None

# Let me just run the backtest and check what SL values are generated
asset_key = "EURUSD"
config = ASSET_CONFIGS[asset_key]
pip_size = config["pip_value"]
tier_config = config["tiers"]

# Run with current engine
bt = SymmetryTrapBacktest(
    pip_size=pip_size,
    tier_config=tier_config,
    symbol=asset_key,
    config=config,
)

csv_path = Path(__file__).parent.parent / "data" / f"{asset_key}_M5.csv"
result = bt.run_from_csv(str(csv_path))

# Check first 20 trades for SL placement
print("=== First 20 trades SL analysis ===")
for i, t in enumerate(result.trades[:20]):
    entry = t.entry_price
    sl = t.sl_price
    tp = t.tp_price
    dist_sl = abs(entry - sl) / pip_size
    dist_tp = abs(tp - entry) / pip_size
    sl_dir = "above" if sl > entry else "below" if sl < entry else "AT"
    print(f"  {i+1}. {t.direction:5s} entry={entry:.5f} sl={sl:.5f} ({sl_dir}, {dist_sl:.1f}p) tp={tp:.5f} ({dist_tp:.1f}p) -> {t.result} {t.pnl_pips:+.1f}p")

# Count SL placement direction
above = sum(1 for t in result.trades if t.sl_price > t.entry_price)
below = sum(1 for t in result.trades if t.sl_price < t.entry_price)
at = sum(1 for t in result.trades if t.sl_price == t.entry_price)
print(f"\nSL placement: {above} above entry, {below} below entry, {at} at entry")

# For SHORT trades: SL should be ABOVE entry (loss direction)
short_trades = [t for t in result.trades if t.direction == 'SHORT']
long_trades = [t for t in result.trades if t.direction == 'LONG']

if short_trades:
    short_sl_above = sum(1 for t in short_trades if t.sl_price > t.entry_price)
    short_sl_below = sum(1 for t in short_trades if t.sl_price < t.entry_price)
    print(f"SHORT: {short_sl_above}/{len(short_trades)} SL above entry, {short_sl_below}/{len(short_trades)} SL below entry")
    short_wr = sum(1 for t in short_trades if t.pnl_pips > 0) / len(short_trades) * 100
    print(f"SHORT WR: {short_wr:.1f}%")

if long_trades:
    long_sl_above = sum(1 for t in long_trades if t.sl_price > t.entry_price)
    long_sl_below = sum(1 for t in long_trades if t.sl_price < t.entry_price)
    print(f"LONG: {long_sl_below}/{len(long_trades)} SL below entry, {long_sl_above}/{len(long_trades)} SL above entry")
    long_wr = sum(1 for t in long_trades if t.pnl_pips > 0) / len(long_trades) * 100
    print(f"LONG WR: {long_wr:.1f}%")

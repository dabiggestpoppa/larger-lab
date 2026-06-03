"""Test 3: Run EURUSD with OLD SL = impulse_extreme to reproduce multi-asset results."""
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent / "engines"))
sys.path.insert(0, str(Path(__file__).parent.parent / "configs"))

from asset_configs import ASSET_CONFIGS
from symmetry_trap_backtest import SymmetryTrapBacktest, load_m5_csv, BacktestResult, TradeRecord, compute_stats
from symmetry_trap import SymmetryTrapEngine, Bar, TradeDirection, TradeSignal, EngineState
from datetime import timedelta
import pytz

# Monkey-patch: replace SL placement with old logic
_orig_process_bar = SymmetryTrapEngine.process_bar

def _patched_process_bar(self, bar: Bar):
    # Run original but intercept ENTRY signals and override SL
    # Actually, we need to patch at the point where SL is set
    # Let's copy the original process_bar but change the SL line
    
    # Call original
    signal = _orig_process_bar(self, bar)
    
    # If this was an entry, override SL with impulse_extreme
    if signal and signal.event == "ENTRY":
        self.sl_price = self.impulse_extreme  # OLD logic
        signal.sl_price = self.sl_price
    
    return signal

SymmetryTrapEngine.process_bar = _patched_process_bar

asset_key = "EURUSD"
config = ASSET_CONFIGS[asset_key]
pip_size = config["pip_value"]
tier_config = config["tiers"]

bt = SymmetryTrapBacktest(
    pip_size=pip_size,
    tier_config=tier_config,
    symbol=asset_key,
    config=config,
)

csv_path = Path(__file__).parent.parent / "data" / f"{asset_key}_M5.csv"
result = bt.run_from_csv(str(csv_path))

print(f"EURUSD (OLD SL = impulse_extreme):")
print(f"  Trades: {result.total_trades} | WR: {result.win_rate:.1f}% | PnL: {result.total_pnl_pips:+.1f}p | PF: {result.profit_factor:.2f}")
print(f"  Long: {result.long_trades} tr, {result.long_wr:.1f}% WR")
print(f"  Short: {result.short_trades} tr, {result.short_wr:.1f}% WR")

# SL placement analysis
short_trades = [t for t in result.trades if t.direction == 'SHORT']
long_trades = [t for t in result.trades if t.direction == 'LONG']

if short_trades:
    sl_above = sum(1 for t in short_trades if t.sl_price > t.entry_price)
    sl_below = sum(1 for t in short_trades if t.sl_price < t.entry_price)
    print(f"\nSHORT SL: {sl_above} above entry, {sl_below} below entry (out of {len(short_trades)})")
    
    from collections import Counter
    exits = Counter(t.result for t in short_trades)
    for et, cnt in exits.most_common():
        print(f"  {et}: {cnt} ({cnt/len(short_trades)*100:.1f}%)")

if long_trades:
    sl_above = sum(1 for t in long_trades if t.sl_price > t.entry_price)
    sl_below = sum(1 for t in long_trades if t.sl_price < t.entry_price)
    print(f"\nLONG SL: {sl_below} below entry, {sl_above} above entry (out of {len(long_trades)})")
    
    from collections import Counter
    exits = Counter(t.result for t in long_trades)
    for et, cnt in exits.most_common():
        print(f"  {et}: {cnt} ({cnt/len(long_trades)*100:.1f}%)")

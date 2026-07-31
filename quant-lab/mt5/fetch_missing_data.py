"""
Fetch missing FX pair data from MT5 for backtesting.
Downloads M5 bars for all missing pairs and saves as CSV.
"""
import MetaTrader5 as mt5
import csv
import sys
import time
from datetime import datetime
from pathlib import Path

DATA_DIR = Path(__file__).parent.parent / "data"

# All missing pairs (using .PRO suffix to match existing naming convention)
MISSING_PAIRS = [
    "EURGBP.PRO", "EURJPY.PRO", "EURAUD.PRO", "EURNZD.PRO", "EURCHF.PRO", "EURCAD.PRO",
    "USDCAD.PRO",
    "AUDJPY.PRO", "NZDJPY.PRO", "CADJPY.PRO",
    "AUDNZD.PRO", "AUDCHF.PRO", "AUDCAD.PRO",
    "NZDCHF.PRO", "NZDCAD.PRO",
    "CADCHF.PRO",
    "GBPCAD.PRO",
]

def fetch_and_save(symbol: str, output_name: str = None):
    """Fetch M5 data from MT5 and save as CSV."""
    if output_name is None:
        output_name = symbol.replace(".", "_") + "_M5.csv"
    
    output_path = DATA_DIR / output_name
    
    # Check if already exists
    if output_path.exists() and output_path.stat().st_size > 1000000:
        print(f"  SKIP {symbol}: {output_name} already exists ({output_path.stat().st_size // 1024}KB)")
        return True
    
    # Make sure symbol is visible
    info = mt5.symbol_info(symbol)
    if info is None or not info.visible:
        mt5.symbol_select(symbol, True)
        time.sleep(1)
    
    # Fetch M5 bars — get as many as possible
    print(f"  Fetching {symbol} M5 bars...")
    rates = mt5.copy_rates_from_pos(symbol, mt5.TIMEFRAME_M5, 0, 500000)
    
    if rates is None or len(rates) == 0:
        print(f"  FAIL {symbol}: no data returned ({mt5.last_error()})")
        return False
    
    print(f"  Got {len(rates)} bars for {symbol}")
    
    # Write CSV
    with open(output_path, "w", newline="") as f:
        writer = csv.writer(f)
        writer.writerow(["time", "open", "high", "low", "close", "volume", "spread"])
        for r in rates:
            t = datetime.fromtimestamp(int(r["time"])).strftime("%Y-%m-%dT%H:%M:%S")
            writer.writerow([
                t,
                r["open"],
                r["high"],
                r["low"],
                r["close"],
                r["tick_volume"],
                r["spread"],
            ])
    
    size_kb = output_path.stat().st_size // 1024
    print(f"  SAVED {output_name}: {len(rates)} bars, {size_kb}KB")
    return True


def main():
    if not mt5.initialize():
        print("MT5 init failed:", mt5.last_error())
        sys.exit(1)
    
    info = mt5.account_info()
    print(f"MT5 connected: {info.login} @ {info.server}")
    print(f"Fetching {len(MISSING_PAIRS)} missing pairs...")
    print()
    
    ok = 0
    fail = 0
    skip = 0
    
    for sym in MISSING_PAIRS:
        # Check if already exists with data
        expected_name = sym.replace(".", "_") + "_M5.csv"
        expected_path = DATA_DIR / expected_name
        if expected_path.exists() and expected_path.stat().st_size > 1000000:
            print(f"  SKIP {sym}: already exists")
            skip += 1
            continue
        
        result = fetch_and_save(sym)
        if result:
            ok += 1
        else:
            fail += 1
        time.sleep(0.5)  # Rate limit
    
    print()
    print(f"Done: {ok} fetched, {fail} failed, {skip} skipped")
    mt5.shutdown()


if __name__ == "__main__":
    main()

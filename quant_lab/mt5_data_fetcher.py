"""
CEREBUS FX v4.0 — MT5 Data Fetcher
====================================
Pulls M5 historical data directly from MT5 via Python API.
No more manual CSV exports needed.

Usage:
    python mt5_data_fetcher.py --symbol USDCHF.PRO --years 3 --output data/usdchf_m5.csv
    python mt5_data_fetcher.py --symbol EURUSD.PRO --years 2
    python mt5_data_fetcher.py --all  # Fetch all 20 assets from config registry
"""

import sys
import os
import csv
import argparse
from datetime import datetime, timedelta
from pathlib import Path

# Setup paths for config import
sys.path.insert(0, os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", "configs"))

try:
    import MetaTrader5 as mt5
except ImportError:
    print("ERROR: MetaTrader5 package not installed. Run: pip install MetaTrader5")
    sys.exit(1)


def get_mt5_exe_path():
    """Find MT5 terminal executable."""
    common_paths = [
        r"C:\Program Files\Ox Securities MetaTrader 5\terminal64.exe",
        r"C:\Program Files\MetaTrader 5\terminal64.exe",
        r"C:\Program Files (x86)\MetaTrader 5\terminal64.exe",
    ]
    for p in common_paths:
        if os.path.exists(p):
            return p
    return None


def connect_mt5():
    """Initialize MT5 connection. Auto-launch if needed."""
    if mt5.initialize():
        print(f"MT5 connected. Account: {mt5.account_info().login}")
        return True

    # Try launching
    exe = get_mt5_exe_path()
    if exe:
        import subprocess, time
        print(f"Launching MT5: {exe}")
        subprocess.Popen([exe])
        time.sleep(10)
        if mt5.initialize():
            print(f"MT5 connected after launch. Account: {mt5.account_info().login}")
            return True

    print(f"ERROR: MT5 init failed: {mt5.last_error()}")
    return False


def fetch_symbol_data(symbol: str, years: int = 3, output_dir: str = "data"):
    """
    Fetch M5 historical data for a symbol from MT5.

    Args:
        symbol: MT5 symbol name (e.g., "USDCHF.PRO")
        years: How many years of history to fetch
        output_dir: Directory to save CSV files

    Returns:
        Output file path or None on failure
    """
    # Find the symbol in MT5
    mt5_symbol = symbol
    symbols = mt5.symbols_get()
    symbol_names = [s.name for s in symbols]

    if mt5_symbol not in symbol_names:
        # Try variants
        for variant in [symbol, symbol + ".PRO", symbol + ".RAW", symbol + ".STP"]:
            if variant in symbol_names:
                mt5_symbol = variant
                break
        else:
            print(f"WARNING: {symbol} not found in MT5 ({len(symbol_names)} symbols available)")
            print(f"  Similar: {[s for s in symbol_names if symbol.replace('.PRO','') in s][:5]}")
            return None

    # Enable symbol in Market Watch
    if not mt5.symbol_select(mt5_symbol, True):
        print(f"WARNING: Could not select {mt5_symbol} in Market Watch")

    # Calculate date range
    end_date = datetime.now()
    start_date = end_date - timedelta(days=years * 365)

    print(f"Fetching {mt5_symbol} M5: {start_date.strftime('%Y-%m-%d')} → {end_date.strftime('%Y-%m-%d')} ({years} years)")

    # Fetch M5 rates
    rates = mt5.copy_rates_range(mt5_symbol, mt5.TIMEFRAME_M5, start_date, end_date)

    if rates is None or len(rates) == 0:
        print(f"ERROR: No data returned for {mt5_symbol}. Error: {mt5.last_error()}")
        return None

    print(f"  Retrieved {len(rates):,} M5 bars")

    # Save to CSV
    os.makedirs(output_dir, exist_ok=True)
    safe_name = mt5_symbol.replace(".", "_")
    output_path = os.path.join(output_dir, f"{safe_name}_M5_{start_date.strftime('%Y%m%d')}_{end_date.strftime('%Y%m%d')}.csv")

    with open(output_path, "w", newline="", encoding="utf-8") as f:
        writer = csv.writer(f)
        writer.writerow(["timestamp", "open", "high", "low", "close"])
        for bar in rates:
            dt = datetime.fromtimestamp(bar["time"])
            writer.writerow([
                dt.strftime("%Y-%m-%d %H:%M:%S"),
                bar["open"],
                bar["high"],
                bar["low"],
                bar["close"]
            ])

    file_size = os.path.getsize(output_path) / (1024 * 1024)
    print(f"  Saved: {output_path} ({file_size:.1f} MB)")
    return output_path


def fetch_all_assets(years: int = 3, output_dir: str = "data"):
    """Fetch M5 data for all configured assets."""
    from asset_configs import ASSET_CONFIGS

    # Map config keys to MT5 symbol names
    symbol_map = {
        "EURUSD": "EURUSD.PRO",
        "GBPUSD": "GBPUSD.PRO",
        "USDCHF": "USDCHF.PRO",
        "USDJPY": "USDJPY.PRO",
        "AUDUSD": "AUDUSD.PRO",
        "NZDUSD": "NZDUSD.PRO",
        "CHFJPY": "CHFJPY.PRO",
        "GBPJPY": "GBPJPY.PRO",
        "GBPAUD": "GBPAUD.PRO",
        "GBPNZD": "GBPNZD.PRO",
        "GBPCHF": "GBPCHF.PRO",
        "XAUUSD": "XAUUSD.PRO",
        "XAGUSD": "XAGUSD.PRO",
        "BTCUSD": "BTCUSD",
        "ETHUSD": "ETHUSD",
        "NAS100": "NAS100",
        "US500": "US500",
        "DE30": "DE30",
        "FR40": "FR40",
        "HK50": "HK50",
    }

    results = {}
    for key, mt5_sym in symbol_map.items():
        print(f"\n--- {key} ({mt5_sym}) ---")
        path = fetch_symbol_data(mt5_sym, years=years, output_dir=output_dir)
        results[key] = path

    print(f"\n=== FETCH COMPLETE ===")
    success = sum(1 for v in results.values() if v is not None)
    print(f"Success: {success}/{len(symbol_map)} assets")
    return results


def main():
    parser = argparse.ArgumentParser(description="CEREBUS FX v4.0 — MT5 Data Fetcher")
    parser.add_argument("--symbol", type=str, help="MT5 symbol (e.g., USDCHF.PRO)")
    parser.add_argument("--years", type=int, default=3, help="Years of history (default: 3)")
    parser.add_argument("--output", type=str, default="data", help="Output directory (default: data/)")
    parser.add_argument("--all", action="store_true", help="Fetch all configured assets")
    args = parser.parse_args()

    if not connect_mt5():
        sys.exit(1)

    try:
        if args.all:
            fetch_all_assets(years=args.years, output_dir=args.output)
        elif args.symbol:
            fetch_symbol_data(args.symbol, years=args.years, output_dir=args.output)
        else:
            print("Usage: python mt5_data_fetcher.py --symbol USDCHF.PRO --years 3")
            print("       python mt5_data_fetcher.py --all --years 3")
    finally:
        mt5.shutdown()


if __name__ == "__main__":
    main()

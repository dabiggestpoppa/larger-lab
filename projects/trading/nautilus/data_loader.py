"""
CSV Data Loader for Nautilus Trader Backtesting.
Supports forex.com and OX Securities CSV formats.
Handles all 13 CEREBUS pairs across multiple timeframes.
"""
import os
import re
import glob
import pandas as pd
from datetime import datetime
from decimal import Decimal

from nautilus_trader.model.data import Bar, BarSpecification, BarType
from nautilus_trader.model.enums import AggregationSource, BarAggregation
from nautilus_trader.model.identifiers import InstrumentId
from nautilus_trader.model.objects import Price, Quantity

from .config import DOWNLOADS_DIR, DATA_DIR

# Symbol Mapping
SYMBOL_MAP = {
    "EURUSD": "EUR/USD", "GBPUSD": "GBP/USD", "USDJPY": "USD/JPY",
    "USDCHF": "USD/CHF", "AUDUSD": "AUD/USD", "NZDUSD": "NZD/USD",
    "USDCAD": "USD/CAD", "EURGBP": "EUR/GBP", "EURJPY": "EUR/JPY",
    "GBPJPY": "GBP/JPY", "CHFJPY": "CHF/JPY", "XAUUSD": "XAU/USD",
    "US500": "US500", "USTEC100": "USTEC100", "DE30": "DE30",
    "FR40": "FR40", "HK50": "HK50",
}

FILENAME_SYMBOL_MAP = {
    "EURUSD": "EURUSD", "EURUSD.PRO": "EUR/USD",
    "GBPUSD": "GBPUSD", "USDCHF": "USDCHF", "USDJPY": "USDJPY",
    "AUDUSD": "AUDUSD", "NZDUSD": "NZDUSD", "USDCAD": "USDCAD",
    "CHFJPY": "CHFJPY", "US500": "US500", "USTEC100": "USTEC100",
    "DE30": "DE30", "FR40": "FR40", "HK50": "HK50",
    "XAUUSD": "XAUUSD",
}


def _fix_ox_line_wrapping(lines):
    """Fix OX Securities CSV where CLOSE value wraps to next line."""
    fixed = []
    i = 0
    while i < len(lines):
        line = lines[i]
        if i + 1 < len(lines) and re.match(r'^\d{4}\.\d{2}\.\d{2}', lines[i + 1]):
            parts = line.strip().split()
            if len(parts) >= 8:
                fixed.append(line)
            else:
                merged = line.strip() + " " + lines[i + 1].strip()
                fixed.append(merged)
                i += 1
        else:
            fixed.append(line)
        i += 1
    return fixed


def _parse_csv(filepath):
    """Parse forex.com or OX Securities CSV into DataFrame."""
    with open(filepath, 'r', encoding='utf-8', errors='ignore') as f:
        raw_lines = f.readlines()

    data_lines = [l for l in raw_lines[1:] if l.strip()]
    data_lines = _fix_ox_line_wrapping(data_lines)

    records = []
    for line in data_lines:
        parts = line.strip().split()
        if len(parts) < 7:
            continue
        try:
            date_str, time_str = parts[0], parts[1]
            open_val, high_val = float(parts[2]), float(parts[3])
            low_val, close_val = float(parts[4]), float(parts[5])
            tick_vol = int(parts[6]) if len(parts) > 6 else 0
            vol = int(parts[7]) if len(parts) > 7 else 0
            spread = int(parts[8]) if len(parts) > 8 else 0
            ts = datetime.strptime(f"{date_str} {time_str}", "%Y.%m.%d %H:%M:%S")
            records.append({
                "timestamp": ts, "open": open_val, "high": high_val,
                "low": low_val, "close": close_val,
                "tick_volume": tick_vol, "volume": vol, "spread": spread,
            })
        except (ValueError, IndexError):
            continue

    if not records:
        return pd.DataFrame()
    df = pd.DataFrame(records)
    df.set_index("timestamp", inplace=True)
    df.sort_index(inplace=True)
    return df


def discover_files(downloads_dir=None):
    """Discover all CSV files. Returns dict: {symbol_name: filepath}."""
    if downloads_dir is None:
        downloads_dir = DOWNLOADS_DIR
    files = {}
    for filepath in glob.glob(os.path.join(downloads_dir, "*.csv")):
        name = os.path.splitext(os.path.basename(filepath))[0]
        symbol = name.split("_")[0].replace("!", "")
        std_name = FILENAME_SYMBOL_MAP.get(symbol, symbol)
        if std_name in files:
            if "_M5_" in filepath or "_M5" in filepath:
                files[std_name] = filepath
        else:
            files[std_name] = filepath
    return files


def load_csv_as_nautilus_bars(filepath, instrument_id_str, bar_aggregation=BarAggregation.MINUTE, step=5):
    """Load CSV and convert to Nautilus Bar objects."""
    df = _parse_csv(filepath)
    if df.empty:
        print(f"  WARNING: No data parsed from {filepath}")
        return []
    print(f"  Loaded {len(df)} rows from {os.path.basename(filepath)}")
    print(f"  Range: {df.index[0]} -> {df.index[-1]}")

    instrument_id = InstrumentId.from_str(instrument_id_str)
    bar_spec = BarSpecification(step, bar_aggregation, AggregationSource.EXTERNAL)
    bar_type = BarType(instrument_id, bar_spec, AggregationSource.EXTERNAL)

    bars = []
    for timestamp, row in df.iterrows():
        try:
            prec = 2 if row["close"] > 1000 else 5
            bar = Bar(
                bar_type=bar_type,
                open=Price(float(row["open"]), prec),
                high=Price(float(row["high"]), prec),
                low=Price(float(row["low"]), prec),
                close=Price(float(row["close"]), prec),
                volume=Quantity(int(row.get("tick_volume", 1000)), 0),
                ts_event=int(timestamp.timestamp() * 1e9),
                ts_init=int(timestamp.timestamp() * 1e9),
            )
            bars.append(bar)
        except Exception:
            pass
    print(f"  Converted {len(bars)} Nautilus bars")
    return bars


if __name__ == "__main__":
    files = discover_files()
    print(f"Discovered {len(files)} data files:")
    for sym, path in files.items():
        df = _parse_csv(path)
        print(f"  {sym:15s} -> {len(df):6d} rows | {df.index[0]} -> {df.index[-1]}")
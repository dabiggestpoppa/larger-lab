"""
Oanda data adapter for Nautilus Trader.
Fetches historical FX data from Oanda API for backtesting.
Supports: FX pairs, commodities (XAU/USD, XAG/USD), indices.

Usage:
    python -m nautilus.oanda_adapter --instrument EUR_USD --granularity D --count 5000
"""
import argparse
import os
import sys
from datetime import datetime, timedelta

import numpy as np
import pandas as pd
import requests
from dotenv import load_dotenv

load_dotenv()

OANDA_API_KEY = os.getenv("OANDA_API_KEY", "")
OANDA_ACCOUNT_ID = os.getenv("OANDA_ACCOUNT_ID", "")
OANDA_ENVIRONMENT = os.getenv("OANDA_ENVIRONMENT", "practice")

# Oanda API endpoints
OANDA_URLS = {
    "practice": "https://api-fxpractice.oanda.com",
    "live": "https://api-fxtrade.oanda.com",
}

# Map common symbols to Oanda instrument format
SYMBOL_MAP = {
    "EUR/USD": "EUR_USD",
    "GBP/USD": "GBP_USD",
    "USD/JPY": "USD_JPY",
    "USD/CHF": "USD_CHF",
    "USD/CAD": "USD_CAD",
    "AUD/USD": "AUD_USD",
    "NZD/USD": "NZD_USD",
    "EUR/GBP": "EUR_GBP",
    "EUR/JPY": "EUR_JPY",
    "GBP/JPY": "GBP_JPY",
    "XAU/USD": "XAU_USD",
    "XAG/USD": "XAG_USD",
    "US30": "US30_USD",
    "SPX500": "SPX500_USD",
    "NAS100": "NAS100_USD",
    "UK100": "UK100_USD",
    "DE30": "DE30_EUR",
    "JP225": "JP225_USD",
}

# Valid Oanda granularities
GRANULARITIES = [
    "S5", "S10", "S15", "S30",  # Seconds
    "M1", "M2", "M3", "M4", "M5", "M10", "M15", "M30",  # Minutes
    "H1", "H2", "H3", "H4", "H6", "H8", "H12",  # Hours
    "D", "W", "M",  # Day, Week, Month
]


def get_oanda_url():
    """Get the appropriate Oanda API URL."""
    return OANDA_URLS.get(OANDA_ENVIRONMENT, OANDA_URLS["practice"])


def get_headers():
    """Get Oanda API headers."""
    return {
        "Authorization": f"Bearer {OANDA_API_KEY}",
        "Content-Type": "application/json",
    }


def fetch_candles(
    instrument: str,
    granularity: str = "D",
    count: int = 500,
    from_date: str = None,
    to_date: str = None,
    price: str = "MBA",  # M=mid, B=bid, A=ask
) -> pd.DataFrame:
    """
    Fetch candle data from Oanda API.

    Args:
        instrument: Oanda instrument name (e.g., "EUR_USD")
        granularity: Candle granularity (e.g., "M1", "H1", "D")
        count: Number of candles to fetch (max 5000)
        from_date: Start date (ISO format)
        to_date: End date (ISO format)
        price: Price type (M=mid, B=bid, A=ask, MBA=all)

    Returns:
        DataFrame with columns: timestamp, open, high, low, close, volume, spread
    """
    if not OANDA_API_KEY or "your_" in OANDA_API_KEY:
        raise ValueError("OANDA_API_KEY not set in .env file")

    url = f"{get_oanda_url()}/v3/instruments/{instrument}/candles"
    params = {
        "granularity": granularity,
        "price": price,
    }

    if from_date and to_date:
        params["from"] = from_date
        params["to"] = to_date
    else:
        params["count"] = min(count, 5000)

    response = requests.get(url, headers=get_headers(), params=params)
    response.raise_for_status()
    data = response.json()

    candles = data.get("candles", [])
    if not candles:
        print(f"⚠️  No data returned for {instrument}")
        return pd.DataFrame()

    records = []
    for candle in candles:
        if not candle.get("complete", True):
            continue

        record = {"timestamp": candle["time"]}

        # Extract mid prices (or bid/ask if requested)
        for price_type in ["mid", "bid", "ask"]:
            if price_type in candle:
                prefix = "" if price_type == "mid" else f"{price_type}_"
                record[f"{prefix}open"] = float(candle[price_type]["o"])
                record[f"{prefix}high"] = float(candle[price_type]["h"])
                record[f"{prefix}low"] = float(candle[price_type]["l"])
                record[f"{prefix}close"] = float(candle[price_type]["c"])

        record["volume"] = int(candle["volume"])
        record["complete"] = candle["complete"]
        records.append(record)

    df = pd.DataFrame(records)
    df["timestamp"] = pd.to_datetime(df["timestamp"])
    df.set_index("timestamp", inplace=True)
    df.sort_index(inplace=True)

    # Calculate spread if bid/ask available
    if "ask_close" in df.columns and "bid_close" in df.columns:
        df["spread"] = df["ask_close"] - df["bid_close"]
        df["spread_pips"] = df["spread"] * 10000  # For FX pairs
        if instrument.endswith("JPY"):
            df["spread_pips"] = df["spread"] * 100  # JPY pairs

    return df


def fetch_multiple_instruments(
    instruments: list,
    granularity: str = "D",
    count: int = 500,
) -> dict:
    """Fetch data for multiple instruments."""
    results = {}
    for symbol in instruments:
        oanda_symbol = SYMBOL_MAP.get(symbol, symbol.replace("/", "_"))
        print(f"  Fetching {symbol} ({oanda_symbol})...")
        try:
            df = fetch_candles(oanda_symbol, granularity, count)
            results[symbol] = df
            print(f"    ✅ {len(df)} candles")
        except Exception as e:
            print(f"    ❌ Error: {e}")
            results[symbol] = pd.DataFrame()
    return results


def save_to_csv(df: pd.DataFrame, instrument: str, granularity: str, data_dir: str = None):
    """Save fetched data to CSV for Nautilus Trader."""
    import os
    from pathlib import Path

    if data_dir is None:
        data_dir = os.path.join(os.path.expanduser("~"), "quant-lab", "data", "oanda")

    Path(data_dir).mkdir(parents=True, exist_ok=True)

    safe_name = instrument.replace("/", "_").replace(" ", "_")
    filename = f"{safe_name}_{granularity}.csv"
    filepath = os.path.join(data_dir, filename)

    df.to_csv(filepath)
    print(f"  💾 Saved to {filepath}")
    return filepath


def convert_to_nautilus_bars(df: pd.DataFrame, instrument_id: str, bar_spec: str):
    """
    Convert Oanda candle data to Nautilus Trader Bar objects.
    This bridges Oanda data into the Nautilus backtesting engine.
    """
    from nautilus_trader.model.data import Bar, BarSpecification, BarType
    from nautilus_trader.model.enums import AggregationSource, BarAggregation, PriceType
    from nautilus_trader.model.identifiers import InstrumentId, Venue
    from nautilus_trader.model.objects import Price, Quantity

    bars = []
    for timestamp, row in df.iterrows():
        bar = Bar(
            bar_type=BarType(
                instrument_id=InstrumentId.from_str(instrument_id),
                bar_spec=BarSpecification.from_str(bar_spec),
                aggregation_source=AggregationSource.EXTERNAL,
            ),
            open=Price(row["open"], 5),
            high=Price(row["high"], 5),
            low=Price(row["low"], 5),
            close=Price(row["close"], 5),
            volume=Quantity(int(row["volume"]), 0),
            ts_event=int(timestamp.timestamp() * 1e9),
            ts_init=int(timestamp.timestamp() * 1e9),
        )
        bars.append(bar)
    return bars


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Fetch Oanda data for Nautilus Trader")
    parser.add_argument("--instrument", type=str, required=True, help="Instrument (e.g., EUR_USD)")
    parser.add_argument("--granularity", type=str, default="D", help="Candle granularity")
    parser.add_argument("--count", type=int, default=500, help="Number of candles")
    parser.add_argument("--save", action="store_true", help="Save to CSV")
    parser.add_argument("--output-dir", type=str, default=None, help="Output directory")

    args = parser.parse_args()

    df = fetch_candles(args.instrument, args.granularity, args.count)
    print(f"\nFetched {len(df)} candles for {args.instrument}")
    print(df.head())
    print(df.tail())

    if args.save:
        save_to_csv(df, args.instrument, args.granularity, args.output_dir)

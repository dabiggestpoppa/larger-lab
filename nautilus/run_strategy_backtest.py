"""
Unified backtest runner for CEREBUS strategies.
Runs a specific strategy from nautilus/strategies/ on available data.
"""
import sys
import json
from pathlib import Path
from datetime import datetime

sys.path.insert(0, str(Path(__file__).parent))

from data_loader import _parse_csv

DOWNLOADS_DIR = Path(r"C:\Users\wifik\Downloads")
RESULTS_DIR = Path(r"C:\Users\wifik\Desktop\projects\larger-lab\nautilus\results")
RESULTS_DIR.mkdir(exist_ok=True)


def get_data(pair="EURUSD"):
    """Load data for a pair."""
    filename = f"{pair}!_M5_202301020000_202605061250.csv"
    filepath = DOWNLOADS_DIR / filename
    if filepath.exists():
        df = _parse_csv(filepath)
        if len(df) > 0:
            print(f"  Loaded {len(df):,} bars for {pair} ({df.index[0]} -> {df.index[-1]})")
            return df
    print(f"  No data found for {pair}")
    return None


def run_cascade_backtest():
    """Run P90 Cascade strategy."""
    from strategies.p90_cascade import P90CascadeStrategy
    df = get_data("EURUSD")
    if df is None:
        return None
    strategy = P90CascadeStrategy()
    results = strategy.run_backtest(df, pair="EUR/USD")
    return results


def run_combo_backtest():
    """Run P90 Cascade + 45-Min Combo strategy."""
    from strategies.p90_cascade_combo import P90CascadeComboStrategy
    df = get_data("EURUSD")
    if df is None:
        return None
    strategy = P90CascadeComboStrategy()
    results = strategy.run_backtest(df, pair="EUR/USD")
    return results


def run_deep_mean_reversion_backtest():
    """Run Deep Mean Reversion strategy."""
    from strategies.deep_mean_reversion import DeepMeanReversionStrategy, DeepMeanReversionConfig
    df = get_data("EURUSD")
    if df is None:
    # Use the pandas-based approach since Nautilus native strategy needs engine
    print("  Using pandas-based backtest for Deep Mean Reversion")
    return run_deep_mean_reversion_pandas(df)


def run_deep_mean_reversion_pandas(df):
    """Pandas-based Deep Mean Reversion backtest."""
    if df is None or len(df) < 500:
        return {"error": "No data"}

    df = df.copy()
    df['est_hour'] = (df.index.hour - 5 + 24) % 24
    df['date'] = df.index.date

    # State
    asian_high = None
    asian_low = None
    ar_pips = None
    activation_level = None
    direction = 0
    position = 0
    entry_price = 0
    pnl = 0
    trades = 0
    sl_price = 0
    tp1_price = 0
    tp2_price = 0
    last_date = None

    for i in range(50, len(df) - 1):
        row = df.iloc[i]
        ts = df.index[i]
        est_h = row['est_hour']
        date = row['date']
        o, h, l, c = row['open'], row['high'], row['low'], row['close']

        # New day reset
        if date != last_date:
            if position > 0:
                pnl += (c - entry_price) * direction * 0.1 * 10000
                trades += 1
                position = 0
            asian_high = None
            asian_low = None
            ar_pips = None
            activation_level = None
            direction = 0
            position = 0
            last_date = date

        # Asian range calc (7PM-3AM EST = 0-8 UTC)
        if est_h >= 19 or est_h < 3:
            if asian_high is None:
                asian_high = h
                asian_low = l
            else:
                asian_high = max(asian_high, h)
                asian_low = min(asian_low, l)
            if est_h == 2 and asian_high is not None:
                ar_pips = (asian_high - asian_low) * 10000
            continue

        if ar_pips is None or ar_pips > 45:
            continue

        # Hard exit at 12PM EST = 17 UTC
        if est_h >= 17:
            if position > 0:
                pnl += (c - entry_price) * direction * 0.1 * 10000
                trades += 1
                position = 0
            continue

        # Manage position
        if position > 0:
            # SL hit
            if direction > 0 and l <= sl_price:
                pnl += (sl_price - entry_price) * 0.1 * 10000
                position = 0
                trades += 1
                continue
            elif direction < 0 and h >= sl_price:
                pnl += (entry_price - sl_price) * 0.1 * 10000
                position = 0
                trades += 1
                continue

            # TP1: return to activation level
            if direction > 0 and l <= tp1_price:
                pnl += (tp1_price - entry_price) * 0.1 * 10000
                position = 0
                trades += 1
                continue
            elif direction < 0 and h >= tp1_price:
                pnl += (entry_price - tp1_price) * 0.1 * 10000
                position = 0
                trades += 1
                continue

        # Entry: look for 168% or 200% extension
        if position == 0 and 2 <= est_h < 17 and ar_pips > 0:
            # Need activation level first (P90 close)
            if activation_level is None:
                # Check for P90 candle
                body_pips = abs(c - o) * 10000
                if 2 <= est_h < 4:
                    thresh = 4.1
                elif 4 <= est_h < 6:
                    thresh = 4.6
                elif 6 <= est_h < 8:
                    thresh = 4.6
                elif 8 <= est_h < 10:
                    thresh = 5.9
                elif 10 <= est_h < 11:
                    thresh = 6.2
                else:
                    thresh = 6.2

                if body_pips >= thresh:
                    activation_level = c
                    direction = 1 if c > o else -1
                continue

            # Check for 168% extension touch
            extension = (c - activation_level) * direction * 10000
            stall_zone = ar_pips * 1.68
            deep_state = ar_pips * 2.0
            kill_switch = ar_pips * 2.2

            if extension >= stall_zone and extension < kill_switch:
                # Enter limit order at deep state (200%)
                deep_price = activation_level + direction * (deep_state / 10000)
                if (direction > 0 and l <= deep_price) or (direction < 0 and h >= deep_price):
                    position = 1
                    entry_price = deep_price
                    sl_price = activation_level + direction * (kill_switch / 10000)
                    tp1_price = activation_level  # Return to 0%
                    tp2_price = activation_level - direction * (ar_pips * 0.50 / 10000)

    total_return = (pnl / 10000) * 100
    return {
        "strategy": "Deep_Mean_Reversion",
        "pair": "EUR/USD",
        "trades": trades,
        "pnl": round(pnl, 2),
        "return_pct": round(total_return, 2),
    }


if __name__ == "__main__":
    import argparse
    parser = argparse.ArgumentParser()
    parser.add_argument("--strategy", type=str, default="cascade",
                        choices=["cascade", "combo", "deep_mean", "all"])
    args = parser.parse_args()

    strategies = {
        "cascade": run_cascade_backtest,
        "combo": run_combo_backtest,
        "deep_mean": run_deep_mean_reversion_backtest,
    }

    if args.strategy == "all":
        to_run = list(strategies.values())
    else:
        to_run = [strategies[args.strategy]]

    all_results = []
    for func in to_run:
        print(f"\n{'='*60}")
        print(f"Running {func.__name__}...")
        result = func()
        if result:
            all_results.append(result)
            print(f"\nResults:")
            for k, v in result.items():
                if k != "trades":
                    print(f"  {k}: {v}")

    # Save results
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    results_file = RESULTS_DIR / f"strategy_backtest_{timestamp}.json"
    with open(results_file, 'w') as f:
        json.dump(all_results, f, indent=2, default=str)
    print(f"\nResults saved to {results_file}")

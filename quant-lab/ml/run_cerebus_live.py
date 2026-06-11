"""
CEREBUS Neuro-Symbolic Scanner — LIVE MT5 Edition
===================================================
Pulls live M15 candle data from MT5, computes CEREBUS features,
runs the Guardian (XGBoost + Orchestrator), and sends alerts to Telegram.
Does NOT execute trades — signals only.

Usage:
    python run_cerebus_live.py                    # Scan EURUSD + BTCUSD (default)
    python run_cerebus_live.py --symbols EURUSD   # Scan specific symbols
    python run_cerebus_live.py --interval 60      # Scan interval in seconds (default: 300)
    python run_cerebus_live.py --once             # Single scan and exit
    python run_cerebus_live.py --dry-run          # Scan without sending Telegram alerts
"""
import os
import sys
import time
import argparse
import logging
from pathlib import Path
from datetime import datetime, timezone

# Load .env
env_path = Path(__file__).resolve().parent.parent.parent / ".env"
if env_path.exists():
    import re
    content = env_path.read_text(encoding="utf-8")
    # Handle both newline-delimited and single-line formats
    lines = content.splitlines()
    if len(lines) <= 1:
        pairs = re.findall(r'([A-Z_][A-Z0-9_]*)=(.*?)(?=(?:[A-Z_][A-Z0-9_]*=|$))', content, re.DOTALL)
        lines = [f"{k}={v}" for k, v in pairs]
    for line in lines:
        line = line.strip().strip("\r")
        if line and not line.startswith("#") and "=" in line:
            k, v = line.split("=", 1)
            k = k.strip()
            v = v.strip().strip('"').strip("'")
            if k:
                os.environ.setdefault(k, v)

os.environ.setdefault("PYTHONIOENCODING", "utf-8")

import numpy as np
import pandas as pd
import MetaTrader5 as mt5

sys.path.insert(0, str(Path(__file__).parent))
from phase4_guardian.guardian import GuardianPipeline, GuardianConfig

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(name)s] %(levelname)s: %(message)s",
    handlers=[logging.StreamHandler(sys.stdout)],
)
logger = logging.getLogger("cerebus.live")

# ─── CONFIG ────────────────────────────────────────────────────────
DEFAULT_SYMBOLS = ["EURUSD", "BTCUSD"]
SCAN_INTERVAL = 300  # 5 minutes (M15 candle close)
LOOKBACK_BARS = 500  # Number of M15 bars to fetch for feature computation

MODEL_PATH = Path(__file__).parent / "models" / "regime_classifier_full.pkl"
RAG_STORE_PATH = Path(__file__).parent / "data" / "rag_chroma"
FEATURES_DIR = Path(__file__).parent / "data" / "full_features_v2"


def get_pip_size(symbol: str) -> float:
    """Return pip size for a symbol."""
    s = symbol.upper()
    if "JPY" in s:
        return 0.01
    if "XAU" in s or "GOLD" in s:
        return 0.1
    if "XAG" in s or "SILVER" in s:
        return 0.001
    if any(x in s for x in ["BTC", "ETH", "US500", "NAS100", "DE30", "FR40", "HK50", "US30"]):
        return 1.0
    return 0.0001


def fetch_live_candles(symbol: str, num_bars: int = LOOKBACK_BARS) -> pd.DataFrame:
    """
    Fetch recent M15 candles from MT5.
    Returns DataFrame with columns: time, open, high, low, close, volume
    """
    if not mt5.initialize():
        logger.error("MT5 initialization failed")
        return pd.DataFrame()

    try:
        # Try the symbol as-is, then with .PRO suffix
        rates = mt5.copy_rates_from_pos(symbol, mt5.TIMEFRAME_M15, 0, num_bars)
        if rates is None or len(rates) == 0:
            rates = mt5.copy_rates_from_pos(f"{symbol}.PRO", mt5.TIMEFRAME_M15, 0, num_bars)
        if rates is None or len(rates) == 0:
            logger.warning(f"No candle data for {symbol}")
            return pd.DataFrame()

        df = pd.DataFrame(rates)
        df['time'] = pd.to_datetime(df['time'], unit='s', utc=True)
        df = df.set_index('time')
        df = df.rename(columns={'tick_volume': 'volume'})
        df = df[['open', 'high', 'low', 'close', 'volume']]

        logger.info(f"Fetched {len(df)} M15 candles for {symbol} (last: {df.index[-1]})")
        return df
    except Exception as e:
        logger.error(f"Error fetching candles for {symbol}: {e}")
        return pd.DataFrame()


def compute_live_features(df: pd.DataFrame, symbol: str) -> pd.DataFrame:
    """
    Compute CEREBUS features from live candle data.
    This is a streamlined version of the full feature engine,
    computing only the features needed by the XGBoost model.
    """
    if df.empty or len(df) < 50:
        logger.warning(f"Insufficient data for {symbol}: {len(df)} bars")
        return pd.DataFrame()

    pip_size = get_pip_size(symbol)
    df = df.copy()

    # ── Basic price features ──
    df['body'] = df['close'] - df['open']
    df['range'] = df['high'] - df['low']
    df['body_ratio'] = df['body'] / df['range'].replace(0, np.nan)
    df['price_range_from_open'] = df['close'] - df['open']

    # ── Time features ──
    df['hour_est'] = df.index.hour - 5  # Convert UTC to EST
    df['hour_est'] = df['hour_est'].apply(lambda x: x + 24 if x < 0 else x)
    df['day_of_week'] = df.index.dayofweek
    df['is_monday'] = (df.index.dayofweek == 0).astype(int)
    df['is_friday'] = (df.index.dayofweek == 4).astype(int)
    df['is_wednesday'] = (df.index.dayofweek == 2).astype(int)
    df['is_wednesday_pm'] = ((df.index.dayofweek == 2) & (df.index.hour >= 12)).astype(int)
    df['minutes_to_12pm_est'] = ((12 - df['hour_est']) % 24) * 60

    # ── Session features ──
    df['is_asian'] = ((df.index.hour >= 0) & (df.index.hour < 8)).astype(int)
    df['is_london'] = ((df.index.hour >= 7) & (df.index.hour < 16)).astype(int)
    df['is_ny'] = ((df.index.hour >= 12) & (df.index.hour < 21)).astype(int)

    # ── Asian Range (00:00-08:00 UTC = 7pm-3am EST) ──
    df['asian_high'] = np.nan
    df['asian_low'] = np.nan
    df['asian_range_pips'] = np.nan

    for date in df.index.date:
        day_mask = df.index.date == date
        asian_mask = day_mask & (df.index.hour >= 0) & (df.index.hour < 8)
        asian_bars = df.loc[asian_mask]
        if len(asian_bars) > 0:
            ah = asian_bars['high'].max()
            al = asian_bars['low'].min()
            df.loc[day_mask, 'asian_high'] = ah
            df.loc[day_mask, 'asian_low'] = al
            df.loc[day_mask, 'asian_range_pips'] = (ah - al) / pip_size

    # ── MLR (Monday London Range: 07:00-15:00 UTC) ──
    df['mlr_high'] = np.nan
    df['mlr_low'] = np.nan
    df['mlr_close'] = np.nan
    df['mlr_range'] = np.nan
    df['mlr_mid'] = np.nan
    df['mlr_range_pips'] = np.nan
    df['bias'] = 'UNKNOWN'
    df['hours_since_mlr'] = np.nan

    for week_start in pd.date_range(df.index.min().normalize(), df.index.max().normalize(), freq='W-MON'):
        week_mask = (df.index >= week_start) & (df.index < week_start + pd.Timedelta(days=7))
        monday_mask = week_mask & (df.index.dayofweek == 0) & (df.index.hour >= 7) & (df.index.hour < 15)
        monday_bars = df.loc[monday_mask]

        if len(monday_bars) > 0:
            mlr_h = monday_bars['high'].max()
            mlr_l = monday_bars['low'].min()
            mlr_c = monday_bars['close'].iloc[-1]
            mlr_range = mlr_h - mlr_l
            mlr_mid = mlr_l + mlr_range / 2

            # Forward fill to all bars in the week
            df.loc[week_mask, 'mlr_high'] = mlr_h
            df.loc[week_mask, 'mlr_low'] = mlr_l
            df.loc[week_mask, 'mlr_close'] = mlr_c
            df.loc[week_mask, 'mlr_range'] = mlr_range
            df.loc[week_mask, 'mlr_mid'] = mlr_mid
            df.loc[week_mask, 'mlr_range_pips'] = mlr_range / pip_size

            # Bias
            if mlr_c > mlr_mid:
                df.loc[week_mask, 'bias'] = 'BULLISH'
            elif mlr_c < mlr_mid:
                df.loc[week_mask, 'bias'] = 'BEARISH'
            else:
                df.loc[week_mask, 'bias'] = 'NEUTRAL'

            # Hours since MLR
            mlr_end = week_start + pd.Timedelta(hours=15)
            for idx in df.loc[week_mask].index:
                df.loc[idx, 'hours_since_mlr'] = (idx - mlr_end).total_seconds() / 3600

    # ── Fibonacci targets ──
    df['target_25'] = np.where(
        df['bias'] == 'BULLISH',
        df['mlr_high'] + 0.25 * df['mlr_range'],
        np.where(df['bias'] == 'BEARISH', df['mlr_low'] - 0.25 * df['mlr_range'], np.nan)
    )
    df['target_50'] = np.where(
        df['bias'] == 'BULLISH',
        df['mlr_high'] + 0.50 * df['mlr_range'],
        np.where(df['bias'] == 'BEARISH', df['mlr_low'] - 0.50 * df['mlr_range'], np.nan)
    )
    df['target_100'] = np.where(
        df['bias'] == 'BULLISH',
        df['mlr_high'] + 1.00 * df['mlr_range'],
        np.where(df['bias'] == 'BEARISH', df['mlr_low'] - 1.00 * df['mlr_range'], np.nan)
    )
    df['target_168'] = np.where(
        df['bias'] == 'BULLISH',
        df['mlr_high'] + 1.68 * df['mlr_range'],
        np.where(df['bias'] == 'BEARISH', df['mlr_low'] - 1.68 * df['mlr_range'], np.nan)
    )
    df['kill_switch_132'] = np.where(
        df['bias'] == 'BULLISH',
        df['mlr_low'] - 1.32 * df['mlr_range'],
        np.where(df['bias'] == 'BEARISH', df['mlr_high'] + 1.32 * df['mlr_range'], np.nan)
    )

    # ── Distance features (pips) ──
    df['dist_to_25_pips'] = (df['close'] - df['target_25']).abs() / pip_size
    df['dist_to_50_pips'] = (df['close'] - df['target_50']).abs() / pip_size
    df['dist_to_100_pips'] = (df['close'] - df['target_100']).abs() / pip_size
    df['dist_to_168_pips'] = (df['close'] - df['target_168']).abs() / pip_size
    df['dist_to_132_pips'] = (df['close'] - df['kill_switch_132']).abs() / pip_size
    df['dist_to_mlr_high_pips'] = (df['close'] - df['mlr_high']).abs() / pip_size
    df['dist_to_mlr_low_pips'] = (df['close'] - df['mlr_low']).abs() / pip_size
    df['dist_to_mlr_mid_pips'] = (df['close'] - df['mlr_mid']).abs() / pip_size

    # ── ILM / Regime features ──
    df['regime_ratio'] = np.nan
    df['regime_status'] = 'UNKNOWN'
    df['ilm_state'] = 'MISALIGNED'

    for date in df.index.date:
        day_mask = df.index.date == date
        asian_bars = df.loc[day_mask & (df.index.hour >= 0) & (df.index.hour < 8)]
        london_bars = df.loc[day_mask & (df.index.hour >= 3) & (df.index.hour < 9)]

        if len(asian_bars) > 0 and len(london_bars) > 0:
            ar = (asian_bars['high'].max() - asian_bars['low'].min()) / pip_size
            lr = (london_bars['high'].max() - london_bars['low'].min()) / pip_size
            ratio = lr / ar if ar > 0 else 0

            df.loc[day_mask, 'regime_ratio'] = ratio
            if ratio >= 1.5:
                df.loc[day_mask, 'regime_status'] = 'CONFIRMED'
                df.loc[day_mask, 'ilm_state'] = 'IELM'
            elif ratio >= 1.45:
                df.loc[day_mask, 'regime_status'] = 'CAUTION'
                df.loc[day_mask, 'ilm_state'] = 'DAILY_ILM'
            elif ratio >= 1.0:
                df.loc[day_mask, 'regime_status'] = 'CAUTION'
                df.loc[day_mask, 'ilm_state'] = 'DAILY_ILM'
            else:
                df.loc[day_mask, 'regime_status'] = 'FAILED'
                df.loc[day_mask, 'ilm_state'] = 'MISALIGNED'

    # ── Volatility features ──
    df['rolling_vol_20'] = df['range'].rolling(20).mean()
    df['vol_ratio'] = df['range'] / df['rolling_vol_20'].replace(0, np.nan)
    df['spread_vs_20d_avg'] = df['range'] / df['range'].rolling(480).mean().replace(0, np.nan)

    # ── Consecutive losses (simplified) ──
    df['consecutive_losses'] = 0
    df['prior_session_wr'] = 0.5

    # ── Encode all categorical features as numeric ──
    # Bias: BULLISH=1, BEARISH=-1, NEUTRAL/UNKNOWN=0
    df['bias_encoded'] = np.where(df['bias'] == 'BULLISH', 1,
                                   np.where(df['bias'] == 'BEARISH', -1, 0))

    # Regime status: CONFIRMED=2, CAUTION=1, FAILED=0, UNKNOWN=0
    df['regime_status_encoded'] = np.where(df['regime_status'] == 'CONFIRMED', 2,
                                            np.where(df['regime_status'] == 'CAUTION', 1, 0))

    # ILM state: IELM=3, DAILY_ILM=2, WILM=1, MISALIGNED/UNKNOWN=0
    df['ilm_state_encoded'] = np.where(df['ilm_state'] == 'IELM', 3,
                                        np.where(df['ilm_state'] == 'DAILY_ILM', 2,
                                                  np.where(df['ilm_state'] == 'WILM', 1, 0)))

    # Session encoding
    df['session_encoded'] = np.where((df.index.hour >= 0) & (df.index.hour < 8), 0,  # Asian
                                      np.where((df.index.hour >= 7) & (df.index.hour < 16), 1,  # London
                                                np.where((df.index.hour >= 12) & (df.index.hour < 21), 2, 3)))  # NY / Other

    # ── Fill NaN values ──
    df = df.ffill().fillna(0)

    # ── Drop string columns that the model can't handle ──
    string_cols = df.select_dtypes(include=['object']).columns.tolist()
    if string_cols:
        df = df.drop(columns=string_cols)

    return df


def scan_symbol(symbol: str, guardian: GuardianPipeline, dry_run: bool = False) -> str:
    """
    Scan a single symbol: fetch live data → compute features → Guardian → alert.
    Returns alert string or None.
    """
    logger.info(f"{'='*50}")
    logger.info(f"Scanning {symbol}...")

    # 1. Fetch live candles
    df = fetch_live_candles(symbol)
    if df.empty:
        logger.warning(f"  No data for {symbol}")
        return None

    # 2. Compute features
    df = compute_live_features(df, symbol)
    if df.empty:
        logger.warning(f"  Feature computation failed for {symbol}")
        return None

    # 3. Run Guardian
    alert = guardian.process_candle(df, symbol)

    if alert:
        logger.info(f"  ✅ ALERT for {symbol}!")
        if not dry_run:
            guardian.dispatch_alert(alert, symbol)
        return alert
    else:
        logger.info(f"  — No alert for {symbol} (conditions not met)")
        return None


def run_live_scan(symbols: list[str], interval: int = SCAN_INTERVAL, dry_run: bool = False, once: bool = False):
    """Main live scan loop."""
    logger.info("=" * 60)
    logger.info("🔱 CEREBUS NEURO-SYMBOLIC SCANNER — LIVE MT5")
    logger.info("=" * 60)
    logger.info(f"Symbols: {', '.join(symbols)}")
    logger.info(f"Interval: {interval}s | Dry run: {dry_run}")
    logger.info(f"Model: {MODEL_PATH.name}")
    logger.info("")

    # Initialize Guardian (sends startup message to Telegram)
    config = GuardianConfig()
    guardian = GuardianPipeline(
        model_path=str(MODEL_PATH),
        rag_store_path=str(RAG_STORE_PATH),
        config=config,
    )

    scan_count = 0
    try:
        while True:
            scan_count += 1
            logger.info(f"\n📊 Scan #{scan_count} — {datetime.now(timezone.utc).strftime('%Y-%m-%d %H:%M:%S UTC')}")

            for symbol in symbols:
                try:
                    scan_symbol(symbol, guardian, dry_run)
                except Exception as e:
                    logger.error(f"  Error scanning {symbol}: {e}")

            if once:
                logger.info("\nSingle scan complete. Exiting.")
                break

            logger.info(f"\n⏳ Next scan in {interval}s... (Ctrl+C to stop)")
            time.sleep(interval)

    except KeyboardInterrupt:
        logger.info("\n\n🛑 CEREBUS scanner stopped by user.")
        logger.info(f"Total scans: {scan_count}")


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="CEREBUS Neuro-Symbolic Scanner — Live MT5")
    parser.add_argument("--symbols", nargs="+", default=DEFAULT_SYMBOLS, help="Symbols to scan")
    parser.add_argument("--interval", type=int, default=SCAN_INTERVAL, help="Scan interval in seconds")
    parser.add_argument("--once", action="store_true", help="Single scan and exit")
    parser.add_argument("--dry-run", action="store_true", help="Scan without sending Telegram alerts")
    args = parser.parse_args()

    run_live_scan(args.symbols, args.interval, args.dry_run, args.once)

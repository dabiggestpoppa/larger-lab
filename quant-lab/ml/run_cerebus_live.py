"""
CEREBUS Neuro-Symbolic Scanner — LIVE MT5 Edition
===================================================
Pulls live M15 candle data from MT5, runs BOTH:
  1. Guardian (XGBoost + Orchestrator + RAG)
  2. ST/P90 Engines (Symmetry Trap + P90 Kinetic)
Sends alerts to Telegram. Does NOT execute trades — signals only.

Usage:
    python run_cerebus_live.py                    # Scan EURUSD + BTCUSD (default)
    python run_cerebus_live.py --symbols EURUSD   # Scan specific symbols
    python run_cerebus_live.py --interval 60      # Scan interval in seconds (default: 300)
    python run_cerebus_live.py --once             # Single scan and exit
    python run_cerebus_live.py --dry-run          # Scan without sending Telegram alerts
    python run_cerebus_live.py --engine guardian  # Only XGBoost Guardian
    python run_cerebus_live.py --engine stp90     # Only ST/P90 engines
    python run_cerebus_live.py --engine both      # Both (default)
"""
import os
import sys
import time
import argparse
import logging
from pathlib import Path
from datetime import datetime, timezone, timedelta

# Load .env
env_path = Path(__file__).resolve().parent.parent.parent / ".env"
if env_path.exists():
    import re
    content = env_path.read_text(encoding="utf-8")
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

# ST/P90 Engine Imports
sys.path.insert(0, str(Path(__file__).parent.parent / "engines"))
from symmetry_trap import SymmetryTrapEngine, Bar, TradeDirection
from p90_engine import P90Engine

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(name)s] %(levelname)s: %(message)s",
    handlers=[logging.StreamHandler(sys.stdout)],
)
logger = logging.getLogger("cerebus.live")

DEFAULT_SYMBOLS = ["EURUSD", "BTCUSD"]
SCAN_INTERVAL = 300
LOOKBACK_BARS = 500

MODEL_PATH = Path(__file__).parent / "models" / "regime_classifier_full.pkl"
RAG_STORE_PATH = Path(__file__).parent / "data" / "rag_chroma"
EST = timezone(timedelta(hours=-5))


def get_pip_size(symbol):
    s = symbol.upper()
    if "JPY" in s: return 0.01
    if "XAU" in s: return 0.1
    if "XAG" in s: return 0.001
    if any(x in s for x in ["BTC","ETH","US500","NAS100","DE30","FR40","HK50","US30"]): return 1.0
    return 0.0001


def fetch_live_candles(symbol, num_bars=LOOKBACK_BARS):
    if not mt5.initialize():
        logger.error("MT5 init failed")
        return pd.DataFrame()
    try:
        rates = mt5.copy_rates_from_pos(symbol, mt5.TIMEFRAME_M15, 0, num_bars)
        if rates is None or len(rates) == 0:
            rates = mt5.copy_rates_from_pos(f"{symbol}.PRO", mt5.TIMEFRAME_M15, 0, num_bars)
        if rates is None or len(rates) == 0:
            logger.warning(f"No data for {symbol}")
            return pd.DataFrame()
        df = pd.DataFrame(rates)
        df['time'] = pd.to_datetime(df['time'], unit='s', utc=True)
        df = df.set_index('time').rename(columns={'tick_volume': 'volume'})
        df = df[['open','high','low','close','volume']]
        logger.info(f"Fetched {len(df)} M15 candles for {symbol}")
        return df
    except Exception as e:
        logger.error(f"Error fetching {symbol}: {e}")
        return pd.DataFrame()


def compute_live_features(df, symbol):
    if df.empty or len(df) < 50: return pd.DataFrame()
    ps = get_pip_size(symbol)
    df = df.copy()
    df['body'] = df['close'] - df['open']
    df['range'] = df['high'] - df['low']
    df['body_ratio'] = df['body'] / df['range'].replace(0, np.nan)
    df['price_range_from_open'] = df['close'] - df['open']
    df['hour_est'] = ((df.index.hour - 5) % 24)
    df['day_of_week'] = df.index.dayofweek
    df['is_monday'] = (df.index.dayofweek == 0).astype(int)
    df['is_friday'] = (df.index.dayofweek == 4).astype(int)
    df['is_wednesday'] = (df.index.dayofweek == 2).astype(int)
    df['is_wednesday_pm'] = ((df.index.dayofweek == 2) & (df.index.hour >= 12)).astype(int)
    df['minutes_to_12pm_est'] = ((12 - df['hour_est']) % 24) * 60
    df['is_asian'] = ((df.index.hour >= 0) & (df.index.hour < 8)).astype(int)
    df['is_london'] = ((df.index.hour >= 7) & (df.index.hour < 16)).astype(int)
    df['is_ny'] = ((df.index.hour >= 12) & (df.index.hour < 21)).astype(int)

    # Asian Range
    for date in df.index.date:
        dm = df.index.date == date
        am = dm & (df.index.hour >= 0) & (df.index.hour < 8)
        ab = df.loc[am]
        if len(ab) > 0:
            df.loc[dm, 'asian_high'] = ab['high'].max()
            df.loc[dm, 'asian_low'] = ab['low'].min()
            df.loc[dm, 'asian_range_pips'] = (ab['high'].max() - ab['low'].min()) / ps

    # MLR
    df['mlr_high'] = np.nan; df['mlr_low'] = np.nan; df['mlr_close'] = np.nan
    df['mlr_range'] = np.nan; df['mlr_mid'] = np.nan; df['mlr_range_pips'] = np.nan
    df['hours_since_mlr'] = np.nan
    for ws in pd.date_range(df.index.min().normalize(), df.index.max().normalize(), freq='W-MON'):
        wm = (df.index >= ws) & (df.index < ws + pd.Timedelta(days=7))
        mm = wm & (df.index.dayofweek == 0) & (df.index.hour >= 7) & (df.index.hour < 15)
        mb = df.loc[mm]
        if len(mb) > 0:
            mh, ml = mb['high'].max(), mb['low'].min()
            mc = mb['close'].iloc[-1]
            mr = mh - ml
            df.loc[wm, 'mlr_high'] = mh; df.loc[wm, 'mlr_low'] = ml
            df.loc[wm, 'mlr_close'] = mc; df.loc[wm, 'mlr_range'] = mr
            df.loc[wm, 'mlr_mid'] = ml + mr/2; df.loc[wm, 'mlr_range_pips'] = mr/ps
            bias = np.where(mc > ml+mr/2, 'BULLISH', np.where(mc < ml+mr/2, 'BEARISH', 'NEUTRAL'))
            df.loc[wm, 'bias'] = bias
            me = ws + pd.Timedelta(hours=15)
            for idx in df.loc[wm].index:
                df.loc[idx, 'hours_since_mlr'] = (idx - me).total_seconds() / 3600

    # Fib targets
    df['target_25'] = np.where(df['bias']=='BULLISH', df['mlr_high']+0.25*df['mlr_range'],
                                np.where(df['bias']=='BEARISH', df['mlr_low']-0.25*df['mlr_range'], np.nan))
    df['target_50'] = np.where(df['bias']=='BULLISH', df['mlr_high']+0.50*df['mlr_range'],
                                np.where(df['bias']=='BEARISH', df['mlr_low']-0.50*df['mlr_range'], np.nan))
    df['target_100'] = np.where(df['bias']=='BULLISH', df['mlr_high']+1.00*df['mlr_range'],
                                 np.where(df['bias']=='BEARISH', df['mlr_low']-1.00*df['mlr_range'], np.nan))
    df['target_168'] = np.where(df['bias']=='BULLISH', df['mlr_high']+1.68*df['mlr_range'],
                                  np.where(df['bias']=='BEARISH', df['mlr_low']-1.68*df['mlr_range'], np.nan))
    df['kill_switch_132'] = np.where(df['bias']=='BULLISH', df['mlr_low']-1.32*df['mlr_range'],
                                      np.where(df['bias']=='BEARISH', df['mlr_high']+1.32*df['mlr_range'], np.nan))
    df['dist_to_25_pips'] = (df['close']-df['target_25']).abs()/ps
    df['dist_to_50_pips'] = (df['close']-df['target_50']).abs()/ps
    df['dist_to_100_pips'] = (df['close']-df['target_100']).abs()/ps
    df['dist_to_168_pips'] = (df['close']-df['target_168']).abs()/ps
    df['dist_to_132_pips'] = (df['close']-df['kill_switch_132']).abs()/ps
    df['dist_to_mlr_high_pips'] = (df['close']-df['mlr_high']).abs()/ps
    df['dist_to_mlr_low_pips'] = (df['close']-df['mlr_low']).abs()/ps
    df['dist_to_mlr_mid_pips'] = (df['close']-df['mlr_mid']).abs()/ps

    # ILM/Regime
    df['regime_ratio'] = np.nan; df['regime_status'] = 'UNKNOWN'; df['ilm_state'] = 'MISALIGNED'
    for date in df.index.date:
        dm = df.index.date == date
        ab = df.loc[dm & (df.index.hour>=0) & (df.index.hour<8)]
        lb = df.loc[dm & (df.index.hour>=3) & (df.index.hour<9)]
        if len(ab)>0 and len(lb)>0:
            ar = (ab['high'].max()-ab['low'].min())/ps
            lr = (lb['high'].max()-lb['low'].min())/ps
            ratio = lr/ar if ar>0 else 0
            df.loc[dm,'regime_ratio'] = ratio
            if ratio >= 1.5: df.loc[dm,'regime_status']='CONFIRMED'; df.loc[dm,'ilm_state']='IELM'
            elif ratio >= 1.0: df.loc[dm,'regime_status']='CAUTION'; df.loc[dm,'ilm_state']='DAILY_ILM'
            else: df.loc[dm,'regime_status']='FAILED'; df.loc[dm,'ilm_state']='MISALIGNED'

    df['rolling_vol_20'] = df['range'].rolling(20).mean()
    df['vol_ratio'] = df['range']/df['rolling_vol_20'].replace(0,np.nan)
    df['spread_vs_20d_avg'] = df['range']/df['range'].rolling(480).mean().replace(0,np.nan)
    df['consecutive_losses'] = 0; df['prior_session_wr'] = 0.5
    df['bias_encoded'] = np.where(df['bias']=='BULLISH', 1, np.where(df['bias']=='BEARISH', -1, 0))
    df['regime_status_encoded'] = np.where(df['regime_status']=='CONFIRMED', 2, np.where(df['regime_status']=='CAUTION', 1, 0))
    df['ilm_state_encoded'] = np.where(df['ilm_state']=='IELM', 3, np.where(df['ilm_state']=='DAILY_ILM', 2, np.where(df['ilm_state']=='WILM', 1, 0)))
    df['session_encoded'] = np.where((df.index.hour>=0)&(df.index.hour<8), 0, np.where((df.index.hour>=7)&(df.index.hour<16), 1, np.where((df.index.hour>=12)&(df.index.hour<21), 2, 3)))
    df = df.ffill().fillna(0)
    sc = df.select_dtypes(include=['object']).columns.tolist()
    if sc: df = df.drop(columns=sc)
    return df


def scan_with_guardian(symbol, df, guardian, dry_run):
    try:
        alert = guardian.process_candle(df, symbol)
        if alert:
            logger.info(f"  ✅ GUARDIAN ALERT for {symbol}!")
            if not dry_run: guardian.dispatch_alert(alert, symbol)
            return alert
    except Exception as e:
        logger.error(f"  Guardian error: {e}")
    return None


def scan_with_st_p90(symbol, df, dry_run):
    """Run ST + P90 engines with convergence detection."""
    signals = []
    ps = get_pip_size(symbol)
    try:
        bars = [Bar(timestamp=idx, open=float(r['open']), high=float(r['high']), low=float(r['low']), close=float(r['close'])) for idx, r in df.iterrows()]
        if len(bars) < 50: return signals

        # Run both engines on the same bar stream
        st = SymmetryTrapEngine()
        p90 = P90Engine()
        st_signal = None
        p90_signal = None

        for bar in bars:
            if st_signal is None:
                st_result = st.process_bar(bar)
                if st_result:
                    st_signal = st_result
            if p90_signal is None:
                p90_result = p90.process_bar(bar)
                if p90_result:
                    p90_signal = p90_result
            if st_signal and p90_signal:
                break

        # Check convergence: both engines fired in same direction
        convergence = False
        if st_signal and p90_signal:
            st_dir = st_signal.direction
            p90_dir = p90_signal.direction
            # Both LONG or both SHORT
            if st_dir == p90_dir and st_dir != TradeDirection.FLAT:
                convergence = True
                logger.info(f"  🔥 CONVERGENCE: {symbol} both engines {st_dir.name}")

        # Build signals
        if st_signal:
            d = "LONG" if st_signal.direction == TradeDirection.LONG else "SHORT"
            sl_p = abs(st_signal.entry_price - st_signal.sl_price)/ps
            tp_p = abs(st_signal.tp_price - st_signal.entry_price)/ps
            conv_tag = " 🔥CONV" if convergence else ""
            msg = f"⚡ ST SIGNAL: {symbol} {d}{conv_tag}\n  Entry: {st_signal.entry_price:.5f}\n  SL: {st_signal.sl_price:.5f} ({sl_p:.1f}p)\n  TP: {st_signal.tp_price:.5f} ({tp_p:.1f}p)"
            logger.info(f"  {msg}")
            signals.append({'engine':'ST','symbol':symbol,'direction':d,'entry':st_signal.entry_price,'sl':st_signal.sl_price,'tp':st_signal.tp_price,'convergence':convergence,'message':msg})

        if p90_signal:
            d = "LONG" if p90_signal.direction == TradeDirection.LONG else "SHORT"
            sl_p = abs(p90_signal.entry_price - p90_signal.sl_price)/ps
            tp_p = abs(p90_signal.tp_price - p90_signal.entry_price)/ps
            conv_tag = " 🔥CONV" if convergence else ""
            msg = f"🎯 P90 SIGNAL: {symbol} {d}{conv_tag}\n  Entry: {p90_signal.entry_price:.5f}\n  SL: {p90_signal.sl_price:.5f} ({sl_p:.1f}p)\n  TP: {p90_signal.tp_price:.5f} ({tp_p:.1f}p)"
            logger.info(f"  {msg}")
            signals.append({'engine':'P90','symbol':symbol,'direction':d,'entry':p90_signal.entry_price,'sl':p90_signal.sl_price,'tp':p90_signal.tp_price,'convergence':convergence,'message':msg})

        if signals and not dry_run:
            import requests
            cfg = GuardianConfig()
            token = cfg.TELEGRAM_BOT_TOKEN
            chat_id = cfg.TELEGRAM_CHAT_ID
            if not chat_id:
                r = requests.get(f"https://api.telegram.org/bot{token}/getUpdates?limit=1&timeout=5", timeout=10)
                d = r.json()
                if d.get("ok") and d.get("result"):
                    chat_id = str(d["result"][0]["message"]["chat"]["id"])
            if chat_id:
                for sig in signals:
                    requests.post(f"https://api.telegram.org/bot{token}/sendMessage", json={"chat_id":chat_id,"text":sig['message'],"parse_mode":"HTML"}, timeout=15)
                    logger.info(f"  📨 {sig['engine']} signal sent to Telegram")
    except Exception as e:
        logger.error(f"  ST/P90 error: {e}")
    return signals


def scan_symbol(symbol, guardian, engine, dry_run):
    logger.info(f"{'='*50}\nScanning {symbol}...")
    df = fetch_live_candles(symbol)
    if df.empty: return

    if engine in ('guardian','both'):
        df_feat = compute_live_features(df, symbol)
        if not df_feat.empty:
            scan_with_guardian(symbol, df_feat, guardian, dry_run)
        else:
            logger.warning(f"  Feature computation failed for {symbol}")

    if engine in ('stp90','both'):
        scan_with_st_p90(symbol, df, dry_run)


def run_live_scan(symbols, interval, dry_run, once, engine):
    logger.info("="*60+"\n🔱 CEREBUS NEURO-SYMBOLIC SCANNER — LIVE MT5\n"+"="*60)
    logger.info(f"Symbols: {', '.join(symbols)} | Engine: {engine} | Interval: {interval}s")
    config = GuardianConfig()
    guardian = GuardianPipeline(model_path=str(MODEL_PATH), rag_store_path=str(RAG_STORE_PATH), config=config)
    scan_count = 0
    try:
        while True:
            scan_count += 1
            logger.info(f"\n📊 Scan #{scan_count} — {datetime.now(timezone.utc).strftime('%Y-%m-%d %H:%M:%S UTC')}")
            for sym in symbols:
                try: scan_symbol(sym, guardian, engine, dry_run)
                except Exception as e: logger.error(f"  Error: {e}")
            if once:
                logger.info("\nSingle scan complete."); break
            logger.info(f"\n⏳ Next scan in {interval}s... (Ctrl+C to stop)")
            time.sleep(interval)
    except KeyboardInterrupt:
        logger.info(f"\n🛑 Stopped. Total scans: {scan_count}")


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="CEREBUS Live MT5 Scanner")
    parser.add_argument("--symbols", nargs="+", default=DEFAULT_SYMBOLS)
    parser.add_argument("--interval", type=int, default=SCAN_INTERVAL)
    parser.add_argument("--once", action="store_true")
    parser.add_argument("--dry-run", action="store_true")
    parser.add_argument("--engine", choices=["guardian","stp90","both"], default="both")
    args = parser.parse_args()
    run_live_scan(args.symbols, args.interval, args.dry_run, args.once, args.engine)
